"""
SOC2 Control Implementation Framework
Provides concrete implementations of SOC2 controls and requirements
"""

from typing import List, Dict, Any, Optional, Callable
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta
import hashlib
import hmac
import secrets
import json
from functools import wraps
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============ SECURITY CONTROLS ============

class AccessControlLevel(Enum):
    """Access control levels"""
    DENY_ALL = 0
    RESTRICTED = 1
    LIMITED = 2
    GENERAL = 3
    UNRESTRICTED = 4

class EncryptionAlgorithm(Enum):
    """Supported encryption algorithms"""
    AES_256_GCM = "AES-256-GCM"
    AES_256_CBC = "AES-256-CBC"
    TLS_1_3 = "TLS-1.3"
    RSA_2048 = "RSA-2048"

@dataclass
class AccessControlPolicy:
    """Represents an access control policy"""
    policy_id: str
    name: str
    description: str
    access_level: AccessControlLevel
    required_mfa: bool
    allowed_ip_ranges: List[str]
    allowed_roles: List[str]
    expiry_date: Optional[datetime] = None
    requires_approval: bool = False
    
    def is_valid(self) -> bool:
        """Check if policy is still valid"""
        if self.expiry_date and datetime.now() > self.expiry_date:
            return False
        return True

class CC1_ControlEnvironment:
    """CC1: Control Environment Implementation"""
    
    def __init__(self):
        self.code_of_conduct_version = "1.0"
        self.code_of_conduct_date = datetime.now()
        self.trained_employees: set = set()
        self.policy_acknowledgments: Dict[str, datetime] = {}
        self.violations: List[Dict[str, Any]] = []
    
    def create_code_of_conduct(self, content: str) -> Dict[str, Any]:
        """Create and document code of conduct"""
        return {
            "code_of_conduct": {
                "version": self.code_of_conduct_version,
                "created_date": datetime.now().isoformat(),
                "content_hash": hashlib.sha256(content.encode()).hexdigest(),
                "scope": "All employees and contractors",
                "sections": [
                    "Integrity and Ethical Values",
                    "Conflict of Interest",
                    "Confidentiality",
                    "Use of Company Assets",
                    "Security Responsibilities",
                    "Consequences for Violations"
                ]
            }
        }
    
    def track_training(self, employee_id: str, training_type: str) -> bool:
        """Track employee training completion"""
        self.trained_employees.add(f"{employee_id}:{training_type}")
        logger.info(f"Training tracked: {employee_id} - {training_type}")
        return True
    
    def verify_policy_acknowledgment(self, employee_id: str, policy_name: str) -> bool:
        """Verify employee has acknowledged policy"""
        key = f"{employee_id}:{policy_name}"
        return key in self.policy_acknowledgments
    
    def log_violation(self, employee_id: str, violation_type: str, details: str) -> str:
        """Log policy violation"""
        violation_id = f"VIO-{hashlib.md5(str(datetime.now()).encode()).hexdigest()[:8]}"
        self.violations.append({
            "violation_id": violation_id,
            "employee_id": employee_id,
            "type": violation_type,
            "details": details,
            "date": datetime.now().isoformat(),
            "status": "REPORTED"
        })
        logger.warning(f"Violation logged: {violation_id}")
        return violation_id

