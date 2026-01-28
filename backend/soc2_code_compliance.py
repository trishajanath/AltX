"""
SOC2 Code Compliance Integration for AI-Generated Projects

This module integrates SOC2 compliance verification into the AI code generation workflow.
It ensures all generated codebases follow SOC2 Trust Services Criteria and produces
detailed audit-ready documentation for each project.

Features:
- Real-time compliance verification during code generation
- Gap identification and automatic remediation
- Audit-ready documentation generation
- Control implementation verification
- Evidence collection for SOC2 audits

Integration Points:
- PureAIGenerator: Validates generated code against SOC2 requirements
- ValidatedAIGenerator: Adds compliance layer to validation
- AIEnhancedGenerator: Ensures templates meet compliance standards
"""

from __future__ import annotations

import json
import hashlib
import os
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from enum import Enum
import logging

# Import SOC2 compliance components
from soc2_rag_database import SOC2RAGDatabase, TrustServiceCriteria
from soc2_compliance_agent import SOC2ComplianceAgent, ComplianceLevel, ComplianceAssessment
from soc2_compliance_verifier import SOC2ComplianceVerifier, VerificationStatus
from soc2_control_implementation import (
    CC6_AccessControls,
    CC8_ChangeManagement,
    AuditLogger,
    EncryptionAlgorithm
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CodeComplianceLevel(Enum):
    """Compliance levels for generated code"""
    FULLY_COMPLIANT = "fully_compliant"
    MOSTLY_COMPLIANT = "mostly_compliant"
    PARTIALLY_COMPLIANT = "partially_compliant"
    NON_COMPLIANT = "non_compliant"
    NOT_ASSESSED = "not_assessed"


class SecurityCategory(Enum):
    """Security categories for code analysis"""
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    DATA_PROTECTION = "data_protection"
    INPUT_VALIDATION = "input_validation"
    ERROR_HANDLING = "error_handling"
    LOGGING = "logging"
    SESSION_MANAGEMENT = "session_management"
    ENCRYPTION = "encryption"
    SECURE_COMMUNICATION = "secure_communication"
    CODE_QUALITY = "code_quality"


@dataclass
class CodeSecurityFinding:
    """Individual security finding in generated code"""
    finding_id: str
    category: SecurityCategory
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    file_path: str
    line_number: Optional[int]
    code_snippet: Optional[str]
    description: str
    remediation: str
    soc2_control: str  # Related SOC2 control (e.g., CC6.1)
    auto_fixed: bool = False
    fix_applied: Optional[str] = None


@dataclass
class ComplianceGap:
    """Gap identified in code compliance"""
    gap_id: str
    control_code: str
    control_name: str
    description: str
    severity: str
    affected_files: List[str]
    remediation_steps: List[str]
    timeline_days: int
    status: str = "identified"  # identified, in_progress, remediated, verified
    evidence: Optional[str] = None


@dataclass
class CodeComplianceResult:
    """Complete compliance result for generated code"""
    project_name: str
    assessment_id: str
    assessment_date: str
    compliance_level: CodeComplianceLevel
    compliance_score: float  # 0-100
    
    # Findings
    security_findings: List[CodeSecurityFinding] = field(default_factory=list)
    compliance_gaps: List[ComplianceGap] = field(default_factory=list)
    
    # Controls assessed
    controls_assessed: Dict[str, str] = field(default_factory=dict)  # control_code -> status
    
    # Statistics
    total_files_scanned: int = 0
    files_with_issues: int = 0
    critical_findings: int = 0
    high_findings: int = 0
    medium_findings: int = 0
    low_findings: int = 0
    
    # Fixes applied
    auto_fixes_applied: int = 0
    manual_fixes_required: int = 0
    
    # Audit trail
    audit_log: List[Dict] = field(default_factory=list)
    evidence_collected: List[str] = field(default_factory=list)


@dataclass
class AuditDocumentation:
    """Audit-ready documentation for SOC2 compliance"""
    project_name: str
    document_id: str
    generated_date: str
    
    # Executive summary
    executive_summary: str
    compliance_status: str
    risk_rating: str
    
    # Control mappings
    control_implementations: Dict[str, Dict] = field(default_factory=dict)
    
    # Evidence
    evidence_references: List[Dict] = field(default_factory=list)
    
    # Findings and remediation
    findings_summary: Dict = field(default_factory=dict)
    remediation_plan: List[Dict] = field(default_factory=list)
    
    # Sign-off
    assessor_signature: Optional[str] = None
    assessment_methodology: str = ""


class SOC2CodeComplianceEngine:
    """
    Main engine for SOC2 compliance verification of generated code.
    
    Integrates with the AI code generation pipeline to:
    1. Scan generated code for security issues
    2. Map findings to SOC2 controls
    3. Auto-fix common issues
    4. Generate audit-ready documentation
    """
    
    def __init__(self):
        """Initialize the compliance engine"""
        self.rag_database = SOC2RAGDatabase()
        self.compliance_agent = SOC2ComplianceAgent()
        self.verifier = SOC2ComplianceVerifier()
        self.audit_logger = AuditLogger()
        
        # Security patterns to check
        self.security_patterns = self._initialize_security_patterns()
        
        # Auto-fix mappings
        self.auto_fixes = self._initialize_auto_fixes()
        
        logger.info("✅ SOC2 Code Compliance Engine initialized")
    
    def _initialize_security_patterns(self) -> Dict[SecurityCategory, List[Dict]]:
        """Initialize security patterns to detect in code"""
        return {
            SecurityCategory.AUTHENTICATION: [
                {
                    "pattern": r"password\s*=\s*['\"][^'\"]+['\"]",
                    "severity": "CRITICAL",
                    "description": "Hardcoded password detected",
                    "control": "CC6.1",
                    "remediation": "Use environment variables or secure secret management"
                },
                {
                    "pattern": r"api[_-]?key\s*=\s*['\"][^'\"]+['\"]",
                    "severity": "CRITICAL",
                    "description": "Hardcoded API key detected",
                    "control": "CC6.1",
                    "remediation": "Store API keys in environment variables"
                },
                {
                    "pattern": r"secret\s*=\s*['\"][^'\"]+['\"]",
                    "severity": "HIGH",
                    "description": "Hardcoded secret detected",
                    "control": "CC6.1",
                    "remediation": "Use secure secret management"
                },
            ],
            SecurityCategory.INPUT_VALIDATION: [
                {
                    "pattern": r"eval\s*\(",
                    "severity": "CRITICAL",
                    "description": "Use of eval() function - potential code injection",
                    "control": "CC6.6",
                    "remediation": "Avoid eval() and use safe alternatives"
                },
                {
                    "pattern": r"exec\s*\(",
                    "severity": "CRITICAL",
                    "description": "Use of exec() function - potential code injection",
                    "control": "CC6.6",
                    "remediation": "Avoid exec() and use safe alternatives"
                },
                {
                    "pattern": r"dangerouslySetInnerHTML",
                    "severity": "HIGH",
                    "description": "Use of dangerouslySetInnerHTML - XSS risk",
                    "control": "CC6.6",
                    "remediation": "Sanitize HTML content before rendering"
                },
                {
                    "pattern": r"innerHTML\s*=",
                    "severity": "HIGH",
                    "description": "Direct innerHTML assignment - XSS risk",
                    "control": "CC6.6",
                    "remediation": "Use textContent or sanitize input"
                },
            ],
            SecurityCategory.DATA_PROTECTION: [
                {
                    "pattern": r"SELECT\s+\*\s+FROM.*\+.*\+",
                    "severity": "CRITICAL",
                    "description": "Potential SQL injection - string concatenation in query",
                    "control": "CC6.1",
                    "remediation": "Use parameterized queries"
                },
                {
                    "pattern": r"localStorage\.setItem\s*\([^)]*password",
                    "severity": "HIGH",
                    "description": "Storing password in localStorage",
                    "control": "CC6.1",
                    "remediation": "Never store passwords in browser storage"
                },
                {
                    "pattern": r"console\.log\s*\([^)]*password",
                    "severity": "MEDIUM",
                    "description": "Logging sensitive data",
                    "control": "CC6.7",
                    "remediation": "Remove sensitive data from logs"
                },
            ],
            SecurityCategory.ERROR_HANDLING: [
                {
                    "pattern": r"except:\s*pass",
                    "severity": "MEDIUM",
                    "description": "Silent exception handling",
                    "control": "CC7.2",
                    "remediation": "Log exceptions properly"
                },
                {
                    "pattern": r"catch\s*\([^)]*\)\s*\{\s*\}",
                    "severity": "MEDIUM",
                    "description": "Empty catch block",
                    "control": "CC7.2",
                    "remediation": "Handle errors appropriately"
                },
            ],
            SecurityCategory.LOGGING: [
                {
                    "pattern": r"print\s*\([^)]*(?:password|secret|token|key)",
                    "severity": "HIGH",
                    "description": "Printing sensitive data",
                    "control": "CC7.2",
                    "remediation": "Never print sensitive information"
                },
            ],
            SecurityCategory.SECURE_COMMUNICATION: [
                {
                    "pattern": r"http://(?!localhost|127\.0\.0\.1)",
                    "severity": "HIGH",
                    "description": "Non-HTTPS URL detected",
                    "control": "CC6.7",
                    "remediation": "Use HTTPS for all external communications"
                },
                {
                    "pattern": r"verify\s*=\s*False",
                    "severity": "CRITICAL",
                    "description": "SSL verification disabled",
                    "control": "CC6.7",
                    "remediation": "Never disable SSL verification"
                },
            ],
            SecurityCategory.SESSION_MANAGEMENT: [
                {
                    "pattern": r"session\.permanent\s*=\s*True",
                    "severity": "MEDIUM",
                    "description": "Permanent session enabled",
                    "control": "CC6.1",
                    "remediation": "Set appropriate session timeouts"
                },
            ],
            SecurityCategory.CODE_QUALITY: [
                {
                    "pattern": r"TODO|FIXME|HACK|XXX",
                    "severity": "LOW",
                    "description": "Development marker found",
                    "control": "CC8.1",
                    "remediation": "Review and resolve before deployment"
                },
                {
                    "pattern": r"#\s*debug",
                    "severity": "LOW",
                    "description": "Debug code detected",
                    "control": "CC8.1",
                    "remediation": "Remove debug code before deployment"
                },
            ],
        }
    
    def _initialize_auto_fixes(self) -> Dict[str, str]:
        """Initialize auto-fix patterns"""
        return {
            # Replace hardcoded secrets with env vars
            r"password\s*=\s*['\"]([^'\"]+)['\"]": 'password = os.getenv("DB_PASSWORD", "")',
            r"api_key\s*=\s*['\"]([^'\"]+)['\"]": 'api_key = os.getenv("API_KEY", "")',
            r"secret\s*=\s*['\"]([^'\"]+)['\"]": 'secret = os.getenv("SECRET_KEY", "")',
            
            # Fix HTTP to HTTPS
            r"http://((?!localhost|127\.0\.0\.1)[^\s\"\']+)": r"https://\1",
            
            # Add SSL verification
            r"verify\s*=\s*False": "verify=True",
            
            # Fix empty exception handlers
            r"except:\s*pass": "except Exception as e:\n        logger.error(f'Error: {e}')",
            
            # Add proper error handling for fetch
            r"fetch\(([^)]+)\)\s*\.then": r"fetch(\1).then(response => { if (!response.ok) throw new Error('Network response was not ok'); return response; }).then",
        }
    
    async def verify_generated_code(
        self,
        project_name: str,
        files_content: Dict[str, str],
        auto_fix: bool = True
    ) -> CodeComplianceResult:
        """
        Verify generated code against SOC2 requirements.
        
        Args:
            project_name: Name of the project being generated
            files_content: Dict of file_path -> content
            auto_fix: Whether to automatically fix identified issues
            
        Returns:
            CodeComplianceResult with findings and fixes
        """
        import re
        
        logger.info(f"🔍 Starting SOC2 compliance verification for: {project_name}")
        
        # Initialize result
        result = CodeComplianceResult(
            project_name=project_name,
            assessment_id=self._generate_assessment_id(),
            assessment_date=datetime.now().isoformat(),
            compliance_level=CodeComplianceLevel.NOT_ASSESSED,
            compliance_score=0.0,
            total_files_scanned=len(files_content)
        )
        
        # Log the assessment start
        self.audit_logger.log_event(
            event_type="soc2_assessment_started",
            user_id="system",
            resource=project_name,
            action="compliance_scan",
            result="started",
            details={"project": project_name, "files": len(files_content)}
        )
        
        fixed_files = {}
        
        # Scan each file
        for file_path, content in files_content.items():
            file_findings = []
            fixed_content = content
            
            # Skip binary files
            if self._is_binary_file(file_path):
                continue
            
            # Check against all security patterns
            for category, patterns in self.security_patterns.items():
                for pattern_def in patterns:
                    pattern = pattern_def["pattern"]
                    matches = list(re.finditer(pattern, content, re.IGNORECASE))
                    
                    for match in matches:
                        # Calculate line number
                        line_number = content[:match.start()].count('\n') + 1
                        
                        # Create finding
                        finding = CodeSecurityFinding(
                            finding_id=self._generate_finding_id(),
                            category=category,
                            severity=pattern_def["severity"],
                            file_path=file_path,
                            line_number=line_number,
                            code_snippet=match.group(0)[:100],
                            description=pattern_def["description"],
                            remediation=pattern_def["remediation"],
                            soc2_control=pattern_def["control"]
                        )
                        
                        # Try auto-fix if enabled
                        if auto_fix and pattern in self.auto_fixes:
                            fix = self.auto_fixes[pattern]
                            fixed_content = re.sub(pattern, fix, fixed_content, flags=re.IGNORECASE)
                            finding.auto_fixed = True
                            finding.fix_applied = fix
                            result.auto_fixes_applied += 1
                        else:
                            result.manual_fixes_required += 1
                        
                        file_findings.append(finding)
                        result.security_findings.append(finding)
                        
                        # Count by severity
                        if pattern_def["severity"] == "CRITICAL":
                            result.critical_findings += 1
                        elif pattern_def["severity"] == "HIGH":
                            result.high_findings += 1
                        elif pattern_def["severity"] == "MEDIUM":
                            result.medium_findings += 1
                        else:
                            result.low_findings += 1
            
            if file_findings:
                result.files_with_issues += 1
            
            # Store fixed content
            fixed_files[file_path] = fixed_content
            
            # Add compliance controls if missing
            fixed_files[file_path] = self._inject_compliance_controls(
                file_path, fixed_content
            )
        
        # Map findings to compliance gaps
        result.compliance_gaps = self._map_findings_to_gaps(result.security_findings)
        
        # Assess SOC2 controls
        result.controls_assessed = self._assess_soc2_controls(files_content)
        
        # Calculate compliance score
        result.compliance_score = self._calculate_compliance_score(result)
        result.compliance_level = self._determine_compliance_level(result.compliance_score)
        
        # Log completion
        self.audit_logger.log_event(
            event_type="soc2_assessment_completed",
            user_id="system",
            resource=project_name,
            action="compliance_scan",
            result="completed",
            details={
                "project": project_name,
                "score": result.compliance_score,
                "findings": len(result.security_findings),
                "auto_fixes": result.auto_fixes_applied
            }
        )
        
        logger.info(f"✅ Compliance verification complete. Score: {result.compliance_score:.1f}%")
        
        return result, fixed_files
    
    def _inject_compliance_controls(self, file_path: str, content: str) -> str:
        """Inject compliance controls into code"""
        
        # Add security headers for Python web files
        if file_path.endswith('.py') and 'fastapi' in content.lower():
            if 'SECURITY_HEADERS' not in content:
                security_headers = '''
# SOC2 CC6.7: Security Headers for HTTP responses
SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "Content-Security-Policy": "default-src 'self'",
    "Cache-Control": "no-store, no-cache, must-revalidate"
}

'''
                # Insert after imports
                import_end = content.rfind('import ')
                if import_end != -1:
                    next_newline = content.find('\n', import_end)
                    content = content[:next_newline+1] + security_headers + content[next_newline+1:]
        
        # Add input validation for API endpoints
        if 'def ' in content and ('@app.' in content or '@router.' in content):
            if 'InputValidator' not in content:
                content = self._add_input_validation_comment(content)
        
        # Add logging for audit trail (CC7.2)
        if file_path.endswith('.py') and 'logging' not in content:
            logging_setup = '''
# SOC2 CC7.2: Audit Logging Setup
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

'''
            content = logging_setup + content
        
        return content
    
    def _add_input_validation_comment(self, content: str) -> str:
        """Add input validation reminder comments"""
        comment = "\n# SOC2 CC6.6: Input validation required - validate all user inputs\n"
        return comment + content
    
    def _map_findings_to_gaps(
        self, 
        findings: List[CodeSecurityFinding]
    ) -> List[ComplianceGap]:
        """Map security findings to SOC2 compliance gaps"""
        gaps_by_control = {}
        
        for finding in findings:
            if finding.auto_fixed:
                continue  # Skip already fixed issues
            
            control = finding.soc2_control
            if control not in gaps_by_control:
                # Get control details from RAG database
                control_req = self.rag_database.get_control(control)
                
                gaps_by_control[control] = ComplianceGap(
                    gap_id=self._generate_gap_id(),
                    control_code=control,
                    control_name=control_req.name if control_req else control,
                    description=f"Security findings related to {control}",
                    severity="HIGH" if finding.severity in ["CRITICAL", "HIGH"] else "MEDIUM",
                    affected_files=[],
                    remediation_steps=[],
                    timeline_days=7 if finding.severity == "CRITICAL" else 30
                )
            
            # Add file if not already present
            if finding.file_path not in gaps_by_control[control].affected_files:
                gaps_by_control[control].affected_files.append(finding.file_path)
            
            # Add remediation step
            if finding.remediation not in gaps_by_control[control].remediation_steps:
                gaps_by_control[control].remediation_steps.append(finding.remediation)
        
        return list(gaps_by_control.values())
    
    def _assess_soc2_controls(self, files_content: Dict[str, str]) -> Dict[str, str]:
        """Assess which SOC2 controls are implemented"""
        controls = {}
        all_content = "\n".join(files_content.values()).lower()
        
        # CC1.1 - Control Environment
        if "code of conduct" in all_content or "ethics" in all_content:
            controls["CC1.1"] = "IMPLEMENTED"
        else:
            controls["CC1.1"] = "NOT_ASSESSED"
        
        # CC6.1 - Logical and Physical Access
        if any(x in all_content for x in ["authentication", "login", "jwt", "oauth", "password"]):
            controls["CC6.1"] = "IMPLEMENTED"
        else:
            controls["CC6.1"] = "PARTIAL"
        
        # CC6.6 - Input Validation
        if any(x in all_content for x in ["validate", "sanitize", "pydantic", "schema"]):
            controls["CC6.6"] = "IMPLEMENTED"
        else:
            controls["CC6.6"] = "PARTIAL"
        
        # CC6.7 - Encryption
        if any(x in all_content for x in ["https", "ssl", "tls", "encrypt", "bcrypt", "hash"]):
            controls["CC6.7"] = "IMPLEMENTED"
        else:
            controls["CC6.7"] = "PARTIAL"
        
        # CC7.2 - Monitoring
        if any(x in all_content for x in ["logging", "logger", "audit", "monitor"]):
            controls["CC7.2"] = "IMPLEMENTED"
        else:
            controls["CC7.2"] = "PARTIAL"
        
        # CC8.1 - Change Management
        if any(x in all_content for x in [".git", "version", "changelog"]):
            controls["CC8.1"] = "IMPLEMENTED"
        else:
            controls["CC8.1"] = "PARTIAL"
        
        return controls
    
    def _calculate_compliance_score(self, result: CodeComplianceResult) -> float:
        """Calculate overall compliance score"""
        # Base score starts at 100
        score = 100.0
        
        # Deduct for findings
        score -= result.critical_findings * 15
        score -= result.high_findings * 8
        score -= result.medium_findings * 3
        score -= result.low_findings * 1
        
        # Add back for auto-fixes
        score += result.auto_fixes_applied * 5
        
        # Ensure score is between 0 and 100
        return max(0, min(100, score))
    
    def _determine_compliance_level(self, score: float) -> CodeComplianceLevel:
        """Determine compliance level from score"""
        if score >= 90:
            return CodeComplianceLevel.FULLY_COMPLIANT
        elif score >= 75:
            return CodeComplianceLevel.MOSTLY_COMPLIANT
        elif score >= 50:
            return CodeComplianceLevel.PARTIALLY_COMPLIANT
        else:
            return CodeComplianceLevel.NON_COMPLIANT
    
    def _generate_assessment_id(self) -> str:
        """Generate unique assessment ID"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"SOC2-ASM-{timestamp}-{hashlib.md5(timestamp.encode()).hexdigest()[:6]}"
    
    def _generate_finding_id(self) -> str:
        """Generate unique finding ID"""
        import uuid
        return f"FND-{uuid.uuid4().hex[:8].upper()}"
    
    def _generate_gap_id(self) -> str:
        """Generate unique gap ID"""
        import uuid
        return f"GAP-{uuid.uuid4().hex[:8].upper()}"
    
    def _is_binary_file(self, file_path: str) -> bool:
        """Check if file is binary"""
        binary_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.ico', '.pdf', '.zip', '.tar', '.gz'}
        return Path(file_path).suffix.lower() in binary_extensions
    
    def generate_audit_documentation(
        self,
        result: CodeComplianceResult,
        include_remediation_plan: bool = True
    ) -> AuditDocumentation:
        """
        Generate comprehensive audit-ready documentation for SOC2 compliance.
        
        This produces documentation that can be directly used for:
        - SOC2 Type I and Type II audits
        - Internal compliance reviews
        - Security assessments
        - Client due diligence requests
        """
        
        # Generate executive summary
        executive_summary = self._generate_executive_summary(result)
        
        # Determine risk rating
        risk_rating = self._calculate_risk_rating(result)
        
        # Build control implementations map
        control_implementations = self._build_control_implementations(result)
        
        # Collect evidence references
        evidence_references = self._collect_evidence_references(result)
        
        # Create findings summary
        findings_summary = {
            "total_findings": len(result.security_findings),
            "critical": result.critical_findings,
            "high": result.high_findings,
            "medium": result.medium_findings,
            "low": result.low_findings,
            "auto_fixed": result.auto_fixes_applied,
            "manual_required": result.manual_fixes_required,
            "by_category": self._group_findings_by_category(result.security_findings)
        }
        
        # Create remediation plan
        remediation_plan = []
        if include_remediation_plan:
            remediation_plan = self._create_remediation_plan(result)
        
        doc = AuditDocumentation(
            project_name=result.project_name,
            document_id=f"DOC-{result.assessment_id}",
            generated_date=datetime.now().isoformat(),
            executive_summary=executive_summary,
            compliance_status=result.compliance_level.value,
            risk_rating=risk_rating,
            control_implementations=control_implementations,
            evidence_references=evidence_references,
            findings_summary=findings_summary,
            remediation_plan=remediation_plan,
            assessment_methodology="Automated SOC2 compliance verification using AI-powered code analysis"
        )
        
        return doc
    
    def _generate_executive_summary(self, result: CodeComplianceResult) -> str:
        """Generate executive summary for audit documentation"""
        return f"""
SOC2 COMPLIANCE ASSESSMENT EXECUTIVE SUMMARY
=============================================

Project: {result.project_name}
Assessment Date: {result.assessment_date}
Assessment ID: {result.assessment_id}

COMPLIANCE STATUS
-----------------
Overall Compliance Level: {result.compliance_level.value.upper()}
Compliance Score: {result.compliance_score:.1f}%

ASSESSMENT SCOPE
----------------
Files Analyzed: {result.total_files_scanned}
Files with Findings: {result.files_with_issues}
SOC2 Controls Assessed: {len(result.controls_assessed)}

FINDINGS SUMMARY
----------------
- Critical Findings: {result.critical_findings}
- High Severity: {result.high_findings}
- Medium Severity: {result.medium_findings}
- Low Severity: {result.low_findings}
- Total Findings: {len(result.security_findings)}

REMEDIATION STATUS
------------------
- Automatically Fixed: {result.auto_fixes_applied}
- Manual Remediation Required: {result.manual_fixes_required}

RECOMMENDATION
--------------
{"This project meets SOC2 compliance requirements with minor issues addressed." if result.compliance_score >= 75 
else "This project requires remediation before achieving SOC2 compliance. See detailed findings below."}

This assessment was conducted using automated SOC2 compliance verification
tools aligned with AICPA Trust Services Criteria.
"""
    
    def _calculate_risk_rating(self, result: CodeComplianceResult) -> str:
        """Calculate risk rating"""
        if result.critical_findings > 0:
            return "HIGH"
        elif result.high_findings > 2:
            return "HIGH"
        elif result.high_findings > 0 or result.medium_findings > 5:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _build_control_implementations(
        self, 
        result: CodeComplianceResult
    ) -> Dict[str, Dict]:
        """Build detailed control implementation map"""
        implementations = {}
        
        for control_code, status in result.controls_assessed.items():
            control_req = self.rag_database.get_control(control_code)
            
            implementations[control_code] = {
                "control_name": control_req.name if control_req else control_code,
                "description": control_req.description if control_req else "",
                "implementation_status": status,
                "trust_service": control_req.trust_service if control_req else "Security",
                "evidence": [],
                "gaps": [],
                "findings": []
            }
            
            # Add related findings
            for finding in result.security_findings:
                if finding.soc2_control == control_code:
                    implementations[control_code]["findings"].append({
                        "severity": finding.severity,
                        "description": finding.description,
                        "file": finding.file_path,
                        "remediation": finding.remediation,
                        "auto_fixed": finding.auto_fixed
                    })
            
            # Add related gaps
            for gap in result.compliance_gaps:
                if gap.control_code == control_code:
                    implementations[control_code]["gaps"].append({
                        "description": gap.description,
                        "affected_files": gap.affected_files,
                        "remediation_steps": gap.remediation_steps,
                        "timeline_days": gap.timeline_days
                    })
        
        return implementations
    
    def _collect_evidence_references(self, result: CodeComplianceResult) -> List[Dict]:
        """Collect evidence references for audit"""
        evidence = [
            {
                "type": "automated_scan",
                "description": "Automated code security scan results",
                "date": result.assessment_date,
                "reference": result.assessment_id
            },
            {
                "type": "compliance_assessment",
                "description": "SOC2 compliance assessment report",
                "date": result.assessment_date,
                "reference": f"DOC-{result.assessment_id}"
            }
        ]
        
        # Add evidence for each control
        for control_code, status in result.controls_assessed.items():
            if status == "IMPLEMENTED":
                evidence.append({
                    "type": "control_implementation",
                    "description": f"Implementation evidence for {control_code}",
                    "date": result.assessment_date,
                    "reference": f"{result.assessment_id}-{control_code}"
                })
        
        return evidence
    
    def _group_findings_by_category(
        self, 
        findings: List[CodeSecurityFinding]
    ) -> Dict[str, int]:
        """Group findings by security category"""
        by_category = {}
        for finding in findings:
            cat = finding.category.value
            by_category[cat] = by_category.get(cat, 0) + 1
        return by_category
    
    def _create_remediation_plan(self, result: CodeComplianceResult) -> List[Dict]:
        """Create prioritized remediation plan"""
        plan = []
        
        # Group findings by severity
        priority_1 = [f for f in result.security_findings if f.severity == "CRITICAL" and not f.auto_fixed]
        priority_2 = [f for f in result.security_findings if f.severity == "HIGH" and not f.auto_fixed]
        priority_3 = [f for f in result.security_findings if f.severity == "MEDIUM" and not f.auto_fixed]
        priority_4 = [f for f in result.security_findings if f.severity == "LOW" and not f.auto_fixed]
        
        if priority_1:
            plan.append({
                "priority": 1,
                "timeline": "Immediate (24-48 hours)",
                "severity": "CRITICAL",
                "items": [{
                    "file": f.file_path,
                    "issue": f.description,
                    "action": f.remediation,
                    "control": f.soc2_control
                } for f in priority_1]
            })
        
        if priority_2:
            plan.append({
                "priority": 2,
                "timeline": "7 days",
                "severity": "HIGH",
                "items": [{
                    "file": f.file_path,
                    "issue": f.description,
                    "action": f.remediation,
                    "control": f.soc2_control
                } for f in priority_2]
            })
        
        if priority_3:
            plan.append({
                "priority": 3,
                "timeline": "30 days",
                "severity": "MEDIUM",
                "items": [{
                    "file": f.file_path,
                    "issue": f.description,
                    "action": f.remediation,
                    "control": f.soc2_control
                } for f in priority_3]
            })
        
        if priority_4:
            plan.append({
                "priority": 4,
                "timeline": "90 days",
                "severity": "LOW",
                "items": [{
                    "file": f.file_path,
                    "issue": f.description,
                    "action": f.remediation,
                    "control": f.soc2_control
                } for f in priority_4]
            })
        
        return plan
    
    def export_audit_documentation(
        self,
        doc: AuditDocumentation,
        output_path: Path,
        format: str = "markdown"
    ) -> str:
        """Export audit documentation to file"""
        
        if format == "markdown":
            content = self._format_as_markdown(doc)
        elif format == "json":
            content = json.dumps(asdict(doc), indent=2, default=str)
        else:
            raise ValueError(f"Unsupported format: {format}")
        
        # Write to file
        output_file = output_path / f"SOC2_AUDIT_REPORT_{doc.project_name}.{format}"
        output_file.write_text(content)
        
        logger.info(f"📄 Audit documentation exported to: {output_file}")
        return str(output_file)
    
    def _format_as_markdown(self, doc: AuditDocumentation) -> str:
        """Format audit documentation as markdown"""
        md = f"""# SOC2 Compliance Audit Report

**Project:** {doc.project_name}  
**Document ID:** {doc.document_id}  
**Generated:** {doc.generated_date}  
**Compliance Status:** {doc.compliance_status.upper()}  
**Risk Rating:** {doc.risk_rating}  

---

## Executive Summary

{doc.executive_summary}

---

## Assessment Methodology

{doc.assessment_methodology}

---

## Control Implementations

"""
        
        for control_code, details in doc.control_implementations.items():
            md += f"""
### {control_code}: {details['control_name']}

**Status:** {details['implementation_status']}  
**Trust Service:** {details['trust_service']}  

{details['description']}

"""
            
            if details['findings']:
                md += "**Findings:**\n\n"
                for finding in details['findings']:
                    md += f"- [{finding['severity']}] {finding['description']} ({finding['file']})\n"
                    md += f"  - Remediation: {finding['remediation']}\n"
                    md += f"  - Auto-fixed: {'Yes' if finding['auto_fixed'] else 'No'}\n\n"
            
            if details['gaps']:
                md += "**Gaps:**\n\n"
                for gap in details['gaps']:
                    md += f"- {gap['description']}\n"
                    md += f"  - Affected files: {', '.join(gap['affected_files'])}\n"
                    md += f"  - Timeline: {gap['timeline_days']} days\n\n"
        
        md += """
---

## Findings Summary

"""
        md += f"| Metric | Value |\n"
        md += f"|--------|-------|\n"
        md += f"| Total Findings | {doc.findings_summary['total_findings']} |\n"
        md += f"| Critical | {doc.findings_summary['critical']} |\n"
        md += f"| High | {doc.findings_summary['high']} |\n"
        md += f"| Medium | {doc.findings_summary['medium']} |\n"
        md += f"| Low | {doc.findings_summary['low']} |\n"
        md += f"| Auto-Fixed | {doc.findings_summary['auto_fixed']} |\n"
        md += f"| Manual Required | {doc.findings_summary['manual_required']} |\n"
        
        if doc.remediation_plan:
            md += """
---

## Remediation Plan

"""
            for phase in doc.remediation_plan:
                md += f"""
### Priority {phase['priority']} - {phase['severity']} ({phase['timeline']})

"""
                for item in phase['items']:
                    md += f"- **{item['file']}**: {item['issue']}\n"
                    md += f"  - Action: {item['action']}\n"
                    md += f"  - Control: {item['control']}\n\n"
        
        md += """
---

## Evidence References

| Type | Description | Date | Reference |
|------|-------------|------|-----------|
"""
        for ev in doc.evidence_references:
            md += f"| {ev['type']} | {ev['description']} | {ev['date']} | {ev['reference']} |\n"
        
        md += """
---

## Certification

This report was generated using automated SOC2 compliance verification tools.
The assessment follows AICPA Trust Services Criteria standards.

"""
        
        return md


# Singleton instance for use across the application
soc2_code_compliance = SOC2CodeComplianceEngine()


# Integration function for PureAIGenerator
async def verify_and_document_compliance(
    project_name: str,
    files_content: Dict[str, str],
    output_dir: Optional[Path] = None
) -> Tuple[CodeComplianceResult, Dict[str, str], str]:
    """
    Main integration function for AI code generation pipeline.
    
    Args:
        project_name: Name of the generated project
        files_content: Dict of file_path -> content
        output_dir: Optional directory for audit documentation
        
    Returns:
        Tuple of (compliance_result, fixed_files, documentation_path)
    """
    engine = SOC2CodeComplianceEngine()
    
    # Verify and fix code
    result, fixed_files = await engine.verify_generated_code(
        project_name=project_name,
        files_content=files_content,
        auto_fix=True
    )
    
    # Generate audit documentation
    audit_doc = engine.generate_audit_documentation(result)
    
    # Export documentation if output_dir provided
    doc_path = ""
    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)
        doc_path = engine.export_audit_documentation(
            audit_doc, 
            output_dir, 
            format="markdown"
        )
        
        # Also export JSON for programmatic access
        engine.export_audit_documentation(
            audit_doc,
            output_dir,
            format="json"
        )
    
    return result, fixed_files, doc_path


if __name__ == "__main__":
    # Test the compliance engine
    import asyncio
    
    test_files = {
        "main.py": '''
from fastapi import FastAPI
import os

app = FastAPI()

# Bad: hardcoded secret
password = "my_secret_password"

@app.get("/")
def read_root():
    return {"Hello": "World"}

# Bad: no input validation
@app.post("/user")
def create_user(data: dict):
    return data
''',
        "config.py": '''
# Bad: hardcoded API key
api_key = "sk-1234567890abcdef"

# Bad: HTTP instead of HTTPS
API_URL = "http://api.example.com"
'''
    }
    
    async def test():
        result, fixed_files, doc_path = await verify_and_document_compliance(
            project_name="test_project",
            files_content=test_files,
            output_dir=Path("/tmp/soc2_test")
        )
        
        print(f"\n📊 Compliance Score: {result.compliance_score:.1f}%")
        print(f"📋 Compliance Level: {result.compliance_level.value}")
        print(f"🔍 Total Findings: {len(result.security_findings)}")
        print(f"✅ Auto-Fixed: {result.auto_fixes_applied}")
        print(f"📄 Documentation: {doc_path}")
    
    asyncio.run(test())
