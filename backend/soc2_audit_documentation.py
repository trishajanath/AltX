"""
SOC2 Project Audit Documentation Generator

This module generates comprehensive, audit-ready documentation for each
AI-generated project. The documentation is suitable for:
- SOC2 Type I and Type II audits
- Client due diligence requests
- Internal compliance reviews
- Security assessments
- Regulatory compliance evidence

Output Formats:
- Markdown (human-readable)
- JSON (programmatic access)
- PDF-ready HTML

Documentation Includes:
- Executive Summary
- Control Implementation Matrix
- Gap Analysis Report
- Remediation Plan
- Evidence Collection
- Sign-off Section
"""

from __future__ import annotations

import json
import hashlib
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any
from pathlib import Path
from enum import Enum
import logging

# Import SOC2 components
from soc2_rag_database import SOC2RAGDatabase, TrustServiceCriteria
from soc2_compliance_agent import ComplianceLevel
from soc2_code_compliance import (
    CodeComplianceResult,
    CodeSecurityFinding,
    ComplianceGap,
    SecurityCategory
)

logger = logging.getLogger(__name__)


class DocumentSection(Enum):
    """Sections of the audit documentation"""
    COVER_PAGE = "cover_page"
    EXECUTIVE_SUMMARY = "executive_summary"
    SCOPE = "scope"
    METHODOLOGY = "methodology"
    CONTROL_MATRIX = "control_matrix"
    GAP_ANALYSIS = "gap_analysis"
    FINDINGS = "findings"
    REMEDIATION = "remediation"
    EVIDENCE = "evidence"
    APPENDIX = "appendix"
    SIGN_OFF = "sign_off"


@dataclass
class AuditDocument:
    """Complete audit document structure"""
    
    # Metadata
    document_id: str
    project_name: str
    organization: str
    generated_date: str
    valid_until: str
    version: str = "1.0"
    classification: str = "CONFIDENTIAL"
    
    # Content sections
    sections: Dict[str, str] = field(default_factory=dict)
    
    # Supporting data
    compliance_result: Optional[Dict] = None
    control_mappings: Dict[str, Dict] = field(default_factory=dict)
    evidence_list: List[Dict] = field(default_factory=list)
    
    # Approval
    prepared_by: str = "Automated Compliance System"
    reviewed_by: Optional[str] = None
    approved_by: Optional[str] = None


class SOC2AuditDocumentGenerator:
    """
    Generates comprehensive SOC2 audit documentation for projects.
    
    This generator creates detailed, professional documentation that:
    - Maps all code to SOC2 controls
    - Documents gaps and remediations
    - Collects evidence references
    - Provides sign-off sections
    """
    
    def __init__(self):
        self.rag_database = SOC2RAGDatabase()
        
        # Standard SOC2 control categories
        self.control_categories = {
            "CC1": "Control Environment",
            "CC2": "Communication and Information",
            "CC3": "Risk Assessment",
            "CC4": "Monitoring Activities",
            "CC5": "Control Activities",
            "CC6": "Logical and Physical Access Controls",
            "CC7": "System Operations",
            "CC8": "Change Management",
            "CC9": "Risk Mitigation"
        }
    
    def generate_complete_documentation(
        self,
        project_name: str,
        compliance_result: CodeComplianceResult,
        organization: str = "Organization Name",
        include_remediation: bool = True,
        include_evidence: bool = True
    ) -> AuditDocument:
        """
        Generate complete audit documentation for a project.
        
        Args:
            project_name: Name of the project
            compliance_result: Results from compliance verification
            organization: Organization name for the document
            include_remediation: Whether to include remediation plan
            include_evidence: Whether to include evidence section
            
        Returns:
            Complete AuditDocument
        """
        
        # Generate document ID
        doc_id = self._generate_document_id(project_name)
        
        # Calculate validity period (1 year from generation)
        generated_date = datetime.now()
        valid_until = generated_date + timedelta(days=365)
        
        # Create document
        doc = AuditDocument(
            document_id=doc_id,
            project_name=project_name,
            organization=organization,
            generated_date=generated_date.isoformat(),
            valid_until=valid_until.isoformat(),
            compliance_result=asdict(compliance_result) if compliance_result else None
        )
        
        # Generate all sections
        doc.sections[DocumentSection.COVER_PAGE.value] = self._generate_cover_page(doc)
        doc.sections[DocumentSection.EXECUTIVE_SUMMARY.value] = self._generate_executive_summary(
            compliance_result, project_name
        )
        doc.sections[DocumentSection.SCOPE.value] = self._generate_scope(compliance_result)
        doc.sections[DocumentSection.METHODOLOGY.value] = self._generate_methodology()
        doc.sections[DocumentSection.CONTROL_MATRIX.value] = self._generate_control_matrix(
            compliance_result
        )
        doc.sections[DocumentSection.GAP_ANALYSIS.value] = self._generate_gap_analysis(
            compliance_result
        )
        doc.sections[DocumentSection.FINDINGS.value] = self._generate_findings(
            compliance_result
        )
        
        if include_remediation:
            doc.sections[DocumentSection.REMEDIATION.value] = self._generate_remediation_plan(
                compliance_result
            )
        
        if include_evidence:
            doc.sections[DocumentSection.EVIDENCE.value] = self._generate_evidence_section(
                compliance_result
            )
            doc.evidence_list = self._collect_evidence(compliance_result)
        
        doc.sections[DocumentSection.APPENDIX.value] = self._generate_appendix(compliance_result)
        doc.sections[DocumentSection.SIGN_OFF.value] = self._generate_sign_off(doc)
        
        # Build control mappings
        doc.control_mappings = self._build_control_mappings(compliance_result)
        
        logger.info(f"📄 Generated audit documentation: {doc_id}")
        
        return doc
    
    def _generate_document_id(self, project_name: str) -> str:
        """Generate unique document ID"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        hash_input = f"{project_name}{timestamp}"
        hash_suffix = hashlib.md5(hash_input.encode()).hexdigest()[:8].upper()
        return f"SOC2-DOC-{timestamp}-{hash_suffix}"
    
    def _generate_cover_page(self, doc: AuditDocument) -> str:
        """Generate cover page"""
        return f"""