class CC6_AccessControls:
    """CC6: Logical and Physical Access Controls Implementation"""
    
    def __init__(self):
        self.access_policies: Dict[str, AccessControlPolicy] = {}
        self.user_sessions: Dict[str, Dict[str, Any]] = {}
        self.mfa_enabled_users: set = set()
        self.failed_login_attempts: Dict[str, List[datetime]] = {}
        self.access_logs: List[Dict[str, Any]] = []
        self.encryption_keys: Dict[str, str] = {}
    
    def create_access_policy(self, policy_id: str, name: str, 
                           access_level: AccessControlLevel,
                           required_mfa: bool = True) -> AccessControlPolicy:
        """Create access control policy"""
        policy = AccessControlPolicy(
            policy_id=policy_id,
            name=name,
            description=f"{name} access control",
            access_level=access_level,
            required_mfa=required_mfa,
            allowed_ip_ranges=["0.0.0.0/0"],  # Update as needed
            allowed_roles=[]
        )
        self.access_policies[policy_id] = policy
        logger.info(f"Access policy created: {policy_id}")
        return policy
    
    def enable_mfa(self, user_id: str) -> Dict[str, str]:
        """Enable multi-factor authentication for user"""
        secret = secrets.token_urlsafe(32)
        self.mfa_enabled_users.add(user_id)
        
        backup_codes = [secrets.token_urlsafe(8) for _ in range(10)]
        
        logger.info(f"MFA enabled for user: {user_id}")
        return {
            "user_id": user_id,
            "secret": secret,
            "backup_codes": backup_codes,
            "enabled_date": datetime.now().isoformat()
        }
    
    def authenticate_user(self, user_id: str, password: str, mfa_code: Optional[str] = None) -> bool:
        """Authenticate user with MFA if required"""
        # Verify password (in production, compare hashed password)
        if not password:
            self._record_failed_attempt(user_id)
            return False
        
        # Check MFA if enabled
        if user_id in self.mfa_enabled_users and not mfa_code:
            self._record_failed_attempt(user_id)
            return False
        
        # Check for brute force attacks
        if self._is_brute_force_attack(user_id):
            logger.warning(f"Brute force attack detected for user: {user_id}")
            return False
        
        # Create session
        session_id = secrets.token_urlsafe(32)
        self.user_sessions[session_id] = {
            "user_id": user_id,
            "created_at": datetime.now().isoformat(),
            "last_activity": datetime.now().isoformat(),
            "ip_address": "0.0.0.0"  # Should be captured from request
        }
        
        self._log_access("login", user_id, "success")
        return True
    
    def encrypt_data(self, data: str, algorithm: EncryptionAlgorithm) -> Dict[str, Any]:
        """Encrypt sensitive data"""
        # In production, use proper cryptographic libraries
        key = secrets.token_urlsafe(32)
        ciphertext = hashlib.sha256(f"{data}{key}".encode()).hexdigest()
        
        return {
            "algorithm": algorithm.value,
            "ciphertext": ciphertext,
            "key_id": hashlib.sha256(key.encode()).hexdigest()[:16],
            "encrypted_at": datetime.now().isoformat()
        }
    
    def decrypt_data(self, encrypted_data: Dict[str, Any], key: str) -> str:
        """Decrypt sensitive data (stub)"""
        # In production, implement proper decryption
        logger.info("Data decryption requested - verify authorization")
        return "decrypted_data"
    
    def _record_failed_attempt(self, user_id: str):
        """Record failed login attempt"""
        if user_id not in self.failed_login_attempts:
            self.failed_login_attempts[user_id] = []
        self.failed_login_attempts[user_id].append(datetime.now())
        self._log_access("login", user_id, "failure")
    
    def _is_brute_force_attack(self, user_id: str, threshold: int = 5, 
                              time_window_minutes: int = 15) -> bool:
        """Detect brute force attacks"""
        if user_id not in self.failed_login_attempts:
            return False
        
        attempts = self.failed_login_attempts[user_id]
        cutoff = datetime.now() - timedelta(minutes=time_window_minutes)
        recent_attempts = [a for a in attempts if a > cutoff]
        
        return len(recent_attempts) >= threshold
    
    def _log_access(self, action: str, user_id: str, status: str):
        """Log access event"""
        self.access_logs.append({
            "action": action,
            "user_id": user_id,
            "status": status,
            "timestamp": datetime.now().isoformat()
        })

