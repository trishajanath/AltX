"""
SOC2 Compliance Agent
Validates systems, code, and configurations against SOC2 Trust Services Criteria
Uses RAG database for accurate compliance assessment
"""

from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
import json
from soc2_rag_database import rag_database, ControlRequirement, TrustServiceCriteria

class ComplianceLevel(Enum):
    """Compliance assessment levels"""
    COMPLIANT = "COMPLIANT"
    PARTIAL = "PARTIAL"
    NON_COMPLIANT = "NON_COMPLIANT"
    NOT_ASSESSED = "NOT_ASSESSED"

@dataclass
class ComplianceGap:
    """Represents a compliance gap/finding"""
    control_code: str
    control_name: str
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    gap_description: str
    remediation_steps: List[str]
    estimated_effort: str  # QUICK, MEDIUM, COMPLEX
    timeline_days: int
    affected_systems: List[str]

@dataclass
class ComplianceAssessment:
    """Results of a compliance assessment"""
    assessment_id: str
    assessment_date: str
    assessed_systems: List[str]
    tsc_scope: List[str]  # Trust Services Criteria in scope
    overall_compliance_level: ComplianceLevel
    compliance_percentage: float
    gaps: List[ComplianceGap]
    strengths: List[str]
    recommendations: List[str]
    next_steps: List[str]