═══════════════════════════════════════════════════════════════════════════════
                         SOC 2 COMPLIANCE AUDIT REPORT
═══════════════════════════════════════════════════════════════════════════════

                              {doc.organization}

                         Project: {doc.project_name}

                    ─────────────────────────────────────

                         Document ID: {doc.document_id}
                         Generated: {doc.generated_date[:10]}
                         Valid Until: {doc.valid_until[:10]}
                         Version: {doc.version}

                    ─────────────────────────────────────

                         Classification: {doc.classification}

                         Prepared by: {doc.prepared_by}


═══════════════════════════════════════════════════════════════════════════════

This document contains confidential information regarding the security and
compliance posture of {doc.project_name}. Distribution is limited to
authorized personnel only.

The assessment follows AICPA Trust Services Criteria for SOC 2 compliance.

═══════════════════════════════════════════════════════════════════════════════
"""
    
    def _generate_executive_summary(
        self, 
        result: CodeComplianceResult,
        project_name: str
    ) -> str:
        """Generate executive summary"""
        
        # Determine overall assessment
        if result.compliance_score >= 90:
            overall_assessment = "SATISFACTORY - The project meets SOC 2 compliance requirements."
            recommendation = "The project is ready for production deployment with SOC 2 compliance."
        elif result.compliance_score >= 75:
            overall_assessment = "SATISFACTORY WITH OBSERVATIONS - Minor issues identified."
            recommendation = "Address the identified observations before final deployment."
        elif result.compliance_score >= 50:
            overall_assessment = "NEEDS IMPROVEMENT - Significant gaps identified."
            recommendation = "Remediation required before the project can be considered compliant."
        else:
            overall_assessment = "UNSATISFACTORY - Critical compliance gaps exist."
            recommendation = "Immediate remediation required. Do not deploy until issues are resolved."
        
        return f"""
## EXECUTIVE SUMMARY

### Overview

This report presents the findings of a SOC 2 compliance assessment conducted on
**{project_name}**. The assessment evaluated the project against the AICPA Trust
Services Criteria, focusing on Security, Availability, Processing Integrity,
Confidentiality, and Privacy.

### Assessment Results

| Metric | Value |
|--------|-------|
| **Compliance Score** | {result.compliance_score:.1f}% |
| **Compliance Level** | {result.compliance_level.value.upper()} |
| **Files Analyzed** | {result.total_files_scanned} |
| **Files with Issues** | {result.files_with_issues} |