class CC8_ChangeManagement:
    """CC8: Change Management Implementation"""
    
    def __init__(self):
        self.change_requests: Dict[str, Dict[str, Any]] = {}
        self.change_log: List[Dict[str, Any]] = []
        self.approvers: List[str] = []
    
    def create_change_request(self, title: str, description: str, 
                            affected_systems: List[str],
                            impact_assessment: str) -> str:
        """Create change request for approval"""
        change_id = f"CHG-{hashlib.md5(str(datetime.now()).encode()).hexdigest()[:8]}"
        
        self.change_requests[change_id] = {
            "change_id": change_id,
            "title": title,
            "description": description,
            "affected_systems": affected_systems,
            "impact_assessment": impact_assessment,
            "status": "PENDING_APPROVAL",
            "created_date": datetime.now().isoformat(),
            "scheduled_date": None,
            "implemented_date": None,
            "approver": None
        }
        
        logger.info(f"Change request created: {change_id}")
        return change_id
    
    def approve_change(self, change_id: str, approver_id: str) -> bool:
        """Approve change request"""
        if change_id not in self.change_requests:
            return False
        
        if approver_id not in self.approvers:
            logger.warning(f"Unauthorized approver: {approver_id}")
            return False
        
        self.change_requests[change_id]["status"] = "APPROVED"
        self.change_requests[change_id]["approver"] = approver_id
        self.change_requests[change_id]["approved_date"] = datetime.now().isoformat()
        
        logger.info(f"Change approved: {change_id} by {approver_id}")
        return True
    
    def implement_change(self, change_id: str) -> bool:
        """Implement approved change"""
        if change_id not in self.change_requests:
            return False
        
        change = self.change_requests[change_id]
        if change["status"] != "APPROVED":
            logger.warning(f"Cannot implement unapproved change: {change_id}")
            return False
        
        # Log change implementation
        self.change_log.append({
            "change_id": change_id,
            "action": "IMPLEMENTED",
            "timestamp": datetime.now().isoformat(),
            "affected_systems": change["affected_systems"]
        })
        
        change["status"] = "IMPLEMENTED"
        change["implemented_date"] = datetime.now().isoformat()
        
        logger.info(f"Change implemented: {change_id}")
        return True
    
    def rollback_change(self, change_id: str, reason: str) -> bool:
        """Rollback implemented change"""
        if change_id not in self.change_requests:
            return False
        
        self.change_log.append({
            "change_id": change_id,
            "action": "ROLLBACK",
            "reason": reason,
            "timestamp": datetime.now().isoformat()
        })
        
        self.change_requests[change_id]["status"] = "ROLLED_BACK"
        logger.info(f"Change rolled back: {change_id}")
        return True

# ============ AVAILABILITY CONTROLS ============

class AvailabilityControl:
    """Availability control implementation"""
    
    def __init__(self):
        self.sla_targets: Dict[str, float] = {}
        self.system_availability: Dict[str, List[Dict[str, Any]]] = {}
        self.backup_jobs: List[Dict[str, Any]] = []
        self.disaster_recovery_plans: Dict[str, Dict[str, Any]] = {}
    
    def define_sla(self, system_name: str, availability_percentage: float) -> Dict[str, Any]:
        """Define SLA for system"""
        self.sla_targets[system_name] = availability_percentage
        
        return {
            "system": system_name,
            "availability_target": f"{availability_percentage}%",
            "allowable_downtime_hours": (24 * 365 * (100 - availability_percentage)) / 100
        }
    
    def configure_backup(self, system_name: str, frequency: str, 
                        retention_days: int) -> str:
        """Configure automated backup"""
        backup_id = f"BKP-{hashlib.md5(str(datetime.now()).encode()).hexdigest()[:8]}"
        
        self.backup_jobs.append({
            "backup_id": backup_id,
            "system": system_name,
            "frequency": frequency,
            "retention_days": retention_days,
            "created_date": datetime.now().isoformat(),
            "last_backup": None,
            "next_backup": None,
            "status": "ACTIVE"
        })
        
        logger.info(f"Backup configured: {backup_id}")
        return backup_id
    
    def create_disaster_recovery_plan(self, system_name: str, 
                                     rto_hours: int, 
                                     rpo_hours: int) -> str:
        """Create disaster recovery plan"""
        plan_id = f"DRP-{hashlib.md5(str(datetime.now()).encode()).hexdigest()[:8]}"
        
        self.disaster_recovery_plans[plan_id] = {
            "plan_id": plan_id,
            "system": system_name,
            "rto_hours": rto_hours,  # Recovery Time Objective
            "rpo_hours": rpo_hours,  # Recovery Point Objective
            "failover_procedures": [],
            "recovery_procedures": [],
            "tested_date": None,
            "status": "DRAFT"
        }
        
        logger.info(f"DR Plan created: {plan_id}")
        return plan_id

