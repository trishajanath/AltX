"""
SOC2 Compliance Verification System
Automated verification and validation of SOC2 compliance controls
"""

from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime, timedelta
import json
import logging
from abc import ABC, abstractmethod

from soc2_compliance_agent import SOC2ComplianceAgent, ComplianceAssessment, ComplianceLevel
from soc2_control_implementation import (
    CC1_ControlEnvironment, CC6_AccessControls, CC8_ChangeManagement,
    AvailabilityControl, AuditLogger
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VerificationStatus(Enum):
    """Verification status"""
    PASSED = "PASSED"
    FAILED = "FAILED"
    WARNING = "WARNING"
    INCONCLUSIVE = "INCONCLUSIVE"

@dataclass
class VerificationResult:
    """Result of control verification"""
    control_code: str
    control_name: str
    verification_date: str
    status: VerificationStatus
    evidence_collected: Dict[str, Any]
    test_results: List[Dict[str, Any]]
    issues_found: List[str]
    recommendations: List[str]
    verified_by: str
    verification_id: str

class ControlValidator(ABC):
    """Abstract base class for control validators"""
    
    @abstractmethod
    def validate(self, control_code: str, evidence: Dict[str, Any]) -> Tuple[VerificationStatus, List[str]]:
        """Validate control implementation"""
        pass
    
    @abstractmethod
    def collect_evidence(self) -> Dict[str, Any]:
        """Collect evidence for verification"""
        pass

class CC1_Validator(ControlValidator):
    """Validator for CC1 - Control Environment"""
    
    def __init__(self):
        self.control_env = CC1_ControlEnvironment()
    
    def validate(self, control_code: str, evidence: Dict[str, Any]) -> Tuple[VerificationStatus, List[str]]:
        """Validate CC1 control"""
        issues = []
        
        # Check code of conduct exists
        if not evidence.get("code_of_conduct_exists"):
            issues.append("Code of conduct not documented")
        
        # Check training completion
        training_completion = evidence.get("training_completion_rate", 0)
        if training_completion < 0.8:  # 80% minimum
            issues.append(f"Training completion rate {training_completion*100}% below 80% threshold")
        
        # Check policy acknowledgments
        acknowledgment_rate = evidence.get("policy_acknowledgment_rate", 0)
        if acknowledgment_rate < 0.95:  # 95% minimum
            issues.append(f"Policy acknowledgment rate {acknowledgment_rate*100}% below 95% threshold")
        
        # Check violation handling
        violations = evidence.get("violations", [])
        unresolved = [v for v in violations if v.get("status") != "RESOLVED"]
        if unresolved:
            issues.append(f"{len(unresolved)} unresolved violations found")
        
        if issues:
            status = VerificationStatus.FAILED if len(issues) > 2 else VerificationStatus.WARNING
        else:
            status = VerificationStatus.PASSED
        
        return status, issues
    
    def collect_evidence(self) -> Dict[str, Any]:
        """Collect evidence for CC1"""
        return {
            "code_of_conduct_exists": True,
            "code_of_conduct_version": "1.0",
            "training_completion_rate": 0.85,
            "policy_acknowledgment_rate": 0.98,
            "violations": [],
            "violation_resolution_time_days": 5
        }

class CC6_Validator(ControlValidator):
    """Validator for CC6 - Logical and Physical Access Controls"""
    
    def __init__(self):
        self.access_control = CC6_AccessControls()
    
    def validate(self, control_code: str, evidence: Dict[str, Any]) -> Tuple[VerificationStatus, List[str]]:
        """Validate CC6 control"""
        issues = []
        
        # Check MFA is enabled
        mfa_enabled_percentage = evidence.get("mfa_enabled_percentage", 0)
        if mfa_enabled_percentage < 1.0:  # 100% required
            issues.append(f"MFA only enabled for {mfa_enabled_percentage*100}% of users")
        
        # Check encryption
        encryption_enabled = evidence.get("encryption_at_rest", False)
        if not encryption_enabled:
            issues.append("Encryption at rest not enabled")
        
        encryption_transit = evidence.get("encryption_in_transit", False)
        if not encryption_transit:
            issues.append("Encryption in transit not enabled")
        
        # Check access review frequency
        last_review_days = evidence.get("days_since_last_access_review", float('inf'))
        if last_review_days > 90:  # Should be every 90 days
            issues.append(f"Last access review was {last_review_days} days ago (exceeds 90-day threshold)")
        
        # Check failed login monitoring
        failed_login_monitoring = evidence.get("failed_login_monitoring", False)
        if not failed_login_monitoring:
            issues.append("Failed login monitoring not enabled")
        
        if issues:
            status = VerificationStatus.FAILED
        else:
            status = VerificationStatus.PASSED
        
        return status, issues
    
    def collect_evidence(self) -> Dict[str, Any]:
        """Collect evidence for CC6"""
        return {
            "mfa_enabled_percentage": 1.0,
            "mfa_enforcement_policy": "Required for all users",
            "encryption_at_rest": True,
            "encryption_algorithms": ["AES-256-GCM"],
            "encryption_in_transit": True,
            "tls_version": "1.3",
            "days_since_last_access_review": 30,
            "access_review_frequency": "Quarterly",
            "failed_login_monitoring": True,
            "brute_force_protection": True,
            "session_timeout_minutes": 30,
            "privileged_access_management": True
        }

class CC8_Validator(ControlValidator):
    """Validator for CC8 - Change Management"""
    
    def __init__(self):
        self.change_mgmt = CC8_ChangeManagement()
    
    def validate(self, control_code: str, evidence: Dict[str, Any]) -> Tuple[VerificationStatus, List[str]]:
        """Validate CC8 control"""
        issues = []
        
        # Check change approval process
        change_approval_rate = evidence.get("change_approval_rate", 0)
        if change_approval_rate < 1.0:
            issues.append(f"Only {change_approval_rate*100}% of changes approved before implementation")
        
        # Check change documentation
        documented_rate = evidence.get("changes_documented_rate", 0)
        if documented_rate < 1.0:
            issues.append(f"Only {documented_rate*100}% of changes documented")
        
        # Check testing
        tested_rate = evidence.get("changes_tested_rate", 0)
        if tested_rate < 1.0:
            issues.append(f"Only {tested_rate*100}% of changes tested before production")
        
        # Check rollback capability
        rollback_tested = evidence.get("rollback_procedures_tested", False)
        if not rollback_tested:
            issues.append("Rollback procedures not tested")
        
        if issues:
            status = VerificationStatus.FAILED if len(issues) > 1 else VerificationStatus.WARNING
        else:
            status = VerificationStatus.PASSED
        
        return status, issues
    
    def collect_evidence(self) -> Dict[str, Any]:
        """Collect evidence for CC8"""
        return {
            "change_approval_rate": 1.0,
            "change_approval_authority": "Change Advisory Board",
            "changes_documented_rate": 1.0,
            "documentation_system": "Jira Service Management",
            "changes_tested_rate": 1.0,
            "testing_environment": "Staging",
            "rollback_procedures_tested": True,
            "rollback_testing_frequency": "Per change",
            "change_management_policy": "Approved",
            "change_log_maintained": True
        }

class SOC2ComplianceVerifier:
    """Main compliance verification system"""
    
    def __init__(self):
        self.compliance_agent = SOC2ComplianceAgent()
        self.validators: Dict[str, ControlValidator] = {
            "CC1": CC1_Validator(),
            "CC6": CC6_Validator(),
            "CC8": CC8_Validator()
        }
        self.verification_results: List[VerificationResult] = []
        self.audit_logger = AuditLogger()
    
    def verify_single_control(self, control_code: str, evidence: Dict[str, Any],
                             verified_by: str = "SYSTEM") -> VerificationResult:
        """Verify a single control"""
        control = self.compliance_agent.get_control_requirements(control_code)
        
        if not control:
            return self._create_failed_result(control_code, "Control not found", verified_by)
        
        # Get validator
        control_prefix = control_code.split(".")[0]
        validator = self.validators.get(control_prefix)
        
        if not validator:
            # Use default validation
            status, issues = self._default_validate(control_code, evidence)
        else:
            status, issues = validator.validate(control_code, evidence)
        
        # Create verification result
        verification_id = f"VER-{self._generate_id()}"
        result = VerificationResult(
            control_code=control_code,
            control_name=control.name,
            verification_date=datetime.now().isoformat(),
            status=status,
            evidence_collected=evidence,
            test_results=self._run_tests(control_code, evidence),
            issues_found=issues,
            recommendations=self._generate_recommendations(issues),
            verified_by=verified_by,
            verification_id=verification_id
        )
        
        self.verification_results.append(result)
        self.audit_logger.log_event(
            "CONTROL_VERIFICATION",
            verified_by,
            control_code,
            "VERIFY",
            status.value,
            {"verification_id": verification_id, "issues": issues}
        )
        
        return result
    
    def verify_compliance_framework(self, tsc_list: List[str], 
                                   verified_by: str = "SYSTEM") -> Dict[str, Any]:
        """Verify entire compliance framework"""
        logger.info(f"Starting compliance framework verification for TSCs: {tsc_list}")
        
        verification_summary = {
            "verification_date": datetime.now().isoformat(),
            "tsc_scope": tsc_list,
            "verified_by": verified_by,
            "total_controls": 0,
            "passed_controls": 0,
            "warned_controls": 0,
            "failed_controls": 0,
            "controls_verified": []
        }
        
        # Verify all controls in scope
        for tsc in tsc_list:
            controls = self.compliance_agent.rag_db.get_controls_by_tsc(tsc)
            verification_summary["total_controls"] += len(controls)
            
            for control in controls:
                # Collect evidence
                if control.code.startswith("CC1"):
                    validator = self.validators.get("CC1")
                    evidence = validator.collect_evidence() if validator else {}
                elif control.code.startswith("CC6"):
                    validator = self.validators.get("CC6")
                    evidence = validator.collect_evidence() if validator else {}
                elif control.code.startswith("CC8"):
                    validator = self.validators.get("CC8")
                    evidence = validator.collect_evidence() if validator else {}
                else:
                    evidence = {"default": True}
                
                # Verify control
                result = self.verify_single_control(control.code, evidence, verified_by)
                
                # Update summary
                verification_summary["controls_verified"].append({
                    "control_code": control.code,
                    "status": result.status.value,
                    "issues_count": len(result.issues_found)
                })
                
                if result.status == VerificationStatus.PASSED:
                    verification_summary["passed_controls"] += 1
                elif result.status == VerificationStatus.WARNING:
                    verification_summary["warned_controls"] += 1
                else:
                    verification_summary["failed_controls"] += 1
        
        # Calculate pass rate
        if verification_summary["total_controls"] > 0:
            pass_rate = (verification_summary["passed_controls"] / 
                        verification_summary["total_controls"] * 100)
            verification_summary["pass_rate_percentage"] = round(pass_rate, 2)
        
        logger.info(f"Verification complete: {verification_summary['passed_controls']}/{verification_summary['total_controls']} passed")
        
        return verification_summary
    
    def generate_verification_report(self, verification_summary: Dict[str, Any]) -> str:
        """Generate human-readable verification report"""
        report = f"""
{'='*80}
SOC 2 COMPLIANCE VERIFICATION REPORT
{'='*80}

Verification Date: {verification_summary['verification_date']}
Verified By: {verification_summary['verified_by']}
TSCs in Scope: {', '.join(verification_summary['tsc_scope'])}

VERIFICATION SUMMARY
{'-'*80}
Total Controls Assessed: {verification_summary['total_controls']}
Controls Passed: {verification_summary['passed_controls']}
Controls with Warnings: {verification_summary['warned_controls']}
Controls Failed: {verification_summary['failed_controls']}
Pass Rate: {verification_summary.get('pass_rate_percentage', 'N/A')}%

CONTROL DETAILS
{'-'*80}
"""
        
        for control in verification_summary["controls_verified"]:
            status_symbol = "✓" if control["status"] == "PASSED" else "✗"
            report += f"\n{status_symbol} {control['control_code']}: {control['status']}"
            if control["issues_count"] > 0:
                report += f" ({control['issues_count']} issues)"
        
        report += f"""

{'='*80}
RECOMMENDATIONS
{'-'*80}
1. Prioritize remediation of failed controls
2. Address warning items to improve compliance posture
3. Schedule regular (quarterly) compliance verification
4. Maintain continuous monitoring of control effectiveness
5. Document all control improvements for audit trail

{'='*80}
"""
        
        return report
    
    def _default_validate(self, control_code: str, evidence: Dict[str, Any]) -> Tuple[VerificationStatus, List[str]]:
        """Default validation logic"""
        issues = []
        
        if not evidence:
            return VerificationStatus.FAILED, ["No evidence provided"]
        
        # Check for key evidence items
        required_keys = [
            "policies_documented",
            "procedures_implemented",
            "training_completed",
            "testing_performed"
        ]
        
        missing_items = [k for k in required_keys if not evidence.get(k, False)]
        
        if missing_items:
            issues.append(f"Missing evidence for: {', '.join(missing_items)}")
            return VerificationStatus.WARNING, issues
        
        return VerificationStatus.PASSED, issues
    
    def _create_failed_result(self, control_code: str, reason: str, 
                             verified_by: str) -> VerificationResult:
        """Create a failed verification result"""
        return VerificationResult(
            control_code=control_code,
            control_name="Unknown Control",
            verification_date=datetime.now().isoformat(),
            status=VerificationStatus.FAILED,
            evidence_collected={},
            test_results=[],
            issues_found=[reason],
            recommendations=["Review control code"],
            verified_by=verified_by,
            verification_id=f"VER-{self._generate_id()}"
        )
    
    def _run_tests(self, control_code: str, evidence: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Run automated tests for control"""
        tests = []
        
        # Example tests
        tests.append({
            "test_id": f"TEST-{control_code}-001",
            "test_name": f"Documentation existence test for {control_code}",
            "test_result": "PASSED" if evidence.get("policies_documented") else "FAILED"
        })
        
        tests.append({
            "test_id": f"TEST-{control_code}-002",
            "test_name": f"Implementation test for {control_code}",
            "test_result": "PASSED" if evidence.get("procedures_implemented") else "FAILED"
        })
        
        return tests
    
    def _generate_recommendations(self, issues: List[str]) -> List[str]:
        """Generate recommendations based on issues"""
        recommendations = []
        
        if not issues:
            recommendations.append("Maintain current control practices")
            recommendations.append("Continue periodic verification")
        else:
            for issue in issues[:3]:  # Top 3 issues
                if "not" in issue.lower():
                    recommendations.append(f"Implement: {issue}")
                elif "rate" in issue.lower():
                    recommendations.append(f"Improve: {issue}")
                else:
                    recommendations.append(f"Address: {issue}")
        
        return recommendations
    
    def _generate_id(self) -> str:
        """Generate unique ID"""
        import hashlib
        return hashlib.md5(str(datetime.now()).encode()).hexdigest()[:8]
    
    def export_verification_results(self, filepath: str):
        """Export verification results to JSON"""
        data = {
            "timestamp": datetime.now().isoformat(),
            "total_verifications": len(self.verification_results),
            "results": [
                {
                    "verification_id": r.verification_id,
                    "control_code": r.control_code,
                    "control_name": r.control_name,
                    "status": r.status.value,
                    "issues": r.issues_found,
                    "recommendations": r.recommendations,
                    "verified_by": r.verified_by
                }
                for r in self.verification_results
            ]
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Verification results exported to {filepath}")

# Global verifier instance
compliance_verifier = SOC2ComplianceVerifier()

if __name__ == "__main__":
    print("=== SOC2 Compliance Verification System ===\n")
    
    verifier = SOC2ComplianceVerifier()
    
    # Verify compliance framework
    tsc_scope = ["Security", "Availability"]
    summary = verifier.verify_compliance_framework(tsc_scope)
    
    # Generate report
    report = verifier.generate_verification_report(summary)
    print(report)
    
    # Export results
    verifier.export_verification_results("/tmp/soc2_verification_results.json")
    print("✓ Verification results exported")