### Findings Summary

| Severity | Count | Auto-Fixed |
|----------|-------|------------|
| Critical | {result.critical_findings} | - |
| High | {result.high_findings} | - |
| Medium | {result.medium_findings} | - |
| Low | {result.low_findings} | - |
| **Total** | **{len(result.security_findings)}** | **{result.auto_fixes_applied}** |

### Overall Assessment

**{overall_assessment}**

### Recommendation

{recommendation}

### Key Observations

1. **Security Controls**: {"Adequately implemented" if result.critical_findings == 0 else "Critical issues require immediate attention"}
2. **Code Quality**: {"Meets standards" if result.low_findings < 5 else "Minor improvements recommended"}
3. **Automated Remediation**: {result.auto_fixes_applied} issues were automatically corrected
4. **Manual Action Required**: {result.manual_fixes_required} issues require manual review

---
"""
    
    def _generate_scope(self, result: CodeComplianceResult) -> str:
        """Generate scope section"""
        
        # Determine TSCs covered
        tscs_covered = []
        for control in result.controls_assessed.keys():
            if control.startswith("CC"):
                if "Security" not in tscs_covered:
                    tscs_covered.append("Security")
            elif control.startswith("A"):
                tscs_covered.append("Availability")
            elif control.startswith("PI"):
                tscs_covered.append("Processing Integrity")
            elif control.startswith("C"):
                tscs_covered.append("Confidentiality")
            elif control.startswith("P"):
                tscs_covered.append("Privacy")
        
        if not tscs_covered:
            tscs_covered = ["Security"]  # Default
        
        return f"""
## SCOPE OF ASSESSMENT

### Trust Services Criteria Covered

This assessment evaluates the following Trust Services Criteria (TSC):

{chr(10).join(f"- **{tsc}**" for tsc in tscs_covered)}

### Assessment Boundaries

**In Scope:**
- Source code analysis
- Security pattern detection
- Compliance control mapping
- Automated vulnerability scanning
- Code quality assessment

**Out of Scope:**
- Infrastructure security (servers, networks)
- Physical security controls
- Personnel security
- Business continuity planning (unless documented in code)
- Third-party vendor assessments

### Files Analyzed

- **Total Files**: {result.total_files_scanned}
- **File Types**: Python, JavaScript, TypeScript, Configuration files

### Controls Assessed

| Control | Description | Status |
|---------|-------------|--------|
{chr(10).join(f"| {code} | {self.control_categories.get(code[:3], 'N/A')} | {status} |" for code, status in result.controls_assessed.items())}

---
"""
    
    def _generate_methodology(self) -> str:
        """Generate methodology section"""
        return """
## ASSESSMENT METHODOLOGY

### Overview

This assessment was conducted using an automated SOC 2 compliance verification
system that analyzes generated code against AICPA Trust Services Criteria.

### Assessment Phases

#### Phase 1: Code Collection
- Gather all generated source code files
- Identify file types and technologies used
- Create file inventory for analysis

#### Phase 2: Security Scanning
- Pattern-based security analysis
- Detection of common vulnerabilities (OWASP Top 10)
- Identification of hardcoded secrets
- Input validation assessment

#### Phase 3: Control Mapping
- Map code patterns to SOC 2 controls
- Identify implemented controls
- Document control gaps

#### Phase 4: Gap Analysis
- Evaluate control implementation completeness
- Assess gap severity and risk
- Prioritize remediation needs

#### Phase 5: Auto-Remediation
- Apply automated fixes where safe
- Document changes made
- Verify fixes maintain functionality

#### Phase 6: Documentation
- Generate audit-ready documentation
- Compile evidence references
- Create remediation plan

### Tools and Techniques

| Tool/Technique | Purpose |
|----------------|---------|
| Static Code Analysis | Security vulnerability detection |
| Pattern Matching | Compliance control identification |
| AST Analysis | Code structure validation |
| Regex Scanning | Secret and credential detection |

### Standards Reference

- AICPA Trust Services Criteria (2017)
- AICPA SOC 2 Type I/II Standards
- OWASP Top 10 (2021)
- CWE/SANS Top 25