class SOC2ComplianceAgent:
    """AI-powered SOC2 Compliance Assessment Agent"""
    
    def __init__(self):
        self.rag_db = rag_database
        self.assessments_history: List[ComplianceAssessment] = []
        self.control_evidence: Dict[str, Dict[str, Any]] = {}
    
    def assess_control(self, control_code: str, evidence: Dict[str, Any]) -> Tuple[ComplianceLevel, str]:
        """
        Assess a specific control against evidence
        Returns (compliance_level, explanation)
        """
        control = self.rag_db.get_control(control_code)
        if not control:
            return ComplianceLevel.NOT_ASSESSED, f"Control {control_code} not found"
        
        # Score based on provided evidence
        score = self._evaluate_evidence(control, evidence)
        
        if score >= 0.9:
            level = ComplianceLevel.COMPLIANT
            explanation = f"Control {control_code} meets all requirements"
        elif score >= 0.7:
            level = ComplianceLevel.PARTIAL
            explanation = f"Control {control_code} partially implemented (Score: {score*100:.1f}%)"
        else:
            level = ComplianceLevel.NON_COMPLIANT
            explanation = f"Control {control_code} does not meet requirements (Score: {score*100:.1f}%)"
        
        # Store evidence
        self.control_evidence[control_code] = {
            "evidence": evidence,
            "assessment_date": datetime.now().isoformat(),
            "compliance_level": level.value,
            "score": score
        }
        
        return level, explanation
    
    def _evaluate_evidence(self, control: ControlRequirement, evidence: Dict[str, Any]) -> float:
        """
        Evaluate evidence against control requirements
        Returns score from 0.0 to 1.0
        """
        if not evidence:
            return 0.0
        
        score = 0.0
        evidence_keys = set(evidence.keys())
        
        # Check for policy documentation
        if "policies_documented" in evidence and evidence["policies_documented"]:
            score += 0.15
        
        # Check for procedures
        if "procedures_implemented" in evidence and evidence["procedures_implemented"]:
            score += 0.15
        
        # Check for training
        if "training_completed" in evidence and evidence["training_completed"]:
            score += 0.10
        
        # Check for automation
        if "automated_controls" in evidence and evidence["automated_controls"]:
            score += 0.15
        
        # Check for monitoring
        if "monitoring_enabled" in evidence and evidence["monitoring_enabled"]:
            score += 0.15
        
        # Check for testing/evidence
        if "testing_performed" in evidence and evidence["testing_performed"]:
            score += 0.15
        
        # Check for documentation
        if "documentation_maintained" in evidence and evidence["documentation_maintained"]:
            score += 0.10
        
        return min(score, 1.0)
    
    def assess_systems(self, system_configs: Dict[str, Dict[str, Any]], 
                      tsc_scope: List[str]) -> ComplianceAssessment:
        """
        Comprehensive assessment of systems against SOC2 controls
        
        Args:
            system_configs: Dictionary of system names to their configurations/evidence
            tsc_scope: List of Trust Services Criteria to assess
            
        Returns:
            ComplianceAssessment object with findings
        """
        assessment_id = f"SOC2-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        gaps = []
        strengths = []
        compliant_count = 0
        partial_count = 0
        non_compliant_count = 0
        
        # Get all controls in scope
        in_scope_controls = []
        for tsc in tsc_scope:
            in_scope_controls.extend(self.rag_db.get_controls_by_tsc(tsc))
        
        # Assess each control
        for control in in_scope_controls:
            # Prepare evidence from system configs
            evidence = self._prepare_evidence(control.code, system_configs)
            
            # Assess control
            compliance_level, explanation = self.assess_control(control.code, evidence)
            
            if compliance_level == ComplianceLevel.COMPLIANT:
                compliant_count += 1
                strengths.append(f"{control.code}: {control.name}")
            elif compliance_level == ComplianceLevel.PARTIAL:
                partial_count += 1
                gap = self._create_gap(control, "Partial implementation", "MEDIUM")
                gaps.append(gap)
            else:
                non_compliant_count += 1
                gap = self._create_gap(control, "Not implemented", "HIGH")
                gaps.append(gap)
        
        # Calculate overall compliance
        total_controls = len(in_scope_controls)
        compliance_percentage = ((compliant_count + partial_count * 0.5) / total_controls * 100) if total_controls > 0 else 0
        
        # Determine overall compliance level
        if compliance_percentage >= 90:
            overall_level = ComplianceLevel.COMPLIANT
        elif compliance_percentage >= 70:
            overall_level = ComplianceLevel.PARTIAL
        else:
            overall_level = ComplianceLevel.NON_COMPLIANT
        
        # Generate recommendations
        recommendations = self._generate_recommendations(gaps, strengths)
        next_steps = self._generate_next_steps(gaps, overall_level)
        
        assessment = ComplianceAssessment(
            assessment_id=assessment_id,
            assessment_date=datetime.now().isoformat(),
            assessed_systems=list(system_configs.keys()),
            tsc_scope=tsc_scope,
            overall_compliance_level=overall_level,
            compliance_percentage=round(compliance_percentage, 2),
            gaps=gaps,
            strengths=strengths[:10],  # Top 10 strengths
            recommendations=recommendations,
            next_steps=next_steps
        )
        
        self.assessments_history.append(assessment)
        return assessment
    
    def _prepare_evidence(self, control_code: str, system_configs: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Prepare evidence dictionary from system configurations"""
        evidence = {}
        
        # Aggregate evidence from all systems
        for system_name, config in system_configs.items():
            if isinstance(config, dict):
                for key, value in config.items():
                    if key not in evidence:
                        evidence[key] = []
                    evidence[key].append(value)
        
        # Determine boolean flags based on evidence presence
        prepared = {
            "policies_documented": len(evidence.get("policies", [])) > 0,
            "procedures_implemented": len(evidence.get("procedures", [])) > 0,
            "training_completed": len(evidence.get("training", [])) > 0,
            "automated_controls": len(evidence.get("automation", [])) > 0,
            "monitoring_enabled": len(evidence.get("monitoring", [])) > 0,
            "testing_performed": len(evidence.get("testing", [])) > 0,
            "documentation_maintained": len(evidence.get("documentation", [])) > 0
        }
        
        return prepared
    
    def _create_gap(self, control: ControlRequirement, issue: str, severity: str) -> ComplianceGap:
        """Create a compliance gap from control analysis"""
        
        # Determine timeline based on severity and complexity
        timeline_map = {
            "CRITICAL": 7,
            "HIGH": 14,
            "MEDIUM": 30,
            "LOW": 60
        }
        
        # Determine effort
        if len(control.requirements) > 5:
            effort = "COMPLEX"
        elif len(control.requirements) > 3:
            effort = "MEDIUM"
        else:
            effort = "QUICK"
        
        return ComplianceGap(
            control_code=control.code,
            control_name=control.name,
            severity=severity,
            gap_description=issue,
            remediation_steps=control.implementation_tips,
            estimated_effort=effort,
            timeline_days=timeline_map.get(severity, 30),
            affected_systems=["All"]
        )
    
    def _generate_recommendations(self, gaps: List[ComplianceGap], 
                                 strengths: List[str]) -> List[str]:
        """Generate recommendations based on assessment results"""
        recommendations = []
        
        # Categorize gaps by severity
        critical_gaps = [g for g in gaps if g.severity == "CRITICAL"]
        high_gaps = [g for g in gaps if g.severity == "HIGH"]
        
        if critical_gaps:
            recommendations.append(
                f"URGENT: Address {len(critical_gaps)} critical gaps immediately. "
                f"These pose direct risk to compliance status."
            )
        
        if high_gaps:
            recommendations.append(
                f"Prioritize remediation of {len(high_gaps)} high-severity findings "
                f"within 30 days to reduce compliance risk."
            )
        
        if not gaps:
            recommendations.append(
                "All assessed controls are compliant. Maintain current practices "
                "and continue periodic assessments."
            )
        
        recommendations.append(
            "Implement continuous monitoring of control effectiveness "
            "to maintain SOC2 compliance."
        )
        
        recommendations.append(
            "Establish compliance dashboard for real-time visibility into "
            "control status and audit readiness."
        )
        
        return recommendations
    
    def _generate_next_steps(self, gaps: List[ComplianceGap], 
                            compliance_level: ComplianceLevel) -> List[str]:
        """Generate actionable next steps"""
        next_steps = []
        
        if compliance_level == ComplianceLevel.COMPLIANT:
            next_steps.append("Schedule SOC2 Type 1 audit with qualified auditor")
            next_steps.append("Document control operating effectiveness for past 6 months")
            next_steps.append("Prepare for SOC2 Type 2 audit in 12 months")
        elif compliance_level == ComplianceLevel.PARTIAL:
            next_steps.append(f"Create remediation plan for {len(gaps)} identified gaps")
            next_steps.append("Assign ownership and timelines for each gap")
            next_steps.append("Implement highest-severity items first")
            next_steps.append("Re-assess controls after remediation")
        else:
            next_steps.append("Conduct gap analysis workshop with stakeholders")
            next_steps.append("Develop comprehensive remediation roadmap")
            next_steps.append("Allocate resources for control implementation")
            next_steps.append("Establish governance and oversight structure")
        
        return next_steps
    
    def get_control_requirements(self, control_code: str) -> Optional[ControlRequirement]:
        """Get detailed requirements for a specific control"""
        return self.rag_db.get_control(control_code)
    
    def search_by_keyword(self, keyword: str) -> List[ControlRequirement]:
        """Search controls by keyword"""
        return self.rag_db.search_controls(keyword)
    
    def generate_report(self, assessment: ComplianceAssessment) -> str:
        """Generate human-readable compliance report"""
        report = f"""
{'='*80}
SOC 2 COMPLIANCE ASSESSMENT REPORT
{'='*80}

Assessment ID: {assessment.assessment_id}
Assessment Date: {assessment.assessment_date}

EXECUTIVE SUMMARY
{'-'*80}
Overall Compliance Level: {assessment.overall_compliance_level.value}
Compliance Percentage: {assessment.compliance_percentage}%
Systems Assessed: {', '.join(assessment.assessed_systems)}
Trust Services Criteria Scope: {', '.join(assessment.tsc_scope)}

KEY FINDINGS
{'-'*80}
Total Gaps Identified: {len(assessment.gaps)}
Critical Findings: {len([g for g in assessment.gaps if g.severity == 'CRITICAL'])}
High Findings: {len([g for g in assessment.gaps if g.severity == 'HIGH'])}
Medium Findings: {len([g for g in assessment.gaps if g.severity == 'MEDIUM'])}
Low Findings: {len([g for g in assessment.gaps if g.severity == 'LOW'])}

CONTROL GAPS
{'-'*80}
"""
        
        for gap in sorted(assessment.gaps, key=lambda g: g.severity):
            report += f"""
Control: {gap.control_code} - {gap.control_name}
Severity: {gap.severity}
Issue: {gap.gap_description}
Estimated Effort: {gap.estimated_effort}
Timeline: {gap.timeline_days} days

Remediation Steps:
"""
            for i, step in enumerate(gap.remediation_steps, 1):
                report += f"  {i}. {step}\n"
        
        report += f"""
STRENGTHS
{'-'*80}
"""
        for strength in assessment.strengths:
            report += f"✓ {strength}\n"
        
        report += f"""
RECOMMENDATIONS
{'-'*80}
"""
        for i, rec in enumerate(assessment.recommendations, 1):
            report += f"{i}. {rec}\n"
        
        report += f"""
NEXT STEPS
{'-'*80}
"""
        for i, step in enumerate(assessment.next_steps, 1):
            report += f"{i}. {step}\n"
        
        report += f"""
{'='*80}
"""
        
        return report
    
    def export_assessment(self, assessment: ComplianceAssessment, filepath: str):
        """Export assessment to JSON file"""
        data = {
            "assessment_id": assessment.assessment_id,
            "assessment_date": assessment.assessment_date,
            "assessed_systems": assessment.assessed_systems,
            "tsc_scope": assessment.tsc_scope,
            "overall_compliance_level": assessment.overall_compliance_level.value,
            "compliance_percentage": assessment.compliance_percentage,
            "gaps": [
                {
                    "control_code": gap.control_code,
                    "control_name": gap.control_name,
                    "severity": gap.severity,
                    "gap_description": gap.gap_description,
                    "remediation_steps": gap.remediation_steps,
                    "estimated_effort": gap.estimated_effort,
                    "timeline_days": gap.timeline_days
                }
                for gap in assessment.gaps
            ],
            "strengths": assessment.strengths,
            "recommendations": assessment.recommendations,
            "next_steps": assessment.next_steps
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)


# Global agent instance
compliance_agent = SOC2ComplianceAgent()

if __name__ == "__main__":
    # Example usage
    agent = SOC2ComplianceAgent()
    
    # Sample system configuration
    sample_systems = {
        "Web Application": {
            "policies": ["Security Policy v1.0", "Access Control Policy"],
            "procedures": ["Change Management Procedure", "Incident Response Procedure"],
            "training": ["Security Awareness Training", "Data Protection Training"],
            "automation": ["Automated access reviews"],
            "monitoring": ["System logs", "Access logs", "Audit trails"],
            "testing": ["Annual penetration test", "Control testing"],
            "documentation": ["Control documentation", "Evidence repository"]
        },
        "Database": {
            "policies": ["Data Protection Policy"],
            "procedures": ["Backup Procedure", "Disaster Recovery Procedure"],
            "monitoring": ["Database logs", "Performance monitoring"],
            "documentation": ["Database documentation"]
        }
    }
    
    # Perform assessment
    assessment = agent.assess_systems(
        sample_systems,
        tsc_scope=["Security", "Availability"]
    )
    
    # Generate and print report
    report = agent.generate_report(assessment)
    print(report)
    
    # Export assessment
    agent.export_assessment(assessment, "/tmp/soc2_assessment.json")
    print(f"\nAssessment exported to /tmp/soc2_assessment.json")
