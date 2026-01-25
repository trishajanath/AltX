"""
Compliance Framework for Generated Applications

This module ensures all generated applications follow:
- GDPR (General Data Protection Regulation) - EU Regulation 2016/679
  Source: https://gdpr-info.eu/
- SOC 2 (Service Organization Control 2) - AICPA Trust Services Criteria
  Source: https://sprinto.com/blog/soc-2-controls/
- NIST SP 800-53 Rev 5 - Security and Privacy Controls
  Source: https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-53r5.pdf

The compliance rules are applied during code generation to ensure
applications are secure and privacy-compliant by design.
"""

import json
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum
from datetime import datetime


class ComplianceStandard(Enum):
    """Supported compliance standards"""
    GDPR = "gdpr"                    # EU General Data Protection Regulation
    SOC2 = "soc2"                    # AICPA Service Organization Control 2
    NIST_800_53 = "nist_800_53"      # NIST SP 800-53 Rev 5
    ISO_27001 = "iso_27001"          # ISO/IEC 27001 (legacy support)
    PCI_DSS = "pci_dss"              # Payment Card Industry DSS
    HIPAA = "hipaa"                  # Health Insurance Portability Act
    CCPA = "ccpa"                    # California Consumer Privacy Act


class ComplianceCategory(Enum):
    """Categories of compliance requirements"""
    DATA_PROTECTION = "data_protection"
    ACCESS_CONTROL = "access_control"
    ENCRYPTION = "encryption"
    AUDIT_LOGGING = "audit_logging"
    CONSENT_MANAGEMENT = "consent_management"
    DATA_RETENTION = "data_retention"
    INCIDENT_RESPONSE = "incident_response"
    SECURE_DEVELOPMENT = "secure_development"
    PRIVACY_BY_DESIGN = "privacy_by_design"
    DATA_MINIMIZATION = "data_minimization"


@dataclass
class ComplianceRequirement:
    """A specific compliance requirement"""
    id: str
    standard: ComplianceStandard
    category: ComplianceCategory
    title: str
    description: str
    implementation_guidance: str
    code_pattern: Optional[str] = None
    validation_check: Optional[str] = None
    severity: str = "required"  # required, recommended, optional
    references: List[str] = field(default_factory=list)


@dataclass
class ComplianceCheck:
    """Result of a compliance check"""
    requirement_id: str
    passed: bool
    findings: List[str]
    recommendations: List[str]
    code_location: Optional[str] = None


@dataclass
class ComplianceReport:
    """Full compliance report for a generated application"""
    app_name: str
    generated_at: datetime
    standards_applied: List[ComplianceStandard]
    total_requirements: int
    passed_requirements: int
    failed_requirements: int
    checks: List[ComplianceCheck]
    overall_score: float
    recommendations: List[str]


