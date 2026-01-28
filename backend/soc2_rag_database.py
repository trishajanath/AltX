"""
SOC2 Compliance RAG (Retrieval-Augmented Generation) Database
Stores SOC2 Trust Services Criteria and Control Requirements in structured format
"""

from typing import List, Dict, Any
from dataclasses import dataclass, asdict
from enum import Enum
import json
from datetime import datetime
import hashlib

class TrustServiceCriteria(Enum):
    """5 Trust Services Criteria for SOC2 Compliance"""
    SECURITY = "Security"
    AVAILABILITY = "Availability"
    PROCESSING_INTEGRITY = "Processing Integrity"
    CONFIDENTIALITY = "Confidentiality"
    PRIVACY = "Privacy"

class CommonCriteria(Enum):
    """9 Common Criteria (Security related) - CC1 through CC9"""
    CC1 = "Control Environment"
    CC2 = "Communication and Information"
    CC3 = "Risk Assessment"
    CC4 = "Monitoring Activities"
    CC5 = "Control Activities"
    CC6 = "Logical and Physical Access Controls"
    CC7 = "System Operations"
    CC8 = "Change Management"
    CC9 = "Risk Mitigation"

@dataclass
class ControlRequirement:
    """Represents a single SOC2 control requirement"""
    code: str
    name: str
    description: str
    trust_service: str
    category: str
    requirements: List[str]
    implementation_tips: List[str]
    audit_considerations: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