---
"""
    
    def _generate_control_matrix(self, result: CodeComplianceResult) -> str:
        """Generate control implementation matrix"""
        
        matrix_rows = []
        
        for control_code, status in result.controls_assessed.items():
            # Get control details
            control = self.rag_database.get_control(control_code)
            
            # Count findings for this control
            findings_count = sum(
                1 for f in result.security_findings 
                if f.soc2_control == control_code
            )
            
            # Determine implementation rating
            if status == "IMPLEMENTED" and findings_count == 0:
                rating = "✅ Fully Implemented"
            elif status == "IMPLEMENTED":
                rating = "⚠️ Implemented with Issues"
            elif status == "PARTIAL":
                rating = "🟨 Partially Implemented"
            else:
                rating = "❌ Not Implemented"
            
            matrix_rows.append(
                f"| {control_code} | "
                f"{control.name if control else 'N/A'} | "
                f"{control.trust_service if control else 'Security'} | "
                f"{rating} | "
                f"{findings_count} |"
            )
        
        return f"""
## CONTROL IMPLEMENTATION MATRIX

### Overview

The following matrix shows the implementation status of SOC 2 controls
evaluated during this assessment.

### Implementation Legend

- ✅ **Fully Implemented**: Control is properly implemented with no issues
- ⚠️ **Implemented with Issues**: Control exists but has findings
- 🟨 **Partially Implemented**: Control is incomplete
- ❌ **Not Implemented**: Control is missing or not detected

### Control Matrix

| Control | Name | Category | Status | Findings |
|---------|------|----------|--------|----------|
{chr(10).join(matrix_rows)}

### Summary Statistics

| Status | Count |
|--------|-------|
| Fully Implemented | {sum(1 for s in result.controls_assessed.values() if s == 'IMPLEMENTED')} |
| Partially Implemented | {sum(1 for s in result.controls_assessed.values() if s == 'PARTIAL')} |
| Not Assessed | {sum(1 for s in result.controls_assessed.values() if s == 'NOT_ASSESSED')} |

---
"""
    
    def _generate_gap_analysis(self, result: CodeComplianceResult) -> str:
        """Generate gap analysis section"""
        
        gaps_content = []
        
        for i, gap in enumerate(result.compliance_gaps, 1):
            gaps_content.append(f"""
### Gap {i}: {gap.control_code} - {gap.control_name}

**Gap ID:** {gap.gap_id}  
**Severity:** {gap.severity}  
**Status:** {gap.status}  
**Timeline:** {gap.timeline_days} days  

**Description:**
{gap.description}

**Affected Files:**
{chr(10).join(f"- `{f}`" for f in gap.affected_files)}

**Remediation Steps:**
{chr(10).join(f"{j}. {step}" for j, step in enumerate(gap.remediation_steps, 1))}

---
""")
        
        if not gaps_content:
            gaps_content = ["No significant compliance gaps identified."]
        
        return f"""
## GAP ANALYSIS

### Overview

This section identifies gaps between current implementation and SOC 2 requirements.
Gaps are prioritized by severity and include remediation guidance.

### Gap Summary

| Severity | Count |
|----------|-------|
| Critical | {sum(1 for g in result.compliance_gaps if g.severity == 'CRITICAL')} |
| High | {sum(1 for g in result.compliance_gaps if g.severity == 'HIGH')} |
| Medium | {sum(1 for g in result.compliance_gaps if g.severity == 'MEDIUM')} |
| Low | {sum(1 for g in result.compliance_gaps if g.severity == 'LOW')} |
| **Total** | **{len(result.compliance_gaps)}** |

### Detailed Gaps

{chr(10).join(gaps_content)}
"""
    
    def _generate_findings(self, result: CodeComplianceResult) -> str:
        """Generate detailed findings section"""
        
        # Group findings by category
        by_category: Dict[str, List[CodeSecurityFinding]] = {}
        for finding in result.security_findings:
            cat = finding.category.value
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(finding)
        
        findings_content = []
        
        for category, findings in by_category.items():
            findings_content.append(f"\n### {category.replace('_', ' ').title()}\n")
            
            for finding in findings:
                fix_status = "✅ Auto-Fixed" if finding.auto_fixed else "⚠️ Manual Fix Required"
                
                findings_content.append(f"""
#### {finding.finding_id}

