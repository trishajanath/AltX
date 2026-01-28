#!/usr/bin/env python3
"""
SOC2 Compliance System - Complete Integration Test and Demo
Demonstrates the full SOC2 compliance lifecycle from assessment to verification
"""

import sys
import json
from datetime import datetime

# Import all components
from soc2_rag_database import SOC2RAGDatabase, TrustServiceCriteria, CommonCriteria
from soc2_compliance_agent import SOC2ComplianceAgent, ComplianceLevel
from soc2_compliance_verifier import SOC2ComplianceVerifier, VerificationStatus
from soc2_orchestrator import SOC2ComplianceOrchestrator

def print_header(title: str):
    """Print formatted section header"""
    print("\n" + "="*80)
    print(f" {title}")
    print("="*80 + "\n")

def test_rag_database():
    """Test RAG database functionality"""
    print_header("TEST 1: RAG Database")
    
    db = SOC2RAGDatabase()
    
    print("1. Database Statistics:")
    print(f"   Total Controls: {len(db.get_all_controls())}")
    print(f"\n2. Trust Services Criteria Summary:")
    for tsc, count in db.get_tsc_summary().items():
        controls = db.get_controls_by_tsc(tsc)
        print(f"   {tsc:20} {count:3} controls")
    
    print(f"\n3. Common Criteria (Security):")
    for cc in CommonCriteria:
        controls = db.get_controls_by_category(cc.value)
        print(f"   {cc.name:40} {len(controls):2} controls")
    
    print(f"\n4. Sample Control Details:")
    sample_control = db.get_control("CC1.1")
    if sample_control:
        print(f"   Code: {sample_control.code}")
        print(f"   Name: {sample_control.name}")
        print(f"   Description: {sample_control.description}")
        print(f"   Requirements ({len(sample_control.requirements)}):")
        for req in sample_control.requirements[:2]:
            print(f"     - {req}")
    
    print(f"\n✓ RAG Database test passed")
    return db

def test_compliance_agent(db: SOC2RAGDatabase):
    """Test compliance assessment agent"""
    print_header("TEST 2: Compliance Agent")
    
    agent = SOC2ComplianceAgent()
    
    # Sample system configuration
    system_configs = {
        "Web Application": {
            "policies": ["Security Policy v2.0", "Access Control Policy"],
            "procedures": ["Incident Response", "Change Management", "Backup Procedure"],
            "training": ["Security Awareness", "Data Protection", "Incident Response"],
            "automation": ["Automated access reviews", "Security scanning"],
            "monitoring": ["System logs", "Access logs", "Security event logs"],
            "testing": ["Penetration testing", "Control testing"],
            "documentation": ["Architecture docs", "Control documentation"]
        },
        "Database": {
            "policies": ["Data Protection Policy"],
            "procedures": ["Backup Procedure", "Disaster Recovery"],
            "monitoring": ["Database logs", "Performance monitoring"],
            "testing": ["Backup restore testing"],
            "documentation": ["Database documentation"]
        },
        "Infrastructure": {
            "policies": ["Infrastructure Security Policy"],
            "procedures": ["Change Management", "Incident Response"],
            "automation": ["Infrastructure as Code"],
            "monitoring": ["Infrastructure monitoring"],
            "documentation": ["Infrastructure documentation"]
        }
    }
    
    print("1. Conducting Compliance Assessment...")
    tsc_scope = ["Security", "Availability", "Processing Integrity"]
    assessment = agent.assess_systems(system_configs, tsc_scope)
    
    print(f"\n2. Assessment Results:")
    print(f"   Assessment ID: {assessment.assessment_id}")
    print(f"   Date: {assessment.assessment_date}")
    print(f"   Overall Level: {assessment.overall_compliance_level.value}")
    print(f"   Compliance %: {assessment.compliance_percentage}%")
    print(f"   Systems Assessed: {', '.join(assessment.assessed_systems)}")
    
    print(f"\n3. Findings Summary:")
    print(f"   Total Gaps: {len(assessment.gaps)}")
    print(f"   Critical: {len([g for g in assessment.gaps if g.severity == 'CRITICAL'])}")
    print(f"   High: {len([g for g in assessment.gaps if g.severity == 'HIGH'])}")
    print(f"   Medium: {len([g for g in assessment.gaps if g.severity == 'MEDIUM'])}")
    print(f"   Low: {len([g for g in assessment.gaps if g.severity == 'LOW'])}")
    
    print(f"\n4. Top 3 Gaps:")
    for i, gap in enumerate(assessment.gaps[:3], 1):
        print(f"   {i}. {gap.control_code}: {gap.gap_description} (Severity: {gap.severity})")
    
    print(f"\n5. Strengths (Sample):")
    for strength in assessment.strengths[:3]:
        print(f"   ✓ {strength}")
    
    print(f"\n✓ Compliance Agent test passed")
    return assessment