class SOC2RAGDatabase:
    """Retrieval-Augmented Generation database for SOC2 compliance"""
    
    def __init__(self):
        self.controls: Dict[str, ControlRequirement] = {}
        self.tsc_mapping: Dict[str, List[str]] = {}
        self.cc_mapping: Dict[str, List[str]] = {}
        self._initialize_database()
    
    def _initialize_database(self):
        """Initialize with comprehensive SOC2 control requirements"""
        
        # ============ COMMON CRITERIA (CC1-CC9) ============
        
        # CC1: Control Environment
        self._add_control(ControlRequirement(
            code="CC1.1",
            name="Organization Values Integrity and Security",
            description="The organization demonstrates a commitment to integrity and ethical values in its control environment",
            trust_service="Security",
            category="Control Environment",
            requirements=[
                "Board and management establish commitment to integrity and ethical values",
                "Leadership communicates expectations regarding ethical behavior",
                "Standards of conduct are documented and communicated",
                "Adherence to standards is evaluated and enforced",
                "Consequences for violations are communicated"
            ],
            implementation_tips=[
                "Develop formal code of conduct",
                "Establish ethics training programs",
                "Create reporting mechanisms for violations",
                "Document and communicate policies"
            ],
            audit_considerations=[
                "Review board minutes and governance documents",
                "Inspect code of conduct documentation",
                "Interview management about values and culture",
                "Verify training records for all employees"
            ]
        ))
        
        # CC1.2: Board of Directors
        self._add_control(ControlRequirement(
            code="CC1.2",
            name="Board Demonstrates Independence and Accountability",
            description="The board demonstrates independence from management and exercises oversight",
            trust_service="Security",
            category="Control Environment",
            requirements=[
                "Board composition includes independent members",
                "Board charter is documented and approved",
                "Board evaluates effectiveness of internal controls",
                "Board meets regularly without management",
                "Board evaluates competence of internal control activities"
            ],
            implementation_tips=[
                "Establish independent board committees",
                "Document board charter and responsibilities",
                "Schedule regular executive sessions",
                "Implement board performance evaluations"
            ],
            audit_considerations=[
                "Review board composition and charter",
                "Inspect meeting minutes",
                "Verify independence of board members",
                "Assess effectiveness evaluations"
            ]
        ))
        
        # CC1.3: Management Accountability
        self._add_control(ControlRequirement(
            code="CC1.3",
            name="Management Establishes and Maintains Accountability",
            description="Management establishes structures, reporting lines, and authority to achieve objectives",
            trust_service="Security",
            category="Control Environment",
            requirements=[
                "Organizational structure is clearly defined",
                "Authority and responsibilities are documented",
                "Reporting lines are established",
                "Segregation of duties is implemented",
                "Roles are communicated throughout organization"
            ],
            implementation_tips=[
                "Create organizational charts",
                "Document job descriptions with assigned responsibilities",
                "Implement role-based access controls",
                "Maintain RACI matrices"
            ],
            audit_considerations=[
                "Review organizational structure documentation",
                "Verify reporting lines and authorities",
                "Assess segregation of duties",
                "Interview personnel about responsibilities"
            ]
        ))
        
        # CC2: Communication and Information
        self._add_control(ControlRequirement(
            code="CC2.1",
            name="Policies and Procedures Are Communicated",
            description="Policies and procedures regarding system and operational responsibilities are communicated",
            trust_service="Security",
            category="Communication and Information",
            requirements=[
                "Information policies address security responsibilities",
                "System operating policies are documented",
                "Personnel receive communication of policies",
                "Communication includes operational procedures",
                "Updates to policies are communicated promptly",
                "Third parties understand their responsibilities"
            ],
            implementation_tips=[
                "Develop comprehensive policy documentation",
                "Implement training programs",
                "Use multiple communication channels",
                "Track acknowledgment of policies",
                "Create vendor/partner agreements"
            ],
            audit_considerations=[
                "Review policy documentation",
                "Verify training records and certifications",
                "Interview personnel about policy knowledge",
                "Inspect vendor/partner agreements"
            ]
        ))
        
        # CC3: Risk Assessment
        self._add_control(ControlRequirement(
            code="CC3.1",
            name="Risk Assessment Identifies and Analyzes Relevant Risk",
            description="The organization identifies potential risks affecting system objectives and determines response",
            trust_service="Security",
            category="Risk Assessment",
            requirements=[
                "Risk assessment methodology is documented",
                "Internal and external risks are identified",
                "Risk impact and likelihood are assessed",
                "Risks are prioritized",
                "Risk assessment considers changes to systems",
                "Risk remediation plans are developed"
            ],
            implementation_tips=[
                "Establish risk assessment committee",
                "Conduct annual risk assessments",
                "Use quantitative and qualitative methods",
                "Maintain risk register",
                "Document remediation timelines"
            ],
            audit_considerations=[
                "Review risk assessment documentation",
                "Inspect risk register and prioritization",
                "Verify assessment methodology",
                "Assess adequacy of risk responses"
            ]
        ))
        
        # CC4: Monitoring Activities
        self._add_control(ControlRequirement(
            code="CC4.1",
            name="Objectives Are Established and Communicated",
            description="Objectives related to system controls are identified and communicated",
            trust_service="Security",
            category="Monitoring Activities",
            requirements=[
                "System objectives are clearly defined",
                "Control objectives align with system objectives",
                "Responsibilities for achieving objectives are assigned",
                "Objectives are communicated to relevant personnel",
                "Progress toward objectives is monitored"
            ],
            implementation_tips=[
                "Create documented control objectives",
                "Link objectives to business requirements",
                "Establish metrics and KPIs",
                "Conduct regular reviews",
                "Document responsibility assignments"
            ],
            audit_considerations=[
                "Review documented objectives",
                "Verify communication to personnel",
                "Assess alignment with business goals",
                "Inspect monitoring reports"
            ]
        ))
        
        # CC5: Control Activities
        self._add_control(ControlRequirement(
            code="CC5.1",
            name="Control Activities Are Selected and Developed",
            description="Organization selects and develops control activities that contribute to risk mitigation",
            trust_service="Security",
            category="Control Activities",
            requirements=[
                "Control activities are designed to prevent or detect errors",
                "Controls address identified risks",
                "Both preventive and detective controls exist",
                "Controls are embedded in processes",
                "Controls are cost-effective relative to risk"
            ],
            implementation_tips=[
                "Design layered controls (preventive and detective)",
                "Automate controls where possible",
                "Document control procedures",
                "Perform periodic control testing",
                "Maintain control matrices"
            ],
            audit_considerations=[
                "Review control design documentation",
                "Test operating effectiveness",
                "Verify coverage of identified risks",
                "Assess control efficiency"
            ]
        ))
        
        # CC6: Logical and Physical Access Controls
        self._add_control(ControlRequirement(
            code="CC6.1",
            name="Logical and Physical Access Controls",
            description="Access to systems and information is restricted to authorized personnel",
            trust_service="Security",
            category="Logical and Physical Access Controls",
            requirements=[
                "Physical access to systems is restricted",
                "Logical access controls are implemented",
                "User authentication is required",
                "Segregation of duties is enforced",
                "Privileged access is limited and monitored",
                "Access is revoked upon termination"
            ],
            implementation_tips=[
                "Implement multi-factor authentication",
                "Use encryption for data at rest and in transit",
                "Maintain access control lists",
                "Conduct regular access reviews",
                "Implement automated access revocation"
            ],
            audit_considerations=[
                "Review access control policies",
                "Verify authentication mechanisms",
                "Inspect physical security measures",
                "Assess logical access enforcement"
            ]
        ))
        
        # CC7: System Operations
        self._add_control(ControlRequirement(
            code="CC7.1",
            name="System Operations Are Monitored and Maintained",
            description="System operations are monitored and maintained to achieve objectives",
            trust_service="Security",
            category="System Operations",
            requirements=[
                "System performance is monitored",
                "Incidents are detected and reported",
                "Incident response procedures exist",
                "System availability is maintained",
                "Disaster recovery plans are tested",
                "Backups are performed and tested"
            ],
            implementation_tips=[
                "Implement monitoring and alerting systems",
                "Establish incident response procedures",
                "Create disaster recovery plans",
                "Perform regular backup testing",
                "Maintain runbooks for common incidents"
            ],
            audit_considerations=[
                "Review monitoring systems and logs",
                "Inspect incident response documentation",
                "Verify disaster recovery testing",
                "Assess backup procedures"
            ]
        ))
        
        # CC8: Change Management
        self._add_control(ControlRequirement(
            code="CC8.1",
            name="Changes Are Controlled and Managed",
            description="Changes to systems and controls are authorized, tested, and documented",
            trust_service="Security",
            category="Change Management",
            requirements=[
                "Change management process is documented",
                "Changes require authorization",
                "Changes are tested before implementation",
                "Changes are documented",
                "Rollback procedures exist",
                "Impact analysis is performed"
            ],
            implementation_tips=[
                "Create change request procedures",
                "Implement change advisory board",
                "Require change documentation",
                "Test changes in non-production environments",
                "Maintain change logs"
            ],
            audit_considerations=[
                "Review change request documentation",
                "Verify authorization and testing",
                "Inspect change logs",
                "Assess change control effectiveness"
            ]
        ))
        
        # CC9: Risk Mitigation
        self._add_control(ControlRequirement(
            code="CC9.1",
            name="Risk Response Is Implemented",
            description="The organization implements responses to identified risks",
            trust_service="Security",
            category="Risk Mitigation",
            requirements=[
                "Risk response strategy is selected",
                "Risk mitigation activities are implemented",
                "Residual risk is assessed",
                "Risk responses are monitored",
                "Third-party risks are managed"
            ],
            implementation_tips=[
                "Develop vendor risk management program",
                "Conduct third-party assessments",
                "Maintain vendor inventory",
                "Implement contract requirements",
                "Monitor vendor compliance"
            ],
            audit_considerations=[
                "Review vendor assessments",
                "Verify contract compliance monitoring",
                "Assess third-party risk management",
                "Inspect residual risk documentation"
            ]
        ))
        
        # ============ AVAILABILITY CRITERIA ============
        
        self._add_control(ControlRequirement(
            code="A1.1",
            name="System Availability Is Ensured",
            description="Systems and services are available and operational to meet user needs",
            trust_service="Availability",
            category="System Availability",
            requirements=[
                "System availability requirements are defined",
                "Infrastructure supports required availability",
                "Redundancy is implemented for critical systems",
                "Capacity planning is performed",
                "Service level agreements define availability targets"
            ],
            implementation_tips=[
                "Define SLAs with availability targets (e.g., 99.9%)",
                "Implement redundant infrastructure",
                "Monitor uptime and availability metrics",
                "Maintain spare equipment",
                "Implement auto-scaling where applicable"
            ],
            audit_considerations=[
                "Review SLA documentation",
                "Verify infrastructure redundancy",
                "Inspect availability monitoring",
                "Assess capacity management practices"
            ]
        ))
        
        # ============ PROCESSING INTEGRITY CRITERIA ============
        
        self._add_control(ControlRequirement(
            code="PI1.1",
            name="Transaction Completeness, Accuracy, and Authorization",
            description="System processing is complete, valid, accurate, and authorized",
            trust_service="Processing Integrity",
            category="Data Processing",
            requirements=[
                "Transaction data requirements are defined",
                "Input validation is implemented",
                "Transactions are authorized before processing",
                "Transaction logs are maintained",
                "Error handling procedures exist"
            ],
            implementation_tips=[
                "Implement input validation and sanitization",
                "Create transaction audit logs",
                "Establish authorization workflows",
                "Monitor for failed transactions",
                "Test error handling procedures"
            ],
            audit_considerations=[
                "Review transaction processing logic",
                "Inspect audit logs for completeness",
                "Verify authorization controls",
                "Assess error handling"
            ]
        ))
        
        # ============ CONFIDENTIALITY CRITERIA ============
        
        self._add_control(ControlRequirement(
            code="C1.1",
            name="Confidential Information Is Protected",
            description="Information classified as confidential is protected from unauthorized access",
            trust_service="Confidentiality",
            category="Data Protection",
            requirements=[
                "Confidential data is identified and classified",
                "Access to confidential data is restricted",
                "Confidential data is encrypted",
                "Data handling procedures are defined",
                "Data destruction procedures are implemented"
            ],
            implementation_tips=[
                "Implement data classification scheme",
                "Use encryption for sensitive data",
                "Enforce access controls based on classification",
                "Create data handling guidelines",
                "Implement secure data destruction"
            ],
            audit_considerations=[
                "Review data classification scheme",
                "Verify encryption implementation",
                "Inspect access controls",
                "Assess data handling compliance"
            ]
        ))
        
        # ============ PRIVACY CRITERIA ============
        
        self._add_control(ControlRequirement(
            code="P1.1",
            name="Personal Information Privacy Is Protected",
            description="Personal information is handled in accordance with privacy requirements",
            trust_service="Privacy",
            category="Personal Data Protection",
            requirements=[
                "Privacy policies are defined and communicated",
                "Personal data collection is authorized",
                "Data retention limits are established",
                "Individual rights are supported",
                "Third-party data sharing is controlled"
            ],
            implementation_tips=[
                "Create privacy policy documentation",
                "Implement privacy controls in systems",
                "Establish data retention schedules",
                "Support data subject rights (access, deletion)",
                "Maintain vendor privacy agreements"
            ],
            audit_considerations=[
                "Review privacy policy",
                "Inspect data handling procedures",
                "Verify retention compliance",
                "Assess third-party data handling"
            ]
        ))
        
        # Build trust service to control mappings
        self._build_mappings()
    
    def _add_control(self, control: ControlRequirement):
        """Add control to database"""
        self.controls[control.code] = control
    
    def _build_mappings(self):
        """Build Trust Service Criteria and Common Criteria mappings"""
        for code, control in self.controls.items():
            # Build TSC mapping
            tsc = control.trust_service
            if tsc not in self.tsc_mapping:
                self.tsc_mapping[tsc] = []
            self.tsc_mapping[tsc].append(code)
            
            # Build CC mapping for Common Criteria
            if control.category in [cc.value for cc in CommonCriteria]:
                if control.category not in self.cc_mapping:
                    self.cc_mapping[control.category] = []
                self.cc_mapping[control.category].append(code)
    
    def get_controls_by_tsc(self, tsc: str) -> List[ControlRequirement]:
        """Retrieve all controls for a Trust Service Criteria"""
        control_codes = self.tsc_mapping.get(tsc, [])
        return [self.controls[code] for code in control_codes if code in self.controls]
    
    def get_controls_by_category(self, category: str) -> List[ControlRequirement]:
        """Retrieve all controls for a category"""
        control_codes = self.cc_mapping.get(category, [])
        return [self.controls[code] for code in control_codes if code in self.controls]
    
    def get_control(self, code: str) -> ControlRequirement:
        """Get specific control by code"""
        return self.controls.get(code)
    
    def search_controls(self, keyword: str) -> List[ControlRequirement]:
        """Search controls by keyword"""
        results = []
        keyword_lower = keyword.lower()
        for control in self.controls.values():
            if (keyword_lower in control.name.lower() or 
                keyword_lower in control.description.lower() or
                any(keyword_lower in req.lower() for req in control.requirements)):
                results.append(control)
        return results
    
    def get_all_controls(self) -> List[ControlRequirement]:
        """Get all controls in database"""
        return list(self.controls.values())
    
    def get_tsc_summary(self) -> Dict[str, int]:
        """Get summary of controls per Trust Service Criteria"""
        return {tsc: len(codes) for tsc, codes in self.tsc_mapping.items()}
    
    def export_to_json(self, filepath: str):
        """Export RAG database to JSON file"""
        data = {
            "timestamp": datetime.now().isoformat(),
            "controls": {code: control.to_dict() for code, control in self.controls.items()},
            "tsc_mapping": self.tsc_mapping,
            "cc_mapping": self.cc_mapping
        }
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    
    def generate_hash(self) -> str:
        """Generate hash of current database state for integrity checking"""
        content = json.dumps({
            code: control.to_dict() 
            for code, control in sorted(self.controls.items())
        }, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()


# Initialize global RAG database
rag_database = SOC2RAGDatabase()

if __name__ == "__main__":
    # Example usage
    db = SOC2RAGDatabase()
    
    print("=== SOC2 RAG Database Summary ===")
    print(f"Total Controls: {len(db.get_all_controls())}")
    print(f"\nControls by Trust Service Criteria:")
    for tsc, count in db.get_tsc_summary().items():
        print(f"  {tsc}: {count} controls")
    
    print(f"\n\nCommon Criteria (Security):")
    for cc in CommonCriteria:
        controls = db.get_controls_by_category(cc.value)
        print(f"  {cc.name} ({cc.value}): {len(controls)} controls")
    
    # Export database
    db.export_to_json("/tmp/soc2_rag_database.json")
    print(f"\n\nDatabase exported to /tmp/soc2_rag_database.json")
    print(f"Database Hash: {db.generate_hash()}")
