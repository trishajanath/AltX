"""
SOC2 Compliance Integration for AI Code Generators

This module provides seamless integration of SOC2 compliance verification
into the existing AI code generation pipeline (PureAIGenerator, ValidatedAIGenerator).

Features:
- Automatic compliance scanning during code generation
- Real-time gap identification and auto-fixing
- Audit documentation generation for each project
- Compliance reports accessible via API

Usage:
    from soc2_generator_integration import SOC2ComplianceWrapper
    
    # Wrap the existing generator
    generator = SOC2ComplianceWrapper(PureAIGenerator())
    
    # Generate with compliance
    files = await generator.generate_with_compliance(...)
"""

from __future__ import annotations

import json
import os
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
import logging

# Import compliance engine
from soc2_code_compliance import (
    SOC2CodeComplianceEngine,
    CodeComplianceResult,
    AuditDocumentation,
    verify_and_document_compliance
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ComplianceGenerationResult:
    """Result of compliance-verified code generation"""
    success: bool
    project_name: str
    files_created: List[str]
    files_fixed: List[str]
    
    # Compliance details
    compliance_score: float
    compliance_level: str
    findings_count: int
    auto_fixes_applied: int
    manual_fixes_required: int
    
    # Documentation
    audit_report_path: Optional[str]
    json_report_path: Optional[str]
    
    # Gaps and recommendations
    critical_gaps: List[Dict]
    high_gaps: List[Dict]
    remediation_plan: List[Dict]
    
    # Metadata
    generation_time: str
    compliance_verification_time: float


class SOC2ComplianceWrapper:
    """
    Wrapper that adds SOC2 compliance verification to any code generator.
    
    This wrapper intercepts generated code, verifies it against SOC2 requirements,
    auto-fixes issues where possible, and generates audit documentation.
    """
    
    def __init__(
        self,
        generator: Any,
        auto_fix: bool = True,
        generate_documentation: bool = True,
        documentation_output_dir: Optional[Path] = None
    ):
        """
        Initialize the compliance wrapper.
        
        Args:
            generator: The underlying code generator (PureAIGenerator, etc.)
            auto_fix: Whether to automatically fix compliance issues
            generate_documentation: Whether to generate audit documentation
            documentation_output_dir: Directory for audit documents (defaults to project dir)
        """
        self.generator = generator
        self.auto_fix = auto_fix
        self.generate_documentation = generate_documentation
        self.documentation_output_dir = documentation_output_dir
        
        # Initialize compliance engine
        self.compliance_engine = SOC2CodeComplianceEngine()
        
        logger.info("✅ SOC2 Compliance Wrapper initialized")
        logger.info(f"   Auto-fix: {'Enabled' if auto_fix else 'Disabled'}")
        logger.info(f"   Documentation: {'Enabled' if generate_documentation else 'Disabled'}")
    
    async def generate_with_compliance(
        self,
        project_path: Path,
        project_spec: dict,
        project_name: str,
        tech_stack: List[str] = None,
        **kwargs
    ) -> ComplianceGenerationResult:
        """
        Generate code with SOC2 compliance verification.
        
        This method:
        1. Generates code using the underlying generator
        2. Scans for compliance issues
        3. Auto-fixes where possible
        4. Generates audit documentation
        5. Returns comprehensive results
        """
        import time
        start_time = time.time()
        
        logger.info(f"🚀 Starting compliance-verified generation for: {project_name}")
        
        result = ComplianceGenerationResult(
            success=False,
            project_name=project_name,
            files_created=[],
            files_fixed=[],
            compliance_score=0.0,
            compliance_level="NOT_ASSESSED",
            findings_count=0,
            auto_fixes_applied=0,
            manual_fixes_required=0,
            audit_report_path=None,
            json_report_path=None,
            critical_gaps=[],
            high_gaps=[],
            remediation_plan=[],
            generation_time=datetime.now().isoformat(),
            compliance_verification_time=0.0
        )
        
        try:
            # Step 1: Generate code using underlying generator
            logger.info("📝 Step 1: Generating code...")
            
            # Call the underlying generator
            if hasattr(self.generator, 'generate_project_structure'):
                generated_files = await self.generator.generate_project_structure(
                    project_path, project_spec, project_name, tech_stack, **kwargs
                )
            elif hasattr(self.generator, 'generate_project'):
                generated_files = await self.generator.generate_project(
                    project_path, project_spec.get('idea', ''), project_name
                )
            else:
                raise AttributeError("Generator does not have a compatible generation method")
            
            result.files_created = generated_files if isinstance(generated_files, list) else []
            
            # Step 2: Read generated files for compliance check
            logger.info("📂 Step 2: Reading generated files...")
            files_content = {}
            
            for file_info in result.files_created:
                if isinstance(file_info, str):
                    file_path = project_path / file_info
                elif isinstance(file_info, dict):
                    file_path = project_path / file_info.get('path', '')
                else:
                    continue
                
                if file_path.exists() and file_path.is_file():
                    try:
                        files_content[str(file_path.relative_to(project_path))] = file_path.read_text()
                    except Exception as e:
                        logger.warning(f"Could not read {file_path}: {e}")
            
            # Step 3: Verify compliance
            logger.info("🔍 Step 3: Verifying SOC2 compliance...")
            compliance_start = time.time()
            
            compliance_result, fixed_files = await self.compliance_engine.verify_generated_code(
                project_name=project_name,
                files_content=files_content,
                auto_fix=self.auto_fix
            )
            
            result.compliance_verification_time = time.time() - compliance_start
            result.compliance_score = compliance_result.compliance_score
            result.compliance_level = compliance_result.compliance_level.value
            result.findings_count = len(compliance_result.security_findings)
            result.auto_fixes_applied = compliance_result.auto_fixes_applied
            result.manual_fixes_required = compliance_result.manual_fixes_required
            
            # Step 4: Write fixed files back
            if self.auto_fix and fixed_files:
                logger.info("✏️ Step 4: Writing fixed files...")
                for file_path, content in fixed_files.items():
                    full_path = project_path / file_path
                    if files_content.get(file_path) != content:
                        full_path.parent.mkdir(parents=True, exist_ok=True)
                        full_path.write_text(content)
                        result.files_fixed.append(file_path)
            
            # Step 5: Generate documentation
            if self.generate_documentation:
                logger.info("📄 Step 5: Generating audit documentation...")
                
                audit_doc = self.compliance_engine.generate_audit_documentation(
                    compliance_result,
                    include_remediation_plan=True
                )
                
                # Determine output directory
                doc_dir = self.documentation_output_dir or (project_path / "compliance")
                doc_dir.mkdir(parents=True, exist_ok=True)
                
                # Export markdown report
                result.audit_report_path = self.compliance_engine.export_audit_documentation(
                    audit_doc, doc_dir, format="markdown"
                )
                
                # Export JSON report
                result.json_report_path = self.compliance_engine.export_audit_documentation(
                    audit_doc, doc_dir, format="json"
                )
                
                # Store gaps and remediation plan
                result.critical_gaps = [
                    {"control": g.control_code, "description": g.description}
                    for g in compliance_result.compliance_gaps
                    if g.severity == "CRITICAL"
                ]
                result.high_gaps = [
                    {"control": g.control_code, "description": g.description}
                    for g in compliance_result.compliance_gaps
                    if g.severity == "HIGH"
                ]
                result.remediation_plan = audit_doc.remediation_plan
            
            result.success = True
            logger.info(f"✅ Compliance-verified generation complete!")
            logger.info(f"   Score: {result.compliance_score:.1f}%")
            logger.info(f"   Level: {result.compliance_level}")
            logger.info(f"   Auto-fixes: {result.auto_fixes_applied}")
            
        except Exception as e:
            logger.error(f"❌ Compliance generation failed: {e}")
            raise
        
        return result


class SOC2ComplianceMiddleware:
    """
    Middleware for adding SOC2 compliance to existing generation pipelines.
    
    This can be injected into the generation flow without modifying
    the existing generator classes.
    """
    
    def __init__(self):
        self.compliance_engine = SOC2CodeComplianceEngine()
        self.compliance_history: Dict[str, CodeComplianceResult] = {}
    
    async def process_generated_files(
        self,
        project_name: str,
        files_content: Dict[str, str],
        auto_fix: bool = True
    ) -> Tuple[Dict[str, str], CodeComplianceResult]:
        """
        Process generated files through compliance verification.
        
        Args:
            project_name: Name of the project
            files_content: Dict of file_path -> content
            auto_fix: Whether to auto-fix issues
            
        Returns:
            Tuple of (fixed_files, compliance_result)
        """
        result, fixed_files = await self.compliance_engine.verify_generated_code(
            project_name=project_name,
            files_content=files_content,
            auto_fix=auto_fix
        )
        
        # Store in history
        self.compliance_history[project_name] = result
        
        return fixed_files, result
    
    def get_compliance_status(self, project_name: str) -> Optional[Dict]:
        """Get compliance status for a project"""
        result = self.compliance_history.get(project_name)
        if result:
            return {
                "project": project_name,
                "score": result.compliance_score,
                "level": result.compliance_level.value,
                "findings": len(result.security_findings),
                "critical": result.critical_findings,
                "high": result.high_findings,
                "auto_fixed": result.auto_fixes_applied
            }
        return None
    
    def get_all_compliance_statuses(self) -> List[Dict]:
        """Get compliance status for all processed projects"""
        return [
            self.get_compliance_status(name)
            for name in self.compliance_history.keys()
        ]


# Global middleware instance
compliance_middleware = SOC2ComplianceMiddleware()


def integrate_with_pure_ai_generator():
    """
    Patch the PureAIGenerator to include SOC2 compliance verification.
    
    This function modifies the generator to automatically verify
    compliance after code generation.
    """
    try:
        from pure_ai_generator import PureAIGenerator
        
        # Store original method
        original_generate = PureAIGenerator.generate_project_structure
        
        async def compliant_generate(
            self,
            project_path: Path,
            project_spec: dict,
            project_name: str,
            tech_stack: List[str] = None,
            **kwargs
        ):
            """Enhanced generation with SOC2 compliance"""
            
            # Call original generation
            result = await original_generate(
                self, project_path, project_spec, project_name, tech_stack, **kwargs
            )
            
            # Read generated files
            files_content = {}
            if isinstance(result, list):
                for file_info in result:
                    file_path = project_path / file_info if isinstance(file_info, str) else None
                    if file_path and file_path.exists():
                        try:
                            files_content[file_info] = file_path.read_text()
                        except:
                            pass
            
            # Process through compliance middleware
            if files_content:
                fixed_files, compliance_result = await compliance_middleware.process_generated_files(
                    project_name=project_name,
                    files_content=files_content,
                    auto_fix=True
                )
                
                # Write fixed files
                for file_path, content in fixed_files.items():
                    full_path = project_path / file_path
                    full_path.write_text(content)
                
                # Generate compliance documentation
                compliance_dir = project_path / "compliance"
                compliance_dir.mkdir(exist_ok=True)
                
                engine = SOC2CodeComplianceEngine()
                audit_doc = engine.generate_audit_documentation(compliance_result)
                engine.export_audit_documentation(audit_doc, compliance_dir, "markdown")
                engine.export_audit_documentation(audit_doc, compliance_dir, "json")
                
                logger.info(f"📋 SOC2 Compliance: {compliance_result.compliance_score:.1f}%")
            
            return result
        
        # Patch the method
        PureAIGenerator.generate_project_structure = compliant_generate
        logger.info("✅ PureAIGenerator patched with SOC2 compliance")
        
    except ImportError:
        logger.warning("⚠️ PureAIGenerator not available for patching")


def create_compliance_api_routes(app):
    """
    Add compliance-related API routes to a FastAPI app.
    
    Routes added:
    - GET /api/compliance/{project_name} - Get compliance status
    - GET /api/compliance/{project_name}/report - Get full report
    - GET /api/compliance/all - Get all compliance statuses
    """
    from fastapi import HTTPException
    from fastapi.responses import JSONResponse, PlainTextResponse
    
    @app.get("/api/compliance/{project_name}")
    async def get_compliance_status(project_name: str):
        """Get compliance status for a project"""
        status = compliance_middleware.get_compliance_status(project_name)
        if status:
            return JSONResponse(content=status)
        raise HTTPException(status_code=404, detail="Project not found")
    
    @app.get("/api/compliance/{project_name}/report")
    async def get_compliance_report(project_name: str, format: str = "json"):
        """Get full compliance report for a project"""
        result = compliance_middleware.compliance_history.get(project_name)
        if not result:
            raise HTTPException(status_code=404, detail="Project not found")
        
        engine = SOC2CodeComplianceEngine()
        audit_doc = engine.generate_audit_documentation(result)
        
        if format == "json":
            return JSONResponse(content=asdict(audit_doc))
        elif format == "markdown":
            md = engine._format_as_markdown(audit_doc)
            return PlainTextResponse(content=md, media_type="text/markdown")
        else:
            raise HTTPException(status_code=400, detail="Invalid format")
    
    @app.get("/api/compliance/all")
    async def get_all_compliance():
        """Get compliance status for all projects"""
        return JSONResponse(content=compliance_middleware.get_all_compliance_statuses())
    
    logger.info("✅ Compliance API routes added")


# Compliance-injected code templates
COMPLIANCE_CODE_TEMPLATES = {
    "python_security_imports": '''
# SOC2 Compliance: Security Imports
import os
import logging
import hashlib
import secrets
from datetime import datetime, timedelta

# Configure secure logging (CC7.2)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
''',
    
    "fastapi_security_middleware": '''
# SOC2 Compliance: Security Middleware (CC6.7)
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses"""
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Security headers (CC6.7)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
        
        return response

# Add to app: app.add_middleware(SecurityHeadersMiddleware)
''',
    
    "input_validation": '''
# SOC2 Compliance: Input Validation (CC6.6)
from pydantic import BaseModel, validator, Field
from typing import Optional
import re

class SecureInput(BaseModel):
    """Base model with security validation"""
    
    @validator('*', pre=True)
    def sanitize_strings(cls, v):
        if isinstance(v, str):
            # Remove potential XSS patterns
            v = re.sub(r'<script[^>]*>.*?</script>', '', v, flags=re.IGNORECASE | re.DOTALL)
            # Limit length
            v = v[:10000]
        return v
''',
    
    "audit_logging": '''
# SOC2 Compliance: Audit Logging (CC7.2)
import json
from datetime import datetime
from typing import Any, Dict

class AuditLog:
    """Audit logging for compliance"""
    
    @staticmethod
    def log_event(
        event_type: str,
        details: Dict[str, Any],
        user_id: str = "system",
        ip_address: str = None
    ):
        """Log an auditable event"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "user_id": user_id,
            "ip_address": ip_address,
            "details": details
        }
        logger.info(f"AUDIT: {json.dumps(log_entry)}")
        return log_entry

# Usage: AuditLog.log_event("user_login", {"email": user.email}, user.id)
''',
    
    "secure_password_handling": '''
# SOC2 Compliance: Secure Password Handling (CC6.1)
import bcrypt
import secrets
import string

def hash_password(password: str) -> str:
    """Securely hash a password"""
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode(), salt).decode()

def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against its hash"""
    return bcrypt.checkpw(password.encode(), hashed.encode())

def generate_secure_token(length: int = 32) -> str:
    """Generate a cryptographically secure token"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))
''',
    
    "rate_limiting": '''
# SOC2 Compliance: Rate Limiting (CC6.1)
from collections import defaultdict
from datetime import datetime, timedelta
from fastapi import HTTPException, Request

class RateLimiter:
    """Simple in-memory rate limiter"""
    
    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = defaultdict(list)
    
    def check_rate_limit(self, client_id: str) -> bool:
        """Check if client has exceeded rate limit"""
        now = datetime.utcnow()
        window_start = now - timedelta(seconds=self.window_seconds)
        
        # Clean old requests
        self.requests[client_id] = [
            req_time for req_time in self.requests[client_id]
            if req_time > window_start
        ]
        
        # Check limit
        if len(self.requests[client_id]) >= self.max_requests:
            return False
        
        # Record request
        self.requests[client_id].append(now)
        return True

rate_limiter = RateLimiter()

async def rate_limit_middleware(request: Request, call_next):
    client_ip = request.client.host
    if not rate_limiter.check_rate_limit(client_ip):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    return await call_next(request)
'''
}


def get_compliance_code_template(template_name: str) -> str:
    """Get a compliance code template by name"""
    return COMPLIANCE_CODE_TEMPLATES.get(template_name, "")


def inject_compliance_into_code(content: str, file_type: str) -> str:
    """
    Inject compliance-related code into generated files.
    
    Args:
        content: Original file content
        file_type: Type of file (python, javascript, etc.)
        
    Returns:
        Content with compliance code injected
    """
    if file_type == "python":
        # Add security imports if not present
        if "import logging" not in content and "fastapi" in content.lower():
            content = COMPLIANCE_CODE_TEMPLATES["python_security_imports"] + "\n" + content
        
        # Add audit logging setup
        if "AuditLog" not in content and "def " in content:
            content = content + "\n\n" + COMPLIANCE_CODE_TEMPLATES["audit_logging"]
    
    return content


if __name__ == "__main__":
    # Test the integration
    import asyncio
    
    async def test_wrapper():
        # Create a mock generator
        class MockGenerator:
            async def generate_project_structure(self, path, spec, name, stack):
                # Create test files
                path.mkdir(parents=True, exist_ok=True)
                (path / "main.py").write_text('''
from fastapi import FastAPI
password = "secret123"  # Bad!

app = FastAPI()

@app.get("/")
def home():
    return {"hello": "world"}
''')
                return ["main.py"]
        
        # Test compliance wrapper
        wrapper = SOC2ComplianceWrapper(MockGenerator())
        result = await wrapper.generate_with_compliance(
            project_path=Path("/tmp/test_compliance_project"),
            project_spec={"idea": "Test app"},
            project_name="test_project",
            tech_stack=["python", "fastapi"]
        )
        
        print(f"\n✅ Test completed!")
        print(f"   Score: {result.compliance_score:.1f}%")
        print(f"   Level: {result.compliance_level}")
        print(f"   Files fixed: {result.files_fixed}")
        print(f"   Report: {result.audit_report_path}")
    
    asyncio.run(test_wrapper())