| Attribute | Value |
|-----------|-------|
| **Severity** | {finding.severity} |
| **File** | `{finding.file_path}` |
| **Line** | {finding.line_number or 'N/A'} |
| **Control** | {finding.soc2_control} |
| **Status** | {fix_status} |

**Description:** {finding.description}

**Code Snippet:**
```
{finding.code_snippet or 'N/A'}
```

**Remediation:** {finding.remediation}

{f"**Fix Applied:** `{finding.fix_applied}`" if finding.auto_fixed else ""}

---
""")
        
        if not findings_content:
            findings_content = ["No security findings identified."]
        
        return f"""
## DETAILED FINDINGS

### Overview

This section provides detailed information about each security finding
identified during the assessment.

### Findings by Severity

| Severity | Count | Description |
|----------|-------|-------------|
| Critical | {result.critical_findings} | Immediate security risk |
| High | {result.high_findings} | Significant security concern |
| Medium | {result.medium_findings} | Moderate risk |
| Low | {result.low_findings} | Minor issue |

### Findings by Category

| Category | Count |
|----------|-------|
{chr(10).join(f"| {cat.replace('_', ' ').title()} | {len(findings)} |" for cat, findings in by_category.items())}

{chr(10).join(findings_content)}
"""
    
    def _generate_remediation_plan(self, result: CodeComplianceResult) -> str:
        """Generate remediation plan section"""
        
        # Group unfixed findings by priority
        critical = [f for f in result.security_findings if f.severity == "CRITICAL" and not f.auto_fixed]
        high = [f for f in result.security_findings if f.severity == "HIGH" and not f.auto_fixed]
        medium = [f for f in result.security_findings if f.severity == "MEDIUM" and not f.auto_fixed]
        low = [f for f in result.security_findings if f.severity == "LOW" and not f.auto_fixed]
        
        plan_content = []
        
        if critical:
            plan_content.append("""
### Priority 1: Critical (Immediate - 24-48 hours)

These issues pose immediate security risks and must be addressed before deployment.

| Finding | File | Action | Owner |
|---------|------|--------|-------|
""")
            for f in critical:
                plan_content.append(f"| {f.finding_id} | `{f.file_path}` | {f.remediation} | TBD |")
        
        if high:
            plan_content.append("""

### Priority 2: High (7 days)

These issues represent significant security concerns.

| Finding | File | Action | Owner |
|---------|------|--------|-------|
""")
            for f in high:
                plan_content.append(f"| {f.finding_id} | `{f.file_path}` | {f.remediation} | TBD |")
        
        if medium:
            plan_content.append("""

### Priority 3: Medium (30 days)

These issues should be addressed during normal development cycles.

| Finding | File | Action | Owner |
|---------|------|--------|-------|
""")
            for f in medium:
                plan_content.append(f"| {f.finding_id} | `{f.file_path}` | {f.remediation} | TBD |")
        
        if low:
            plan_content.append("""

### Priority 4: Low (90 days)

These are minor issues that can be addressed as time permits.

| Finding | File | Action | Owner |
|---------|------|--------|-------|
""")
            for f in low:
                plan_content.append(f"| {f.finding_id} | `{f.file_path}` | {f.remediation} | TBD |")
        
        if not plan_content:
            plan_content = ["All identified issues have been automatically remediated."]
        
        return f"""
## REMEDIATION PLAN

### Overview

This section outlines the recommended remediation plan for addressing
identified compliance gaps and security findings.

### Remediation Summary

| Priority | Severity | Count | Timeline |
|----------|----------|-------|----------|
| 1 | Critical | {len(critical)} | 24-48 hours |
| 2 | High | {len(high)} | 7 days |
| 3 | Medium | {len(medium)} | 30 days |
| 4 | Low | {len(low)} | 90 days |

### Auto-Remediation Status

- **Issues Automatically Fixed:** {result.auto_fixes_applied}
- **Issues Requiring Manual Fix:** {result.manual_fixes_required}

{chr(10).join(plan_content)}

### Remediation Process

1. **Assign Owners**: Designate responsible parties for each finding
2. **Schedule Work**: Add remediation tasks to sprint/project planning
3. **Implement Fixes**: Apply recommended remediations
4. **Verify Fixes**: Re-run compliance scan after fixes
5. **Document Changes**: Update this report with remediation evidence

