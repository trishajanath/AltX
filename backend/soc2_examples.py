"""
SOC2 Compliance System - Practical Usage Examples
Complete real-world examples of using the system
"""

from soc2_orchestrator import SOC2ComplianceOrchestrator
from soc2_rag_database import SOC2RAGDatabase
from soc2_compliance_agent import SOC2ComplianceAgent
from soc2_compliance_verifier import SOC2ComplianceVerifier

# ============ EXAMPLE 1: Quick Compliance Check ============

def example_quick_compliance_check():
    """
    Scenario: Need quick compliance assessment for management
    Time: 15 minutes
    """
    print("\n" + "="*80)
    print("EXAMPLE 1: Quick Compliance Check")
    print("="*80)
    
    orchestrator = SOC2ComplianceOrchestrator()
    
    # Quick assessment with minimal systems
    systems = {
        "Main Application": {
            "policies": ["Security Policy v2.0"],
            "procedures": ["Incident Response"],
            "monitoring": ["Application logs"]
        }
    }
    
    assessment = orchestrator.conduct_gap_analysis(systems, ["Security"])
    
    print(f"\nCompliance Status: {assessment.overall_compliance_level.value}")
    print(f"Compliance Score: {assessment.compliance_percentage}%")
    print(f"Critical Issues: {len([g for g in assessment.gaps if g.severity == 'CRITICAL'])}")
    print(f"\nAction: " + ("Ready for audit" if assessment.compliance_percentage >= 90 else "Remediation needed"))

# ============ EXAMPLE 2: Full Compliance Journey ============

def example_full_compliance_journey():
    """
    Scenario: Starting SOC2 compliance from scratch
    Duration: 22 weeks
    """
    print("\n" + "="*80)
    print("EXAMPLE 2: Full Compliance Journey (22 weeks)")
    print("="*80)
    
    orchestrator = SOC2ComplianceOrchestrator()
    
    # Step 1: Create roadmap
    print("\n[WEEK 1-2] PHASE 1: DISCOVERY")
    roadmap = orchestrator.start_compliance_journey(
        "TechStartup Inc.",
        ["Security", "Availability", "Confidentiality"]
    )
    print(f"✓ Roadmap created with {roadmap['total_controls']} controls")
    print(f"✓ Estimated timeline: {roadmap['estimated_total_duration_weeks']} weeks")
    
    # Step 2: Assess systems
    print("\n[WEEK 3-6] PHASE 2: ASSESSMENT")
    systems = {
        "SaaS Platform": {
            "policies": ["Security Policy"],
            "procedures": ["Change Management", "Incident Response"],
            "training": ["Security Training"],
            "monitoring": ["System logs"],
            "documentation": ["Architecture"]
        },
        "Database": {
            "policies": ["Data Protection"],
            "procedures": ["Backup"],
            "monitoring": ["Database logs"]
        }
    }
    
    assessment = orchestrator.conduct_gap_analysis(systems, ["Security"])
    print(f"✓ Assessment complete: {assessment.compliance_percentage}% compliant")
    print(f"✓ Identified {len(assessment.gaps)} gaps")
    
    # Step 3: Create remediation plan
    print("\n[WEEK 7] PHASE 3: PLANNING")
    plan = orchestrator.create_remediation_plan(assessment)
    print(f"✓ Remediation plan created: {plan['plan_id']}")
    
    critical = plan['priority_breakdown']['CRITICAL']
    high = plan['priority_breakdown']['HIGH']
    print(f"✓ Priority breakdown: {critical} Critical, {high} High priority items")
    
    # Step 4: Implementation
    print("\n[WEEK 8-18] PHASE 3: REMEDIATION")
    implementation = orchestrator.implement_controls(plan)
    print(f"✓ Controls implemented: {len(implementation['implementations'])} items")
    
    # Step 5: Verification
    print("\n[WEEK 19-22] PHASE 4: VERIFICATION")
    verification = orchestrator.verify_compliance(["Security"])
    print(f"✓ Verification complete: {verification['pass_rate_percentage']}% pass rate")
    
    # Status
    print("\n[WEEK 22] FINAL STATUS")
    status = orchestrator.get_compliance_status()
    print(f"✓ Current Phase: {status['current_phase']}")
    print("\n→ Ready for SOC2 Type 1 audit")