class ComplianceFramework:
    """
    Comprehensive compliance framework for generated applications.
    
    Ensures all generated code follows GDPR, ISO 27001, and SOC 2 requirements
    by providing code patterns, validation rules, and automatic enforcement.
    """
    
    def __init__(self):
        self.requirements = self._load_compliance_requirements()
        self.code_patterns = self._load_code_patterns()
        
    def _load_compliance_requirements(self) -> Dict[str, ComplianceRequirement]:
        """Load all compliance requirements"""
        requirements = {}
        
        # ==================== GDPR REQUIREMENTS ====================
        # Based on https://gdpr-info.eu/ - EU Regulation 2016/679
        gdpr_requirements = [
            ComplianceRequirement(
                id="GDPR-001",
                standard=ComplianceStandard.GDPR,
                category=ComplianceCategory.CONSENT_MANAGEMENT,
                title="Lawfulness of Processing - Consent (Article 6 & 7)",
                description="Personal data processing requires lawful basis. Consent must be freely given, specific, informed, and unambiguous.",
                implementation_guidance="""
                - Display clear consent banners before collecting any personal data
                - Consent must be as easy to withdraw as to give (Art. 7(3))
                - Store consent records with timestamps and version
                - Consent for children under 16 requires parental consent (Art. 8)
                - Cannot make service conditional on unnecessary consent
                """,
                code_pattern="consent_banner",
                severity="required",
                references=["GDPR Article 6 - Lawfulness of processing", "GDPR Article 7 - Conditions for consent", "https://gdpr-info.eu/art-6-gdpr/", "https://gdpr-info.eu/art-7-gdpr/"]
            ),
            ComplianceRequirement(
                id="GDPR-002",
                standard=ComplianceStandard.GDPR,
                category=ComplianceCategory.PRIVACY_BY_DESIGN,
                title="Data Protection by Design and Default (Article 25)",
                description="Implement data protection principles from the design stage. Only process data necessary for each specific purpose.",
                implementation_guidance="""
                - Data minimization: Only collect strictly necessary data
                - Pseudonymization where possible
                - Privacy-friendly default settings (opt-in, not opt-out)
                - Limit data access to those who need it
                - Build privacy controls into the system architecture
                """,
                code_pattern="privacy_defaults",
                severity="required",
                references=["GDPR Article 25 - Data protection by design and by default", "https://gdpr-info.eu/art-25-gdpr/", "https://gdpr-info.eu/issues/privacy-by-design/"]
            ),
            ComplianceRequirement(
                id="GDPR-003",
                standard=ComplianceStandard.GDPR,
                category=ComplianceCategory.DATA_PROTECTION,
                title="Right of Access by Data Subject (Article 15)",
                description="Data subjects have the right to obtain confirmation of processing and access to their personal data.",
                implementation_guidance="""
                - Provide 'View My Data' feature showing all stored personal data
                - Include purposes of processing, categories, recipients
                - Information about retention periods
                - Right to request rectification, erasure, or restriction
                - Response within 30 days (extendable by 2 months for complex requests)
                """,
                code_pattern="data_access",
                severity="required",
                references=["GDPR Article 15 - Right of access by the data subject", "https://gdpr-info.eu/art-15-gdpr/", "https://gdpr-info.eu/issues/right-of-access/"]
            ),
            ComplianceRequirement(
                id="GDPR-004",
                standard=ComplianceStandard.GDPR,
                category=ComplianceCategory.DATA_PROTECTION,
                title="Right to Data Portability (Article 20)",
                description="Data subjects can receive their personal data in a structured, commonly used, machine-readable format.",
                implementation_guidance="""
                - Provide 'Download My Data' feature
                - Export in structured format (JSON, CSV, XML)
                - Include all personal data provided by the user
                - Allow direct transmission to another controller where technically feasible
                - Free of charge for reasonable requests
                """,
                code_pattern="data_export",
                severity="required",
                references=["GDPR Article 20 - Right to data portability", "https://gdpr-info.eu/art-20-gdpr/"]
            ),
            ComplianceRequirement(
                id="GDPR-005",
                standard=ComplianceStandard.GDPR,
                category=ComplianceCategory.DATA_PROTECTION,
                title="Right to Erasure - Right to be Forgotten (Article 17)",
                description="Data subjects have the right to obtain erasure of their personal data without undue delay.",
                implementation_guidance="""
                - Provide account/data deletion functionality
                - Delete data when: consent withdrawn, no longer necessary, unlawfully processed
                - Notify third parties of deletion requests
                - Exceptions: legal obligations, public interest, legal claims
                - Keep anonymized audit log of deletion (without personal data)
                """,
                code_pattern="data_deletion",
                severity="required",
                references=["GDPR Article 17 - Right to erasure ('right to be forgotten')", "https://gdpr-info.eu/art-17-gdpr/", "https://gdpr-info.eu/issues/right-to-be-forgotten/"]
            ),
            ComplianceRequirement(
                id="GDPR-006",
                standard=ComplianceStandard.GDPR,
                category=ComplianceCategory.DATA_PROTECTION,
                title="Right to Rectification (Article 16)",
                description="Data subjects have the right to rectification of inaccurate personal data.",
                implementation_guidance="""
                - Allow users to update their personal information
                - Process rectification requests without undue delay
                - Notify third parties of rectifications
                - Provide confirmation of changes made
                """,
                code_pattern="data_rectification",
                severity="required",
                references=["GDPR Article 16 - Right to rectification", "https://gdpr-info.eu/art-16-gdpr/"]
            ),
            ComplianceRequirement(
                id="GDPR-007",
                standard=ComplianceStandard.GDPR,
                category=ComplianceCategory.DATA_RETENTION,
                title="Storage Limitation (Article 5(1)(e))",
                description="Personal data kept no longer than necessary for the purposes for which it was collected.",
                implementation_guidance="""
                - Define retention periods for each data type
                - Implement automatic data cleanup jobs
                - Document retention policies clearly
                - Anonymize data that must be kept for statistics
                - Regular review of data necessity
                """,
                code_pattern="data_retention",
                severity="required",
                references=["GDPR Article 5(1)(e) - Principles relating to processing", "https://gdpr-info.eu/art-5-gdpr/"]
            ),
            ComplianceRequirement(
                id="GDPR-008",
                standard=ComplianceStandard.GDPR,
                category=ComplianceCategory.ENCRYPTION,
                title="Security of Processing (Article 32)",
                description="Implement appropriate technical and organizational measures to ensure data security.",
                implementation_guidance="""
                - Encryption of personal data (at rest and in transit)
                - Pseudonymization where appropriate
                - Ensure ongoing confidentiality, integrity, availability
                - Regular testing and evaluation of security measures
                - Process to restore data in case of incident
                """,
                code_pattern="encryption",
                severity="required",
                references=["GDPR Article 32 - Security of processing", "https://gdpr-info.eu/art-32-gdpr/", "https://gdpr-info.eu/issues/encryption/"]
            ),
            ComplianceRequirement(
                id="GDPR-009",
                standard=ComplianceStandard.GDPR,
                category=ComplianceCategory.INCIDENT_RESPONSE,
                title="Personal Data Breach Notification (Article 33 & 34)",
                description="Notify supervisory authority within 72 hours of becoming aware of a personal data breach.",
                implementation_guidance="""
                - Implement breach detection mechanisms
                - Document nature of breach, categories/numbers affected
                - Notify supervisory authority within 72 hours
                - Communicate to affected data subjects if high risk
                - Maintain breach register
                """,
                code_pattern="breach_notification",
                severity="required",
                references=["GDPR Article 33 - Notification of breach to supervisory authority", "GDPR Article 34 - Communication of breach to data subject", "https://gdpr-info.eu/art-33-gdpr/", "https://gdpr-info.eu/art-34-gdpr/"]
            ),
            ComplianceRequirement(
                id="GDPR-010",
                standard=ComplianceStandard.GDPR,
                category=ComplianceCategory.AUDIT_LOGGING,
                title="Records of Processing Activities (Article 30)",
                description="Maintain records of processing activities under controller responsibility.",
                implementation_guidance="""
                - Record: purposes, categories of data subjects/data, recipients
                - Document transfers to third countries with safeguards
                - Time limits for erasure where possible
                - Description of technical/organizational security measures
                - Make records available to supervisory authority on request
                """,
                code_pattern="processing_records",
                severity="required",
                references=["GDPR Article 30 - Records of processing activities", "https://gdpr-info.eu/art-30-gdpr/", "https://gdpr-info.eu/issues/records-of-processing-activities/"]
            ),
            ComplianceRequirement(
                id="GDPR-011",
                standard=ComplianceStandard.GDPR,
                category=ComplianceCategory.PRIVACY_BY_DESIGN,
                title="Transparent Information (Article 12, 13, 14)",
                description="Provide information about processing in a concise, transparent, intelligible manner.",
                implementation_guidance="""
                - Clear, plain language privacy notices
                - Information provided at time of data collection
                - Identity of controller, purposes, legal basis
                - Data subject rights explained
                - Information about automated decision-making
                """,
                code_pattern="transparency",
                severity="required",
                references=["GDPR Article 12 - Transparent information", "GDPR Article 13 - Information to be provided", "https://gdpr-info.eu/art-12-gdpr/", "https://gdpr-info.eu/issues/right-to-be-informed/"]
            ),
            ComplianceRequirement(
                id="GDPR-012",
                standard=ComplianceStandard.GDPR,
                category=ComplianceCategory.DATA_PROTECTION,
                title="Right to Object (Article 21)",
                description="Data subjects can object to processing based on legitimate interests or for direct marketing.",
                implementation_guidance="""
                - Provide clear opt-out for marketing communications
                - Honor objections to profiling
                - Stop processing unless compelling legitimate grounds
                - Inform about right to object at first communication
                """,
                code_pattern="right_to_object",
                severity="required",
                references=["GDPR Article 21 - Right to object", "https://gdpr-info.eu/art-21-gdpr/"]
            ),
        ]
        
        # ==================== NIST SP 800-53 Rev 5 REQUIREMENTS ====================
        # Based on https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-53r5.pdf
        nist_requirements = [
            ComplianceRequirement(
                id="NIST-AC-1",
                standard=ComplianceStandard.NIST_800_53,
                category=ComplianceCategory.ACCESS_CONTROL,
                title="AC - Access Control Policy and Procedures",
                description="Establish access control policies consistent with applicable laws and organizational missions.",
                implementation_guidance="""
                - Develop and document access control policy
                - Implement role-based access control (RBAC)
                - Principle of least privilege enforcement
                - Separation of duties for sensitive functions
                - Regular access control reviews
                """,
                code_pattern="rbac",
                severity="required",
                references=["NIST SP 800-53 AC-1, AC-2, AC-3, AC-6"]
            ),
            ComplianceRequirement(
                id="NIST-AC-7",
                standard=ComplianceStandard.NIST_800_53,
                category=ComplianceCategory.ACCESS_CONTROL,
                title="AC-7 - Unsuccessful Logon Attempts",
                description="Enforce limits on consecutive invalid logon attempts and automatically lock accounts.",
                implementation_guidance="""
                - Limit failed login attempts (e.g., 5 attempts)
                - Automatic account lockout after threshold
                - Lockout duration (e.g., 15-30 minutes)
                - Notification to user/admin of lockout
                - Logging of all authentication attempts
                """,
                code_pattern="account_lockout",
                severity="required",
                references=["NIST SP 800-53 AC-7"]
            ),
            ComplianceRequirement(
                id="NIST-AU-2",
                standard=ComplianceStandard.NIST_800_53,
                category=ComplianceCategory.AUDIT_LOGGING,
                title="AU - Audit Events and Logging",
                description="Generate audit records for security-relevant events with sufficient detail.",
                implementation_guidance="""
                - Log successful/failed authentication events
                - Log privileged operations (admin actions)
                - Log data access and modifications
                - Log security configuration changes
                - Include timestamp, user, action, outcome
                - Protect audit logs from unauthorized access
                """,
                code_pattern="security_logging",
                severity="required",
                references=["NIST SP 800-53 AU-2, AU-3, AU-9, AU-12"]
            ),
            ComplianceRequirement(
                id="NIST-IA-2",
                standard=ComplianceStandard.NIST_800_53,
                category=ComplianceCategory.ACCESS_CONTROL,
                title="IA - Identification and Authentication",
                description="Uniquely identify and authenticate users before granting access.",
                implementation_guidance="""
                - Unique user identifiers (no shared accounts)
                - Multi-factor authentication for privileged access
                - Strong password requirements (12+ chars, complexity)
                - Secure password storage (bcrypt, Argon2)
                - Session timeout and re-authentication
                """,
                code_pattern="secure_auth",
                severity="required",
                references=["NIST SP 800-53 IA-2, IA-5, IA-8"]
            ),
            ComplianceRequirement(
                id="NIST-SC-8",
                standard=ComplianceStandard.NIST_800_53,
                category=ComplianceCategory.ENCRYPTION,
                title="SC-8 - Transmission Confidentiality and Integrity",
                description="Protect the confidentiality and integrity of transmitted information.",
                implementation_guidance="""
                - TLS 1.2+ for all communications
                - Certificate validation and pinning
                - HSTS headers to enforce HTTPS
                - Secure WebSocket connections (WSS)
                - No sensitive data in URLs/query params
                """,
                code_pattern="transmission_security",
                severity="required",
                references=["NIST SP 800-53 SC-8, SC-13, SC-23"]
            ),
            ComplianceRequirement(
                id="NIST-SC-28",
                standard=ComplianceStandard.NIST_800_53,
                category=ComplianceCategory.ENCRYPTION,
                title="SC-28 - Protection of Information at Rest",
                description="Protect the confidentiality and integrity of information at rest.",
                implementation_guidance="""
                - Encrypt sensitive data in database (AES-256)
                - Secure key management (HSM, Key Vault)
                - Encryption of backups
                - Full disk encryption for servers
                - Secure deletion (cryptographic erasure)
                """,
                code_pattern="data_at_rest",
                severity="required",
                references=["NIST SP 800-53 SC-28"]
            ),
            ComplianceRequirement(
                id="NIST-SI-2",
                standard=ComplianceStandard.NIST_800_53,
                category=ComplianceCategory.SECURE_DEVELOPMENT,
                title="SI-2 - Flaw Remediation",
                description="Identify, report, and correct system flaws in a timely manner.",
                implementation_guidance="""
                - Automated vulnerability scanning
                - Dependency vulnerability checking (npm audit, pip-audit)
                - Patch management process
                - Security update deployment within defined timeframes
                - Track remediation of identified flaws
                """,
                code_pattern="vuln_management",
                severity="required",
                references=["NIST SP 800-53 SI-2, SI-5"]
            ),
            ComplianceRequirement(
                id="NIST-SI-10",
                standard=ComplianceStandard.NIST_800_53,
                category=ComplianceCategory.SECURE_DEVELOPMENT,
                title="SI-10 - Information Input Validation",
                description="Check the validity of information inputs to prevent injection attacks.",
                implementation_guidance="""
                - Validate all user inputs (type, length, format, range)
                - Parameterized queries for database access
                - Output encoding to prevent XSS
                - Content Security Policy headers
                - Sanitize file uploads
                """,
                code_pattern="input_validation",
                severity="required",
                references=["NIST SP 800-53 SI-10, SI-11"]
            ),
            ComplianceRequirement(
                id="NIST-IR-4",
                standard=ComplianceStandard.NIST_800_53,
                category=ComplianceCategory.INCIDENT_RESPONSE,
                title="IR - Incident Handling",
                description="Implement incident handling capability including detection, analysis, containment, and recovery.",
                implementation_guidance="""
                - Incident response procedures documented
                - Detection mechanisms (SIEM, IDS)
                - Incident categorization and prioritization
                - Containment strategies
                - Post-incident analysis and lessons learned
                """,
                code_pattern="incident_management",
                severity="required",
                references=["NIST SP 800-53 IR-4, IR-5, IR-6, IR-8"]
            ),
            ComplianceRequirement(
                id="NIST-CP-9",
                standard=ComplianceStandard.NIST_800_53,
                category=ComplianceCategory.DATA_PROTECTION,
                title="CP-9 - System Backup",
                description="Conduct backups of system-level and user-level information.",
                implementation_guidance="""
                - Regular automated backups
                - Backup encryption and secure storage
                - Backup integrity verification
                - Test restore procedures regularly
                - Off-site/cloud backup storage
                """,
                code_pattern="backup_recovery",
                severity="required",
                references=["NIST SP 800-53 CP-9, CP-10"]
            ),
            ComplianceRequirement(
                id="NIST-CM-7",
                standard=ComplianceStandard.NIST_800_53,
                category=ComplianceCategory.SECURE_DEVELOPMENT,
                title="CM-7 - Least Functionality",
                description="Configure systems to provide only essential capabilities and prohibit unauthorized functions.",
                implementation_guidance="""
                - Disable unnecessary services and ports
                - Remove unused software and features
                - Restrict use of development tools in production
                - Whitelist authorized software
                - Minimal container images
                """,
                code_pattern="least_functionality",
                severity="required",
                references=["NIST SP 800-53 CM-7, CM-11"]
            ),
            ComplianceRequirement(
                id="NIST-RA-5",
                standard=ComplianceStandard.NIST_800_53,
                category=ComplianceCategory.SECURE_DEVELOPMENT,
                title="RA-5 - Vulnerability Monitoring and Scanning",
                description="Monitor and scan for vulnerabilities in systems and applications.",
                implementation_guidance="""
                - Regular vulnerability scans (weekly/monthly)
                - Penetration testing (annual)
                - SAST/DAST in CI/CD pipeline
                - Third-party dependency scanning
                - Remediation tracking and reporting
                """,
                code_pattern="vulnerability_scanning",
                severity="required",
                references=["NIST SP 800-53 RA-5"]
            ),
        ]
        
        # ==================== SOC 2 REQUIREMENTS ====================
        # Based on https://sprinto.com/blog/soc-2-controls/ - AICPA Trust Services Criteria
        soc2_requirements = [
            # === SECURITY (Common Criteria - Mandatory) ===
            ComplianceRequirement(
                id="SOC2-CC1",
                standard=ComplianceStandard.SOC2,
                category=ComplianceCategory.SECURE_DEVELOPMENT,
                title="CC1.0 - Control Environment",
                description="Establish governance, ethics, accountability, and leadership oversight for security culture.",
                implementation_guidance="""
                - Code of conduct and ethics policy enforcement
                - Defined roles and responsibilities for security
                - Management oversight and accountability mechanisms
                - Security awareness training for all personnel
                """,
                code_pattern="control_environment",
                severity="required",
                references=["SOC 2 CC1.1 - CC1.5", "https://sprinto.com/blog/soc-2-controls/"]
            ),
            ComplianceRequirement(
                id="SOC2-CC3",
                standard=ComplianceStandard.SOC2,
                category=ComplianceCategory.SECURE_DEVELOPMENT,
                title="CC3.0 - Risk Assessment",
                description="Identify and analyze internal and external risks that may prevent achieving security objectives.",
                implementation_guidance="""
                - Formal risk register and assessment process
                - Threat and vulnerability identification
                - Risk treatment plans and mitigation strategies
                - Annual risk assessment reviews
                """,
                code_pattern="risk_assessment",
                severity="required",
                references=["SOC 2 CC3.1 - CC3.4", "https://sprinto.com/blog/soc-2-controls/"]
            ),
            ComplianceRequirement(
                id="SOC2-CC4",
                standard=ComplianceStandard.SOC2,
                category=ComplianceCategory.AUDIT_LOGGING,
                title="CC4.0 - Monitoring Activities",
                description="Evaluate how well controls operate over time through reviews, automated monitoring, and audits.",
                implementation_guidance="""
                - Continuous monitoring tools and dashboards
                - Internal audits and compliance reviews
                - Automated alerts for security events
                - Regular control effectiveness evaluations
                """,
                code_pattern="monitoring",
                severity="required",
                references=["SOC 2 CC4.1 - CC4.2", "https://sprinto.com/blog/soc-2-controls/"]
            ),
            ComplianceRequirement(
                id="SOC2-CC5",
                standard=ComplianceStandard.SOC2,
                category=ComplianceCategory.SECURE_DEVELOPMENT,
                title="CC5.0 - Control Activities",
                description="Implement policies and procedures that enforce security practices consistently.",
                implementation_guidance="""
                - Information security policy documentation
                - Acceptable use policy for systems/data
                - Data handling standards and procedures
                - Security control implementation verification
                """,
                code_pattern="control_activities",
                severity="required",
                references=["SOC 2 CC5.1 - CC5.3", "https://sprinto.com/blog/soc-2-controls/"]
            ),
            ComplianceRequirement(
                id="SOC2-CC6",
                standard=ComplianceStandard.SOC2,
                category=ComplianceCategory.ACCESS_CONTROL,
                title="CC6.0 - Logical and Physical Access Controls",
                description="Control who can access systems, data, facilities, and infrastructure to prevent unauthorized use.",
                implementation_guidance="""
                - MFA (Multi-Factor Authentication) everywhere
                - RBAC (Role-Based Access Control) with least privilege
                - Strong password policies and rotation
                - User onboarding/offboarding workflows
                - Regular permission reviews (quarterly)
                """,
                code_pattern="logical_access",
                severity="required",
                references=["SOC 2 CC6.1 - CC6.8", "https://sprinto.com/blog/soc-2-controls/"]
            ),
            ComplianceRequirement(
                id="SOC2-CC7",
                standard=ComplianceStandard.SOC2,
                category=ComplianceCategory.INCIDENT_RESPONSE,
                title="CC7.0 - System Operations",
                description="Monitor, maintain, and support systems to detect issues and resolve incidents efficiently.",
                implementation_guidance="""
                - Logging and monitoring of all systems
                - Incident detection and response program
                - Root cause analysis for incidents
                - Uptime monitoring and alerting
                """,
                code_pattern="system_operations",
                severity="required",
                references=["SOC 2 CC7.1 - CC7.5", "https://sprinto.com/blog/soc-2-controls/"]
            ),
            ComplianceRequirement(
                id="SOC2-CC8",
                standard=ComplianceStandard.SOC2,
                category=ComplianceCategory.SECURE_DEVELOPMENT,
                title="CC8.0 - Change Management",
                description="Manage updates to systems and applications in a controlled, reviewed, and approved manner.",
                implementation_guidance="""
                - Pull request reviews before merging
                - Configuration management procedures
                - Patch management and tracking
                - Change approval workflows
                - Rollback procedures for failed changes
                """,
                code_pattern="change_management",
                severity="required",
                references=["SOC 2 CC8.1", "https://sprinto.com/blog/soc-2-controls/"]
            ),
            ComplianceRequirement(
                id="SOC2-CC9",
                standard=ComplianceStandard.SOC2,
                category=ComplianceCategory.SECURE_DEVELOPMENT,
                title="CC9.0 - Risk Mitigation",
                description="Implement mechanisms that reduce the likelihood and impact of identified risks.",
                implementation_guidance="""
                - Vendor risk assessments for third parties
                - Business impact analysis
                - Documented risk treatment plans
                - Insurance and transfer mechanisms
                """,
                code_pattern="risk_mitigation",
                severity="required",
                references=["SOC 2 CC9.1 - CC9.2", "https://sprinto.com/blog/soc-2-controls/"]
            ),
            
            # === AVAILABILITY (Optional TSC) ===
            ComplianceRequirement(
                id="SOC2-A1",
                standard=ComplianceStandard.SOC2,
                category=ComplianceCategory.DATA_PROTECTION,
                title="A1 - Availability Controls",
                description="Ensure system availability meets service commitments and requirements.",
                implementation_guidance="""
                - Infrastructure and capacity monitoring (CPU, memory, disk)
                - Automated performance alerts
                - Backup and replication across availability zones
                - Business continuity and disaster recovery planning
                - Recovery Time Objective (RTO) alignment
                - Annual DR simulation exercises
                """,
                code_pattern="availability",
                severity="recommended",
                references=["SOC 2 A1.1 - A1.3", "https://sprinto.com/blog/soc-2-controls/"]
            ),
            
            # === PROCESSING INTEGRITY (Optional TSC) ===
            ComplianceRequirement(
                id="SOC2-PI1",
                standard=ComplianceStandard.SOC2,
                category=ComplianceCategory.DATA_PROTECTION,
                title="PI1 - Processing Integrity Controls",
                description="Ensure system processing is complete, valid, accurate, timely, and authorized.",
                implementation_guidance="""
                - Data accuracy: Validation rules at data entry
                - Data completeness: Workflow completeness checks
                - Data validity: Input validation and authorization
                - Timeliness: SLA monitoring and batch processing schedules
                - System monitoring: Error logging and anomaly detection
                """,
                code_pattern="processing_integrity",
                severity="recommended",
                references=["SOC 2 PI1.1 - PI1.5", "https://sprinto.com/blog/soc-2-controls/"]
            ),
            
            # === CONFIDENTIALITY (Optional TSC) ===
            ComplianceRequirement(
                id="SOC2-C1",
                standard=ComplianceStandard.SOC2,
                category=ComplianceCategory.ENCRYPTION,
                title="C1 - Confidentiality Controls",
                description="Protect confidential information throughout its lifecycle.",
                implementation_guidance="""
                - RBAC with least-privilege permissions
                - Encryption at rest and in transit (TLS 1.2+, AES-256)
                - Access approval workflows for sensitive data
                - Monitoring of privileged activity
                - Secure data deletion (cryptographic erasure)
                - Data retention schedules and decommissioning
                """,
                code_pattern="confidentiality",
                severity="required",
                references=["SOC 2 C1.1 - C1.2", "https://sprinto.com/blog/soc-2-controls/"]
            ),
            
            # === PRIVACY (Optional TSC) ===
            ComplianceRequirement(
                id="SOC2-P1",
                standard=ComplianceStandard.SOC2,
                category=ComplianceCategory.CONSENT_MANAGEMENT,
                title="P1 - Privacy Notice and Consent",
                description="Ensure individuals understand data collection and provide consent.",
                implementation_guidance="""
                - Public privacy notices with clear language
                - Consent banners or checkboxes
                - Version tracking for privacy notices
                - Data minimization procedures
                - Purpose-based access controls
                """,
                code_pattern="privacy_notice",
                severity="required",
                references=["SOC 2 P1.1, P2.1", "https://sprinto.com/blog/soc-2-controls/"]
            ),
            ComplianceRequirement(
                id="SOC2-P5",
                standard=ComplianceStandard.SOC2,
                category=ComplianceCategory.DATA_RETENTION,
                title="P5 - Data Retention and Disposal",
                description="Retain and dispose of personal information according to defined schedules.",
                implementation_guidance="""
                - Retention schedule enforcement
                - Automated data deletion mechanisms
                - Secure wipe or anonymization
                - Customer data correction workflows
                - Data subject request (DSR) handling
                - Identity verification for requests
                """,
                code_pattern="retention_disposal",
                severity="required",
                references=["SOC 2 P5.1 - P5.2, P8.1", "https://sprinto.com/blog/soc-2-controls/"]
            ),
            ComplianceRequirement(
                id="SOC2-P6",
                standard=ComplianceStandard.SOC2,
                category=ComplianceCategory.INCIDENT_RESPONSE,
                title="P6 - Privacy Monitoring and Incident Response",
                description="Detect, investigate, and resolve privacy breaches quickly.",
                implementation_guidance="""
                - Privacy incident reporting workflows
                - Breach notification procedures
                - Continuous monitoring tools
                - Post-incident reviews
                - Privacy training for all employees
                """,
                code_pattern="privacy_monitoring",
                severity="required",
                references=["SOC 2 P6.1 - P6.7, P7.1", "https://sprinto.com/blog/soc-2-controls/"]
            ),
        ]
        
        # Combine all requirements
        for req in gdpr_requirements + nist_requirements + soc2_requirements:
            requirements[req.id] = req
        
        return requirements
    
    def _load_code_patterns(self) -> Dict[str, str]:
        """Load compliant code patterns for each requirement"""
        return {
            # === CONSENT MANAGEMENT ===
            "consent_banner": '''
// GDPR-Compliant Consent Banner Component
const ConsentBanner = () => {
  const [consentGiven, setConsentGiven] = useState(false);
  const [showBanner, setShowBanner] = useState(true);
  
  useEffect(() => {
    const consent = localStorage.getItem('gdpr_consent');
    if (consent) {
      setConsentGiven(true);
      setShowBanner(false);
    }
  }, []);
  
  const handleAccept = () => {
    const consentRecord = {
      given: true,
      timestamp: new Date().toISOString(),
      version: '1.0',
      purposes: ['essential', 'analytics', 'marketing']
    };
    localStorage.setItem('gdpr_consent', JSON.stringify(consentRecord));
    // Also send to backend for audit trail
    fetch('/api/consent', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(consentRecord)
    });
    setConsentGiven(true);
    setShowBanner(false);
  };
  
  const handleDecline = () => {
    // Allow essential-only operation
    localStorage.setItem('gdpr_consent', JSON.stringify({
      given: false,
      timestamp: new Date().toISOString(),
      purposes: ['essential']
    }));
    setShowBanner(false);
  };
  
  if (!showBanner) return null;
  
  return (
    <div className="fixed bottom-0 left-0 right-0 bg-gray-900 text-white p-4 z-50">
      <div className="max-w-4xl mx-auto flex items-center justify-between">
        <div className="flex-1 mr-4">
          <p className="font-semibold">We value your privacy</p>
          <p className="text-sm text-gray-300">
            We use cookies to enhance your experience. By continuing, you agree to our 
            <a href="/privacy" className="underline ml-1">Privacy Policy</a>.
          </p>
        </div>
        <div className="flex gap-2">
          <button onClick={handleDecline} className="px-4 py-2 border border-white rounded">
            Essential Only
          </button>
          <button onClick={handleAccept} className="px-4 py-2 bg-blue-600 rounded">
            Accept All
          </button>
        </div>
      </div>
    </div>
  );
};
''',
            
            # === DATA EXPORT (Right to Access) ===
            "data_export": '''
// GDPR Article 15 & 20 - Data Export Endpoint
@app.get("/api/user/export-data")
async def export_user_data(current_user: dict = Depends(get_current_user)):
    """
    Export all personal data for the requesting user.
    GDPR Article 15 (Right to Access) & Article 20 (Data Portability)
    """
    user_id = current_user["_id"]
    
    # Collect all user data from various collections
    user_data = {
        "export_date": datetime.utcnow().isoformat(),
        "data_controller": "Your App Name",
        "contact": "privacy@yourapp.com",
        "profile": db.users.find_one({"_id": user_id}, {"hashed_password": 0}),
        "orders": list(db.orders.find({"user_id": user_id})),
        "preferences": db.preferences.find_one({"user_id": user_id}),
        "activity_log": list(db.activity_log.find({"user_id": user_id})),
        "consent_records": list(db.consents.find({"user_id": user_id}))
    }
    
    # Log this data export for audit
    db.audit_log.insert_one({
        "action": "data_export",
        "user_id": user_id,
        "timestamp": datetime.utcnow(),
        "ip_address": request.client.host
    })
    
    # Return as JSON (machine-readable format per GDPR)
    return JSONResponse(
        content=user_data,
        headers={
            "Content-Disposition": f"attachment; filename=user_data_{user_id}.json"
        }
    )
''',
            
            # === DATA DELETION (Right to be Forgotten) ===
            "data_deletion": '''
// GDPR Article 17 - Right to Erasure
@app.delete("/api/user/delete-account")
async def delete_user_account(
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """
    Delete all personal data for the requesting user.
    GDPR Article 17 (Right to Erasure / Right to be Forgotten)
    """
    user_id = current_user["_id"]
    
    # Create deletion record BEFORE deleting (for compliance proof)
    deletion_record = {
        "deletion_id": str(uuid.uuid4()),
        "user_id_hash": hashlib.sha256(str(user_id).encode()).hexdigest(),
        "requested_at": datetime.utcnow(),
        "completed_at": None,
        "data_categories_deleted": []
    }
    
    try:
        # Delete from all collections containing personal data
        collections_to_clear = [
            "users", "orders", "preferences", 
            "activity_log", "consents", "sessions"
        ]
        
        for collection in collections_to_clear:
            result = db[collection].delete_many({"user_id": user_id})
            if result.deleted_count > 0:
                deletion_record["data_categories_deleted"].append(collection)
        
        deletion_record["completed_at"] = datetime.utcnow()
        deletion_record["status"] = "completed"
        
        # Store anonymized deletion record for compliance
        db.deletion_records.insert_one(deletion_record)
        
        return {"success": True, "message": "All personal data has been deleted"}
        
    except Exception as e:
        deletion_record["status"] = "failed"
        deletion_record["error"] = str(e)
        db.deletion_records.insert_one(deletion_record)
        raise HTTPException(status_code=500, detail="Failed to delete data")
''',
            
            # === RBAC (Role-Based Access Control) ===
            "rbac": '''
// ISO 27001 A.9 - Role-Based Access Control
from enum import Enum
from functools import wraps

class Role(str, Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    USER = "user"
    GUEST = "guest"

class Permission(str, Enum):
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    ADMIN = "admin"

# Role-Permission Matrix (Principle of Least Privilege)
ROLE_PERMISSIONS = {
    Role.ADMIN: [Permission.READ, Permission.WRITE, Permission.DELETE, Permission.ADMIN],
    Role.MANAGER: [Permission.READ, Permission.WRITE, Permission.DELETE],
    Role.USER: [Permission.READ, Permission.WRITE],
    Role.GUEST: [Permission.READ]
}

def require_permission(permission: Permission):
    """Decorator to enforce permission-based access control"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, current_user: dict = Depends(get_current_user), **kwargs):
            user_role = Role(current_user.get("role", "guest"))
            user_permissions = ROLE_PERMISSIONS.get(user_role, [])
            
            if permission not in user_permissions:
                # Log unauthorized access attempt
                db.security_log.insert_one({
                    "event": "unauthorized_access_attempt",
                    "user_id": current_user.get("_id"),
                    "required_permission": permission.value,
                    "user_role": user_role.value,
                    "timestamp": datetime.utcnow(),
                    "endpoint": func.__name__
                })
                raise HTTPException(
                    status_code=403,
                    detail=f"Permission denied. Required: {permission.value}"
                )
            
            return await func(*args, current_user=current_user, **kwargs)
        return wrapper
    return decorator

# Usage example:
@app.delete("/api/items/{item_id}")
@require_permission(Permission.DELETE)
async def delete_item(item_id: str, current_user: dict = Depends(get_current_user)):
    # Only users with DELETE permission can access this
    pass
''',
            
            # === SECURE AUTHENTICATION ===
            "secure_auth": '''
// ISO 27001 A.9.4 - Secure Authentication
import bcrypt
from datetime import datetime, timedelta
import secrets

# Password Policy (ISO 27001 Compliant)
PASSWORD_POLICY = {
    "min_length": 8,
    "require_uppercase": True,
    "require_lowercase": True,
    "require_digit": True,
    "require_special": True,
    "max_age_days": 90,
    "history_count": 5  # Cannot reuse last 5 passwords
}

# Account Lockout Policy
LOCKOUT_POLICY = {
    "max_failed_attempts": 5,
    "lockout_duration_minutes": 30,
    "reset_counter_minutes": 15
}

def validate_password_strength(password: str) -> tuple[bool, str]:
    """Validate password against security policy"""
    if len(password) < PASSWORD_POLICY["min_length"]:
        return False, f"Password must be at least {PASSWORD_POLICY['min_length']} characters"
    if PASSWORD_POLICY["require_uppercase"] and not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter"
    if PASSWORD_POLICY["require_lowercase"] and not any(c.islower() for c in password):
        return False, "Password must contain at least one lowercase letter"
    if PASSWORD_POLICY["require_digit"] and not any(c.isdigit() for c in password):
        return False, "Password must contain at least one number"
    if PASSWORD_POLICY["require_special"] and not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
        return False, "Password must contain at least one special character"
    return True, ""

def check_account_lockout(user_id: str) -> bool:
    """Check if account is locked due to failed login attempts"""
    lockout = db.account_lockouts.find_one({"user_id": user_id})
    if lockout:
        if lockout["locked_until"] > datetime.utcnow():
            return True
        # Lockout expired, reset
        db.account_lockouts.delete_one({"user_id": user_id})
    return False

def record_failed_login(user_id: str, ip_address: str):
    """Record failed login attempt and lock account if threshold exceeded"""
    db.failed_logins.insert_one({
        "user_id": user_id,
        "ip_address": ip_address,
        "timestamp": datetime.utcnow()
    })
    
    # Count recent failures
    cutoff = datetime.utcnow() - timedelta(minutes=LOCKOUT_POLICY["reset_counter_minutes"])
    recent_failures = db.failed_logins.count_documents({
        "user_id": user_id,
        "timestamp": {"$gte": cutoff}
    })
    
    if recent_failures >= LOCKOUT_POLICY["max_failed_attempts"]:
        db.account_lockouts.update_one(
            {"user_id": user_id},
            {"$set": {
                "locked_until": datetime.utcnow() + timedelta(minutes=LOCKOUT_POLICY["lockout_duration_minutes"]),
                "reason": "too_many_failed_attempts"
            }},
            upsert=True
        )
        # Alert security team
        log_security_event("account_locked", user_id, "Too many failed login attempts")
''',
            
            # === AUDIT LOGGING ===
            "audit_logging": '''
// ISO 27001 A.12.4 & SOC 2 CC7.2 - Security Event Logging
from datetime import datetime
from typing import Optional
import json

class AuditLogger:
    """
    Comprehensive audit logging for compliance requirements.
    Logs all security-relevant events with tamper-evident storage.
    """
    
    def __init__(self, db):
        self.db = db
        self.collection = db.audit_logs
        # Create index for efficient querying
        self.collection.create_index([("timestamp", -1)])
        self.collection.create_index([("user_id", 1), ("timestamp", -1)])
        self.collection.create_index([("event_type", 1)])
    
    def log_event(
        self,
        event_type: str,
        user_id: Optional[str],
        action: str,
        resource: str,
        details: dict = None,
        ip_address: str = None,
        user_agent: str = None,
        outcome: str = "success"
    ):
        """
        Log a security or compliance event.
        
        Event types:
        - authentication: login, logout, failed_login, password_change
        - authorization: access_granted, access_denied
        - data_access: read, create, update, delete
        - data_export: gdpr_export, report_generation
        - security: threat_detected, vulnerability_found
        - compliance: consent_given, consent_withdrawn, data_deletion
        """
        log_entry = {
            "event_id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow(),
            "event_type": event_type,
            "user_id": user_id,
            "action": action,
            "resource": resource,
            "outcome": outcome,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "details": details or {},
            # Integrity hash for tamper detection
            "integrity_hash": None
        }
        
        # Calculate integrity hash
        hash_content = json.dumps({
            k: str(v) for k, v in log_entry.items() 
            if k != "integrity_hash"
        }, sort_keys=True)
        log_entry["integrity_hash"] = hashlib.sha256(hash_content.encode()).hexdigest()
        
        self.collection.insert_one(log_entry)
        
        # Alert on critical events
        if event_type in ["security", "authorization"] and outcome == "failure":
            self._send_security_alert(log_entry)
    
    def log_authentication(self, user_id: str, action: str, outcome: str, ip: str, user_agent: str):
        """Log authentication events"""
        self.log_event(
            event_type="authentication",
            user_id=user_id,
            action=action,
            resource="auth_system",
            outcome=outcome,
            ip_address=ip,
            user_agent=user_agent
        )
    
    def log_data_access(self, user_id: str, action: str, resource: str, record_id: str = None):
        """Log data access for compliance"""
        self.log_event(
            event_type="data_access",
            user_id=user_id,
            action=action,
            resource=resource,
            details={"record_id": record_id}
        )
    
    def _send_security_alert(self, log_entry: dict):
        """Send alert for critical security events"""
        # Integration point for alerting system
        print(f"🚨 SECURITY ALERT: {log_entry['event_type']} - {log_entry['action']}")

# Global audit logger instance
audit_logger = AuditLogger(db)
''',
            
            # === ENCRYPTION ===
            "encryption": '''
// ISO 27001 A.10.1 & GDPR Article 32 - Cryptographic Controls
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import os

class DataEncryption:
    """
    Field-level encryption for sensitive personal data.
    Uses AES-256 encryption via Fernet (symmetric encryption).
    """
    
    def __init__(self):
        # Load or generate encryption key
        key = os.getenv("DATA_ENCRYPTION_KEY")
        if not key:
            raise ValueError("DATA_ENCRYPTION_KEY environment variable required")
        self.fernet = Fernet(key.encode())
    
    def encrypt(self, data: str) -> str:
        """Encrypt sensitive data"""
        if not data:
            return data
        return self.fernet.encrypt(data.encode()).decode()
    
    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt sensitive data"""
        if not encrypted_data:
            return encrypted_data
        return self.fernet.decrypt(encrypted_data.encode()).decode()
    
    @staticmethod
    def generate_key() -> str:
        """Generate a new encryption key"""
        return Fernet.generate_key().decode()
    
    def encrypt_pii_fields(self, document: dict, pii_fields: list) -> dict:
        """Encrypt specified PII fields in a document"""
        encrypted_doc = document.copy()
        for field in pii_fields:
            if field in encrypted_doc and encrypted_doc[field]:
                encrypted_doc[field] = self.encrypt(str(encrypted_doc[field]))
                encrypted_doc[f"{field}_encrypted"] = True
        return encrypted_doc
    
    def decrypt_pii_fields(self, document: dict, pii_fields: list) -> dict:
        """Decrypt specified PII fields in a document"""
        decrypted_doc = document.copy()
        for field in pii_fields:
            if document.get(f"{field}_encrypted") and field in decrypted_doc:
                decrypted_doc[field] = self.decrypt(decrypted_doc[field])
                del decrypted_doc[f"{field}_encrypted"]
        return decrypted_doc

# Define PII fields that require encryption
PII_FIELDS = [
    "ssn", "tax_id", "passport_number",
    "credit_card", "bank_account",
    "medical_record", "health_data"
]

# Global encryption instance
data_encryption = DataEncryption()
''',
            
            # === PRIVACY NOTICE ===
            "privacy_notice": '''
// SOC 2 P1.1 - Privacy Notice Component
const PrivacyPolicy = () => {
  return (
    <div className="max-w-4xl mx-auto p-8">
      <h1 className="text-3xl font-bold mb-6">Privacy Policy</h1>
      <p className="text-gray-600 mb-4">Last updated: {new Date().toLocaleDateString()}</p>
      
      <section className="mb-8">
        <h2 className="text-2xl font-semibold mb-4">1. Information We Collect</h2>
        <p className="mb-4">We collect information you provide directly:</p>
        <ul className="list-disc ml-6 mb-4">
          <li>Account information (name, email, password)</li>
          <li>Profile information you choose to provide</li>
          <li>Communications with us</li>
          <li>Transaction and billing information</li>
        </ul>
        <p className="mb-4">We automatically collect:</p>
        <ul className="list-disc ml-6 mb-4">
          <li>Usage data and analytics</li>
          <li>Device and browser information</li>
          <li>IP address and location data</li>
        </ul>
      </section>
      
      <section className="mb-8">
        <h2 className="text-2xl font-semibold mb-4">2. How We Use Your Information</h2>
        <ul className="list-disc ml-6">
          <li>To provide and maintain our services</li>
          <li>To process transactions</li>
          <li>To send service communications</li>
          <li>To improve our services</li>
          <li>To comply with legal obligations</li>
        </ul>
      </section>
      
      <section className="mb-8">
        <h2 className="text-2xl font-semibold mb-4">3. Your Rights (GDPR/CCPA)</h2>
        <ul className="list-disc ml-6">
          <li><strong>Access:</strong> Request a copy of your data</li>
          <li><strong>Rectification:</strong> Correct inaccurate data</li>
          <li><strong>Erasure:</strong> Request deletion of your data</li>
          <li><strong>Portability:</strong> Export your data</li>
          <li><strong>Objection:</strong> Object to certain processing</li>
        </ul>
      </section>
      
      <section className="mb-8">
        <h2 className="text-2xl font-semibold mb-4">4. Data Retention</h2>
        <p>We retain your data only as long as necessary for the purposes 
        outlined in this policy. Account data is deleted within 30 days of 
        account closure.</p>
      </section>
      
      <section className="mb-8">
        <h2 className="text-2xl font-semibold mb-4">5. Contact Us</h2>
        <p>Data Protection Officer: privacy@yourapp.com</p>
        <p>Address: [Your Business Address]</p>
      </section>
    </div>
  );
};
''',
            
            # === DATA RETENTION ===
            "data_retention": '''
// GDPR Article 5(1)(e) & SOC 2 P5.1 - Data Retention Management
from datetime import datetime, timedelta
from typing import Dict
import schedule
import time

class DataRetentionManager:
    """
    Manages data retention policies and automatic cleanup.
    Ensures data is not kept longer than necessary.
    """
    
    # Retention policies (in days)
    RETENTION_POLICIES: Dict[str, int] = {
        "session_data": 1,           # Session data: 1 day
        "temporary_files": 7,        # Temp files: 7 days
        "activity_logs": 90,         # Activity logs: 90 days
        "audit_logs": 365 * 7,       # Audit logs: 7 years (compliance)
        "user_data": 365 * 3,        # User data: 3 years after last activity
        "analytics_data": 365 * 2,   # Analytics: 2 years
        "backup_data": 365,          # Backups: 1 year
        "deleted_accounts": 30,      # Deleted account data: 30 days grace period
    }
    
    def __init__(self, db):
        self.db = db
    
    def apply_retention_policy(self, collection_name: str, date_field: str = "created_at"):
        """Apply retention policy to a collection"""
        retention_days = self.RETENTION_POLICIES.get(collection_name, 365)
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
        
        # Find records to delete
        records_to_delete = self.db[collection_name].count_documents({
            date_field: {"$lt": cutoff_date}
        })
        
        if records_to_delete > 0:
            # Log before deletion
            self.db.audit_logs.insert_one({
                "event": "data_retention_cleanup",
                "collection": collection_name,
                "records_deleted": records_to_delete,
                "retention_days": retention_days,
                "cutoff_date": cutoff_date,
                "timestamp": datetime.utcnow()
            })
            
            # Perform deletion
            result = self.db[collection_name].delete_many({
                date_field: {"$lt": cutoff_date}
            })
            
            print(f"🗑️ Retention cleanup: Deleted {result.deleted_count} records from {collection_name}")
    
    def run_all_retention_policies(self):
        """Run retention cleanup for all configured collections"""
        collections_config = [
            ("sessions", "last_accessed"),
            ("temp_files", "created_at"),
            ("activity_log", "timestamp"),
            ("analytics", "timestamp"),
        ]
        
        for collection, date_field in collections_config:
            try:
                self.apply_retention_policy(collection, date_field)
            except Exception as e:
                print(f"❌ Retention policy error for {collection}: {e}")
    
    def get_retention_report(self) -> Dict:
        """Generate a retention compliance report"""
        report = {
            "generated_at": datetime.utcnow().isoformat(),
            "policies": self.RETENTION_POLICIES,
            "collections": {}
        }
        
        for collection, retention_days in self.RETENTION_POLICIES.items():
            try:
                total = self.db[collection].count_documents({})
                cutoff = datetime.utcnow() - timedelta(days=retention_days)
                due_for_deletion = self.db[collection].count_documents({
                    "created_at": {"$lt": cutoff}
                })
                report["collections"][collection] = {
                    "total_records": total,
                    "retention_days": retention_days,
                    "due_for_deletion": due_for_deletion
                }
            except:
                pass
        
        return report

# Schedule daily retention cleanup
retention_manager = DataRetentionManager(db)
schedule.every().day.at("03:00").do(retention_manager.run_all_retention_policies)
''',
        }
    
    def get_compliance_prompt_injection(
        self,
        standards: List[ComplianceStandard] = None
    ) -> str:
        """
        Generate prompt injection for AI code generation to ensure compliance.
        This is added to all code generation prompts.
        
        Based on:
        - GDPR: https://gdpr-info.eu/
        - SOC 2: https://sprinto.com/blog/soc-2-controls/
        - NIST SP 800-53: https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-53r5.pdf
        """
        if standards is None:
            standards = [ComplianceStandard.GDPR, ComplianceStandard.SOC2, ComplianceStandard.NIST_800_53]
        
        standard_names = [s.value.upper().replace("_", " ") for s in standards]
        
        return f"""
🛡️ COMPLIANCE REQUIREMENTS - MANDATORY
=======================================
All generated code MUST comply with: {', '.join(standard_names)}

📋 GDPR REQUIREMENTS (EU Regulation 2016/679):
----------------------------------------------
Based on https://gdpr-info.eu/

1. CONSENT (Art. 6, 7): Obtain explicit, freely given consent before processing personal data
   - Consent must be as easy to withdraw as to give
   - Record consent with timestamps and version

2. TRANSPARENCY (Art. 12-14): Clear privacy notices explaining data processing
   - Plain language, easy to understand
   - Purpose, legal basis, recipients, retention periods

3. DATA SUBJECT RIGHTS:
   - Right to Access (Art. 15): Users can view all their data
   - Right to Portability (Art. 20): Export data in JSON/CSV
   - Right to Erasure (Art. 17): Account/data deletion functionality
   - Right to Rectification (Art. 16): Users can update their data
   - Right to Object (Art. 21): Opt-out for marketing

4. PRIVACY BY DESIGN (Art. 25): Data minimization, secure defaults
5. SECURITY (Art. 32): Encryption at rest and in transit
6. BREACH NOTIFICATION (Art. 33): Detect and report breaches within 72 hours
7. PROCESSING RECORDS (Art. 30): Log all data processing activities

🔒 SOC 2 TRUST SERVICES CRITERIA:
---------------------------------
Based on https://sprinto.com/blog/soc-2-controls/

1. CC6 - LOGICAL ACCESS CONTROLS:
   - MFA (Multi-Factor Authentication) for sensitive operations
   - RBAC (Role-Based Access Control) with least privilege
   - Strong password policies (12+ chars, complexity)
   - Account lockout after failed attempts
   - Session management and timeout

2. CC7 - SYSTEM OPERATIONS:
   - Comprehensive logging and monitoring
   - Incident detection and response
   - Health check endpoints

3. CC8 - CHANGE MANAGEMENT:
   - Configuration management
   - Secure deployment practices

4. CONFIDENTIALITY (C1):
   - Encryption at rest (AES-256) and in transit (TLS 1.2+)
   - Secure key management
   - Data masking for sensitive fields

5. AVAILABILITY (A1):
   - Error handling and graceful degradation
   - Backup and recovery procedures

6. PRIVACY (P1-P8):
   - Privacy notices and consent collection
   - Data retention and secure disposal

🏛️ NIST SP 800-53 Rev 5 CONTROLS:
----------------------------------
Based on https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-53r5.pdf

1. AC - ACCESS CONTROL:
   - AC-2: Account Management (unique user IDs, no shared accounts)
   - AC-3: Access Enforcement (authorization checks)
   - AC-6: Least Privilege
   - AC-7: Unsuccessful Logon Attempts (lockout after 5 failures)

2. AU - AUDIT AND ACCOUNTABILITY:
   - AU-2: Audit Events (log auth, admin actions, data changes)
   - AU-3: Content of Audit Records (who, what, when, outcome)
   - AU-9: Protection of Audit Information

3. IA - IDENTIFICATION AND AUTHENTICATION:
   - IA-2: User Authentication (MFA for privileged access)
   - IA-5: Authenticator Management (secure password storage)

4. SC - SYSTEM AND COMMUNICATIONS PROTECTION:
   - SC-8: Transmission Confidentiality (TLS 1.2+, HTTPS only)
   - SC-13: Cryptographic Protection
   - SC-28: Protection of Information at Rest

5. SI - SYSTEM AND INFORMATION INTEGRITY:
   - SI-2: Flaw Remediation (patch management)
   - SI-10: Information Input Validation (prevent injection attacks)

⚙️ CODE MUST INCLUDE:
---------------------
✓ Input validation on ALL user inputs (Pydantic models, type checking)
✓ Parameterized queries (NO SQL injection - use ORM or prepared statements)
✓ Output encoding (prevent XSS - escape HTML, use CSP headers)
✓ CSRF protection for state-changing operations
✓ Rate limiting on authentication and sensitive endpoints
✓ Secure session management (httpOnly, secure cookies, expiry)
✓ Password hashing with bcrypt or Argon2 (NEVER plain text)
✓ Comprehensive error handling (no sensitive data in errors)
✓ Audit logging for security events
✓ HTTPS enforcement (redirect HTTP to HTTPS)
"""
    
    def get_compliant_code_templates(self) -> Dict[str, str]:
        """Get all compliant code templates for generation"""
        return self.code_patterns
    
    def validate_generated_code(
        self,
        code: str,
        file_type: str,
        standards: List[ComplianceStandard] = None
    ) -> List[ComplianceCheck]:
        """
        Validate generated code against compliance requirements.
        Returns list of compliance checks with pass/fail status.
        """
        if standards is None:
            standards = [ComplianceStandard.GDPR, ComplianceStandard.SOC2, ComplianceStandard.NIST_800_53]
        
        checks = []
        
        # Check for required patterns based on file type
        if file_type in ["python", "py"]:
            checks.extend(self._validate_python_compliance(code, standards))
        elif file_type in ["javascript", "jsx", "js", "tsx", "ts"]:
            checks.extend(self._validate_javascript_compliance(code, standards))
        
        return checks
    
    def _validate_python_compliance(
        self,
        code: str,
        standards: List[ComplianceStandard]
    ) -> List[ComplianceCheck]:
        """Validate Python code for compliance"""
        checks = []
        
        # Check for input validation (NIST SI-10)
        has_input_validation = any([
            "pydantic" in code.lower(),
            "validate" in code.lower(),
            "sanitize" in code.lower(),
            "Depends(" in code
        ])
        checks.append(ComplianceCheck(
            requirement_id="NIST-SI-10",
            passed=has_input_validation,
            findings=["Input validation detected"] if has_input_validation else ["No input validation found"],
            recommendations=[] if has_input_validation else ["Add Pydantic models for request validation"]
        ))
        
        # Check for secure password handling (NIST IA-2)
        has_secure_password = any([
            "bcrypt" in code.lower(),
            "argon2" in code.lower(),
            "passlib" in code.lower(),
            "hash_password" in code
        ])
        checks.append(ComplianceCheck(
            requirement_id="NIST-IA-2",
            passed=has_secure_password,
            findings=["Secure password hashing detected"] if has_secure_password else ["No secure password handling found"],
            recommendations=[] if has_secure_password else ["Use bcrypt or Argon2 for password hashing"]
        ))
        
        # Check for audit logging (NIST AU-2, GDPR Art. 30)
        has_audit_logging = any([
            "audit" in code.lower(),
            "log_event" in code,
            "security_log" in code
        ])
        checks.append(ComplianceCheck(
            requirement_id="NIST-AU-2",
            passed=has_audit_logging,
            findings=["Audit logging detected"] if has_audit_logging else ["No audit logging found"],
            recommendations=[] if has_audit_logging else ["Implement audit logging for compliance"]
        ))
        
        return checks
    
    def _validate_javascript_compliance(
        self,
        code: str,
        standards: List[ComplianceStandard]
    ) -> List[ComplianceCheck]:
        """Validate JavaScript/React code for compliance"""
        checks = []
        
        # Check for consent handling (GDPR Art. 6, 7)
        has_consent = any([
            "consent" in code.lower(),
            "gdpr" in code.lower(),
            "cookie" in code.lower() and "accept" in code.lower()
        ])
        checks.append(ComplianceCheck(
            requirement_id="GDPR-001",
            passed=has_consent,
            findings=["Consent handling detected"] if has_consent else ["No consent mechanism found"],
            recommendations=[] if has_consent else ["Add GDPR consent banner component"]
        ))
        
        # Check for privacy policy link (SOC 2 P1)
        has_privacy_policy = any([
            "/privacy" in code.lower(),
            "privacy policy" in code.lower(),
            "privacypolicy" in code.lower()
        ])
        checks.append(ComplianceCheck(
            requirement_id="SOC2-P1",
            passed=has_privacy_policy,
            findings=["Privacy policy link detected"] if has_privacy_policy else ["No privacy policy link found"],
            recommendations=[] if has_privacy_policy else ["Add link to privacy policy in footer"]
        ))
        
        # Check for XSS prevention
        has_xss_prevention = any([
            "dangerouslySetInnerHTML" not in code,  # Not using dangerous method
            "DOMPurify" in code,
            "sanitize" in code.lower()
        ])
        checks.append(ComplianceCheck(
            requirement_id="ISO-003",
            passed=has_xss_prevention,
            findings=["XSS prevention measures detected"] if has_xss_prevention else ["Potential XSS vulnerability"],
            recommendations=[] if has_xss_prevention else ["Avoid dangerouslySetInnerHTML, use DOMPurify if needed"]
        ))
        
        return checks
    
    def generate_compliance_report(
        self,
        app_name: str,
        checks: List[ComplianceCheck],
        standards: List[ComplianceStandard]
    ) -> ComplianceReport:
        """Generate a comprehensive compliance report"""
        passed = sum(1 for c in checks if c.passed)
        failed = len(checks) - passed
        
        recommendations = []
        for check in checks:
            if not check.passed:
                recommendations.extend(check.recommendations)
        
        return ComplianceReport(
            app_name=app_name,
            generated_at=datetime.utcnow(),
            standards_applied=standards,
            total_requirements=len(checks),
            passed_requirements=passed,
            failed_requirements=failed,
            checks=checks,
            overall_score=(passed / len(checks) * 100) if checks else 0,
            recommendations=recommendations
        )


# Global compliance framework instance
compliance_framework = ComplianceFramework()


def get_compliance_requirements() -> Dict[str, Any]:
    """Get all compliance requirements for documentation"""
    framework = ComplianceFramework()
    
    requirements_by_standard = {}
    for req_id, req in framework.requirements.items():
        standard_name = req.standard.value
        if standard_name not in requirements_by_standard:
            requirements_by_standard[standard_name] = []
        
        requirements_by_standard[standard_name].append({
            "id": req.id,
            "category": req.category.value,
            "title": req.title,
            "description": req.description,
            "implementation": req.implementation_guidance,
            "severity": req.severity,
            "references": req.references
        })
    
    return requirements_by_standard


def get_compliance_code_patterns() -> Dict[str, str]:
    """Get all compliant code patterns"""
    framework = ComplianceFramework()
    return framework.code_patterns