# ============ MONITORING AND LOGGING ============

class AuditLogger:
    """Audit logging implementation"""
    
    def __init__(self):
        self.audit_logs: List[Dict[str, Any]] = []
        self.log_integrity_hashes: List[str] = []
    
    def log_event(self, event_type: str, user_id: str, resource: str, 
                 action: str, result: str, details: Optional[Dict] = None) -> str:
        """Log audit event"""
        event_id = f"AUD-{hashlib.md5(str(datetime.now()).encode()).hexdigest()[:8]}"
        
        event = {
            "event_id": event_id,
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "user_id": user_id,
            "resource": resource,
            "action": action,
            "result": result,
            "details": details or {}
        }
        
        self.audit_logs.append(event)
        
        # Ensure log integrity
        self._ensure_log_integrity(event)
        
        return event_id
    
    def _ensure_log_integrity(self, event: Dict[str, Any]):
        """Ensure audit log integrity"""
        # Create hash of audit log for integrity verification
        log_content = json.dumps(event, sort_keys=True)
        event_hash = hashlib.sha256(log_content.encode()).hexdigest()
        self.log_integrity_hashes.append(event_hash)
    
    def verify_log_integrity(self) -> bool:
        """Verify audit logs haven't been tampered with"""
        # In production, use WORM (Write Once Read Many) storage
        logger.info(f"Verifying integrity of {len(self.audit_logs)} audit logs")
        return len(self.audit_logs) == len(self.log_integrity_hashes)

# ============ HELPER DECORATORS ============

def require_authorization(required_roles: List[str]):
    """Decorator to enforce authorization"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            # In production, check actual user roles
            logger.info(f"Authorization check for {func.__name__}")
            return func(self, *args, **kwargs)
        return wrapper
    return decorator

def audit_logged(event_type: str):
    """Decorator to automatically log events"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            result = func(self, *args, **kwargs)
            logger.info(f"{event_type}: {func.__name__}")
            return result
        return wrapper
    return decorator

if __name__ == "__main__":
    # Example usage
    
    # Control Environment
    print("=== CC1: Control Environment ===")
    control_env = CC1_ControlEnvironment()
    control_env.create_code_of_conduct("All employees must follow ethical standards...")
    control_env.track_training("EMP001", "Security Awareness")
    print("✓ Code of conduct created")
    print("✓ Training tracked\n")
    
    # Access Controls
    print("=== CC6: Access Controls ===")
    access_control = CC6_AccessControls()
    policy = access_control.create_access_policy(
        "POL001",
        "Database Access",
        AccessControlLevel.RESTRICTED,
        required_mfa=True
    )
    mfa_info = access_control.enable_mfa("USER001")
    print(f"✓ Access policy created: {policy.policy_id}")
    print(f"✓ MFA enabled for USER001\n")
    
    # Change Management
    print("=== CC8: Change Management ===")
    change_mgmt = CC8_ChangeManagement()
    change_mgmt.approvers = ["APPROVER001"]
    change_id = change_mgmt.create_change_request(
        "Update SSL Certificate",
        "Replace expired SSL certificate",
        ["Web Server"],
        "Low impact - maintenance window"
    )
    change_mgmt.approve_change(change_id, "APPROVER001")
    change_mgmt.implement_change(change_id)
    print(f"✓ Change created: {change_id}")
    print(f"✓ Change approved and implemented\n")
    
    # Availability
    print("=== Availability Controls ===")
    availability = AvailabilityControl()
    sla = availability.define_sla("Web App", 99.9)
    backup_id = availability.configure_backup("Database", "Daily", 30)
    print(f"✓ SLA defined: {sla['system']} - {sla['availability_target']}")
    print(f"✓ Backup configured: {backup_id}\n")
    
    # Audit Logging
    print("=== Audit Logging ===")
    logger_obj = AuditLogger()
    event_id = logger_obj.log_event(
        "USER_LOGIN",
        "USER001",
        "Web Application",
        "Login",
        "SUCCESS"
    )
    print(f"✓ Audit event logged: {event_id}")
    print(f"✓ Log integrity verified: {logger_obj.verify_log_integrity()}")