# ============ EXAMPLE 3: Gap Analysis for Specific TSC ============

def example_gap_analysis_specific_tsc():
    """
    Scenario: Need gap analysis for Availability TSC
    Focus: Data centers and SaaS services
    """
    print("\n" + "="*80)
    print("EXAMPLE 3: Availability TSC Gap Analysis")
    print("="*80)
    
    agent = SOC2ComplianceAgent()
    
    # Cloud infrastructure assessment
    systems = {
        "Production Cloud": {
            "procedures": ["Disaster Recovery Plan"],
            "monitoring": ["Infrastructure monitoring"],
            "testing": ["DR test results"]
        },
        "Backup System": {
            "procedures": ["Backup procedure"],
            "documentation": ["Backup documentation"]
        }
    }
    
    assessment = agent.assess_systems(systems, ["Availability"])
    
    print(f"\nAvailability Compliance: {assessment.compliance_percentage}%")
    print(f"\nGaps identified:")
    for gap in assessment.gaps:
        print(f"  • {gap.control_code}: {gap.gap_description}")
        print(f"    Severity: {gap.severity}")
        print(f"    Timeline: {gap.timeline_days} days")

# ============ EXAMPLE 4: Control Implementation Validation ============

def example_control_validation():
    """
    Scenario: Validate that implemented controls meet requirements
    Use: Ongoing control verification
    """
    print("\n" + "="*80)
    print("EXAMPLE 4: Control Implementation Validation")
    print("="*80)
    
    verifier = SOC2ComplianceVerifier()
    
    # Evidence of implemented CC6 controls
    cc6_evidence = {
        "mfa_enabled_percentage": 1.0,
        "encryption_at_rest": True,
        "encryption_in_transit": True,
        "days_since_last_access_review": 30,
        "failed_login_monitoring": True
    }
    
    print("\nValidating CC6 (Access Controls)...")
    result = verifier.verify_single_control("CC6.1", cc6_evidence)
    
    print(f"Control Code: {result.control_code}")
    print(f"Status: {result.status.value}")
    print(f"Issues Found: {len(result.issues_found)}")
    
    if result.issues_found:
        print("Issues:")
        for issue in result.issues_found:
            print(f"  • {issue}")
    
    print("Recommendations:")
    for rec in result.recommendations:
        print(f"  • {rec}")

# ============ EXAMPLE 5: Search Controls by Keyword ============

def example_search_controls():
    """
    Scenario: Find all controls related to encryption
    Use: Understanding requirements for specific area
    """
    print("\n" + "="*80)
    print("EXAMPLE 5: Search Controls by Keyword")
    print("="*80)
    
    agent = SOC2ComplianceAgent()
    
    print("\nSearching for controls related to 'encryption'...")
    results = agent.search_by_keyword("encryption")
    
    print(f"Found {len(results)} controls:")
    for control in results:
        print(f"\n  {control.code}: {control.name}")
        print(f"  Description: {control.description}")
        print(f"  TSC: {control.trust_service}")

# ============ EXAMPLE 6: Generate Compliance Reports ============

def example_compliance_reports():
    """
    Scenario: Generate reports for audit preparation
    Use: Documentation for auditor
    """
    print("\n" + "="*80)
    print("EXAMPLE 6: Generate Compliance Reports")
    print("="*80)
    
    orchestrator = SOC2ComplianceOrchestrator()
    
    # Quick assessment
    systems = {
        "Application": {
            "policies": ["Security Policy"],
            "procedures": ["Incident Response", "Change Management"],
            "training": ["Security Training"],
            "monitoring": ["Comprehensive logging"],
            "documentation": ["Full documentation"]
        }
    }
    
    assessment = orchestrator.conduct_gap_analysis(systems, ["Security"])
    
    # Generate report
    report = orchestrator.compliance_agent.generate_report(assessment)
    
    print("\n" + report)