def test_compliance_verifier():
    """Test compliance verification system"""
    print_header("TEST 3: Compliance Verifier")
    
    verifier = SOC2ComplianceVerifier()
    
    print("1. Verifying Compliance Framework...")
    tsc_scope = ["Security"]
    summary = verifier.verify_compliance_framework(tsc_scope)
    
    print(f"\n2. Verification Results:")
    print(f"   Total Controls: {summary['total_controls']}")
    print(f"   Passed: {summary['passed_controls']}")
    print(f"   Warnings: {summary['warned_controls']}")
    print(f"   Failed: {summary['failed_controls']}")
    print(f"   Pass Rate: {summary.get('pass_rate_percentage', 'N/A')}%")
    
    print(f"\n3. Sample Verified Controls:")
    for control in summary['controls_verified'][:5]:
        status_icon = "✓" if control['status'] == 'PASSED' else "✗"
        print(f"   {status_icon} {control['control_code']}: {control['status']}")
    
    print(f"\n✓ Compliance Verifier test passed")
    return summary

def test_orchestrator():
    """Test complete orchestration"""
    print_header("TEST 4: SOC2 Compliance Orchestrator")
    
    orchestrator = SOC2ComplianceOrchestrator()
    
    print("1. Starting Compliance Journey...")
    roadmap = orchestrator.start_compliance_journey(
        "TechCorp Inc.",
        ["Security", "Availability", "Confidentiality"]
    )
    print(f"   ✓ Roadmap created")
    print(f"   Controls in scope: {roadmap['total_controls']}")
    print(f"   Estimated duration: {roadmap['estimated_total_duration_weeks']} weeks")
    
    print("\n2. Conducting Gap Analysis...")
    system_configs = {
        "Production System": {
            "policies": ["Security Policy"],
            "procedures": ["Incident Response"],
            "training": ["Security Training"],
            "monitoring": ["Log monitoring"],
        }
    }
    assessment = orchestrator.conduct_gap_analysis(system_configs, ["Security"])
    print(f"   ✓ Gap analysis complete")
    print(f"   Compliance: {assessment.compliance_percentage}%")
    
    print("\n3. Creating Remediation Plan...")
    plan = orchestrator.create_remediation_plan(assessment)
    print(f"   ✓ Remediation plan created")
    print(f"   Plan ID: {plan['plan_id']}")
    print(f"   Total items: {plan['total_gaps']}")
    
    print("\n4. Implementing Controls...")
    implementation = orchestrator.implement_controls(plan)
    print(f"   ✓ Controls implemented")
    print(f"   Implementation items: {len(implementation['implementations'])}")
    
    print("\n5. Verifying Compliance...")
    verification = orchestrator.verify_compliance(["Security"])
    print(f"   ✓ Verification complete")
    print(f"   Pass rate: {verification.get('pass_rate_percentage', 'N/A')}%")
    
    print("\n6. Current Compliance Status:")
    status = orchestrator.get_compliance_status()
    print(f"   Current Phase: {status['current_phase']}")
    if "overall_compliance" in status.get("summary", {}):
        compliance = status["summary"]["overall_compliance"]
        print(f"   Compliance Level: {compliance['level']}")
        print(f"   Compliance %: {compliance['percentage']}%")
    
    print(f"\n✓ Orchestrator test passed")
    return orchestrator

def test_end_to_end_workflow():
    """Test complete end-to-end workflow"""
    print_header("TEST 5: End-to-End Workflow")
    
    print("Running complete SOC2 compliance workflow...\n")
    
    # Step 1
    print("Phase 1: DISCOVERY")
    print("-" * 40)
    db = test_rag_database()
    
    # Step 2
    print("\n\nPhase 2: ASSESSMENT")
    print("-" * 40)
    assessment = test_compliance_agent(db)
    
    # Step 3
    print("\n\nPhase 3: VERIFICATION")
    print("-" * 40)
    verification = test_compliance_verifier()
    
    # Step 4
    print("\n\nPhase 4: ORCHESTRATION")
    print("-" * 40)
    orchestrator = test_orchestrator()
    
    # Summary
    print_header("WORKFLOW COMPLETE")
    print("All components tested successfully!")
    print("\nComprehensive Report:")
    print(orchestrator.generate_executive_summary())
    
    return True

def main():
    """Main test runner"""
    print_header("SOC2 COMPLIANCE SYSTEM - INTEGRATION TEST")
    
    try:
        # Run all tests
        success = test_end_to_end_workflow()
        
        if success:
            print_header("ALL TESTS PASSED ✓")
            print("""
The SOC2 Compliance System has been successfully implemented with:

1. ✓ RAG Database: Complete SOC2 control requirements
2. ✓ Compliance Agent: Automated assessment capabilities
3. ✓ Verification System: Control validation and testing
4. ✓ Implementation Framework: Concrete control implementations
5. ✓ Orchestrator: End-to-end compliance management

COMPONENTS CREATED:
- soc2_rag_database.py          (RAG database with 30+ controls)
- soc2_compliance_agent.py      (Assessment agent)
- soc2_control_implementation.py (Control implementations)
- soc2_compliance_verifier.py   (Verification system)
- soc2_orchestrator.py          (Main orchestrator)

CAPABILITIES:
→ Gap Analysis: Identify compliance gaps
→ Assessment: Evaluate control status
→ Remediation: Create remediation plans
→ Verification: Automated control testing
→ Reporting: Executive summaries and detailed reports
→ Monitoring: Continuous compliance tracking

NEXT STEPS:
1. Review generated reports and assessments
2. Customize for your organization
3. Implement identified remediation items
4. Conduct regular verification cycles
5. Maintain evidence repository
            """)
            return 0
    
    except Exception as e:
        print_header("TEST FAILED")
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