---
"""
    
    def _generate_evidence_section(self, result: CodeComplianceResult) -> str:
        """Generate evidence section"""
        return f"""
## EVIDENCE COLLECTION

### Overview

This section documents the evidence collected during the compliance assessment.
Evidence items can be used to support SOC 2 audit activities.

### Evidence Inventory

| Evidence ID | Type | Description | Date |
|-------------|------|-------------|------|
| {result.assessment_id}-SCAN | Automated Scan | Code security scan results | {result.assessment_date[:10]} |
| {result.assessment_id}-RPT | Compliance Report | This audit documentation | {result.assessment_date[:10]} |
| {result.assessment_id}-FIX | Remediation Log | Auto-fix actions applied | {result.assessment_date[:10]} |

### Evidence Categories

#### 1. Automated Security Scans
- Complete scan of {result.total_files_scanned} source files
- Detection of {len(result.security_findings)} security findings
- Pattern matching against known vulnerabilities

#### 2. Control Implementation Evidence
- Mapping of code patterns to {len(result.controls_assessed)} SOC 2 controls
- Documentation of implemented security controls
- Identification of control gaps

#### 3. Remediation Evidence
- {result.auto_fixes_applied} automated fixes applied
- Fix patterns documented for audit trail
- Before/after comparison available

### Evidence Retention

All evidence is retained for audit purposes. Evidence includes:
- Original scan results (JSON format)
- This documentation (Markdown/PDF)
- Code snapshots before and after remediation

---
"""
    
    def _generate_appendix(self, result: CodeComplianceResult) -> str:
        """Generate appendix section"""
        return f"""
## APPENDIX

### A. SOC 2 Trust Services Criteria Reference

#### Security (Common Criteria)
| Control | Description |
|---------|-------------|
| CC1 | Control Environment |
| CC2 | Communication and Information |
| CC3 | Risk Assessment |
| CC4 | Monitoring Activities |
| CC5 | Control Activities |
| CC6 | Logical and Physical Access Controls |
| CC7 | System Operations |
| CC8 | Change Management |
| CC9 | Risk Mitigation |

#### Additional Criteria
| Category | Description |
|----------|-------------|
| Availability | System availability commitments |
| Processing Integrity | Processing accuracy and completeness |
| Confidentiality | Information protection |
| Privacy | Personal information handling |

### B. Severity Definitions

| Severity | Definition | Response Time |
|----------|------------|---------------|
| Critical | Immediate security risk, potential data breach | 24-48 hours |
| High | Significant vulnerability, regulatory impact | 7 days |
| Medium | Moderate risk, defense-in-depth concern | 30 days |
| Low | Best practice deviation, minor risk | 90 days |

### C. Assessment Tool Information

- **Tool**: SOC2 Code Compliance Engine
- **Version**: 1.0
- **Assessment Date**: {result.assessment_date}
- **Assessment ID**: {result.assessment_id}

### D. Glossary

| Term | Definition |
|------|------------|
| TSC | Trust Services Criteria |
| CC | Common Criteria (Security) |
| SOC 2 | Service Organization Control 2 |
| AICPA | American Institute of CPAs |
| Gap | Missing or incomplete control implementation |

---
"""
    
    def _generate_sign_off(self, doc: AuditDocument) -> str:
        """Generate sign-off section"""
        return f"""
## SIGN-OFF

### Document Approval

This document has been reviewed and approved by the following parties:

| Role | Name | Signature | Date |
|------|------|-----------|------|
| Prepared By | {doc.prepared_by} | _Auto-generated_ | {doc.generated_date[:10]} |
| Technical Review | {doc.reviewed_by or '________________'} | ________________ | ________ |
| Management Approval | {doc.approved_by or '________________'} | ________________ | ________ |

### Certification Statement

I certify that this assessment was conducted in accordance with professional
standards and the findings accurately represent the compliance posture of
**{doc.project_name}** as of the assessment date.

This assessment is valid until **{doc.valid_until[:10]}** unless material changes
occur to the assessed systems.

### Distribution List

This document is classified as **{doc.classification}** and should only be
distributed to:

- [ ] Security Team
- [ ] Compliance Team
- [ ] Development Team Lead
- [ ] Executive Management
- [ ] External Auditors (upon request)

### Contact Information

For questions regarding this assessment, please contact the compliance team.

---