# ============ EXAMPLE 7: Timeline-Based Planning ============

def example_timeline_planning():
    """
    Scenario: Understand remediation timeline
    Use: Project planning and resource allocation
    """
    print("\n" + "="*80)
    print("EXAMPLE 7: Timeline-Based Remediation Planning")
    print("="*80)
    
    orchestrator = SOC2ComplianceOrchestrator()
    
    systems = {
        "App": {
            "policies": ["Basic Policy"]
        }
    }
    
    assessment = orchestrator.conduct_gap_analysis(systems, ["Security"])
    plan = orchestrator.create_remediation_plan(assessment)
    
    print("\nREMEDIATION TIMELINE:")
    print(f"\nCRITICAL (Due in 7 days):")
    critical = [item for item in plan['remediation_items'] if item['severity'] == 'CRITICAL']
    for item in critical[:3]:
        print(f"  [{item['estimated_effort']}] {item['control_code']}: {item['description']}")
    
    print(f"\nHIGH (Due in 30 days):")
    high = [item for item in plan['remediation_items'] if item['severity'] == 'HIGH']
    for item in high[:3]:
        print(f"  [{item['estimated_effort']}] {item['control_code']}: {item['description']}")
    
    print(f"\nMEDIUM (Due in 60 days):")
    medium = [item for item in plan['remediation_items'] if item['severity'] == 'MEDIUM']
    for item in medium[:3]:
        print(f"  [{item['estimated_effort']}] {item['control_code']}: {item['description']}")

# ============ EXAMPLE 8: Regular Monitoring & Re-assessment ============

def example_continuous_monitoring():
    """
    Scenario: Regular (quarterly) compliance check
    Use: Maintain compliance status
    """
    print("\n" + "="*80)
    print("EXAMPLE 8: Continuous Monitoring & Quarterly Re-assessment")
    print("="*80)
    
    orchestrator = SOC2ComplianceOrchestrator()
    
    # Current systems (updated quarterly)
    current_systems = {
        "Production": {
            "policies": ["Security Policy v2.1"],
            "procedures": ["Change Management v3", "Incident Response v2"],
            "training": ["Q1 Security Training"],
            "monitoring": ["SIEM", "Log aggregation"],
            "testing": ["Q1 Penetration Test"]
        }
    }
    
    print("\n[QUARTERLY CHECK]")
    assessment = orchestrator.conduct_gap_analysis(current_systems, ["Security"])
    
    print(f"Current Compliance: {assessment.compliance_percentage}%")
    print(f"Open Gaps: {len(assessment.gaps)}")
    print(f"\nStatus: {'COMPLIANT ✓' if assessment.compliance_percentage >= 90 else 'Improvements needed'}")
    
    if assessment.gaps:
        print(f"\nTop gaps to address:")
        for gap in assessment.gaps[:3]:
            print(f"  • {gap.control_code}: {gap.gap_description}")

# ============ EXAMPLE 9: Multi-System Assessment ============

def example_multi_system():
    """
    Scenario: Assess complex multi-system environment
    Use: Enterprise deployments
    """
    print("\n" + "="*80)
    print("EXAMPLE 9: Multi-System Complex Environment Assessment")
    print("="*80)
    
    agent = SOC2ComplianceAgent()
    
    # Enterprise environment
    systems = {
        "Web Application": {
            "policies": ["Application Security Policy"],
            "procedures": ["Deployment Procedure"],
            "training": ["Developer Training"],
            "monitoring": ["Application monitoring"],
            "testing": ["SAST/DAST testing"]
        },
        "Database Layer": {
            "policies": ["Database Security Policy"],
            "procedures": ["Backup and Recovery"],
            "monitoring": ["Database monitoring"],
            "documentation": ["Database documentation"]
        },
        "Infrastructure": {
            "policies": ["Infrastructure Policy"],
            "procedures": ["Change Management"],
            "training": ["Infrastructure Training"],
            "monitoring": ["Infrastructure monitoring"]
        },
        "Security Operations": {
            "procedures": ["Incident Response"],
            "monitoring": ["Security logs"],
            "documentation": ["Security procedures"]
        }
    }
    
    assessment = agent.assess_systems(
        systems,
        ["Security", "Availability", "Confidentiality"]
    )
    
    print(f"\nSystems Assessed: {len(systems)}")
    print(f"Trust Services in Scope: {', '.join(assessment.tsc_scope)}")
    print(f"\nOverall Compliance: {assessment.overall_compliance_level.value}")
    print(f"Compliance Score: {assessment.compliance_percentage}%")
    
    print(f"\nGaps by Severity:")
    print(f"  Critical: {len([g for g in assessment.gaps if g.severity == 'CRITICAL'])}")
    print(f"  High: {len([g for g in assessment.gaps if g.severity == 'HIGH'])}")
    print(f"  Medium: {len([g for g in assessment.gaps if g.severity == 'MEDIUM'])}")
    print(f"  Low: {len([g for g in assessment.gaps if g.severity == 'LOW'])}")

# ============ EXAMPLE 10: Pre-Audit Readiness ============

def example_pre_audit_readiness():
    """
    Scenario: Prepare for SOC2 audit
    Timeline: 2 weeks before audit date
    """
    print("\n" + "="*80)
    print("EXAMPLE 10: Pre-Audit Readiness Check")
    print("="*80)
    
    verifier = SOC2ComplianceVerifier()
    
    print("\n[2 WEEKS BEFORE AUDIT]")
    print("-" * 80)
    
    # Run full verification
    summary = verifier.verify_compliance_framework(
        ["Security", "Availability", "Confidentiality"]
    )
    
    print(f"\nAudit Readiness Assessment:")
    print(f"  Total Controls: {summary['total_controls']}")
    print(f"  Passed: {summary['passed_controls']} ✓")
    print(f"  Warnings: {summary['warned_controls']} ⚠")
    print(f"  Failed: {summary['failed_controls']} ✗")
    
    pass_rate = summary.get('pass_rate_percentage', 0)
    print(f"\nPass Rate: {pass_rate}%")
    
    if pass_rate >= 95:
        print("✓ AUDIT READY - Excellent compliance posture")
    elif pass_rate >= 80:
        print("⚠ MOSTLY READY - Verify warning items")
    else:
        print("✗ NOT READY - Address failed controls immediately")

# ============ Main: Run All Examples ============

if __name__ == "__main__":
    print("\n" + "="*80)
    print("SOC2 COMPLIANCE SYSTEM - PRACTICAL USAGE EXAMPLES")
    print("="*80)
    
    examples = [
        ("Quick Compliance Check", example_quick_compliance_check),
        ("Full Compliance Journey", example_full_compliance_journey),
        ("Gap Analysis - Specific TSC", example_gap_analysis_specific_tsc),
        ("Control Validation", example_control_validation),
        ("Search Controls", example_search_controls),
        ("Generate Reports", example_compliance_reports),
        ("Timeline Planning", example_timeline_planning),
        ("Continuous Monitoring", example_continuous_monitoring),
        ("Multi-System Assessment", example_multi_system),
        ("Pre-Audit Readiness", example_pre_audit_readiness)
    ]
    
    print("\nAvailable Examples:")
    for i, (name, _) in enumerate(examples, 1):
        print(f"  {i:2}. {name}")
    
    print("\n" + "="*80)
    print("Running Example 1: Quick Compliance Check")
    print("="*80)
    
    # Run first example
    example_quick_compliance_check()
    
    print("\n" + "="*80)
    print("To run other examples, call them directly:")
    print("  python3 -c \"from soc2_examples import *; example_full_compliance_journey()\"")
    print("="*80)