**Document ID:** {doc.document_id}  
**Generated:** {doc.generated_date}  
**Valid Until:** {doc.valid_until}

*End of Document*
"""
    
    def _build_control_mappings(
        self, 
        result: CodeComplianceResult
    ) -> Dict[str, Dict]:
        """Build control mappings dictionary"""
        mappings = {}
        
        for control_code, status in result.controls_assessed.items():
            control = self.rag_database.get_control(control_code)
            
            mappings[control_code] = {
                "name": control.name if control else control_code,
                "category": control.trust_service if control else "Security",
                "status": status,
                "description": control.description if control else "",
                "requirements": control.requirements if control else [],
                "findings": [
                    {
                        "id": f.finding_id,
                        "severity": f.severity,
                        "description": f.description,
                        "file": f.file_path,
                        "auto_fixed": f.auto_fixed
                    }
                    for f in result.security_findings
                    if f.soc2_control == control_code
                ]
            }
        
        return mappings
    
    def _collect_evidence(self, result: CodeComplianceResult) -> List[Dict]:
        """Collect evidence references"""
        evidence = [
            {
                "id": f"{result.assessment_id}-SCAN",
                "type": "automated_scan",
                "description": "Automated code security scan",
                "date": result.assessment_date,
                "files_scanned": result.total_files_scanned,
                "findings_count": len(result.security_findings)
            },
            {
                "id": f"{result.assessment_id}-CTRL",
                "type": "control_assessment",
                "description": "SOC 2 control implementation assessment",
                "date": result.assessment_date,
                "controls_assessed": len(result.controls_assessed)
            }
        ]
        
        if result.auto_fixes_applied > 0:
            evidence.append({
                "id": f"{result.assessment_id}-FIX",
                "type": "remediation",
                "description": "Automated remediation actions",
                "date": result.assessment_date,
                "fixes_applied": result.auto_fixes_applied
            })
        
        return evidence
    
    def export_document(
        self,
        doc: AuditDocument,
        output_dir: Path,
        formats: List[str] = None
    ) -> Dict[str, str]:
        """
        Export audit document to files.
        
        Args:
            doc: The audit document to export
            output_dir: Directory for output files
            formats: List of formats ('markdown', 'json', 'html')
            
        Returns:
            Dict of format -> file path
        """
        if formats is None:
            formats = ['markdown', 'json']
        
        output_dir.mkdir(parents=True, exist_ok=True)
        outputs = {}
        
        if 'markdown' in formats:
            md_path = output_dir / f"SOC2_AUDIT_{doc.project_name}_{doc.document_id}.md"
            md_content = self._compile_markdown(doc)
            md_path.write_text(md_content)
            outputs['markdown'] = str(md_path)
            logger.info(f"📄 Exported Markdown: {md_path}")
        
        if 'json' in formats:
            json_path = output_dir / f"SOC2_AUDIT_{doc.project_name}_{doc.document_id}.json"
            json_content = json.dumps(asdict(doc), indent=2, default=str)
            json_path.write_text(json_content)
            outputs['json'] = str(json_path)
            logger.info(f"📄 Exported JSON: {json_path}")
        
        if 'html' in formats:
            html_path = output_dir / f"SOC2_AUDIT_{doc.project_name}_{doc.document_id}.html"
            html_content = self._compile_html(doc)
            html_path.write_text(html_content)
            outputs['html'] = str(html_path)
            logger.info(f"📄 Exported HTML: {html_path}")
        
        return outputs
    
    def _compile_markdown(self, doc: AuditDocument) -> str:
        """Compile all sections into markdown"""
        sections_order = [
            DocumentSection.COVER_PAGE,
            DocumentSection.EXECUTIVE_SUMMARY,
            DocumentSection.SCOPE,
            DocumentSection.METHODOLOGY,
            DocumentSection.CONTROL_MATRIX,
            DocumentSection.GAP_ANALYSIS,
            DocumentSection.FINDINGS,
            DocumentSection.REMEDIATION,
            DocumentSection.EVIDENCE,
            DocumentSection.APPENDIX,
            DocumentSection.SIGN_OFF
        ]
        
        content = []
        for section in sections_order:
            if section.value in doc.sections:
                content.append(doc.sections[section.value])
        
        return "\n".join(content)
    
    def _compile_html(self, doc: AuditDocument) -> str:
        """Compile document as HTML (PDF-ready)"""
        md_content = self._compile_markdown(doc)
        
        # Convert markdown to HTML (basic conversion)
        html_content = md_content
        html_content = html_content.replace("## ", "<h2>").replace("\n### ", "</h2>\n<h3>")
        html_content = html_content.replace("#### ", "<h4>").replace("\n", "<br>\n")
        html_content = html_content.replace("| ", "<td>").replace(" |", "</td>")
        
        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>SOC2 Audit Report - {doc.project_name}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }}
        h1 {{ color: #333; border-bottom: 2px solid #333; }}
        h2 {{ color: #444; border-bottom: 1px solid #ccc; }}
        h3 {{ color: #555; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
        th {{ background-color: #f4f4f4; }}
        code {{ background-color: #f5f5f5; padding: 2px 6px; border-radius: 3px; }}
        pre {{ background-color: #f5f5f5; padding: 15px; border-radius: 5px; overflow-x: auto; }}
        .critical {{ color: #d32f2f; font-weight: bold; }}
        .high {{ color: #f57c00; font-weight: bold; }}
        .medium {{ color: #fbc02d; }}
        .low {{ color: #388e3c; }}
        @media print {{
            body {{ margin: 20px; }}
            .no-print {{ display: none; }}
        }}
    </style>
</head>
<body>
    <h1>SOC 2 Compliance Audit Report</h1>
    <p><strong>Project:</strong> {doc.project_name}</p>
    <p><strong>Document ID:</strong> {doc.document_id}</p>
    <p><strong>Generated:</strong> {doc.generated_date}</p>
    
    {html_content}
</body>
</html>
"""


# Convenience function
def generate_project_audit_documentation(
    project_name: str,
    compliance_result: CodeComplianceResult,
    output_dir: Path,
    organization: str = "Organization",
    formats: List[str] = None
) -> Dict[str, str]:
    """
    Generate complete audit documentation for a project.
    
    Args:
        project_name: Name of the project
        compliance_result: Results from compliance verification
        output_dir: Directory for output files
        organization: Organization name
        formats: Output formats (default: markdown, json)
        
    Returns:
        Dict of format -> file path
    """
    generator = SOC2AuditDocumentGenerator()
    doc = generator.generate_complete_documentation(
        project_name=project_name,
        compliance_result=compliance_result,
        organization=organization
    )
    return generator.export_document(doc, output_dir, formats or ['markdown', 'json'])


if __name__ == "__main__":
    # Test the documentation generator
    from soc2_code_compliance import CodeComplianceLevel, CodeSecurityFinding, SecurityCategory
    
    # Create mock compliance result
    mock_result = CodeComplianceResult(
        project_name="test_project",
        assessment_id="SOC2-TEST-001",
        assessment_date=datetime.now().isoformat(),
        compliance_level=CodeComplianceLevel.MOSTLY_COMPLIANT,
        compliance_score=78.5,
        total_files_scanned=15,
        files_with_issues=3,
        critical_findings=0,
        high_findings=2,
        medium_findings=3,
        low_findings=5,
        auto_fixes_applied=4,
        manual_fixes_required=2
    )
    
    mock_result.controls_assessed = {
        "CC6.1": "IMPLEMENTED",
        "CC6.6": "PARTIAL",
        "CC6.7": "IMPLEMENTED",
        "CC7.2": "PARTIAL",
        "CC8.1": "NOT_ASSESSED"
    }
    
    mock_result.security_findings = [
        CodeSecurityFinding(
            finding_id="FND-001",
            category=SecurityCategory.AUTHENTICATION,
            severity="HIGH",
            file_path="main.py",
            line_number=10,
            code_snippet="password = 'secret'",
            description="Hardcoded password detected",
            remediation="Use environment variables",
            soc2_control="CC6.1",
            auto_fixed=True,
            fix_applied="os.getenv('PASSWORD')"
        )
    ]
    
    # Generate documentation
    output = generate_project_audit_documentation(
        project_name="test_project",
        compliance_result=mock_result,
        output_dir=Path("/tmp/soc2_audit_test"),
        organization="Test Organization",
        formats=['markdown', 'json', 'html']
    )
    
    print(f"📄 Documentation generated:")
    for fmt, path in output.items():
        print(f"   {fmt}: {path}")
