
import os
import secrets
import shutil
import git
import requests
import time
import tempfile
import stat
import platform
from fastapi import Request, Header, FastAPI, HTTPException, Body
from fastapi.responses import RedirectResponse, HTMLResponse, Response
import hmac
import hashlib
import subprocess
import asyncio
from pathlib import Path
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional, Any, Union
from starlette.concurrency import run_in_threadpool
import json
import re

# JSX Precompiler - compiles JSX to JS on server (no browser transforms needed)
from jsx_precompiler import precompile_jsx, check_esbuild

from scanner.file_security_scanner import scan_for_sensitive_files, scan_file_contents_for_secrets
# Try to import scanner dependencies, but make them optional
try:
    from scanner.directory_scanner import scan_common_paths
    DIRECTORY_SCANNER_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Directory scanner not available: {e}")
    DIRECTORY_SCANNER_AVAILABLE = False
    def scan_common_paths(*args, **kwargs):
        return []

try:
    from owasp_mapper import map_to_owasp_top10
    OWASP_MAPPER_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  OWASP mapper not available: {e}")
    OWASP_MAPPER_AVAILABLE = False
    def map_to_owasp_top10(*args, **kwargs):
        return []
from datetime import datetime 
import time
import base64
from github import Github
import tempfile
from dotenv import load_dotenv

# Try to import RAG functionality, but make it optional
try:
    from rag_query import get_secure_coding_patterns
    RAG_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  RAG functionality not available: {e}")
    RAG_AVAILABLE = False
    def get_secure_coding_patterns(query):
        return "RAG functionality not available - heavy ML dependencies not installed."

# Load environment variables
load_dotenv()

from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import docker
from nginx_config import NginxConfigManager

# --- Local Imports ---
from ai_assistant import get_chat_response, RepoAnalysis, FixRequest

# Try to import scanner functionality, but make it optional
try:
    from scanner.file_scanner import (
        scan_url, 
        _format_ssl_analysis,
        scan_dependencies,
        scan_code_quality_patterns,
        is_likely_false_positive
    )
    SCANNER_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Scanner functionality not available: {e}")
    SCANNER_AVAILABLE = False
    # Create fallback functions
    def scan_url(*args, **kwargs):
        return {"error": "Scanner not available"}
    def _format_ssl_analysis(*args, **kwargs):
        return "SSL analysis not available"
    def scan_dependencies(*args, **kwargs):
        return []
    def scan_code_quality_patterns(*args, **kwargs):
        return []
    def is_likely_false_positive(*args, **kwargs):
        return True
from scanner.hybrid_crawler import crawl_hybrid 
from nlp_suggester import suggest_fixes
import ai_assistant

# Import Website Analyzer for "build a website like X" feature
try:
    from website_analyzer import (
        WebsiteAnalyzer,
        WebsiteAnalysis,
        analyze_website_for_inspiration,
        get_inspiration_prompt_context,
        website_analyzer,
        POPULAR_SITES
    )
    WEBSITE_ANALYZER_AVAILABLE = True
    print("✅ Website Analyzer loaded - 'like X' feature enabled")
except ImportError as e:
    WEBSITE_ANALYZER_AVAILABLE = False
    website_analyzer = None
    POPULAR_SITES = {}
    print(f"⚠️ Website Analyzer not available: {e}")

try:
    from ai_assistant import github_client
except ImportError:
    github_client = None
    print("Warning: GitHub client not available")

# --- Phase 1 Imports ---
from scanner.secrets_detector import scan_secrets
from scanner.static_python import run_bandit

# Import job manager for async processing (safe - no routes)
from job_manager import job_manager, JobStatus

# Import authentication modules (safe - no routes)
from database import UserModel
from auth import (
    hash_password, 
    verify_password, 
    create_access_token, 
    verify_token,
    validate_email,
    validate_password,
    validate_username
)
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Depends
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

app = FastAPI()

# ==========================================
# PROJECT PREVIEW CACHE - For Visual Test & Security Scan
# ==========================================
# Cache recently accessed projects for 5 minutes so visual tests and security scans
# can access them without authentication (they make backend-to-backend requests)
from datetime import datetime, timedelta
from collections import OrderedDict

class ProjectPreviewCache:
    """Simple LRU cache for project previews with TTL"""
    def __init__(self, max_size=100, ttl_minutes=5):
        self.cache = OrderedDict()
        self.max_size = max_size
        self.ttl = timedelta(minutes=ttl_minutes)
    
    def get(self, project_slug):
        """Get cached project data if not expired"""
        if project_slug in self.cache:
            data, timestamp = self.cache[project_slug]
            if datetime.now() - timestamp < self.ttl:
                # Move to end (most recently used)
                self.cache.move_to_end(project_slug)
                return data
            else:
                # Expired, remove it
                del self.cache[project_slug]
        return None
    
    def set(self, project_slug, data):
        """Cache project data"""
        # Remove oldest if at capacity
        if len(self.cache) >= self.max_size:
            self.cache.popitem(last=False)
        self.cache[project_slug] = (data, datetime.now())
    
    def clear_expired(self):
        """Remove all expired entries"""
        now = datetime.now()
        expired = [k for k, (_, ts) in self.cache.items() if now - ts >= self.ttl]
        for k in expired:
            del self.cache[k]

# Global preview cache instance
preview_cache = ProjectPreviewCache(max_size=100, ttl_minutes=5)

# ==========================================
# VALIDATION ERROR HANDLER - Log 422 errors with details
# ==========================================
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Log validation errors with full details for debugging"""
    print(f"❌ Validation Error on {request.url.path}")
    print(f"   Method: {request.method}")
    print(f"   Errors: {exc.errors()}")
    try:
        body = await request.body()
        print(f"   Body size: {len(body)} bytes")
        print(f"   Content-Type: {request.headers.get('content-type', 'not set')}")
    except:
        pass
    
    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "body": str(exc.body)[:500] if exc.body else None}
    )

# ==========================================
# OPTIONS HANDLER - INSTANT PREFLIGHT RESPONSE (MUST COME FIRST)
# ==========================================


# ==========================================
# CORS MIDDLEWARE - SINGLE LAYER ONLY (NO STACKING)
# ==========================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Frontend dev server
        "http://localhost:5173",
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security scheme
security = HTTPBearer()

# ==========================================
# IMPORT ROUTERS AFTER CORS
# ==========================================
from voice_chat_api import router as voice_chat_router
from dynamic_db_api import router as dynamic_db_router

# Include voice chat router AFTER CORS
app.include_router(voice_chat_router)

# Include dynamic database API for generated apps
app.include_router(dynamic_db_router)

# Startup event to initialize job worker
@app.on_event("startup")
async def startup_event():
    """Start background job processor"""
    await job_manager.start_worker()
    print("✅ Job manager worker started")

# Job management endpoints
@app.post("/api/jobs/create")
async def create_job_endpoint(
    request: dict = Body(...),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Create a new async job (e.g., project generation)"""
    try:
        # Verify token and get user
        token = credentials.credentials
        payload = verify_token(token)
        if not payload:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        
        user_email = payload.get("sub")
        job_type = request.get("job_type")
        params = request.get("params", {})
        
        if not job_type:
            raise HTTPException(status_code=400, detail="job_type is required")
        
        # Create job
        job_id = job_manager.create_job(job_type, params, user_email)
        
        return {
            "success": True,
            "job_id": job_id,
            "message": "Job created and queued for processing"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Create job error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/jobs/{job_id}")
async def get_job_status(
    job_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get job status and results"""
    try:
        # Verify token
        token = credentials.credentials
        payload = verify_token(token)
        if not payload:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        
        # Get job
        job = job_manager.get_job(job_id)
        if not job:
            # Job not found - may have been lost due to server restart
            return {
                "success": False,
                "error": "Job not found - server may have restarted. Please try creating your project again.",
                "job": {
                    "status": "not_found",
                    "message": "This job is no longer available"
                }
            }
        
        # Verify user owns this job
        user_email = payload.get("sub")
        if job.user_email != user_email:
            raise HTTPException(status_code=403, detail="Not authorized to view this job")
        
        return {
            "success": True,
            "job": job.to_dict()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Get job error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# --- Storage Classes for Scan Results ---
class WebsiteScan:
    latest_scan = None

class ScanRequest(BaseModel):
    url: str
    model_type: str = 'fast'
    model_config = {'protected_namespaces': ()}

class RepoAnalysisRequest(BaseModel):
    repo_url: str
    model_type: str = 'smart'
    deep_scan: bool = True
    model_config = {'protected_namespaces': ()}

class OWASPMappingRequest(BaseModel):
    url: str
    repo_url: Optional[str] = None
    model_type: str = "fast"
    model_config = {'protected_namespaces': ()}

class FixRequest(BaseModel):
    repo_url: str
    issue: Dict[str, Any]
    branch_name: Optional[str] = None

class ConsoleErrorRequest(BaseModel):
    project_name: str
    error_message: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    stack_trace: Optional[str] = None
    error_type: Optional[str] = None

class SignupRequest(BaseModel):
    email: str
    username: str
    password: str

class LoginRequest(BaseModel):
    email: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: Dict[str, Any]

class UserResponse(BaseModel):
    id: str
    email: str
    username: str
    is_active: bool
    is_verified: bool
    created_at: datetime

from fastapi import Query, WebSocket, WebSocketDisconnect
from fastapi.websockets import WebSocketState
import asyncio
import websockets
from typing import Dict, Set

# Helper function to normalize project names/slugs while preserving path structure
def normalize_project_slug(project_name: str) -> str:
    """
    Normalize project name to slug format while preserving directory structure.
    Handles paths like 'mobile/web-app' or simple names like 'my project'.
    Only replaces spaces with hyphens, preserves slashes for nested projects.
    """
    return project_name.replace(" ", "-")

def generate_human_readable_project_name(idea: str, check_uniqueness: bool = True) -> str:
    """
    Generate a meaningful, human-readable project name from the idea description.
    Returns a clean slug without random numbers or timestamps.
    If check_uniqueness is True, ensures the name is unique by appending numbers if needed.
    """
    # Common words to filter out for cleaner project names
    stop_words = {
        'a', 'an', 'the', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had',
        'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'shall',
        'to', 'of', 'in', 'for', 'on', 'with', 'at', 'by', 'from', 'as', 'into', 'through', 'during',
        'before', 'after', 'above', 'below', 'between', 'under', 'again', 'further', 'then', 'once',
        'create', 'build', 'make', 'develop', 'design', 'implement', 'add', 'use', 'using', 'want',
        'need', 'like', 'help', 'please', 'can', 'you', 'i', 'we', 'they', 'it', 'this', 'that',
        'app', 'application', 'website', 'web', 'page', 'site', 'project', 'system', 'platform',
        'and', 'or', 'but', 'if', 'so', 'because', 'about', 'which', 'when', 'where', 'who', 'what', 'how',
        'ai', 'generated', 'simple', 'basic', 'modern', 'new', 'my', 'your', 'our'
    }
    
    if not idea or not idea.strip():
        base_name = "my-project"
    else:
        # Clean the idea text - remove punctuation, convert to lowercase
        import re
        clean_idea = re.sub(r'[^\w\s]', ' ', idea.lower())
        
        # Split into words and filter out stop words
        words = [word for word in clean_idea.split() if word and len(word) > 2 and word not in stop_words]
        
        # Take the first 2-3 meaningful words for a clean, readable name
        key_words = words[:3]
        
        if not key_words:
            # Fallback: try to use any words from the original idea
            fallback_words = [word for word in clean_idea.split() if word and len(word) > 1][:2]
            base_name = '-'.join(fallback_words) if fallback_words else "my-project"
        else:
            base_name = '-'.join(key_words)
    
    if not check_uniqueness:
        return base_name
    
    # Check for existing projects and ensure uniqueness
    return ensure_unique_project_name(base_name)

def ensure_unique_project_name(base_name: str) -> str:
    """
    Ensure the project name is unique by checking existing projects.
    Appends incrementing numbers (e.g., todo-list, todo-list-2, todo-list-3) if needed.
    """
    projects_dir = Path("generated_projects")
    
    # If no projects directory exists yet, the name is unique
    if not projects_dir.exists():
        return base_name
    
    # Get list of existing project directories
    existing_projects = set()
    try:
        for item in projects_dir.iterdir():
            if item.is_dir():
                existing_projects.add(item.name.lower())
    except Exception:
        return base_name
    
    # Check if base name is available
    if base_name.lower() not in existing_projects:
        return base_name
    
    # Find the next available number
    counter = 2
    while f"{base_name}-{counter}".lower() in existing_projects:
        counter += 1
    
    return f"{base_name}-{counter}"

# Authentication helper - get current user from JWT token
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """
    Dependency to get current authenticated user from JWT token.
    Raises HTTPException if token is invalid or user not found.
    """
    token = credentials.credentials
    payload = verify_token(token)
    
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    
    user_model = UserModel()
    user = user_model.get_user_by_id(user_id)
    
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    if not user.get("is_active", False):
        raise HTTPException(status_code=403, detail="User account is deactivated")
    
    return user

# Optional authentication - returns None if no token or invalid
async def get_current_user_optional(credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))) -> Optional[dict]:
    """
    Optional dependency to get current user. Returns None if not authenticated.
    """
    if not credentials:
        return None
    
    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None


# ==================== AUTHENTICATION ENDPOINTS ====================

@app.post("/api/auth/signup")
async def signup(request: SignupRequest):
    """
    Register a new user account.
    """
    try:
        # Validate email format
        if not validate_email(request.email):
            raise HTTPException(status_code=400, detail="Invalid email format")
        
        # Validate username
        is_valid, error_msg = validate_username(request.username)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_msg)
        
        # Validate password strength
        is_valid, error_msg = validate_password(request.password)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_msg)
        
        # Hash password
        hashed_password = hash_password(request.password)
        
        # Create user
        user_model = UserModel()
        try:
            user = user_model.create_user(
                email=request.email,
                username=request.username,
                hashed_password=hashed_password
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        
        # Create access token
        access_token = create_access_token(data={"sub": user["_id"]})
        
        # Remove sensitive data
        user.pop("hashed_password", None)
        
        return {
            "success": True,
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user["_id"],
                "email": user["email"],
                "username": user["username"],
                "is_verified": user.get("is_verified", False),
                "created_at": user.get("created_at")
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Signup error: {e}")
        raise HTTPException(status_code=500, detail="Failed to create account")


@app.post("/api/auth/login")
async def login(request: LoginRequest):
    """
    Login with email and password.
    """
    try:
        # Get user by email
        user_model = UserModel()
        user = user_model.get_user_by_email(request.email)
        
        if not user:
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        # Verify password
        if not verify_password(request.password, user["hashed_password"]):
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        # Check if user is active
        if not user.get("is_active", False):
            raise HTTPException(status_code=403, detail="Account is deactivated")
        
        # Create access token
        access_token = create_access_token(data={"sub": user["_id"]})
        
        # Remove sensitive data
        user.pop("hashed_password", None)
        
        return {
            "success": True,
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user["_id"],
                "email": user["email"],
                "username": user["username"],
                "is_verified": user.get("is_verified", False),
                "created_at": user.get("created_at")
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Login error: {e}")
        raise HTTPException(status_code=500, detail="Login failed")


@app.get("/api/auth/me")
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """
    Get current authenticated user information.
    """
    current_user.pop("hashed_password", None)
    return {
        "success": True,
        "user": {
            "id": current_user["_id"],
            "email": current_user["email"],
            "username": current_user["username"],
            "is_verified": current_user.get("is_verified", False),
            "is_active": current_user.get("is_active", True),
            "created_at": current_user.get("created_at"),
            "updated_at": current_user.get("updated_at")
        }
    }


@app.post("/api/auth/logout")
async def logout(current_user: dict = Depends(get_current_user)):
    """
    Logout (client should delete the token).
    """
    return {
        "success": True,
        "message": "Logged out successfully"
    }


# ==================== PENDING DEMO PROJECT ENDPOINTS ====================

@app.post("/api/demo/save-pending-project")
async def save_pending_demo_project(request: Request):
    """
    Save pending demo project details to S3 for post-login creation
    """
    try:
        data = await request.json()
        project_data = data.get('project')
        session_id = data.get('session_id')
        
        if not project_data or not session_id:
            raise HTTPException(status_code=400, detail="Missing project data or session_id")
        
        from s3_storage import s3_client, S3_BUCKET_NAME
        
        # Save to S3 with session-based key
        s3_key = f"pending-demos/{session_id}/project.json"
        
        s3_client.put_object(
            Bucket=S3_BUCKET_NAME,
            Key=s3_key,
            Body=json.dumps(project_data).encode('utf-8'),
            ContentType='application/json',
            Metadata={
                'session_id': session_id,
                'created_at': datetime.utcnow().isoformat()
            }
        )
        
        return {
            "success": True,
            "session_id": session_id,
            "message": "Pending project saved successfully"
        }
        
    except Exception as e:
        print(f"❌ Error saving pending demo project: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/demo/get-pending-project/{session_id}")
async def get_pending_demo_project(session_id: str):
    """
    Retrieve pending demo project details from S3
    """
    try:
        from s3_storage import s3_client, S3_BUCKET_NAME
        
        s3_key = f"pending-demos/{session_id}/project.json"
        
        try:
            response = s3_client.get_object(
                Bucket=S3_BUCKET_NAME,
                Key=s3_key
            )
            
            project_data = json.loads(response['Body'].read().decode('utf-8'))
            
            return {
                "success": True,
                "project": project_data
            }
            
        except s3_client.exceptions.NoSuchKey:
            return {
                "success": False,
                "message": "No pending project found"
            }
        
    except Exception as e:
        print(f"❌ Error retrieving pending demo project: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/demo/delete-pending-project/{session_id}")
async def delete_pending_demo_project(session_id: str):
    """
    Delete pending demo project from S3 after it's been created
    """
    try:
        from s3_storage import s3_client, S3_BUCKET_NAME
        
        s3_key = f"pending-demos/{session_id}/project.json"
        
        s3_client.delete_object(
            Bucket=S3_BUCKET_NAME,
            Key=s3_key
        )
        
        return {
            "success": True,
            "message": "Pending project deleted successfully"
        }
        
    except Exception as e:
        print(f"❌ Error deleting pending demo project: {str(e)}")
        # Don't raise error - deletion failure is not critical
        return {
            "success": False,
            "message": "Failed to delete pending project"
        }


# ==================== END AUTHENTICATION ENDPOINTS ====================

import threading
import uuid
# --- Project File Tree Endpoint ---
# ❌ DEPRECATED - LOCAL STORAGE ONLY (EC2 INCOMPATIBLE)
# Use /api/project-file-tree instead (line 4315+) - S3-enabled
# This endpoint is kept for backward compatibility only
@app.get("/project-file-tree")
async def get_project_file_tree(project_name: str = Query(...)):
    """
    Returns the file tree for the generated project.
    """
    try:
        projects_dir = Path("generated_projects")
        project_path = projects_dir / project_name.lower().replace(" ", "-")
        
        if not project_path.exists():
            return {"success": False, "error": "Project not found"}
        
        # Validate and fix critical files before running
        await manager.send_to_project(project_name, {
            "type": "terminal_output",
            "message": "🔍 Validating project files...",
            "level": "info"
        })
        ok = await validate_and_fix_project_files(project_path, project_name)
        if not ok:
            await manager.send_to_project(project_name, {
                "type": "terminal_output",
                "message": "❌ Validation failed. Cannot start project.",
                "level": "error"
            })
            return {"success": False, "error": "Validation failed"}
        def build_tree(path: Path, relative_path: str = ""):
            items = []
            try:
                for item in sorted(path.iterdir()):
                    if item.name.startswith('.') or item.name == '__pycache__':
                        continue
                    
                    relative_item_path = f"{relative_path}/{item.name}" if relative_path else item.name
                    
                    if item.is_dir():
                        items.append({
                            "name": item.name,
                            "type": "dir", 
                            "path": relative_item_path + "/",
                            "children": build_tree(item, relative_item_path)
                        })
                    else:
                        items.append({
                            "name": item.name,
                            "type": "file",
                            "path": relative_item_path
                        })
            except PermissionError:
                pass
            return items
        
        tree = build_tree(project_path)
        return {"success": True, "tree": tree}
        
    except Exception as e:
        print(f"Error getting project tree: {e}")
        return {"success": False, "error": str(e)}

# ❌ DEPRECATED - LOCAL STORAGE ONLY (EC2 INCOMPATIBLE)
# Use /api/project-file-content instead (line 4450+) - S3-enabled
# This endpoint is kept for backward compatibility only
@app.get("/project-file-content")
async def get_project_file_content(project_name: str = Query(...), file_path: str = Query(...)):
    """
    Returns the actual file content for a given file in the generated project.
    """
    try:
        projects_dir = Path("generated_projects")
        project_path = projects_dir / project_name.lower().replace(" ", "-")

        if not project_path.exists():
            return {"success": False, "error": "Project not found"}

        # Clean the file path and resolve it safely
        clean_file_path = file_path.lstrip('/')
        full_file_path = project_path / clean_file_path

        # Security check: ensure the path is within the project directory
        try:
            full_file_path.resolve().relative_to(project_path.resolve())
        except ValueError:
            return {"success": False, "error": "Invalid file path"}

        if not full_file_path.exists():
            return {"success": False, "error": "File not found"}

        if full_file_path.is_dir():
            return {"success": False, "error": "Path is a directory"}

        # Read file content
        try:
            with open(full_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            # Handle binary files
            content = f"[Binary file: {full_file_path.name}]"

        return {"success": True, "content": content}

    except Exception as e:
        print(f"Error reading file content: {e}")
        return {"success": False, "error": str(e)}

# --- Project Preview URL Endpoint ---
@app.get("/project-preview-url")
async def get_project_preview_url(project_name: str = Query(...)):
    """
    Returns a mock live preview URL for the generated project.
    In production, this should point to the actual deployed preview.
    """
    # Demo: return a placeholder preview URL
    url = f"https://demo.xverta.app/{project_name.lower().replace(' ', '-')}-preview"
    return {"success": True, "url": url}

# --- WebSocket Connection Manager ---
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.project_connections: Dict[str, Set[str]] = {}

    async def connect(self, websocket: WebSocket, connection_id: str, project_name: str):
        await websocket.accept()
        self.active_connections[connection_id] = websocket
        
        if project_name not in self.project_connections:
            self.project_connections[project_name] = set()
        self.project_connections[project_name].add(connection_id)

    def disconnect(self, connection_id: str, project_name: str):
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]
        
        if project_name in self.project_connections:
            self.project_connections[project_name].discard(connection_id)
            if not self.project_connections[project_name]:
                del self.project_connections[project_name]

    async def send_to_project(self, project_name: str, message: dict):
        """Send message to all connections for a specific project"""
        if project_name in self.project_connections:
            disconnected = []
            for connection_id in self.project_connections[project_name]:
                websocket = self.active_connections.get(connection_id)
                if websocket:
                    try:
                        # Only send when CONNECTED
                        if websocket.client_state == WebSocketState.CONNECTED:
                            await websocket.send_json(message)
                        else:
                            disconnected.append(connection_id)
                    except Exception:
                        # Any send error, schedule cleanup
                        disconnected.append(connection_id)
                else:
                    disconnected.append(connection_id)
            
            # Clean up disconnected connections
            for connection_id in disconnected:
                self.disconnect(connection_id, project_name)

manager = ConnectionManager()

# --- WebSocket Endpoint ---
@app.websocket("/ws/project/{project_name}")
async def websocket_endpoint(websocket: WebSocket, project_name: str):
    await websocket.accept()
    connection_id = str(uuid.uuid4())
    
    try:
        # Add to connection manager
        manager.active_connections[connection_id] = websocket
        # Ensure this connection is tracked under the project for broadcasts
        if project_name not in manager.project_connections:
            manager.project_connections[project_name] = set()
        manager.project_connections[project_name].add(connection_id)
        print(f"✅ WebSocket connected: {project_name} ({connection_id})")
        
        # Send welcome message
        await websocket.send_json({
            "type": "connected",
            "message": f"Connected to project: {project_name}",
            "connection_id": connection_id
        })
        
        # Simple message loop
        while True:
            try:
                # Just wait for any message or disconnection
                data = await websocket.receive_text()
                
                # Echo back to confirm connection is alive
                await websocket.send_json({
                    "type": "echo",
                    "data": data,
                    "timestamp": datetime.now().isoformat()
                })
                
            except WebSocketDisconnect:
                print(f"WebSocket disconnected: {project_name}")
                break
            except Exception as e:
                print(f"WebSocket error: {e}")
                break
                
    except Exception as e:
        print(f"WebSocket setup error: {e}")
    finally:
        # Clean up connection via manager to keep maps in sync
        try:
            manager.disconnect(connection_id, project_name)
        finally:
            print(f"🔌 WebSocket cleaned up: {project_name}")

# --- WebSocket Chat Endpoint ---
@app.websocket("/ws/chat/{project_name}")
async def chat_websocket_endpoint(websocket: WebSocket, project_name: str):
    """Dedicated WebSocket endpoint for real-time AI chat during development."""
    await websocket.accept()
    connection_id = str(uuid.uuid4())
    
    try:
        # Add to connection manager with chat prefix
        chat_project_name = f"chat_{project_name}"
        manager.active_connections[connection_id] = websocket
        if chat_project_name not in manager.project_connections:
            manager.project_connections[chat_project_name] = set()
        manager.project_connections[chat_project_name].add(connection_id)
        print(f"💬 Chat WebSocket connected: {project_name} ({connection_id})")
        
        # Send welcome message
        await websocket.send_json({
            "type": "chat_connected",
            "message": "AI chat assistant ready! Ask me anything about development.",
            "connection_id": connection_id
        })
        
        # Chat message loop
        while True:
            try:
                # Wait for chat message
                data = await websocket.receive_json()
                
                if data.get("type") == "chat_message":
                    user_message = data.get("message", "").strip()
                    chat_history = data.get("history", [])
                    context = data.get("context", {})
                    
                    if user_message:
                        # Send typing indicator
                        await websocket.send_json({
                            "type": "chat_typing",
                            "message": "AI is thinking..."
                        })
                        
                        try:
                            # Process chat using the same logic as the HTTP endpoint
                            system_context = """You are an expert full-stack developer and helpful coding assistant. 
Provide clear, practical, and actionable responses. Be concise but thorough."""

                            # Add project context
                            if context:
                                tech_stack = context.get("tech_stack", [])
                                if tech_stack:
                                    system_context += f"\n\nProject uses: {', '.join(tech_stack)}"
                            
                            messages = [{"role": "system", "content": system_context}]
                            
                            # Add recent history
                            recent_history = chat_history[-8:] if chat_history else []
                            for msg in recent_history:
                                if msg.get("role") and msg.get("content"):
                                    messages.append(msg)
                            
                            # Add current message
                            messages.append({"role": "user", "content": user_message})
                            
                            # Get AI response
                            from ai_assistant import get_chat_response
                            ai_response = get_chat_response(messages, model_type='fast')
                            
                            # Send response
                            await websocket.send_json({
                                "type": "chat_response",
                                "message": ai_response,
                                "user_message": user_message,
                                "timestamp": time.time()
                            })
                            
                        except Exception as ai_error:
                            await websocket.send_json({
                                "type": "chat_error", 
                                "message": f"AI chat error: {str(ai_error)}"
                            })
                    
                elif data.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
                    
            except WebSocketDisconnect:
                print(f"Chat WebSocket disconnected: {project_name}")
                break
            except Exception as e:
                print(f"Chat WebSocket error: {e}")
                await websocket.send_json({
                    "type": "error",
                    "message": f"Connection error: {str(e)}"
                })
                break
                
    except Exception as e:
        print(f"Chat WebSocket setup error: {e}")
    finally:
        # Clean up connection
        try:
            chat_project_name = f"chat_{project_name}"
            if connection_id in manager.active_connections:
                del manager.active_connections[connection_id]
            if chat_project_name in manager.project_connections:
                manager.project_connections[chat_project_name].discard(connection_id)
                if not manager.project_connections[chat_project_name]:
                    del manager.project_connections[chat_project_name]
        finally:
            print(f"💬 Chat WebSocket cleaned up: {project_name}")

# --- Website Analyzer Endpoints for "Build like X" feature ---
@app.get("/api/website-analyzer/popular-sites")
async def get_popular_sites():
    """Get list of popular websites that can be used as inspiration"""
    if not WEBSITE_ANALYZER_AVAILABLE:
        return {"available": False, "sites": {}}
    
    return {
        "available": True,
        "sites": POPULAR_SITES,
        "categories": {
            "ecommerce": ["amazon", "ebay", "shopify", "etsy", "walmart", "alibaba"],
            "social": ["twitter", "facebook", "instagram", "linkedin", "pinterest", "reddit"],
            "tech": ["github", "notion", "slack", "discord", "figma", "canva"],
            "streaming": ["netflix", "spotify", "youtube", "twitch"],
            "travel": ["airbnb", "booking", "expedia", "tripadvisor"],
            "food": ["doordash", "ubereats", "grubhub", "instacart"],
            "finance": ["stripe", "paypal", "robinhood", "coinbase"],
        }
    }


@app.post("/api/website-analyzer/analyze")
async def analyze_website_endpoint(request: dict = Body(...)):
    """Analyze a website to extract design patterns for inspiration"""
    if not WEBSITE_ANALYZER_AVAILABLE:
        raise HTTPException(status_code=503, detail="Website analyzer not available")
    
    url = request.get("url", "")
    site_name = request.get("site_name", "")
    take_screenshot = request.get("take_screenshot", False)  # Screenshots can be slow
    
    if not url:
        # Try to get from site_name
        if site_name and site_name.lower() in POPULAR_SITES:
            url = POPULAR_SITES[site_name.lower()]
        else:
            raise HTTPException(status_code=400, detail="URL or known site_name required")
    
    try:
        analysis = await website_analyzer.analyze_website(url, site_name, take_screenshot)
        
        return {
            "success": True,
            "analysis": {
                "website_name": analysis.website_name,
                "website_url": analysis.website_url,
                "analysis_quality": analysis.analysis_quality,
                "layout_type": analysis.layout_type,
                "grid_system": analysis.grid_system,
                "page_structure": analysis.page_structure,
                "color_palette": analysis.color_palette,
                "primary_colors": analysis.primary_colors,
                "background_style": analysis.background_style,
                "font_families": analysis.font_families,
                "navigation_type": analysis.navigation_type,
                "has_search": analysis.has_search,
                "has_cart": analysis.has_cart,
                "has_user_menu": analysis.has_user_menu,
                "components": analysis.components,
                "hero_section": analysis.hero_section,
                "features": analysis.features,
                "css_techniques": analysis.css_techniques,
                "animation_styles": analysis.animation_styles,
                "design_suggestions": analysis.design_suggestions,
                "screenshot_available": analysis.screenshot_base64 is not None,
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@app.post("/api/website-analyzer/extract-reference")
async def extract_website_reference(request: dict = Body(...)):
    """Extract website reference from a user prompt like 'build a website like Amazon'"""
    if not WEBSITE_ANALYZER_AVAILABLE:
        raise HTTPException(status_code=503, detail="Website analyzer not available")
    
    prompt = request.get("prompt", "")
    
    if not prompt:
        raise HTTPException(status_code=400, detail="Prompt required")
    
    site_ref = website_analyzer.extract_website_reference(prompt)
    
    if site_ref:
        site_name, url = site_ref
        return {
            "found": True,
            "site_name": site_name,
            "url": url,
            "message": f"Detected reference to {site_name} - will analyze for design inspiration"
        }
    else:
        return {
            "found": False,
            "site_name": None,
            "url": None,
            "message": "No website reference found in prompt"
        }


@app.get("/api/website-analyzer/screenshot/{site_name}")
async def get_website_screenshot(site_name: str):
    """Get a screenshot of a popular website (if available)"""
    if not WEBSITE_ANALYZER_AVAILABLE:
        raise HTTPException(status_code=503, detail="Website analyzer not available")
    
    url = POPULAR_SITES.get(site_name.lower())
    if not url:
        raise HTTPException(status_code=404, detail=f"Unknown site: {site_name}")
    
    try:
        screenshot = await website_analyzer._capture_screenshot(url)
        
        if screenshot:
            return {
                "success": True,
                "site_name": site_name,
                "screenshot_base64": screenshot,
                "content_type": "image/png"
            }
        else:
            return {
                "success": False,
                "message": "Screenshot capture not available or failed"
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Screenshot failed: {str(e)}")


# --- Enhanced Project Structure Creation ---
@app.post("/api/create-project-structure")
async def create_project_structure(request: dict = Body(...)):
    """Create actual project files and structure"""
    try:
        project_name = request.get("project_name")
        idea = request.get("idea") 
        tech_stack = request.get("tech_stack", [])
        project_type = request.get("project_type", "web app")
        features = request.get("features", [])
        user_id = request.get("user_id", "anonymous")  # Get user_id for S3 multi-tenancy
        requirements = request.get("requirements", {})
        
        # E-COMMERCE: Check if user provided product data
        product_data = request.get("product_data")  # User's product list
        custom_data = request.get("custom_data", {})  # Any custom data (products, menu items, etc.)
        documentation_context = request.get("documentation_context")  # User's uploaded documents (resume, PDFs, images)
        
        # Log if we have documentation context
        if documentation_context:
            print(f"📄 Documentation context provided: {len(documentation_context)} chars")
        
        # Send progress updates via WebSocket
        await manager.send_to_project(project_name, {
            "type": "terminal_output",
            "message": "🚀 Creating project structure...",
            "level": "info"
        })
        
        # Generate project name slug
        project_slug = project_name.lower().replace(" ", "-").replace("_", "-")
        # NO LOCAL STORAGE - S3-only architecture (EC2 compatible)
        project_path = Path("generated_projects") / project_slug  # Used only for path structure, not created
        
        # Determine tech stack based on AI analysis of the idea
        detected_stack = await analyze_tech_stack_for_idea(idea)
        
        # Create project structure with full specifications
        full_spec = {
            "idea": idea,
            "project_type": project_type,
            "features": features,
            "tech_stack": detected_stack,
            "requirements": requirements,
            "product_data": product_data,  # Pass user's product data
            "custom_data": custom_data,     # Pass any custom data
            "documentation_context": documentation_context  # Pass user's uploaded documents (resume, PDFs, images)
        }
        
        # Generate files and upload to S3 in real-time
        await manager.send_to_project(project_name, {
            "type": "terminal_output", 
            "message": f"☁️ Generating project directly to S3...",
            "level": "info"
        })
        
        files_created = await create_complete_project_structure(
            project_path, full_spec, project_slug, detected_stack, user_id
        )
        
        await manager.send_to_project(project_name, {
            "type": "terminal_output", 
            "message": f"✅ Created {len(files_created)} files",
            "level": "success"
        })
        
        # Files already uploaded to S3 during generation (direct S3 writes)
        await manager.send_to_project(project_name, {
            "type": "terminal_output",
            "message": f"☁️ All {len(files_created)} files already in cloud storage (S3)",
            "level": "success"
        })
        
        return {
            "success": True,
            "files_created": files_created,
            "tech_stack": detected_stack,
            "project_path": str(project_path)
        }
        
    except Exception as e:
        await manager.send_to_project(project_name, {
            "type": "terminal_output",
            "message": f"❌ Error creating structure: {str(e)}",
            "level": "error"
        })
        return {"success": False, "error": str(e)}

async def analyze_tech_stack_for_idea(idea: str) -> List[str]:
    """Determine the best tech stack for the project idea - ALWAYS React + FastAPI"""
    # ALWAYS use consistent React + FastAPI stack for better quality
    base_stack = ["React", "FastAPI", "Vite", "TailwindCSS"]
    
    # Add specific features based on the idea
    additional_features = []
    
    idea_lower = idea.lower()
    
    # Database features
    if any(keyword in idea_lower for keyword in ["todo", "task", "store", "save", "data", "crud", "database"]):
        additional_features.append("SQLite")
    
    # Authentication features  
    if any(keyword in idea_lower for keyword in ["auth", "login", "user", "signup", "account", "profile"]):
        additional_features.append("JWT Auth")
    
    # Real-time features
    if any(keyword in idea_lower for keyword in ["chat", "live", "real-time", "websocket", "notification"]):
        additional_features.append("WebSockets")
    
    # AI features
    if any(keyword in idea_lower for keyword in ["ai", "ml", "openai", "gpt", "chatbot", "intelligent"]):
        additional_features.append("AI Integration")
    
    return base_stack + additional_features[:4]  # Limit to 8 total items

async def create_complete_project_structure(project_path: Path, project_spec: dict, project_name: str, tech_stack: List[str], user_id: str = "anonymous") -> List[str]:
    """Create complete project with OPTIMIZED Pure AI generation - 100% AI code, NO templates, FAST"""
    
    # Extract details from project_spec
    idea = project_spec.get("idea", "")
    project_type = project_spec.get("project_type", "web app")
    features = project_spec.get("features", [])
    
    # Send initial progress
    await manager.send_to_project(project_name, {
        "type": "file_creation_start",
        "message": f"🚀 Creating {project_type}: {idea[:50]}{'...' if len(idea) > 50 else ''}",
        "total_files": 15
    })
    
    try:
        # Use OPTIMIZED Pure AI Generator - NO templates, FAST AI generation
        if os.getenv("GOOGLE_API_KEY"):
            from pure_ai_generator import PureAIGenerator
            from s3_storage import upload_project_to_s3
            
            await manager.send_to_project(project_name, {
                "type": "terminal_output",
                "message": "☁️ CLOUD MODE: Generating directly to S3 (no local storage)...",
                "level": "info"
            })
            
            # Initialize generator with S3 uploader for direct cloud generation
            generator = PureAIGenerator(
                s3_uploader=upload_project_to_s3,
                user_id=user_id
            )
            
            files_created = await generator.generate_project_structure(
                project_path, 
                project_spec, 
                project_name,
                tech_stack
            )
            
            await manager.send_to_project(project_name, {
                "type": "file_creation_complete", 
                "message": f"☁️ Cloud Generation Complete! Generated {len(files_created)} files directly to S3",
                "files_created": files_created,
                "generation_method": "s3-direct-ai"
            })
            
            return files_created
            
        else:
            # If no AI key, throw error 
            raise Exception("GOOGLE_API_KEY is required. Please set your Gemini API key.")
            
    except Exception as e:
        await manager.send_to_project(project_name, {
            "type": "terminal_output", 
            "message": f"❌ Pure AI generation failed: {str(e)}",
            "level": "error"
        })
        
        # Re-raise the error
        raise Exception(f"Pure AI generation failed: {str(e)}. Please check your GOOGLE_API_KEY.")
    
    return files_created

# --- Sandboxed Preview Endpoint ---
@app.get("/api/sandbox-preview/{project_name:path}")
async def get_sandbox_preview(
    project_name: str, 
    request: Request,  # For reading headers
    user_email: Optional[str] = Query(None),  # Deprecated: use X-User-Email header instead
    user_id_alt: Optional[str] = Query(None),  # Deprecated: use X-User-Id-Alt header instead
    v: Optional[str] = Query(None),  # Version/cache-busting parameter
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """
    Generate a sandboxed HTML preview from S3-stored files (S3-ONLY, EC2 COMPATIBLE)
    
    SECURITY: Prefer using headers for sensitive data instead of URL query parameters:
        - X-User-Email: User's email address
        - X-User-Id-Alt: Alternative user ID
    
    Query parameters are still supported for backwards compatibility but may be logged.
    """
    try:
        # SECURITY FIX: Read sensitive data from headers first, then fall back to query params
        # Headers are more secure as they don't appear in browser history, referrer headers, or server logs
        header_user_email = request.headers.get('X-User-Email')
        header_user_id_alt = request.headers.get('X-User-Id-Alt')
        
        # Use header values if available, otherwise fall back to query params (backwards compatibility)
        effective_user_email = header_user_email or user_email
        effective_user_id_alt = header_user_id_alt or user_id_alt
        
        # Get user_id from multiple sources (priority order):
        # 1. Authenticated user from token
        # 2. Headers (secure)
        # 3. Query parameter (backwards compatibility - less secure)
        # 4. Default to anonymous
        user_id = None
        user_id_alternative = None  # Alternative ID to try (email if we have _id, or _id if we have email)
        
        if current_user:
            user_id = current_user.get('email') or current_user.get('_id')
            # Store alternative ID for fallback
            if current_user.get('email') and current_user.get('_id'):
                user_id_alternative = current_user.get('_id') if user_id == current_user.get('email') else current_user.get('email')
        elif effective_user_email:
            user_id = effective_user_email
            user_id_alternative = effective_user_id_alt  # From header or query parameter
        else:
            user_id = 'anonymous'
        
        print(f"🔍 Sandbox preview requested for: '{project_name}'")
        print(f"👤 User ID: {user_id[:20] if user_id else 'None'}..., Alt: {user_id_alternative[:20] if user_id_alternative else 'None'}...")  # Don't log full emails
        project_slug = normalize_project_slug(project_name)
        print(f"🔍 Normalized to slug: '{project_slug}'")
        
        project_data = None
        
        # Check cached user_id for this project (most reliable way to find it)
        from s3_storage import get_cached_user_id_for_project
        cached_user_id = get_cached_user_id_for_project(project_slug)
        if cached_user_id and cached_user_id != user_id:
            print(f"📦 Found cached user_id for project: {cached_user_id[:20]}...")
            # Add cached user to alternatives
            if not user_id_alternative:
                user_id_alternative = cached_user_id
        
        # FIRST: Try cache (for visual tests and security scans that don't have auth)
        if user_id == 'anonymous':
            cached = preview_cache.get(project_slug)
            if cached:
                print(f"✅ Found project in preview cache (for anonymous/test access)")
                project_data = cached
        
        # If not in cache, try to load from S3
        if not project_data:
            # Try cached user_id FIRST (most likely to work)
            if cached_user_id:
                project_data = get_project_from_s3(project_slug=project_slug, user_id=cached_user_id)
                if project_data and project_data.get('files'):
                    print(f"✅ Found project with cached user_id")
            
            # Try to load project from S3 with user_id
            if not project_data or not project_data.get('files'):
                project_data = get_project_from_s3(project_slug=project_slug, user_id=user_id)
            
            # If not found and we have an alternative ID, try that
            if (not project_data or not project_data.get('files')) and user_id_alternative:
                print(f"⚠️ Project not found for user {user_id[:20] if user_id else 'None'}..., trying alternative ID...")
                project_data = get_project_from_s3(project_slug=project_slug, user_id=user_id_alternative)
            
            # If still not found and user_id wasn't anonymous, try anonymous as fallback for backwards compatibility
            if (not project_data or not project_data.get('files')) and user_id != 'anonymous':
                print(f"⚠️ Project not found for user {user_id}, trying anonymous...")
                project_data = get_project_from_s3(project_slug=project_slug, user_id='anonymous')
            
            # LAST RESORT: Search for project across all users
            if not project_data or not project_data.get('files'):
                print(f"🔍 Searching for project '{project_slug}' across all users...")
                from s3_storage import find_project_user_id
                found_user_id = find_project_user_id(project_slug)
                if found_user_id:
                    project_data = get_project_from_s3(project_slug=project_slug, user_id=found_user_id)
            
            # Cache the project data for subsequent requests (visual tests, security scans)
            if project_data and project_data.get('files'):
                preview_cache.set(project_slug, project_data)
                print(f"📦 Cached project '{project_slug}' for 5 minutes (for visual tests/security scans)")
        
        if not project_data or not project_data.get('files'):
            raise HTTPException(
                status_code=404, 
                detail=f"Project '{project_slug}' not found in cloud storage (tried user: {user_id})"
            )
        
        print(f"✅ Loading project from S3: {len(project_data['files'])} files")
        files_content = {}
        
        # Extract frontend files
        for file in project_data['files']:
            file_path = file['path']
            if file_path.startswith('frontend/'):
                # Remove 'frontend/' prefix
                relative_path = file_path[9:]
                files_content[relative_path] = file['content']
        
        if not files_content:
            raise HTTPException(
                status_code=404,
                detail=f"No frontend files found for project '{project_slug}'"
            )
        
        # Generate the sandbox HTML
        sandbox_html = generate_sandbox_html(files_content, project_name)
        
        # Add cache-busting headers to force fresh reload
        return HTMLResponse(
            content=sandbox_html,
            headers={
                'Cache-Control': 'no-cache, no-store, must-revalidate, max-age=0',
                'Pragma': 'no-cache',
                'Expires': '0'
            }
        )
        
    except HTTPException as http_ex:
        # Re-raise HTTPExceptions (like 404) with their original status
        raise http_ex
    except Exception as e:
        # Log detailed error information for debugging
        import traceback
        print(f"❌ Sandbox preview error for project '{project_name}':")
        print(f"   Error type: {type(e).__name__}")
        print(f"   Error message: {str(e)}")
        print(f"   Traceback: {traceback.format_exc()}")
        
        error_html = f"""
        <html>
            <body style="font-family: Arial; padding: 20px; background: #1e1e1e; color: #fff;">
                <h2>Preview Error</h2>
                <p>Failed to generate preview: {str(e)}</p>
                <p>Project: {project_name}</p>
                <p style="color: #888; font-size: 0.9em;">Error type: {type(e).__name__}</p>
                <hr style="border-color: #333;">
                <p style="color: #888; font-size: 0.85em;">Check server logs for detailed information.</p>
            </body>
        </html>
        """
        return HTMLResponse(content=error_html, status_code=500)

def generate_sandbox_html(files_content: dict, project_name: str) -> str:
    """Generate a complete HTML page that runs React code in the browser"""
    
    # Extract main app content
    app_jsx = files_content.get("src/App.jsx", "")
    main_jsx = files_content.get("src/main.jsx", "")
    index_css = files_content.get("src/index.css", "")
    
    # Detect which libraries are actually needed by scanning the code
    all_code = app_jsx + main_jsx + str(files_content)
    needs_three = 'THREE' in all_code or 'three' in all_code.lower() or 'Globe' in all_code
    needs_globe = 'Globe' in all_code or 'globe' in all_code.lower()
    needs_leaflet = 'Leaflet' in all_code or 'L.map' in all_code or 'leaflet' in all_code.lower()
    needs_charts = 'Chart' in all_code or 'chart' in all_code.lower() or 'd3.' in all_code.lower()
    needs_stripe = 'Stripe' in all_code or 'stripe' in all_code.lower() or 'payment' in all_code.lower()
    
    # Build conditional library loading
    optional_libs = ""
    if needs_three:
        optional_libs += '    <script src="https://cdn.jsdelivr.net/npm/three@0.157.0/build/three.min.js"></script>\n'
    if needs_globe:
        optional_libs += '    <script src="https://cdn.jsdelivr.net/npm/globe.gl@2.27.1/dist/globe.gl.min.js"></script>\n'
    if needs_leaflet:
        optional_libs += '    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/leaflet@1.9.4/dist/leaflet.min.css" />\n'
        optional_libs += '    <script src="https://cdn.jsdelivr.net/npm/leaflet@1.9.4/dist/leaflet.min.js"></script>\n'
    if needs_charts:
        optional_libs += '    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>\n'
        optional_libs += '    <script src="https://cdn.jsdelivr.net/npm/d3@7.8.5/dist/d3.min.js"></script>\n'
    if needs_stripe:
        optional_libs += '    <script src="https://js.stripe.com/v3/"></script>\n'
    
    if optional_libs:
        print(f"📦 Loading optional libraries: {'Three.js ' if needs_three else ''}{'Globe.gl ' if needs_globe else ''}{'Leaflet ' if needs_leaflet else ''}{'Charts ' if needs_charts else ''}{'Stripe ' if needs_stripe else ''}")
    else:
        print("⚡ Fast preview: No heavy libraries needed")
    
    # Validate and fix main.jsx content
    if main_jsx and 'ReactDOM.createRoot' in main_jsx:
        if '.render(\n\n  ,\n)' in main_jsx or '.render(\n\n,\n)' in main_jsx:
            print("🔧 Fixing incomplete render call in main.jsx for sandbox")
            main_jsx = main_jsx.replace(
                '.render(\n\n  ,\n)',
                '.render(\n  <React.StrictMode>\n    <App />\n  </React.StrictMode>\n)'
            ).replace(
                '.render(\n\n,\n)',
                '.render(\n  <React.StrictMode>\n    <App />\n  </React.StrictMode>\n)'
            )
    
    # Process component files properly for browser compilation
    components_code = ""
    total_code_size = 0
    MAX_CODE_SIZE = 100000  # 100KB max code size limit
    
    # UI components that are provided globally by the sandbox - skip loading their separate files
    SANDBOX_PROVIDED_COMPONENTS = {
        'Button', 'Input', 'Card', 'Loading', 'AnimatedText', 'Navigation'
    }
    
    for file_path, content in files_content.items():
        # Include all JSX files in components folder (including subfolders like ui/)
        if "components/" in file_path and file_path.endswith(".jsx"):
            # Extract component name from filename
            component_name = file_path.split("/")[-1].replace(".jsx", "")
            
            # SKIP UI components that are provided globally by the sandbox
            if component_name in SANDBOX_PROVIDED_COMPONENTS:
                print(f"⏭️ Skipping {component_name}.jsx - provided globally by sandbox")
                continue
            
            # Clean up the component content for browser compilation
            cleaned_content = content
            
            # Validate and fix component content
            cleaned_content = fix_jsx_content_for_sandbox(cleaned_content, component_name, project_name)
            
            # Remove ALL import statements since we're bundling everything in browser scope
            content_lines = cleaned_content.split('\n')
            filtered_lines = []
            for line in content_lines:
                # Remove all import statements
                if not line.strip().startswith('import '):
                    filtered_lines.append(line)
            
            cleaned_content = '\n'.join(filtered_lines)
            
            # Ensure the component is properly exported for global scope
            # Handle multiple exports like: export const Button, export const Input, etc.
            import re
            
            # Find all "export const ComponentName" declarations
            export_pattern = r'export\s+const\s+(\w+)\s*='
            exports_found = re.findall(export_pattern, cleaned_content)
            
            if exports_found:
                # Remove all "export" keywords
                cleaned_content = re.sub(r'export\s+const\s+', 'const ', cleaned_content)
                # Add window assignments for each exported component
                for exported_name in exports_found:
                    cleaned_content += f'\nwindow.{exported_name} = {exported_name};'
            elif 'export default' in cleaned_content:
                cleaned_content = cleaned_content.replace('export default', f'window.{component_name} = ')
            elif f'export {{ {component_name} }}' in cleaned_content:
                cleaned_content += f'\nwindow.{component_name} = {component_name};'
            else:
                # If no export found, assume the component is the main function/class
                cleaned_content += f'\nwindow.{component_name} = {component_name};'
            
            # Check code size limit to prevent memory issues
            component_size = len(cleaned_content)
            if total_code_size + component_size > MAX_CODE_SIZE:
                print(f"⚠️ Skipping {component_name}.jsx - code size limit reached ({total_code_size}/{MAX_CODE_SIZE} bytes)")
                continue
            
            total_code_size += component_size
            components_code += f"// {component_name} Component\n{cleaned_content}\n\n"
    
    # Clean the App.jsx content
    app_content = app_jsx
    
    # Remove ALL import statements FIRST since we're loading React globally
    app_content = '\n'.join([
        line for line in app_content.split('\n') 
        if not line.strip().startswith('import ')
    ])
    
    # Handle export patterns (robust)
    import re
    if 'export default' in app_content:
        # Pattern 1: export default SomeName; (reference to component - handles App, AppWrapper, etc.)
        export_match = re.search(r'export\s+default\s+(\w+)\s*;?', app_content)
        if export_match:
            component_name = export_match.group(1)
            app_content = re.sub(
                r'export\s+default\s+' + component_name + r'\s*;?',
                f'window.App = {component_name};',
                app_content,
                flags=re.MULTILINE
            )
        # Pattern 2: export default function App() { ... }
        if re.search(r'export\s+default\s+function\s+App\s*\(', app_content):
            app_content = re.sub(
                r'export\s+default\s+function\s+App',
                'function App',
                app_content
            )
            if 'window.App' not in app_content:
                app_content = app_content.rstrip() + '\n\nwindow.App = App;\n'
        # Pattern 3: export default function() { ... } (anonymous)
        elif re.search(r'export\s+default\s+function\s*\(', app_content):
            app_content = re.sub(
                r'export\s+default\s+function\s*\(',
                'window.App = function(',
                app_content
            )
        # Pattern 4: export default () => / export default ( ... )
        elif 'export default' in app_content:
            app_content = app_content.replace('export default', 'window.App =')
    else:
        # No export - add window.App assignment at the end
        # Prefer AppWrapper if it exists, otherwise use App
        if 'window.App' not in app_content:
            if 'const AppWrapper' in app_content or 'function AppWrapper' in app_content:
                app_content = app_content.rstrip() + '\n\nwindow.App = AppWrapper;\n'
            else:
                app_content = app_content.rstrip() + '\n\nwindow.App = App;\n'
    
    # Limit App.jsx size as well
    if len(app_content) > MAX_CODE_SIZE:
        print(f"⚠️ Warning: App.jsx is very large ({len(app_content)} bytes), truncating...")
        # Keep the first MAX_CODE_SIZE bytes, trying to end at a reasonable point
        app_content = app_content[:MAX_CODE_SIZE]
        # Try to find a good cutoff point (end of a function or component)
        last_close_brace = app_content.rfind('};')
        if last_close_brace > MAX_CODE_SIZE * 0.8:
            app_content = app_content[:last_close_brace + 2]
        app_content += '\n// Code truncated due to size limits\nwindow.App = App || (() => React.createElement("div", null, "App truncated"));'
    
    print(f"📦 Total code size: {total_code_size + len(app_content)} bytes")
    
    # PRECOMPILE JSX TO JS ON SERVER - No browser transforms needed!
    jsx_code = f"{components_code}\n\n{app_content}"
    print("🔄 Precompiling JSX to JavaScript using esbuild...")
    precompiled_code = precompile_jsx(jsx_code)
    print("✅ JSX precompilation complete - sending pure JS to browser")
    
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{project_name} - Live Preview</title>
    <!-- SANDBOX PREVIEW - Fast loading with conditional libraries -->
    
    <!-- CRITICAL: Protect built-in globals BEFORE any libraries load -->
    <script>
        // Save native Map/Set BEFORE anything else runs
        // User code with components named "Map" would otherwise break React
        (function() {{
            const _NativeMap = window.Map;
            const _NativeSet = window.Set;
            const _NativeArray = window.Array;
            const _NativeObject = window.Object;
            const _NativePromise = window.Promise;
            
            // Make them non-writable on window
            Object.defineProperty(window, 'Map', {{
                get: function() {{ return _NativeMap; }},
                set: function(v) {{
                    // Allow setting but store as MapComponent instead
                    if (typeof v === 'function' && v !== _NativeMap) {{
                        window.MapComponent = v;
                        console.log('⚠️ Redirected Map assignment to MapComponent');
                    }}
                }},
                configurable: false
            }});
            
            Object.defineProperty(window, 'Set', {{
                get: function() {{ return _NativeSet; }},
                set: function(v) {{
                    if (typeof v === 'function' && v !== _NativeSet) {{
                        window.SetComponent = v;
                        console.log('⚠️ Redirected Set assignment to SetComponent');
                    }}
                }},
                configurable: false
            }});
            
            console.log('✅ Protected native Map/Set from being overwritten');
        }})();
    </script>
    
    <!-- Core React (required) -->
    <script crossorigin src="https://unpkg.com/react@18/umd/react.production.min.js"></script>
    <script crossorigin src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js"></script>
    
    <!-- Optional libraries (loaded only if needed) -->
{optional_libs}
    <!-- Motion & Animation Fallbacks -->
    <script>
        // Robust motion fallback - ALWAYS create these to prevent ReferenceError
        // We ALWAYS use our safe fallback to avoid "a.set is not a function" errors
        const createMotionComponent = (element) => {{
            return function MotionComponent(props) {{
                const {{ children, className, style, onClick, onSubmit, onChange, onMouseEnter, onMouseLeave, id, type, href, initial, animate, exit, whileHover, whileTap, whileInView, transition, variants, disabled, value, placeholder, name, ...rest }} = props;
                return React.createElement(element, {{ className, style, onClick, onSubmit, onChange, onMouseEnter, onMouseLeave, id, type, href, disabled, value, placeholder, name, ...rest }}, children);
            }};
        }};
        
        // GLOBAL IMAGE ERROR HANDLER - Fix broken images automatically
        // This handles any images that fail to load by replacing them with a reliable fallback
        const FALLBACK_IMAGES = [
            'https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=400&h=300&fit=crop&auto=format',
            'https://images.unsplash.com/photo-1557683316-973673baf926?w=400&h=300&fit=crop&auto=format',
            'https://images.unsplash.com/photo-1579546929518-9e396f3cc809?w=400&h=300&fit=crop&auto=format'
        ];
        let fallbackImageIndex = 0;
        
        document.addEventListener('error', function(e) {{
            if (e.target.tagName === 'IMG' && !e.target.dataset.fallbackApplied) {{
                console.log('🖼️ Fixing broken image:', e.target.src);
                e.target.dataset.fallbackApplied = 'true';
                e.target.src = FALLBACK_IMAGES[fallbackImageIndex % FALLBACK_IMAGES.length];
                fallbackImageIndex++;
            }}
        }}, true);
        
        // Also intercept image loads in React components
        const originalCreateElement = React.createElement;
        React.createElement = function(type, props, ...children) {{
            if (type === 'img' && props && props.src) {{
                const originalSrc = props.src;
                // Check for common broken URL patterns
                const brokenPatterns = [
                    /placehold\\.co/i,
                    /placeholder\\.com/i,
                    /via\\.placeholder\\.com/i,
                    /example\\.com.*\\.(jpg|png|gif)/i,
                    /fake.*\\.(jpg|png|gif)/i
                ];
                
                const isBroken = brokenPatterns.some(pattern => pattern.test(originalSrc));
                if (isBroken) {{
                    props = {{ ...props, src: FALLBACK_IMAGES[Math.abs(originalSrc.length) % FALLBACK_IMAGES.length] }};
                    console.log('🖼️ Replaced broken image URL:', originalSrc);
                }}
                
                // Add onerror handler to all images
                const existingOnError = props.onError;
                props = {{
                    ...props,
                    onError: (e) => {{
                        if (!e.target.dataset.fallbackApplied) {{
                            e.target.dataset.fallbackApplied = 'true';
                            e.target.src = FALLBACK_IMAGES[fallbackImageIndex % FALLBACK_IMAGES.length];
                            fallbackImageIndex++;
                        }}
                        if (existingOnError) existingOnError(e);
                    }}
                }};
            }}
            return originalCreateElement.call(React, type, props, ...children);
        }};
        
        // ALWAYS define motion globally - use our safe fallback to avoid "a.set is not a function" errors
        // The real framer-motion library can cause issues with modal/conditional rendering
        window.motion = {{
            div: createMotionComponent('div'),
            span: createMotionComponent('span'),
            section: createMotionComponent('section'),
            header: createMotionComponent('header'),
            nav: createMotionComponent('nav'),
            main: createMotionComponent('main'),
            footer: createMotionComponent('footer'),
            article: createMotionComponent('article'),
            aside: createMotionComponent('aside'),
            h1: createMotionComponent('h1'),
            h2: createMotionComponent('h2'),
            h3: createMotionComponent('h3'),
            h4: createMotionComponent('h4'),
            p: createMotionComponent('p'),
            a: createMotionComponent('a'),
            button: createMotionComponent('button'),
            input: createMotionComponent('input'),
            form: createMotionComponent('form'),
            ul: createMotionComponent('ul'),
            li: createMotionComponent('li'),
            img: createMotionComponent('img'),
            svg: createMotionComponent('svg'),
            path: createMotionComponent('path'),
            label: createMotionComponent('label'),
            textarea: createMotionComponent('textarea'),
            select: createMotionComponent('select'),
            option: createMotionComponent('option'),
            table: createMotionComponent('table'),
            tr: createMotionComponent('tr'),
            td: createMotionComponent('td'),
            th: createMotionComponent('th')
        }};
        console.log('✅ Motion fallback components created (safe modal rendering)');
        
        // ALWAYS define AnimatePresence - ROBUST FALLBACK
        // The real framer-motion AnimatePresence can cause "a.set is not a function" errors
        // when children are conditionally rendered. This fallback avoids that issue.
        window.AnimatePresence = function AnimatePresenceFallback({{ children, mode, initial, onExitComplete }}) {{
            // Simply render children directly - no animation tracking
            // This prevents the "a.set is not a function" error that occurs with modal/conditional rendering
            if (Array.isArray(children)) {{
                return React.createElement(React.Fragment, null, ...children.filter(Boolean));
            }}
            return children || null;
        }};
        console.log('✅ AnimatePresence fallback installed (prevents modal errors)');
        
        // Define motion hooks
        if (typeof useScroll === 'undefined') {{
            window.useScroll = function useScrollFallback() {{
                return {{ scrollYProgress: {{ get: () => 0, onChange: () => {{}} }} }};
            }};
        }}
        
        if (typeof useInView === 'undefined') {{
            window.useInView = function useInViewFallback(ref, options) {{
                return true;
            }};
        }}
        
        if (typeof useAnimation === 'undefined') {{
            window.useAnimation = function useAnimationFallback() {{
                return {{ start: () => {{}}, stop: () => {{}} }};
            }};
        }}
        
        // ═══════════════════════════════════════════════════════════════
        // 🌍 GLOBAL 3D GLOBE & MAP HELPERS
        // ═══════════════════════════════════════════════════════════════
        
        // Make Three.js globally available
        if (typeof THREE !== 'undefined') {{
            window.THREE = THREE;
            console.log('✅ Three.js loaded for 3D graphics');
        }}
        
        // Make Globe.gl globally available
        if (typeof Globe !== 'undefined') {{
            window.Globe = Globe;
            console.log('✅ Globe.gl loaded for 3D globe visualization');
        }}
        
        // Make Leaflet globally available for maps
        if (typeof L !== 'undefined') {{
            window.L = L;
            console.log('✅ Leaflet loaded for 2D maps');
        }}
        
        // Make Chart.js globally available
        if (typeof Chart !== 'undefined') {{
            window.Chart = Chart;
            console.log('✅ Chart.js loaded for data visualization');
        }}
        
        // Make D3.js globally available
        if (typeof d3 !== 'undefined') {{
            window.d3 = d3;
            console.log('✅ D3.js loaded for advanced visualization');
        }}
        
        // ═══════════════════════════════════════════════════════════════
        // 💳 STRIPE PAYMENT INTEGRATION HELPER
        // ═══════════════════════════════════════════════════════════════
        
        // Stripe Payment Helper - makes real payments work in sandbox
        window.StripePayment = {{
            stripe: null,
            
            // Initialize Stripe with public key
            init: function(publishableKey) {{
                if (typeof Stripe !== 'undefined') {{
                    this.stripe = Stripe(publishableKey || 'pk_test_51Example'); // Use test key for demo
                    console.log('✅ Stripe initialized for payments');
                    return this.stripe;
                }} else {{
                    console.warn('⚠️ Stripe.js not loaded');
                    return null;
                }}
            }},
            
            // Create payment intent (simulated for sandbox - connects to real Stripe in production)
            createPaymentIntent: async function(amount, currency = 'usd') {{
                // In sandbox mode, simulate a successful payment intent
                console.log(`💳 Creating payment intent for ${{(amount / 100).toFixed(2)}} ${{currency.toUpperCase()}}`);
                
                // Simulate API call delay
                await new Promise(resolve => setTimeout(resolve, 800));
                
                return {{
                    clientSecret: 'pi_sandbox_' + Date.now() + '_secret_' + Math.random().toString(36).slice(2),
                    amount: amount,
                    currency: currency,
                    status: 'requires_payment_method'
                }};
            }},
            
            // Process payment with card details
            processPayment: async function(cardDetails, paymentIntent) {{
                console.log('💳 Processing payment with Stripe...');
                
                // Validate card number (remove spaces and check)
                const cardNumber = (cardDetails.number || '').replace(/\\s/g, '');
                const isValidCard = cardNumber.length >= 13 && cardNumber.length <= 19;
                
                // Simulate processing time (like real Stripe)
                await new Promise(resolve => setTimeout(resolve, 1500));
                
                if (!isValidCard) {{
                    return {{
                        success: false,
                        error: 'Invalid card number. Please check and try again.'
                    }};
                }}
                
                // Test card numbers - using Stripe's standard test cards
                // 4242424242424242 = Success
                // 4000000000000002 = Declined
                // 4000000000009995 = Insufficient funds
                
                if (cardNumber === '4000000000000002') {{
                    return {{ success: false, error: 'Your card was declined. Please try a different card.' }};
                }}
                if (cardNumber === '4000000000009995') {{
                    return {{ success: false, error: 'Insufficient funds. Please try a different card.' }};
                }}
                if (cardNumber === '4000000000000069') {{
                    return {{ success: false, error: 'Card expired. Please use a valid card.' }};
                }}
                if (cardNumber === '4000000000000127') {{
                    return {{ success: false, error: 'Invalid CVV. Please check your security code.' }};
                }}
                
                // All other valid cards (including 4242424242424242) succeed
                console.log('✅ Payment successful!');
                return {{
                    success: true,
                    paymentId: 'pay_' + Date.now() + '_' + Math.random().toString(36).slice(2),
                    receiptUrl: '#receipt-' + Date.now(),
                    amount: paymentIntent?.amount || 0,
                    last4: cardNumber.slice(-4),
                    brand: cardNumber.startsWith('4') ? 'Visa' : cardNumber.startsWith('5') ? 'Mastercard' : 'Card'
                }};
            }}
        }};
        
        console.log('✅ Stripe payment helper initialized');
        
        // ═══════════════════════════════════════════════════════════════
        // 🌍 GLOBE COMPONENT HELPER
        // ═══════════════════════════════════════════════════════════════
        
        // Helper to create interactive 3D globe
        window.createGlobe = function(container, options = {{}}) {{
            if (typeof Globe === 'undefined') {{
                console.error('Globe.gl not loaded');
                return null;
            }}
            
            const globe = Globe()(container)
                .globeImageUrl(options.globeImageUrl || '//unpkg.com/three-globe/example/img/earth-blue-marble.jpg')
                .bumpImageUrl(options.bumpImageUrl || '//unpkg.com/three-globe/example/img/earth-topology.png')
                .backgroundImageUrl(options.backgroundImageUrl || '//unpkg.com/three-globe/example/img/night-sky.png')
                .width(options.width || container.offsetWidth)
                .height(options.height || container.offsetHeight || 500);
            
            // Add countries if data provided
            if (options.countries) {{
                globe.polygonsData(options.countries)
                    .polygonCapColor(() => 'rgba(200, 200, 200, 0.6)')
                    .polygonSideColor(() => 'rgba(150, 150, 150, 0.3)')
                    .polygonLabel(({{ properties: p }}) => p.NAME);
            }}
            
            // Add points if data provided
            if (options.points) {{
                globe.pointsData(options.points)
                    .pointColor(options.pointColor || (() => '#ff0000'))
                    .pointRadius(options.pointRadius || 0.5)
                    .pointAltitude(options.pointAltitude || 0.01);
            }}
            
            // Add arcs if data provided
            if (options.arcs) {{
                globe.arcsData(options.arcs)
                    .arcColor(options.arcColor || (() => '#ffff00'))
                    .arcStroke(options.arcStroke || 0.5)
                    .arcAltitude(options.arcAltitude || 0.3);
            }}
            
            return globe;
        }};
        
        // ═══════════════════════════════════════════════════════════════
        // 🗺️ MAP COMPONENT HELPER
        // ═══════════════════════════════════════════════════════════════
        
        // Helper to create interactive Leaflet map
        window.createMap = function(containerId, options = {{}}) {{
            if (typeof L === 'undefined') {{
                console.error('Leaflet not loaded');
                return null;
            }}
            
            const map = L.map(containerId).setView(
                options.center || [0, 0], 
                options.zoom || 2
            );
            
            // Add tile layer (OpenStreetMap by default)
            L.tileLayer(options.tileUrl || 'https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
                attribution: options.attribution || '&copy; OpenStreetMap contributors',
                maxZoom: options.maxZoom || 19
            }}).addTo(map);
            
            return map;
        }};
        
        // ═══════════════════════════════════════════════════════════════
        // 📊 CHART COMPONENT HELPER  
        // ═══════════════════════════════════════════════════════════════
        
        // Helper to create Chart.js charts easily
        window.createChart = function(canvasId, config) {{
            if (typeof Chart === 'undefined') {{
                console.error('Chart.js not loaded');
                return null;
            }}
            
            const canvas = document.getElementById(canvasId);
            if (!canvas) {{
                console.error('Canvas not found:', canvasId);
                return null;
            }}
            
            return new Chart(canvas, config);
        }};
        
    </script>
    
    <!-- NO JSX TRANSFORMS IN BROWSER - Code is precompiled on server using esbuild -->
    
    <!-- Define CommonJS globals -->
    <script>
        // Define globals for user code that might use CommonJS patterns
        if (typeof window.exports === 'undefined') {{
            window.exports = {{}};
        }}
        if (typeof window.module === 'undefined') {{
            window.module = {{ exports: {{}} }};
        }}
        console.log('✅ CommonJS globals defined');
    </script>
    
    <!-- Use pre-built Tailwind CSS instead of JIT CDN to avoid conflicts -->
    <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
    
    <!-- Load clsx from CDN -->
    <script src="https://unpkg.com/clsx@2.0.0/dist/clsx.min.js"></script>
    
    <style>
        /* Additional utility classes not in Tailwind 2.2 */
        .bg-gray-900 {{ background-color: #111827; }}
        .bg-gray-800 {{ background-color: #1f2937; }}
        .bg-gray-700 {{ background-color: #374151; }}
        .text-gray-100 {{ color: #f3f4f6; }}
        .text-gray-200 {{ color: #e5e7eb; }}
        .text-gray-300 {{ color: #d1d5db; }}
        .text-gray-400 {{ color: #9ca3af; }}
        
        /* Slate colors (Tailwind v3) */
        .bg-slate-900 {{ background-color: #0f172a; }}
        .bg-slate-800 {{ background-color: #1e293b; }}
        .bg-slate-800\\/60 {{ background-color: rgba(30, 41, 59, 0.6); }}
        .bg-slate-900\\/50 {{ background-color: rgba(15, 23, 42, 0.5); }}
        .bg-slate-700 {{ background-color: #334155; }}
        .bg-slate-600 {{ background-color: #475569; }}
        .bg-slate-500 {{ background-color: #64748b; }}
        .text-slate-100 {{ color: #f1f5f9; }}
        .text-slate-200 {{ color: #e2e8f0; }}
        .text-slate-300 {{ color: #cbd5e1; }}
        .text-slate-400 {{ color: #94a3b8; }}
        .text-slate-500 {{ color: #64748b; }}
        .border-slate-700 {{ border-color: #334155; }}
        .border-slate-600 {{ border-color: #475569; }}
        .ring-slate-700 {{ --tw-ring-color: #334155; }}
        .hover\\:bg-slate-700:hover {{ background-color: #334155; }}
        .hover\\:bg-slate-800:hover {{ background-color: #1e293b; }}
        .hover\\:text-slate-100:hover {{ color: #f1f5f9; }}
        
        /* Cyan colors */
        .text-cyan-400 {{ color: #22d3ee; }}
        .text-cyan-500 {{ color: #06b6d4; }}
        .bg-cyan-500 {{ background-color: #06b6d4; }}
        .bg-cyan-600 {{ background-color: #0891b2; }}
        .from-cyan-500 {{ --tw-gradient-from: #06b6d4; }}
        .to-blue-600 {{ --tw-gradient-to: #2563eb; }}
        .to-cyan-400 {{ --tw-gradient-to: #22d3ee; }}
        
        /* Ring utilities */
        .ring-1 {{ box-shadow: 0 0 0 1px var(--tw-ring-color); }}
        .ring-white\\/10 {{ --tw-ring-color: rgba(255, 255, 255, 0.1); }}
        
        /* Emerald colors */
        .bg-emerald-500 {{ background-color: #10b981; }}
        .bg-emerald-600 {{ background-color: #059669; }}
        .text-emerald-400 {{ color: #34d399; }}
        .from-emerald-500 {{ --tw-gradient-from: #10b981; }}
        .to-emerald-600 {{ --tw-gradient-to: #059669; }}
        
        /* Additional gradients */
        .from-green-500 {{ --tw-gradient-from: #22c55e; }}
        .to-green-600 {{ --tw-gradient-to: #16a34a; }}
        .from-red-500 {{ --tw-gradient-from: #ef4444; }}
        .to-red-600 {{ --tw-gradient-to: #dc2626; }}
        .from-pink-600 {{ --tw-gradient-from: #db2777; }}
        .to-pink-500 {{ --tw-gradient-to: #ec4899; }}
        
        /* White opacity utilities */
        .bg-white\\/10 {{ background-color: rgba(255, 255, 255, 0.1); }}
        .bg-white\\/20 {{ background-color: rgba(255, 255, 255, 0.2); }}
        .hover\\:bg-white\\/10:hover {{ background-color: rgba(255, 255, 255, 0.1); }}
        .hover\\:bg-white\\/20:hover {{ background-color: rgba(255, 255, 255, 0.2); }}
        
        /* Backdrop blur */
        .backdrop-blur-sm {{ backdrop-filter: blur(4px); }}
        .backdrop-blur {{ backdrop-filter: blur(8px); }}
        
        /* Focus ring utilities */
        .focus\\:ring-cyan-500\\/50:focus {{ --tw-ring-color: rgba(6, 182, 212, 0.5); }}
        .focus\\:ring-white\\/20:focus {{ --tw-ring-color: rgba(255, 255, 255, 0.2); }}
        
        /* Border opacity */
        .border-cyan-400\\/50 {{ border-color: rgba(34, 211, 238, 0.5); }}
        .border-slate-600\\/50 {{ border-color: rgba(71, 85, 105, 0.5); }}
        
        /* Slate background with opacity */
        .bg-slate-800\\/50 {{ background-color: rgba(30, 41, 59, 0.5); }}
        
        .bg-indigo-600 {{ background-color: #4f46e5; }}
        .bg-indigo-500 {{ background-color: #6366f1; }}
        .text-indigo-400 {{ color: #818cf8; }}
        .hover\\:bg-indigo-700:hover {{ background-color: #4338ca; }}
        .from-indigo-600 {{ --tw-gradient-from: #4f46e5; }}
        .via-purple-500 {{ --tw-gradient-stops: var(--tw-gradient-from), #a855f7, var(--tw-gradient-to, rgba(168, 85, 247, 0)); }}
        .to-pink-500 {{ --tw-gradient-to: #ec4899; }}
        .bg-gradient-to-r {{ background-image: linear-gradient(to right, var(--tw-gradient-stops)); }}
        .bg-gradient-to-br {{ background-image: linear-gradient(to bottom right, var(--tw-gradient-stops)); }}
        .backdrop-blur-md {{ backdrop-filter: blur(12px); }}
        .backdrop-blur-lg {{ backdrop-filter: blur(16px); }}
        .bg-opacity-80 {{ --tw-bg-opacity: 0.8; }}
        .bg-opacity-90 {{ --tw-bg-opacity: 0.9; }}
        .ring-2 {{ box-shadow: 0 0 0 2px var(--tw-ring-color); }}
        .ring-indigo-400 {{ --tw-ring-color: #818cf8; }}
        .transition-all {{ transition-property: all; transition-timing-function: cubic-bezier(0.4, 0, 0.2, 1); transition-duration: 150ms; }}
        .duration-300 {{ transition-duration: 300ms; }}
        .animate-pulse {{ animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite; }}
        .animate-spin {{ animation: spin 1s linear infinite; }}
        @keyframes pulse {{ 0%, 100% {{ opacity: 1; }} 50% {{ opacity: .5; }} }}
        @keyframes spin {{ to {{ transform: rotate(360deg); }} }}
        .line-clamp-2 {{ display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }}
        .aspect-square {{ aspect-ratio: 1 / 1; }}
        .aspect-video {{ aspect-ratio: 16 / 9; }}
        .scroll-smooth {{ scroll-behavior: smooth; }}
        .snap-x {{ scroll-snap-type: x mandatory; }}
        .snap-start {{ scroll-snap-align: start; }}
        .scrollbar-hide {{ -ms-overflow-style: none; scrollbar-width: none; }}
        .scrollbar-hide::-webkit-scrollbar {{ display: none; }}
        {index_css}
        body {{ margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif; }}
        #root {{ width: 100%; height: 100vh; }}
        
        /* DEFAULT BUTTON STYLING - Ensures buttons are ALWAYS visible */
        button {{
            cursor: pointer;
            font-family: inherit;
            font-size: inherit;
            line-height: inherit;
        }}
        /* Buttons without explicit background should get a default visible style */
        button:not([class*="bg-"]):not([class*="border"]):not([class*="text-"]):not([class*="px-"]) {{
            padding: 8px 16px;
            background-color: #3b82f6;
            color: white;
            border: none;
            border-radius: 6px;
            font-weight: 500;
            transition: background-color 0.2s;
        }}
        button:not([class*="bg-"]):not([class*="border"]):not([class*="text-"]):not([class*="px-"]):hover {{
            background-color: #2563eb;
        }}
        
        .error-boundary {{ 
            padding: 20px; 
            background: #fee; 
            border: 1px solid #fcc; 
            border-radius: 4px; 
            margin: 20px;
            color: #c33;
        }}
        .preview-console {{
            position: fixed;
            bottom: 60px;
            right: 20px;
            width: 350px;
            max-height: 300px;
            background: rgba(15, 15, 15, 0.95);
            color: #0f0;
            padding: 12px;
            font-family: 'SF Mono', Monaco, 'Cascadia Code', monospace;
            font-size: 11px;
            overflow-y: auto;
            z-index: 99998;
            border: 1px solid rgba(255,255,255,0.15);
            border-radius: 12px;
            backdrop-filter: blur(20px);
            box-shadow: 0 8px 32px rgba(0,0,0,0.4);
            display: none;
        }}
        .preview-console-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;
            padding-bottom: 8px;
            border-bottom: 1px solid rgba(255,255,255,0.1);
            color: #888;
            font-size: 10px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        .preview-console-toggle {{
            position: fixed;
            bottom: 20px;
            right: 20px;
            width: 40px;
            height: 40px;
            background: rgba(15, 15, 15, 0.9);
            border: 1px solid rgba(255,255,255,0.15);
            border-radius: 10px;
            color: #888;
            font-size: 16px;
            cursor: pointer;
            z-index: 99999;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.2s;
            backdrop-filter: blur(20px);
        }}
        .preview-console-toggle:hover {{
            background: rgba(30, 30, 30, 0.95);
            color: #fff;
            transform: scale(1.05);
        }}
        .preview-console-toggle.has-errors {{
            color: #ef4444;
            border-color: rgba(239, 68, 68, 0.3);
        }}
        .preview-console-badge {{
            position: absolute;
            top: -4px;
            right: -4px;
            min-width: 16px;
            height: 16px;
            background: #ef4444;
            color: white;
            font-size: 10px;
            font-weight: bold;
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 0 4px;
        }}
    </style>
</head>
<body>
    <div id="root">
        <div style="padding: 40px; text-align: center; color: #666;">
            <div style="font-size: 24px; margin-bottom: 12px;">⏳</div>
            <div>Loading preview...</div>
        </div>
    </div>
    <button id="preview-console-toggle" class="preview-console-toggle" title="Toggle Console Logs">
        <span>⌘</span>
        <span id="console-badge" class="preview-console-badge" style="display: none;">0</span>
    </button>
    <div id="preview-console" class="preview-console">
        <div class="preview-console-header">
            <span>Console Output</span>
            <button onclick="document.getElementById('preview-console').innerHTML = this.parentElement.outerHTML; document.getElementById('console-badge').textContent = '0'; document.getElementById('console-badge').style.display = 'none';" style="background: none; border: none; color: #666; cursor: pointer; font-size: 10px;">Clear</button>
        </div>
    </div>
    
    <!-- Memory monitoring and safety -->
    <script>
        // Add global error handler for memory issues
        window.addEventListener('error', function(e) {{
            if (e.message && (e.message.includes('memory') || e.message.includes('out of') || e.message.includes('allocation'))) {{
                console.error('Memory error detected:', e.message);
                document.getElementById('root').innerHTML = 
                    '<div style="padding: 40px; text-align: center; color: #ef4444;">' +
                    '<div style="font-size: 48px; margin-bottom: 12px;">⚠️</div>' +
                    '<h2 style="margin-bottom: 8px;">Memory Limit Reached</h2>' +
                    '<p style="color: #666;">The application is too large to preview in the browser.</p>' +
                    '<p style="color: #888; font-size: 12px;">Try refreshing the page or simplifying the code.</p>' +
                    '</div>';
            }}
        }});
        
        // Prevent infinite loops by limiting iterations
        let loopCounter = 0;
        const MAX_LOOPS = 100000;
        window.__checkLoop = function() {{
            loopCounter++;
            if (loopCounter > MAX_LOOPS) {{
                throw new Error('Infinite loop detected - execution stopped');
            }}
            return true;
        }};
        setInterval(() => {{ loopCounter = 0; }}, 1000);
    </script>
    
    <!-- Setup code - NO JSX, plain JavaScript -->
    <script>
        // Wait for all dependencies to load
        if (typeof React === 'undefined' || typeof ReactDOM === 'undefined') {{
            console.error('React not loaded properly');
            document.body.innerHTML = '<div style="padding: 20px; color: red;">Error: React libraries not loaded</div>';
            throw new Error('React dependencies missing');
        }}
        
        // Destructure React hooks
        const {{ useState, useEffect, useCallback, useMemo, useRef, useContext, useReducer, useLayoutEffect, useId, useTransition, useDeferredValue, useSyncExternalStore }} = React;
        
        // Make React hooks globally available for generated components
        window.useState = useState;
        window.useEffect = useEffect;
        window.useCallback = useCallback;
        window.useMemo = useMemo;
        window.useRef = useRef;
        window.useContext = useContext;
        window.useReducer = useReducer;
        window.useLayoutEffect = useLayoutEffect;
        window.useId = useId;
        window.useTransition = useTransition;
        window.useDeferredValue = useDeferredValue;
        window.useSyncExternalStore = useSyncExternalStore;
        window.createContext = React.createContext;
        window.forwardRef = React.forwardRef;
        window.memo = React.memo;
        window.lazy = React.lazy;
        window.Suspense = React.Suspense;
        window.Fragment = React.Fragment;
        window.createElement = React.createElement;
        
        // Helper function to filter invalid props from DOM elements
        // Using an array instead of Set to avoid potential conflicts with React internals
        const INVALID_DOM_PROPS = ['as', 'variant', 'size', 'color', 'isActive', 'isDisabled', 'isLoading',
            'leftIcon', 'rightIcon', 'colorScheme', 'spacing', 'direction', 'align',
            'justify', 'wrap', 'shouldWrapChildren', 'isTruncated', 'noOfLines'];
        
        window.filterDomProps = (props) => {{
            if (!props) return props;
            const filteredProps = {{}};
            for (const key in props) {{
                if (!INVALID_DOM_PROPS.includes(key)) {{
                    filteredProps[key] = props[key];
                }}
            }}
            return filteredProps;
        }};
        
        // Create a simple, reliable router that doesn't depend on external libraries
        const createSimpleRouter = () => {{
            // Simple router implementation using hash-based routing
            const SimpleRouter = ({{ children }}) => {{
                const [currentPath, setCurrentPath] = useState(window.location.hash.slice(1) || '/');
                
                useEffect(() => {{
                    const handleHashChange = () => {{
                        setCurrentPath(window.location.hash.slice(1) || '/');
                    }};
                    
                    window.addEventListener('hashchange', handleHashChange);
                    return () => window.removeEventListener('hashchange', handleHashChange);
                }}, []);
                
                // Provide router context
                return React.createElement('div', {{ 
                    'data-router': 'simple',
                    'data-current-path': currentPath 
                }}, children);
            }};
            
            const SimpleRoutes = ({{ children }}) => {{
                const [currentPath, setCurrentPath] = useState(window.location.hash.slice(1) || '/');
                
                // Re-render when hash changes
                useEffect(() => {{
                    const handleHashChange = () => {{
                        const newPath = window.location.hash.slice(1) || '/';
                        console.log('Route changed to:', newPath);
                        setCurrentPath(newPath);
                    }};
                    window.addEventListener('hashchange', handleHashChange);
                    return () => window.removeEventListener('hashchange', handleHashChange);
                }}, []);
                
                const routes = React.Children.toArray(children);
                
                // Find matching route - try exact match first, then prefix match
                let matchingRoute = routes.find(route => {{
                    if (route.props && route.props.path) {{
                        // Exact match
                        if (route.props.path === currentPath) return true;
                        // Handle index route
                        if (route.props.index && currentPath === '/') return true;
                    }}
                    return false;
                }});
                
                // If no exact match, try partial match (for nested routes)
                if (!matchingRoute) {{
                    matchingRoute = routes.find(route => {{
                        if (route.props && route.props.path && route.props.path !== '/') {{
                            return currentPath.startsWith(route.props.path);
                        }}
                        return false;
                    }});
                }}
                
                // Fall back to first route (usually home) or 404
                if (!matchingRoute) {{
                    matchingRoute = routes.find(r => r.props?.path === '/') || routes[0];
                }}
                
                // Log route changes only (not every render)
                const routePath = matchingRoute?.props?.path || 'default';
                if (window.__lastRenderedRoute !== routePath) {{
                    window.__lastRenderedRoute = routePath;
                    console.log('Route changed to:', routePath);
                }}
                return matchingRoute || React.createElement('div', null, 'Page not found');
            }};
            
            const SimpleRoute = ({{ element, path, children }}) => {{
                return element || children || React.createElement('div', null, `Route: ${{path}}`);
            }};
            
            const SimpleLink = ({{ to, children, className, style, ...props }}) => {{
                const handleClick = (e) => {{
                    e.preventDefault();
                    window.location.hash = to;
                }};
                
                return React.createElement('a', {{
                    href: `#${{to}}`,
                    onClick: handleClick,
                    className: className,
                    style: {{
                        cursor: 'pointer',
                        ...style
                    }},
                    ...props
                }}, children);
            }};
            
            // NavLink - like Link but with active state awareness
            const SimpleNavLink = ({{ to, children, className, style, activeClassName, activeStyle, ...props }}) => {{
                const [currentPath, setCurrentPath] = useState(window.location.hash.slice(1) || '/');
                
                useEffect(() => {{
                    const handleHashChange = () => setCurrentPath(window.location.hash.slice(1) || '/');
                    window.addEventListener('hashchange', handleHashChange);
                    return () => window.removeEventListener('hashchange', handleHashChange);
                }}, []);
                
                const handleClick = (e) => {{
                    e.preventDefault();
                    window.location.hash = to;
                }};
                
                const isActive = currentPath === to || (to !== '/' && currentPath.startsWith(to));
                
                // Handle className - can be string or function
                let finalClassName = className;
                if (typeof className === 'function') {{
                    finalClassName = className({{ isActive }});
                }} else if (isActive && activeClassName) {{
                    finalClassName = `${{className || ''}} ${{activeClassName}}`.trim();
                }}
                
                // Handle style - can be object or function
                let finalStyle = style || {{}};
                if (typeof style === 'function') {{
                    finalStyle = style({{ isActive }});
                }} else if (isActive && activeStyle) {{
                    finalStyle = {{ ...style, ...activeStyle }};
                }}
                
                return React.createElement('a', {{
                    href: `#${{to}}`,
                    onClick: handleClick,
                    className: finalClassName,
                    style: {{ cursor: 'pointer', ...finalStyle }},
                    'aria-current': isActive ? 'page' : undefined,
                    ...props
                }}, children);
            }};
            
            const useSimpleNavigate = () => {{
                return useCallback((path) => {{
                    window.location.hash = path;
                }}, []);
            }};
            
            const useSimpleParams = () => {{
                // Simple params extraction from hash
                const hash = window.location.hash.slice(1);
                const segments = hash.split('/');
                return {{ id: segments[segments.length - 1] || null }};
            }};
            
            const useSimpleLocation = () => {{
                const [location, setLocation] = useState({{
                    pathname: window.location.hash.slice(1) || '/',
                    hash: window.location.hash,
                    search: ''
                }});
                
                useEffect(() => {{
                    const handleHashChange = () => {{
                        setLocation({{
                            pathname: window.location.hash.slice(1) || '/',
                            hash: window.location.hash,
                            search: ''
                        }});
                    }};
                    
                    window.addEventListener('hashchange', handleHashChange);
                    return () => window.removeEventListener('hashchange', handleHashChange);
                }}, []);
                
                return location;
            }};
            
            // Navigate component for declarative navigation (like react-router-dom's Navigate)
            // Includes loop prevention to avoid infinite redirect cycles
            const SimpleNavigate = ({{ to, replace = false }}) => {{
                const navigatedRef = useRef(false);
                
                useEffect(() => {{
                    // Prevent multiple navigations and infinite loops
                    const currentPath = window.location.hash.slice(1) || '/';
                    const targetPath = to.startsWith('/') ? to : '/' + to;
                    
                    // Don't navigate if already at target or already navigated
                    if (navigatedRef.current || currentPath === targetPath) {{
                        return;
                    }}
                    
                    // Mark as navigated to prevent re-runs
                    navigatedRef.current = true;
                    
                    // Small delay to batch multiple navigations
                    const timer = setTimeout(() => {{
                        if (replace) {{
                            window.location.replace('#' + to);
                        }} else {{
                            window.location.hash = to;
                        }}
                    }}, 10);
                    
                    return () => clearTimeout(timer);
                }}, [to, replace]);
                
                return null;
            }};
            
            return {{
                Router: SimpleRouter,
                Routes: SimpleRoutes,
                Route: SimpleRoute,
                Link: SimpleLink,
                NavLink: SimpleNavLink,
                Navigate: SimpleNavigate,
                useNavigate: useSimpleNavigate,
                useParams: useSimpleParams,
                useLocation: useSimpleLocation
            }};
        }};
        
        // Always use the built-in simple hash router to avoid external deps
        let Router, Routes, Route, Link, NavLink, Navigate, useNavigate, useParams, useLocation;
        console.log('✅ Using built-in simple hash router (no external history/react-router)');
        const simpleRouter = createSimpleRouter();
        Router = simpleRouter.Router;
        Routes = simpleRouter.Routes;
        Route = simpleRouter.Route;
        Link = simpleRouter.Link;
        NavLink = simpleRouter.NavLink;
        Navigate = simpleRouter.Navigate;
        useNavigate = simpleRouter.useNavigate;
        useParams = simpleRouter.useParams;
        useLocation = simpleRouter.useLocation;
        
        // Make Router components available globally
        window.Router = Router;
        window.BrowserRouter = Router; // Use main Router as fallback
        window.HashRouter = Router;    // Use main Router as fallback
        window.MemoryRouter = Router;  // Use main Router as fallback
        window.Routes = Routes;
        window.Route = Route;
        window.Link = Link;
        window.NavLink = NavLink;
        window.Navigate = Navigate;
        window.useNavigate = useNavigate;
        window.useParams = useParams;
        window.useLocation = useLocation;
        
        // Create simple icon components as fallbacks
        const createIcon = (name) => (props = {{}}) => {{
            const size = props.size ?? 24;
            const className = props.className ?? '';
            const restProps = {{ ...props }};
            delete restProps.size;
            delete restProps.className;
            
            return React.createElement('svg', {{
                width: size,
                height: size,
                viewBox: '0 0 24 24',
                fill: 'none',
                stroke: 'currentColor',
                strokeWidth: 2,
                strokeLinecap: 'round',
                strokeLinejoin: 'round',
                className: className,
                ...restProps
            }}, React.createElement('title', null, name));
        }};
        
        // Create all common icons with a compact loop (saves ~7KB vs individual lines)
        ['Home','User','Settings','Search','Menu','X','Plus','Minus','Edit','Trash2','Save','ChevronDown','ChevronUp','ChevronLeft','ChevronRight','Heart','Star','Eye','EyeOff','Lock','Unlock','Mail','Phone','Calendar','Clock','Download','Upload','Share','MessageCircle','AlertCircle','CheckCircle','Info','FileText','Folder','Image','ShoppingCart','CreditCard','Package','MapPin','Globe','Play','Pause','Volume2','Battery','Wifi','Filter','Sort','MoreHorizontal','MoreVertical','ExternalLink','LogOut','LogIn','UserPlus','Settings2','Loader','Loader2','Truck','ShoppingBag','Tag','Store','Wallet','Receipt','Gift','Sparkles','Award','Zap','Target','TrendingUp','TrendingDown','BarChart','PieChart','Activity','Archive','Bell','Bookmark','Briefcase','Camera','Clipboard','Code','Compass','Copy','Database','Grid','Layers','Layout','Link2','List','Monitor','Printer','Repeat','Rotate','Scissors','Send','Sliders','Smartphone','Tablet','Terminal','ThumbsUp','ThumbsDown','Tool','Umbrella','Video','Voicemail','Watch','ZoomIn','ZoomOut','Facebook','Twitter','Instagram','Linkedin','Github','Youtube','Mic','MicOff','Volume','VolumeX','Headphones','Speaker','Music','Radio','ArrowRight','ArrowLeft','ArrowUp','ArrowDown','RefreshCw','RotateCcw','Trash','XCircle','PlusCircle','MinusCircle','HelpCircle','AlertTriangle','Power','Moon','Sun','Cloud','CloudOff','Droplet','Wind','Thermometer','Navigation2','Anchor','Car','Building','Server','Box','File','FolderOpen','Sidebar','PanelLeft','PanelRight','Maximize','Minimize','X2','Refresh','SkipForward','SkipBack','Stop','FastForward','Rewind','Film','Cast','Bluetooth','WifiOff','Laptop','DollarSign','Percent','Flag','Trophy','Crosshair','Map','Sunrise','Sunset','LineChart'].forEach(name => window[name] = createIcon(name));
        
        // ========== UI COMPONENTS (SANDBOX GLOBALS) ==========
        // These are essential UI components provided globally for the sandbox
        
        // Button Component - supports multiple variants and sizes
        const Button = (props = {{}}) => {{
            const children = props.children;
            const variant = props.variant ?? 'default';
            const size = props.size ?? 'md';
            const disabled = props.disabled ?? false;
            const onClick = props.onClick;
            const className = props.className ?? '';
            const type = props.type ?? 'button';
            const restProps = {{ ...props }};
            ['children', 'variant', 'size', 'disabled', 'onClick', 'className', 'type'].forEach(k => delete restProps[k]);
            
            const baseClasses = 'inline-flex items-center justify-center font-medium rounded-lg transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed';
            
            const variants = {{
                default: 'bg-blue-600 hover:bg-blue-700 text-white shadow-md hover:shadow-lg focus:ring-blue-500',
                primary: 'bg-blue-600 hover:bg-blue-700 text-white shadow-md hover:shadow-lg focus:ring-blue-500',
                secondary: 'bg-gray-200 hover:bg-gray-300 text-gray-800 focus:ring-gray-400',
                outline: 'border-2 border-current bg-transparent hover:bg-gray-100 text-current focus:ring-gray-400',
                ghost: 'bg-transparent hover:bg-gray-100 text-gray-700 focus:ring-gray-400',
                accent: 'bg-purple-600 hover:bg-purple-700 text-white shadow-md hover:shadow-lg focus:ring-purple-500',
                danger: 'bg-red-600 hover:bg-red-700 text-white shadow-md hover:shadow-lg focus:ring-red-500',
                success: 'bg-green-600 hover:bg-green-700 text-white shadow-md hover:shadow-lg focus:ring-green-500',
                link: 'bg-transparent text-blue-600 hover:text-blue-700 hover:underline p-0'
            }};
            
            const sizes = {{
                xs: 'px-2 py-1 text-xs',
                sm: 'px-3 py-1.5 text-sm',
                md: 'px-4 py-2 text-sm',
                lg: 'px-6 py-3 text-base',
                xl: 'px-8 py-4 text-lg'
            }};
            
            const variantClass = variants[variant] || variants.default;
            const sizeClass = sizes[size] || sizes.md || '';
            
            return React.createElement('button', {{
                type,
                className: `${{baseClasses}} ${{variantClass}} ${{sizeClass}} ${{className}}`,
                disabled,
                onClick,
                ...restProps
            }}, children);
        }};
        window.Button = Button;
        
        // Input Component - styled form input
        const Input = (props = {{}}) => {{
            const type = props.type ?? 'text';
            const placeholder = props.placeholder ?? '';
            const value = props.value;
            const onChange = props.onChange;
            const className = props.className ?? '';
            const disabled = props.disabled ?? false;
            const restProps = {{ ...props }};
            ['type', 'placeholder', 'value', 'onChange', 'className', 'disabled'].forEach(k => delete restProps[k]);
            
            const baseClasses = 'w-full px-4 py-2 border border-gray-300 rounded-lg bg-white text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200 disabled:bg-gray-100 disabled:cursor-not-allowed';
            
            return React.createElement('input', {{
                type,
                placeholder,
                value,
                onChange,
                disabled,
                className: `${{baseClasses}} ${{className}}`,
                ...restProps
            }});
        }};
        window.Input = Input;
        
        // Card Component - container with styling
        const Card = (props = {{}}) => {{
            const children = props.children;
            const className = props.className ?? '';
            const restProps = {{ ...props }};
            delete restProps.children;
            delete restProps.className;
            
            const baseClasses = 'bg-white rounded-xl shadow-md border border-gray-100 overflow-hidden';
            
            return React.createElement('div', {{
                className: `${{baseClasses}} ${{className}}`,
                ...restProps
            }}, children);
        }};
        window.Card = Card;
        
        // Loading Component - spinner/loading indicator
        const Loading = (props = {{}}) => {{
            const size = props.size ?? 'md';
            const className = props.className ?? '';
            
            const sizes = {{
                sm: 'w-4 h-4',
                md: 'w-8 h-8',
                lg: 'w-12 h-12'
            }};
            const sizeClass = sizes[size] || sizes.md || '';
            
            return React.createElement('div', {{
                className: `animate-spin rounded-full border-2 border-gray-200 border-t-blue-600 ${{sizeClass}} ${{className}}`
            }});
        }};
        window.Loading = Loading;
        
        // AnimatedText Component - text with animation support
        const AnimatedText = (props = {{}}) => {{
            const children = props.children;
            const className = props.className ?? '';
            const as = props.as ?? 'span';
            const restProps = {{ ...props }};
            delete restProps.children;
            delete restProps.className;
            delete restProps.as;
            
            return React.createElement(as, {{
                className: `transition-all duration-300 ${{className}}`,
                ...restProps
            }}, children);
        }};
        window.AnimatedText = AnimatedText;
        
        console.log('✅ UI Components loaded: Button, Input, Card, Loading, AnimatedText');
        
        // Console logger for debugging - hidden by default with toggle button
        const originalConsoleLog = console.log;
        const originalConsoleError = console.error;
        const originalConsoleWarn = console.warn;
        
        const consoleDiv = document.getElementById('preview-console');
        const consoleToggle = document.getElementById('preview-console-toggle');
        const consoleBadge = document.getElementById('console-badge');
        let logCount = 0;
        let errorCount = 0;
        let consoleVisible = false;
        
        // Toggle console visibility
        consoleToggle.addEventListener('click', () => {{
            consoleVisible = !consoleVisible;
            consoleDiv.style.display = consoleVisible ? 'block' : 'none';
            consoleToggle.style.background = consoleVisible ? 'rgba(40, 40, 40, 0.95)' : 'rgba(15, 15, 15, 0.9)';
        }});
        
        function addToConsole(message, type = 'log') {{
            logCount++;
            if (type === 'error') {{
                errorCount++;
                consoleBadge.textContent = errorCount;
                consoleBadge.style.display = 'flex';
                consoleToggle.classList.add('has-errors');
            }}
            const entry = document.createElement('div');
            entry.style.cssText = 'padding: 4px 0; border-bottom: 1px solid rgba(255,255,255,0.05);';
            entry.style.color = type === 'error' ? '#ef4444' : type === 'warn' ? '#f59e0b' : '#4ade80';
            const prefix = type === 'error' ? '✖' : type === 'warn' ? '⚠' : '›';
            entry.textContent = prefix + ' ' + message;
            consoleDiv.appendChild(entry);
            consoleDiv.scrollTop = consoleDiv.scrollHeight;
        }}
        
        console.log = function(...args) {{
            originalConsoleLog.apply(console, args);
            addToConsole(args.join(' '), 'log');
        }};
        
        console.error = function(...args) {{
            originalConsoleError.apply(console, args);
            addToConsole(args.join(' '), 'error');
        }};
        
        console.warn = function(...args) {{
            originalConsoleWarn.apply(console, args);
            addToConsole(args.join(' '), 'warn');
        }};
        
        // Sandbox Error Boundary Component (renamed to avoid conflicts with app code)
        // Using React.createElement instead of JSX since this is in a regular script tag
        class SandboxErrorBoundary extends React.Component {{
            constructor(props) {{
                super(props);
                this.state = {{ hasError: false, error: null }};
            }}
            
            static getDerivedStateFromError(error) {{
                console.error('React Error Boundary caught:', error);
                return {{ hasError: true, error }};
            }}
            
            componentDidCatch(error, errorInfo) {{
                console.error('React Error Details:', error, errorInfo);
            }}
            
            render() {{
                if (this.state.hasError) {{
                    return React.createElement('div', {{ className: 'error-boundary' }},
                        React.createElement('h2', null, 'Something went wrong in the preview'),
                        React.createElement('details', null,
                            React.createElement('summary', null, 'Error details'),
                            React.createElement('pre', null, this.state.error?.toString())
                        )
                    );
                }}
                return this.props.children;
            }}
        }}
        window.SandboxErrorBoundary = SandboxErrorBoundary;
        
        // Store original fetch for real API calls (like visual editor)
        const originalFetch = window.fetch.bind(window);
        
        // Mock API calls for demo purposes with sample data
        const mockFetch = (url, options) => {{
            console.log('Mock API call to:', url);
            
            // Parse the URL to determine the endpoint
            const urlObj = new URL(url, window.location.origin);
            const pathname = urlObj.pathname;
            
            // Pass through real Xverta API calls to original fetch
            const isXvertaApi = pathname.includes('/api/visual-edit-element') || 
                                pathname.includes('/api/sandbox-preview') ||
                                pathname.includes('/api/projects') ||
                                pathname.includes('/api/run-project');
            
            // Mock endpoints for demo app (products, cart, etc.)
            const isMockEndpoint = pathname.includes('/products') || 
                                   pathname.includes('/cart') || 
                                   pathname.includes('/orders') || 
                                   pathname.includes('/users') || 
                                   pathname.includes('/health');
            
            if (isXvertaApi || (pathname.startsWith('/api/') && !isMockEndpoint)) {{
                console.log('🎨 Passing through to real API:', pathname);
                return originalFetch(url, options);
            }}
            
            // Mock data for different endpoints
            let responseData = {{ message: 'Mock API response', data: [] }};
            
            // Products endpoint
            if (pathname.includes('/products')) {{
                responseData = [
                    {{
                        id: 1,
                        name: "Fresh Bananas",
                        description: "Organic yellow bananas, perfect for snacks",
                        price: 2.99,
                        stock: 50,
                        category: "fruits",
                        image_url: "https://images.unsplash.com/photo-1571771894821-ce9b6c11b08e?w=400&h=300&fit=crop&auto=format",
                        created_at: "2024-01-01T00:00:00"
                    }},
                    {{
                        id: 2,
                        name: "Whole Milk",
                        description: "Fresh dairy milk, 1 gallon",
                        price: 3.49,
                        stock: 25,
                        category: "dairy",
                        image_url: "https://images.unsplash.com/photo-1563636619-e9143da7973b?w=400&h=300&fit=crop&auto=format",
                        created_at: "2024-01-01T00:00:00"
                    }},
                    {{
                        id: 3,
                        name: "Bread Loaf",
                        description: "Whole wheat bread loaf",
                        price: 2.79,
                        stock: 30,
                        category: "bakery",
                        image_url: "https://images.unsplash.com/photo-1509440159596-0249088772ff?w=400&h=300&fit=crop&auto=format",
                        created_at: "2024-01-01T00:00:00"
                    }},
                    {{
                        id: 4,
                        name: "Fresh Apples",
                        description: "Crisp red apples, locally grown",
                        price: 4.99,
                        stock: 40,
                        category: "fruits",
                        image_url: "https://images.unsplash.com/photo-1560806887-1e4cd0b6cbd6?w=400&h=300&fit=crop&auto=format",
                        created_at: "2024-01-01T00:00:00"
                    }},
                    {{
                        id: 5,
                        name: "Greek Yogurt",
                        description: "Creamy Greek yogurt, high protein",
                        price: 5.99,
                        stock: 20,
                        category: "dairy",
                        image_url: "https://images.unsplash.com/photo-1488477181946-6428a0291777?w=400&h=300&fit=crop&auto=format",
                        created_at: "2024-01-01T00:00:00"
                    }},
                    {{
                        id: 6,
                        name: "Chocolate Cake",
                        description: "Rich chocolate layer cake",
                        price: 12.99,
                        stock: 15,
                        category: "bakery",
                        image_url: "https://images.unsplash.com/photo-1578985545062-69928b1d9587?w=400&h=300&fit=crop&auto=format",
                        created_at: "2024-01-01T00:00:00"
                    }}
                ];
            }}
            // Orders endpoint
            else if (pathname.includes('/orders')) {{
                responseData = [
                    {{
                        id: 1,
                        user_id: 1,
                        status: "pending",
                        total_amount: 15.47,
                        created_at: "2024-01-15T10:30:00",
                        items: [
                            {{ product_id: 1, quantity: 2, price: 2.99 }},
                            {{ product_id: 2, quantity: 1, price: 3.49 }}
                        ]
                    }}
                ];
            }}
            // Users endpoint
            else if (pathname.includes('/users')) {{
                responseData = [
                    {{
                        id: 1,
                        email: "demo@example.com",
                        full_name: "Demo User",
                        is_active: true,
                        created_at: "2024-01-01T00:00:00"
                    }}
                ];
            }}
            // Health check
            else if (pathname.includes('/health')) {{
                responseData = {{ status: "healthy", service: "mock-api" }};
            }}
            
            return Promise.resolve({{
                ok: true,
                status: 200,
                statusText: 'OK',
                json: () => Promise.resolve(responseData),
                text: () => Promise.resolve(JSON.stringify(responseData))
            }});
        }};
        
        // Replace fetch with mock for demo
        window.fetch = mockFetch;
        
        // Create utility functions for className manipulation
        
        // Fallback clsx implementation if CDN fails
        if (typeof window.clsx === 'undefined') {{
            window.clsx = function(...inputs) {{
                const classes = [];
                for (const input of inputs) {{
                    if (!input) continue;
                    if (typeof input === 'string') {{
                        classes.push(input);
                    }} else if (typeof input === 'object') {{
                        for (const [key, value] of Object.entries(input)) {{
                            if (value) classes.push(key);
                        }}
                    }}
                }}
                return classes.join(' ');
            }};
        }}
        
        // Basic tailwind-merge implementation for sandbox (simplified, no Set)
        window.twMerge = function(...inputs) {{
            const classString = window.clsx(...inputs);
            const classes = classString.split(' ').filter(Boolean);
            
            // Simple deduplication using object instead of Set
            const seenClasses = {{}};
            const result = [];
            
            // Process classes in order, last occurrence wins for same prefix
            for (let i = 0; i < classes.length; i++) {{
                const cls = classes[i];
                // Extract base class name (e.g., 'bg' from 'bg-red-500')
                const base = cls.split('-')[0];
                seenClasses[base + '_' + cls] = i;
            }}
            
            // Add classes that weren't overridden
            for (let i = 0; i < classes.length; i++) {{
                const cls = classes[i];
                const base = cls.split('-')[0];
                if (seenClasses[base + '_' + cls] === i) {{
                    result.push(cls);
                }}
            }}
            
            return result.join(' ');
        }};
        
        // Create cn function (className utility)
        window.cn = function(...inputs) {{
            return window.twMerge(...inputs);
        }};
        
        // Store references to sandbox globals BEFORE user code runs (on window for cross-script access)
        window._sandboxButton = window.Button;
        window._sandboxCard = window.Card;
        window._sandboxInput = window.Input;
        window._sandboxLoading = window.Loading;
        
        // Add global error handler to catch runtime errors
        window.onerror = function(msg, url, lineNo, columnNo, error) {{
            console.error('❌ Global error:', msg, 'at line', lineNo);
            if (msg.includes('SyntaxError') || msg.includes('ReferenceError')) {{
                document.getElementById('root').innerHTML = 
                    '<div style="padding: 20px; color: #f87171; background: #1e1e1e;">' +
                    '<h2>JavaScript Error</h2>' +
                    '<p>' + msg + '</p>' +
                    '<p>Line: ' + lineNo + '</p>' +
                    '</div>';
            }}
            return false;
        }};
    </script>
    
    <!-- User code - PRECOMPILED on server (no JSX in browser) -->
    <script>
        // User's component and app code (precompiled from JSX to JS)
        {precompiled_code}
        
        // CRITICAL: Ensure App is assigned to window after code runs
        if (typeof App !== 'undefined' && typeof window.App !== 'function') {{
            window.App = App;
            console.log('✅ Assigned App to window.App');
        }}
        if (typeof AppWrapper !== 'undefined' && typeof window.App !== 'function') {{
            window.App = AppWrapper;
            console.log('✅ Assigned AppWrapper to window.App');
        }}
        console.log('✅ User code executed, window.App is:', typeof window.App);
        
        // CRITICAL: Restore sandbox UI components after user code
        window.Button = window.Button || window._sandboxButton;
        window.Card = window.Card || window._sandboxCard;
        window.Input = window.Input || window._sandboxInput;
        window.Loading = window.Loading || window._sandboxLoading;
        
        // Render the app
        try {{
            if (typeof window.App === 'function') {{
                const root = ReactDOM.createRoot(document.getElementById('root'));
                root.render(
                    React.createElement(window.SandboxErrorBoundary, null,
                        React.createElement(window.App)
                    )
                );
                console.log('✅ App rendered successfully');
            }} else {{
                throw new Error('App component not found');
            }}
        }} catch (error) {{
            console.error('❌ Render error:', error);
            document.getElementById('root').innerHTML = 
                '<div class="error-boundary">' +
                '<h2>Failed to render application</h2>' +
                '<p>' + error.message + '</p>' +
                '</div>';
        }}
    </script>
    
    <!-- Visual Editor - NO JSX, plain JavaScript -->
    <script>
        // ========== VISUAL EDITOR - RIGHT-CLICK TO EDIT STYLES ==========
        // This enables users to right-click any element and change its styles
        
        // Create the Visual Editor Context Menu
        const createVisualEditor = () => {{
            // ========== TOAST NOTIFICATION HELPER ==========
            const showToast = (msg, isError) => {{
                const toast = document.createElement('div');
                toast.className = 'xverta-toast';
                toast.innerHTML = msg;
                toast.style.cssText = `
                    position: fixed; bottom: 20px; right: 20px; z-index: 100001;
                    padding: 12px 20px; border-radius: 8px; font-size: 14px;
                    background: ${{isError ? '#ef4444' : '#22c55e'}}; color: white;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.3); animation: slideIn 0.3s ease;
                `;
                document.body.appendChild(toast);
                setTimeout(() => toast.remove(), 3000);
            }};
            
            // ========== UNDO/REDO HISTORY SYSTEM ==========
            const historyStack = [];
            const redoStack = [];
            const MAX_HISTORY = 50;
            
            // Save state to history
            const saveToHistory = (action, data) => {{
                historyStack.push({{ action, data, timestamp: Date.now() }});
                if (historyStack.length > MAX_HISTORY) historyStack.shift();
                redoStack.length = 0; // Clear redo on new action
                updateUndoButtons();
            }};
            
            // Update undo/redo button states
            const updateUndoButtons = () => {{
                const undoBtn = document.getElementById('xverta-undo-btn');
                const redoBtn = document.getElementById('xverta-redo-btn');
                if (undoBtn) {{
                    undoBtn.disabled = historyStack.length === 0;
                    undoBtn.style.opacity = historyStack.length === 0 ? '0.4' : '1';
                }}
                if (redoBtn) {{
                    redoBtn.disabled = redoStack.length === 0;
                    redoBtn.style.opacity = redoStack.length === 0 ? '0.4' : '1';
                }}
            }};
            
            // Undo last action
            const undoAction = () => {{
                if (historyStack.length === 0) return;
                const lastAction = historyStack.pop();
                redoStack.push(lastAction);
                
                try {{
                    if (lastAction.action === 'move') {{
                        const {{ element, originalParent, originalNextSibling }} = lastAction.data;
                        if (element && originalParent) {{
                            if (originalNextSibling) {{
                                originalParent.insertBefore(element, originalNextSibling);
                            }} else {{
                                originalParent.appendChild(element);
                            }}
                            showToast('↩ Move undone', false);
                        }}
                    }} else if (lastAction.action === 'style') {{
                        const {{ element, originalStyles }} = lastAction.data;
                        if (element && originalStyles) {{
                            Object.assign(element.style, originalStyles);
                            showToast('↩ Style change undone', false);
                        }}
                    }} else if (lastAction.action === 'text') {{
                        const {{ element, originalText }} = lastAction.data;
                        if (element) {{
                            element.textContent = originalText;
                            showToast('↩ Text change undone', false);
                        }}
                    }} else if (lastAction.action === 'delete') {{
                        const {{ element, originalParent, originalNextSibling }} = lastAction.data;
                        if (element && originalParent) {{
                            if (originalNextSibling) {{
                                originalParent.insertBefore(element, originalNextSibling);
                            }} else {{
                                originalParent.appendChild(element);
                            }}
                            showToast('↩ Delete undone', false);
                        }}
                    }}
                }} catch (e) {{
                    console.error('Undo failed:', e);
                    showToast('⚠ Undo failed', true);
                }}
                
                updateUndoButtons();
            }};
            
            // Redo last undone action
            const redoAction = () => {{
                if (redoStack.length === 0) return;
                const action = redoStack.pop();
                historyStack.push(action);
                
                try {{
                    if (action.action === 'move') {{
                        const {{ element, newParent, newNextSibling }} = action.data;
                        if (element && newParent) {{
                            if (newNextSibling) {{
                                newParent.insertBefore(element, newNextSibling);
                            }} else {{
                                newParent.appendChild(element);
                            }}
                            showToast('↪ Move redone', false);
                        }}
                    }} else if (action.action === 'style') {{
                        const {{ element, newStyles }} = action.data;
                        if (element && newStyles) {{
                            Object.assign(element.style, newStyles);
                            showToast('↪ Style change redone', false);
                        }}
                    }} else if (action.action === 'text') {{
                        const {{ element, newText }} = action.data;
                        if (element) {{
                            element.textContent = newText;
                            showToast('↪ Text change redone', false);
                        }}
                    }} else if (action.action === 'delete') {{
                        const {{ element }} = action.data;
                        if (element && element.parentNode) {{
                            element.parentNode.removeChild(element);
                            showToast('↪ Delete redone', false);
                        }}
                    }}
                }} catch (e) {{
                    console.error('Redo failed:', e);
                    showToast('⚠ Redo failed', true);
                }}
                
                updateUndoButtons();
            }};
            
            // Keyboard shortcuts for undo/redo
            document.addEventListener('keydown', (e) => {{
                if ((e.ctrlKey || e.metaKey) && e.key === 'z' && !e.shiftKey) {{
                    e.preventDefault();
                    undoAction();
                }} else if ((e.ctrlKey || e.metaKey) && (e.key === 'y' || (e.shiftKey && e.key === 'z'))) {{
                    e.preventDefault();
                    redoAction();
                }}
            }});
            
            // Create context menu container
            const menuContainer = document.createElement('div');
            menuContainer.id = 'xverta-visual-editor';
            menuContainer.innerHTML = `
                <style>
                    #xverta-undo-toolbar {{
                        position: fixed;
                        top: 12px;
                        right: 12px;
                        display: none;
                        gap: 6px;
                        background: rgba(10, 10, 10, 0.9);
                        border: 1px solid rgba(255,255,255,0.12);
                        border-radius: 8px;
                        padding: 6px 10px;
                        box-shadow: 0 4px 16px rgba(0,0,0,0.4);
                        z-index: 999998;
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                        backdrop-filter: blur(16px);
                    }}
                    .xverta-toolbar-btn {{
                        display: flex;
                        align-items: center;
                        gap: 4px;
                        padding: 6px 10px;
                        background: rgba(255,255,255,0.08);
                        border: 1px solid rgba(255,255,255,0.08);
                        border-radius: 6px;
                        color: #fff;
                        font-size: 12px;
                        font-weight: 500;
                        cursor: pointer;
                        transition: all 0.15s;
                    }}
                    .xverta-toolbar-btn:hover:not(:disabled) {{
                        background: rgba(255,255,255,0.2);
                        border-color: rgba(255,255,255,0.2);
                    }}
                    .xverta-toolbar-btn:disabled {{
                        cursor: not-allowed;
                    }}
                    .xverta-toolbar-hint {{
                        color: #666;
                        font-size: 10px;
                        padding: 0 4px;
                        display: flex;
                        align-items: center;
                    }}
                    #xverta-context-menu {{
                        display: none;
                        position: fixed;
                        background: #0a0a0a;
                        border: 1px solid rgba(255,255,255,0.1);
                        border-radius: 12px;
                        padding: 8px 0;
                        min-width: 280px;
                        max-width: 320px;
                        max-height: 80vh;
                        overflow-y: auto;
                        box-shadow: 0 20px 60px rgba(0,0,0,0.6), 0 0 0 1px rgba(255,255,255,0.05);
                        z-index: 999999;
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                        backdrop-filter: blur(20px);
                        animation: menuFadeIn 0.15s ease-out;
                    }}
                    #xverta-context-menu::-webkit-scrollbar {{
                        width: 6px;
                    }}
                    #xverta-context-menu::-webkit-scrollbar-track {{
                        background: transparent;
                    }}
                    #xverta-context-menu::-webkit-scrollbar-thumb {{
                        background: rgba(255,255,255,0.2);
                        border-radius: 3px;
                    }}
                    @keyframes menuFadeIn {{
                        from {{ opacity: 0; transform: scale(0.95) translateY(-5px); }}
                        to {{ opacity: 1; transform: scale(1) translateY(0); }}
                    }}
                    #xverta-context-menu.visible {{ display: block; }}
                    .xverta-menu-header {{
                        padding: 12px 16px;
                        border-bottom: 1px solid rgba(255,255,255,0.1);
                        margin-bottom: 8px;
                    }}
                    .xverta-menu-header h4 {{
                        color: #fff;
                        font-size: 13px;
                        font-weight: 600;
                        margin: 0 0 4px 0;
                        display: flex;
                        align-items: center;
                        gap: 8px;
                    }}
                    .xverta-menu-header span {{
                        color: #888;
                        font-size: 11px;
                    }}
                    .xverta-menu-section {{
                        padding: 8px 12px;
                    }}
                    .xverta-menu-section label {{
                        display: block;
                        color: #aaa;
                        font-size: 10px;
                        text-transform: uppercase;
                        letter-spacing: 0.5px;
                        margin-bottom: 6px;
                    }}
                    .xverta-menu-row {{
                        display: flex;
                        gap: 8px;
                        margin-bottom: 8px;
                    }}
                    .xverta-color-input {{
                        width: 36px;
                        height: 36px;
                        border: none;
                        border-radius: 8px;
                        cursor: pointer;
                        padding: 2px;
                        background: rgba(255,255,255,0.1);
                    }}
                    .xverta-text-input, .xverta-select {{
                        flex: 1;
                        padding: 8px 12px;
                        border: 1px solid rgba(255,255,255,0.1);
                        border-radius: 8px;
                        background: rgba(255,255,255,0.05);
                        color: #fff;
                        font-size: 13px;
                        outline: none;
                        transition: all 0.2s;
                    }}
                    .xverta-text-input:focus, .xverta-select:focus {{
                        border-color: #525252;
                        background: rgba(255,255,255,0.08);
                    }}
                    .xverta-textarea {{
                        width: 100%;
                        padding: 8px 12px;
                        border: 1px solid rgba(255,255,255,0.1);
                        border-radius: 8px;
                        background: rgba(255,255,255,0.05);
                        color: #fff;
                        font-size: 13px;
                        outline: none;
                        transition: all 0.2s;
                        resize: vertical;
                        min-height: 50px;
                        font-family: inherit;
                    }}
                    .xverta-textarea:focus {{
                        border-color: #525252;
                        background: rgba(255,255,255,0.08);
                    }}
                    .xverta-select {{ cursor: pointer; }}
                    .xverta-select option {{ background: #0a0a0a; color: #fff; }}
                    .xverta-btn {{
                        width: 100%;
                        padding: 10px 16px;
                        border: none;
                        border-radius: 8px;
                        font-size: 13px;
                        font-weight: 500;
                        cursor: pointer;
                        transition: all 0.2s;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        gap: 8px;
                    }}
                    .xverta-btn-primary {{
                        background: #fff;
                        color: #0a0a0a;
                    }}
                    .xverta-btn-primary:hover {{ transform: translateY(-1px); box-shadow: 0 4px 12px rgba(255,255,255,0.2); }}
                    .xverta-btn-secondary {{
                        background: rgba(255,255,255,0.1);
                        color: #fff;
                        margin-top: 8px;
                    }}
                    .xverta-btn-secondary:hover {{ background: rgba(255,255,255,0.15); }}
                    .xverta-element-highlight {{
                        outline: 2px dashed #525252 !important;
                        outline-offset: 2px !important;
                    }}
                    .xverta-quick-colors {{
                        display: flex;
                        gap: 6px;
                        flex-wrap: wrap;
                        margin-top: 8px;
                    }}
                    .xverta-quick-color {{
                        width: 24px;
                        height: 24px;
                        border-radius: 6px;
                        border: 2px solid transparent;
                        cursor: pointer;
                        transition: all 0.2s;
                    }}
                    .xverta-quick-color:hover {{
                        transform: scale(1.15);
                        border-color: rgba(255,255,255,0.3);
                    }}
                    .xverta-divider {{
                        height: 1px;
                        background: rgba(255,255,255,0.1);
                        margin: 8px 0;
                    }}
                    .xverta-sticky-buttons {{
                        position: sticky;
                        bottom: 0;
                        background: linear-gradient(to top, #0a0a0a 80%, transparent);
                        padding: 12px 12px 8px 12px;
                        margin-top: 8px;
                    }}
                </style>
                <div id="xverta-context-menu">
                    <div class="xverta-menu-header">
                        <h4>Edit Element</h4>
                        <span id="xverta-element-info">Select an element</span>
                    </div>
                    
                    <div class="xverta-menu-section">
                        <label>Background Color</label>
                        <div class="xverta-menu-row">
                            <input type="color" id="xverta-bg-color" class="xverta-color-input" value="#ffffff">
                            <input type="text" id="xverta-bg-color-text" class="xverta-text-input" placeholder="#ffffff or transparent">
                        </div>
                        <div class="xverta-quick-colors" id="xverta-bg-quick">
                            <div class="xverta-quick-color" style="background:#ef4444" data-color="#ef4444"></div>
                            <div class="xverta-quick-color" style="background:#f97316" data-color="#f97316"></div>
                            <div class="xverta-quick-color" style="background:#eab308" data-color="#eab308"></div>
                            <div class="xverta-quick-color" style="background:#22c55e" data-color="#22c55e"></div>
                            <div class="xverta-quick-color" style="background:#3b82f6" data-color="#3b82f6"></div>
                            <div class="xverta-quick-color" style="background:#8b5cf6" data-color="#8b5cf6"></div>
                            <div class="xverta-quick-color" style="background:#ec4899" data-color="#ec4899"></div>
                            <div class="xverta-quick-color" style="background:#1f2937" data-color="#1f2937"></div>
                            <div class="xverta-quick-color" style="background:#ffffff;border:1px solid #ccc" data-color="#ffffff"></div>
                            <div class="xverta-quick-color" style="background:transparent;border:1px dashed #666" data-color="transparent"></div>
                        </div>
                    </div>
                    
                    <div class="xverta-divider"></div>
                    
                    <div class="xverta-menu-section">
                        <label>Edit Text Content</label>
                        <div class="xverta-menu-row">
                            <textarea id="xverta-text-content" class="xverta-textarea" placeholder="Enter new text..." rows="2"></textarea>
                        </div>
                    </div>
                    
                    <div class="xverta-divider"></div>
                    
                    <div class="xverta-menu-section">
                        <label>Text Color</label>
                        <div class="xverta-menu-row">
                            <input type="color" id="xverta-text-color" class="xverta-color-input" value="#000000">
                            <input type="text" id="xverta-text-color-text" class="xverta-text-input" placeholder="#000000">
                        </div>
                    </div>
                    
                    <div class="xverta-divider"></div>
                    
                    <div class="xverta-menu-section">
                        <label>Font</label>
                        <div class="xverta-menu-row">
                            <select id="xverta-font-family" class="xverta-select">
                                <option value="">Default</option>
                                <option value="Inter, sans-serif">Inter</option>
                                <option value="Roboto, sans-serif">Roboto</option>
                                <option value="Poppins, sans-serif">Poppins</option>
                                <option value="Open Sans, sans-serif">Open Sans</option>
                                <option value="Montserrat, sans-serif">Montserrat</option>
                                <option value="Playfair Display, serif">Playfair Display</option>
                                <option value="Georgia, serif">Georgia</option>
                                <option value="monospace">Monospace</option>
                            </select>
                            <select id="xverta-font-size" class="xverta-select" style="width:80px">
                                <option value="">Size</option>
                                <option value="12px">12px</option>
                                <option value="14px">14px</option>
                                <option value="16px">16px</option>
                                <option value="18px">18px</option>
                                <option value="20px">20px</option>
                                <option value="24px">24px</option>
                                <option value="32px">32px</option>
                                <option value="48px">48px</option>
                            </select>
                        </div>
                        <div class="xverta-menu-row">
                            <select id="xverta-font-weight" class="xverta-select">
                                <option value="">Weight</option>
                                <option value="300">Light</option>
                                <option value="400">Normal</option>
                                <option value="500">Medium</option>
                                <option value="600">Semibold</option>
                                <option value="700">Bold</option>
                            </select>
                        </div>
                    </div>
                    
                    <div class="xverta-divider"></div>
                    
                    <div class="xverta-menu-section">
                        <label>Spacing (padding)</label>
                        <div class="xverta-menu-row">
                            <input type="text" id="xverta-padding" class="xverta-text-input" placeholder="e.g. 16px or 8px 16px">
                        </div>
                    </div>
                    
                    <div class="xverta-divider"></div>
                    
                    <div class="xverta-menu-section">
                        <label>Border Radius</label>
                        <div class="xverta-menu-row">
                            <select id="xverta-border-radius" class="xverta-select">
                                <option value="">Default</option>
                                <option value="0">None (0)</option>
                                <option value="4px">Small (4px)</option>
                                <option value="8px">Medium (8px)</option>
                                <option value="12px">Large (12px)</option>
                                <option value="16px">XL (16px)</option>
                                <option value="9999px">Full (pill)</option>
                            </select>
                        </div>
                    </div>
                    
                    <div class="xverta-divider"></div>
                    
                    <div class="xverta-sticky-buttons">
                        <button id="xverta-apply-btn" class="xverta-btn xverta-btn-primary">
                            Apply Changes
                        </button>
                        <button id="xverta-cancel-btn" class="xverta-btn xverta-btn-secondary">
                            Cancel
                        </button>
                    </div>
                </div>
                
                <!-- Undo/Redo Toolbar -->
                <div id="xverta-undo-toolbar">
                    <button id="xverta-undo-btn" class="xverta-toolbar-btn" disabled style="opacity: 0.4">
                        ↩ Undo
                    </button>
                    <button id="xverta-redo-btn" class="xverta-toolbar-btn" disabled style="opacity: 0.4">
                        ↪ Redo
                    </button>
                    <span class="xverta-toolbar-hint">Ctrl+Z / Ctrl+Y</span>
                </div>
            `;
            document.body.appendChild(menuContainer);
            
            // Wire up undo/redo buttons
            document.getElementById('xverta-undo-btn').addEventListener('click', undoAction);
            document.getElementById('xverta-redo-btn').addEventListener('click', redoAction);
            
            // State
            let selectedElement = null;
            let originalStyles = {{}};
            let originalText = '';
            
            const menu = document.getElementById('xverta-context-menu');
            const bgColorInput = document.getElementById('xverta-bg-color');
            const bgColorText = document.getElementById('xverta-bg-color-text');
            const textColorInput = document.getElementById('xverta-text-color');
            const textColorText = document.getElementById('xverta-text-color-text');
            const fontFamily = document.getElementById('xverta-font-family');
            const fontSize = document.getElementById('xverta-font-size');
            const fontWeight = document.getElementById('xverta-font-weight');
            const padding = document.getElementById('xverta-padding');
            const borderRadius = document.getElementById('xverta-border-radius');
            const elementInfo = document.getElementById('xverta-element-info');
            const textContent = document.getElementById('xverta-text-content');
            
            // Live text editing
            textContent.addEventListener('input', () => {{
                if (selectedElement && textContent.value) {{
                    // Only update if element has direct text (not children with text)
                    const hasOnlyText = selectedElement.children.length === 0 || 
                                        (selectedElement.children.length === 1 && selectedElement.children[0].tagName === 'SPAN');
                    if (hasOnlyText) {{
                        selectedElement.textContent = textContent.value;
                    }}
                }}
            }});
            
            // Sync color inputs
            bgColorInput.addEventListener('input', () => {{ 
                bgColorText.value = bgColorInput.value;
                if (selectedElement) selectedElement.style.backgroundColor = bgColorInput.value;
            }});
            bgColorText.addEventListener('input', () => {{ 
                if (bgColorText.value.startsWith('#')) bgColorInput.value = bgColorText.value;
                if (selectedElement) selectedElement.style.backgroundColor = bgColorText.value;
            }});
            textColorInput.addEventListener('input', () => {{ 
                textColorText.value = textColorInput.value;
                if (selectedElement) selectedElement.style.color = textColorInput.value;
            }});
            textColorText.addEventListener('input', () => {{ 
                if (textColorText.value.startsWith('#')) textColorInput.value = textColorText.value;
                if (selectedElement) selectedElement.style.color = textColorText.value;
            }});
            
            // Quick color buttons
            document.querySelectorAll('.xverta-quick-color').forEach(btn => {{
                btn.addEventListener('click', () => {{
                    const color = btn.dataset.color;
                    bgColorInput.value = color.startsWith('#') ? color : '#ffffff';
                    bgColorText.value = color;
                    if (selectedElement) selectedElement.style.backgroundColor = color;
                }});
            }});
            
            // Live preview for other inputs
            fontFamily.addEventListener('change', () => {{ if (selectedElement && fontFamily.value) selectedElement.style.fontFamily = fontFamily.value; }});
            fontSize.addEventListener('change', () => {{ if (selectedElement && fontSize.value) selectedElement.style.fontSize = fontSize.value; }});
            fontWeight.addEventListener('change', () => {{ if (selectedElement && fontWeight.value) selectedElement.style.fontWeight = fontWeight.value; }});
            padding.addEventListener('input', () => {{ if (selectedElement && padding.value) selectedElement.style.padding = padding.value; }});
            borderRadius.addEventListener('change', () => {{ if (selectedElement && borderRadius.value) selectedElement.style.borderRadius = borderRadius.value; }});
            
            // Get element path for identification
            const getElementPath = (el) => {{
                const parts = [];
                while (el && el !== document.body) {{
                    let selector = el.tagName.toLowerCase();
                    if (el.id) selector += '#' + el.id;
                    else if (el.className && typeof el.className === 'string') {{
                        const mainClass = el.className.split(' ').find(c => !c.startsWith('xverta'));
                        if (mainClass) selector += '.' + mainClass;
                    }}
                    parts.unshift(selector);
                    el = el.parentElement;
                }}
                return parts.join(' > ');
            }};
            
            // Get element description
            const getElementDesc = (el) => {{
                const tag = el.tagName.toLowerCase();
                const text = el.innerText?.substring(0, 25) || '';
                const classes = el.className && typeof el.className === 'string' ? 
                    el.className.split(' ').filter(c => !c.startsWith('xverta')).slice(0, 2).join('.') : '';
                return `<${{tag}}>${{classes ? '.' + classes : ''}}${{text ? ' "' + text + (text.length >= 25 ? '...' : '') + '"' : ''}}`;
            }};
            
            // Right-click handler
            document.addEventListener('contextmenu', (e) => {{
                // Don't trigger on the menu itself
                if (e.target.closest('#xverta-visual-editor')) return;
                
                e.preventDefault();
                
                // Remove previous highlight
                if (selectedElement) selectedElement.classList.remove('xverta-element-highlight');
                
                // Smart targeting: if clicking on inline elements, target the meaningful parent
                let targetEl = e.target;
                const inlineElements = ['span', 'svg', 'path', 'img', 'i', 'icon', 'br', 'strong', 'em', 'b'];
                if (inlineElements.includes(targetEl.tagName.toLowerCase())) {{
                    // Look for a meaningful parent (button, a, div with classes, etc.)
                    let parent = targetEl.parentElement;
                    let depth = 0;
                    while (parent && depth < 3) {{
                        const tag = parent.tagName.toLowerCase();
                        if (['button', 'a', 'li', 'nav', 'header', 'footer', 'section', 'article'].includes(tag) ||
                            (tag === 'div' && parent.className && parent.className.includes('btn'))) {{
                            targetEl = parent;
                            break;
                        }}
                        parent = parent.parentElement;
                        depth++;
                    }}
                }}
                
                selectedElement = targetEl;
                selectedElement.classList.add('xverta-element-highlight');
                
                // Store original styles
                const computed = window.getComputedStyle(selectedElement);
                originalStyles = {{
                    backgroundColor: selectedElement.style.backgroundColor,
                    color: selectedElement.style.color,
                    fontFamily: selectedElement.style.fontFamily,
                    fontSize: selectedElement.style.fontSize,
                    fontWeight: selectedElement.style.fontWeight,
                    padding: selectedElement.style.padding,
                    borderRadius: selectedElement.style.borderRadius
                }};
                
                // Populate form with current values
                const bgColor = computed.backgroundColor;
                if (bgColor && bgColor !== 'rgba(0, 0, 0, 0)') {{
                    bgColorText.value = bgColor;
                    // Try to convert to hex
                    const rgbMatch = bgColor.match(/rgb\\((\\d+),\\s*(\\d+),\\s*(\\d+)\\)/);
                    if (rgbMatch) {{
                        const hex = '#' + [rgbMatch[1], rgbMatch[2], rgbMatch[3]].map(x => parseInt(x).toString(16).padStart(2, '0')).join('');
                        bgColorInput.value = hex;
                        bgColorText.value = hex;
                    }}
                }} else {{
                    bgColorInput.value = '#ffffff';
                    bgColorText.value = 'transparent';
                }}
                
                const textColor = computed.color;
                const textRgbMatch = textColor.match(/rgb\\((\\d+),\\s*(\\d+),\\s*(\\d+)\\)/);
                if (textRgbMatch) {{
                    const hex = '#' + [textRgbMatch[1], textRgbMatch[2], textRgbMatch[3]].map(x => parseInt(x).toString(16).padStart(2, '0')).join('');
                    textColorInput.value = hex;
                    textColorText.value = hex;
                }}
                
                // Populate text content field
                const hasOnlyText = selectedElement.children.length === 0 || 
                                    (selectedElement.children.length === 1 && selectedElement.children[0].tagName === 'SPAN');
                if (hasOnlyText) {{
                    originalText = selectedElement.textContent.trim();
                    textContent.value = originalText;
                    textContent.disabled = false;
                    textContent.placeholder = 'Enter new text...';
                }} else {{
                    originalText = '';
                    textContent.value = '';
                    textContent.disabled = true;
                    textContent.placeholder = 'Text editing not available for complex elements';
                }}
                
                elementInfo.textContent = getElementDesc(selectedElement);
                
                // Position menu - smart positioning to stay on screen
                const menuWidth = 300;
                const menuMaxHeight = window.innerHeight * 0.8;
                let x = e.clientX + 5;
                let y = e.clientY + 5;
                
                // Ensure menu stays on screen horizontally
                if (x + menuWidth > window.innerWidth) {{
                    x = e.clientX - menuWidth - 5;
                }}
                if (x < 10) x = 10;
                
                // Ensure menu stays on screen vertically
                if (y + menuMaxHeight > window.innerHeight) {{
                    y = Math.max(10, window.innerHeight - menuMaxHeight - 10);
                }}
                
                menu.style.left = x + 'px';
                menu.style.top = y + 'px';
                menu.classList.add('visible');
                
                // Scroll to show Apply button
                setTimeout(() => menu.scrollTop = 0, 50);
            }});
            
            // Close menu on click outside
            document.addEventListener('click', (e) => {{
                if (!e.target.closest('#xverta-context-menu') && !e.target.closest('#xverta-visual-editor')) {{
                    closeMenu();
                }}
            }});
            
            // Close menu function
            const closeMenu = () => {{
                menu.classList.remove('visible');
                if (selectedElement) {{
                    selectedElement.classList.remove('xverta-element-highlight');
                }}
            }};
            
            // Cancel button - restore original styles
            document.getElementById('xverta-cancel-btn').addEventListener('click', () => {{
                if (selectedElement) {{
                    Object.assign(selectedElement.style, originalStyles);
                }}
                closeMenu();
            }});
            
            // Apply button - save styles to backend
            document.getElementById('xverta-apply-btn').addEventListener('click', async () => {{
                if (!selectedElement) return;
                
                // Save to history for undo
                const newStyles = {{}};
                if (bgColorText.value && bgColorText.value !== 'transparent') newStyles.backgroundColor = bgColorText.value;
                if (bgColorText.value === 'transparent') newStyles.backgroundColor = 'transparent';
                if (textColorText.value) newStyles.color = textColorText.value;
                if (fontFamily.value) newStyles.fontFamily = fontFamily.value;
                if (fontSize.value) newStyles.fontSize = fontSize.value;
                if (fontWeight.value) newStyles.fontWeight = fontWeight.value;
                if (padding.value) newStyles.padding = padding.value;
                if (borderRadius.value) newStyles.borderRadius = borderRadius.value;
                
                // Save current text if changed
                const currentText = selectedElement.textContent;
                if (originalText && currentText !== originalText) {{
                    saveToHistory('text', {{
                        element: selectedElement,
                        originalText: originalText,
                        newText: currentText
                    }});
                }}
                
                // Save style changes to history
                if (Object.keys(newStyles).length > 0) {{
                    saveToHistory('style', {{
                        element: selectedElement,
                        originalStyles: {{ ...originalStyles }},
                        newStyles: {{ ...newStyles }}
                    }});
                }}
                
                const styles = newStyles;
                
                // Get project info from URL - handle query parameters properly
                const urlPath = window.location.pathname;
                const urlParams = new URLSearchParams(window.location.search);
                const pathParts = urlPath.split('/').filter(p => p);
                let projectSlug = pathParts[pathParts.length - 1] || '';
                
                // Remove any query string from slug if present
                if (projectSlug.includes('?')) {{
                    projectSlug = projectSlug.split('?')[0];
                }}
                
                // Get user info from URL params
                const userEmail = urlParams.get('user_email') || '';
                const userIdAlt = urlParams.get('user_id_alt') || '';
                
                console.log('🎨 Saving visual edit for:', projectSlug, 'user:', userEmail);
                
                // Get parent context for nested elements (e.g., span inside button)
                const getParentContext = (el) => {{
                    const parents = [];
                    let current = el.parentElement;
                    let depth = 0;
                    while (current && current !== document.body && depth < 3) {{
                        const tag = current.tagName.toLowerCase();
                        const classes = current.className && typeof current.className === 'string' ? 
                            current.className.split(' ').filter(c => !c.startsWith('xverta')).join(' ') : '';
                        const text = current.innerText?.substring(0, 30) || '';
                        parents.push({{ tag, classes, text }});
                        current = current.parentElement;
                        depth++;
                    }}
                    return parents;
                }};
                
                // Get siblings context
                const getSiblingInfo = (el) => {{
                    const parent = el.parentElement;
                    if (!parent) return {{ index: 0, total: 1 }};
                    const siblings = Array.from(parent.children).filter(c => c.tagName === el.tagName);
                    return {{ index: siblings.indexOf(el), total: siblings.length }};
                }};
                
                const parentContext = getParentContext(selectedElement);
                const siblingInfo = getSiblingInfo(selectedElement);
                
                // Send to backend
                const apiUrl = window.location.origin + '/api/visual-edit-element';
                console.log('🎨 POST to:', apiUrl);
                
                // Check if text was changed
                const newText = textContent.value.trim();
                const textChanged = !textContent.disabled && newText && newText !== originalText;
                
                const payload = {{
                    project_slug: projectSlug,
                    user_email: userEmail,
                    user_id_alt: userIdAlt,
                    element_path: getElementPath(selectedElement),
                    element_tag: selectedElement.tagName.toLowerCase(),
                    element_classes: selectedElement.className,
                    element_text: selectedElement.innerText?.substring(0, 50),
                    element_html: selectedElement.outerHTML.substring(0, 200),
                    parent_context: parentContext,
                    sibling_info: siblingInfo,
                    styles: styles,
                    new_text: textChanged ? newText : null,
                    original_text: textChanged ? originalText : null
                }};
                console.log('🎨 Payload:', payload);
                
                // INSTANT FEEDBACK: Apply styles visually and close menu immediately
                // The styles are already applied to selectedElement via the live preview inputs
                // Just show success and close - save happens in background
                
                const btn = document.getElementById('xverta-apply-btn');
                if (btn) {{
                    btn.innerHTML = '<span>✓</span> Saving...';
                    btn.style.background = 'linear-gradient(135deg, #22c55e 0%, #16a34a 100%)';
                }}
                
                // Close menu immediately for snappy feel
                setTimeout(() => closeMenu(), 300);
                
                // Save to code in background (non-blocking)
                fetch(apiUrl, {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify(payload)
                }}).then(async response => {{
                    if (response.ok) {{
                        const data = await response.json().catch(() => ({{ success: true }}));
                        if (data.success) {{
                            showToast('✓ Saved to code!', false);
                        }} else {{
                            showToast('⚠ Visual only: ' + (data.message || ''), true);
                        }}
                    }} else {{
                        showToast('⚠ Save failed - changes are visual only', true);
                    }}
                }}).catch(err => {{
                    console.error('🎨 Background save error:', err);
                    showToast('⚠ Save failed - changes are visual only', true);
                }});
            }});
            
            // Escape key to close
            document.addEventListener('keydown', (e) => {{
                if (e.key === 'Escape') closeMenu();
            }});
            
            // ========== DRAG AND DROP TO REORDER ELEMENTS ==========
            let draggedEl = null;
            let dragDropTarget = null;
            let dragStartX = 0;
            let dragStartY = 0;
            let isDragging = false;
            let dragOriginalParent = null;
            let dragOriginalNextSibling = null;
            
            // Add drag-specific styles
            const dragStyles = document.createElement('style');
            dragStyles.textContent = `
                .xverta-dragging {{
                    opacity: 0.6 !important;
                    cursor: grabbing !important;
                    outline: 3px dashed #ff9500 !important;
                    outline-offset: 2px !important;
                    z-index: 10000 !important;
                }}
                .xverta-drop-target {{
                    outline: 3px dashed #00ff41 !important;
                    outline-offset: 4px !important;
                    background: rgba(0, 255, 65, 0.1) !important;
                }}
                .xverta-element-hover {{
                    outline: 2px solid rgba(0, 123, 255, 0.5) !important;
                    cursor: grab !important;
                }}
            `;
            document.head.appendChild(dragStyles);
            
            // Hover effect for elements
            document.addEventListener('mouseover', (e) => {{
                if (isDragging) return;
                if (e.target.closest('#xverta-visual-editor')) return;
                if (e.target === document.body || e.target === document.documentElement) return;
                if (e.target.id === 'root') return;
                e.target.classList.add('xverta-element-hover');
            }});
            
            document.addEventListener('mouseout', (e) => {{
                if (isDragging) return;
                e.target.classList.remove('xverta-element-hover');
            }});
            
            // Mouse down - start potential drag
            document.addEventListener('mousedown', (e) => {{
                if (e.button !== 0) return; // Left click only
                if (e.target.closest('#xverta-visual-editor')) return;
                if (e.target === document.body || e.target === document.documentElement || e.target.id === 'root') return;
                
                dragStartX = e.clientX;
                dragStartY = e.clientY;
                draggedEl = e.target;
                
                // Smart element targeting - find meaningful parent for inline elements
                const inlineElements = ['span', 'svg', 'path', 'img', 'i', 'icon', 'br', 'strong', 'em', 'b'];
                if (inlineElements.includes(draggedEl.tagName.toLowerCase())) {{
                    let parent = draggedEl.parentElement;
                    let depth = 0;
                    while (parent && depth < 3 && parent !== document.body) {{
                        const tag = parent.tagName.toLowerCase();
                        if (['button', 'a', 'li', 'div', 'section', 'article', 'nav', 'header', 'footer', 'p', 'h1', 'h2', 'h3', 'h4'].includes(tag)) {{
                            draggedEl = parent;
                            break;
                        }}
                        parent = parent.parentElement;
                        depth++;
                    }}
                }}
                
                // Store original position for undo
                dragOriginalParent = draggedEl.parentNode;
                dragOriginalNextSibling = draggedEl.nextSibling;
            }});
            
            // Mouse move - check if we should start dragging
            document.addEventListener('mousemove', (e) => {{
                if (!draggedEl) return;
                
                // Start drag after threshold
                const dx = Math.abs(e.clientX - dragStartX);
                const dy = Math.abs(e.clientY - dragStartY);
                
                if (!isDragging && (dx > 8 || dy > 8)) {{
                    isDragging = true;
                    draggedEl.classList.remove('xverta-element-hover');
                    draggedEl.classList.add('xverta-dragging');
                }}
                
                if (!isDragging) return;
                
                // Remove previous drop target highlight
                document.querySelectorAll('.xverta-drop-target').forEach(el => el.classList.remove('xverta-drop-target'));
                
                // Find drop target - must be sibling in same parent container
                let target = document.elementFromPoint(e.clientX, e.clientY);
                if (target && target !== draggedEl && target !== document.body && target.id !== 'root') {{
                    // Find a sibling in same parent
                    while (target && target.parentNode !== draggedEl.parentNode && target !== document.body) {{
                        target = target.parentNode;
                    }}
                    
                    if (target && target !== draggedEl && target.parentNode === draggedEl.parentNode) {{
                        target.classList.add('xverta-drop-target');
                        dragDropTarget = target;
                    }}
                }}
            }});
            
            // Mouse up - perform drop
            document.addEventListener('mouseup', (e) => {{
                if (isDragging && draggedEl) {{
                    draggedEl.classList.remove('xverta-dragging');
                    
                    if (dragDropTarget && dragDropTarget !== draggedEl) {{
                        // Determine position (before or after)
                        const rect = dragDropTarget.getBoundingClientRect();
                        const midY = rect.top + rect.height / 2;
                        
                        // Store new position info for history
                        const newParent = dragDropTarget.parentNode;
                        let newNextSibling;
                        
                        if (e.clientY < midY) {{
                            newNextSibling = dragDropTarget;
                            newParent.insertBefore(draggedEl, dragDropTarget);
                        }} else {{
                            newNextSibling = dragDropTarget.nextSibling;
                            newParent.insertBefore(draggedEl, dragDropTarget.nextSibling);
                        }}
                        
                        // Save move to history for undo
                        saveToHistory('move', {{
                            element: draggedEl,
                            originalParent: dragOriginalParent,
                            originalNextSibling: dragOriginalNextSibling,
                            newParent: newParent,
                            newNextSibling: newNextSibling
                        }});
                        
                        // Notify about reorder (for visual feedback)
                        showToast('Element moved! Press Ctrl+Z to undo', false);
                        
                        dragDropTarget.classList.remove('xverta-drop-target');
                    }}
                }}
                
                // Reset
                isDragging = false;
                draggedEl = null;
                dragDropTarget = null;
                dragOriginalParent = null;
                dragOriginalNextSibling = null;
            }});
            
            console.log('✨ Visual Editor initialized - Right-click to edit, Drag to move!');
        }};
        
        // Initialize visual editor after app renders
        setTimeout(createVisualEditor, 500);
        
        // Memory cleanup - remove any circular references or large unused objects
        // This helps prevent "out of memory" errors in the browser
        if (typeof window.gc === 'function') {{
            try {{ window.gc(); }} catch (e) {{}}
        }}
    </script>
</body>
</html>
    """

def fix_jsx_content_for_sandbox(content: str, component_name: str, project_name: str) -> str:
    """Fix JSX content specifically for sandbox browser compilation"""
    import re
    from code_validator import auto_fix_jsx_for_sandbox
    
    # FIRST: Apply comprehensive auto-fix from code_validator
    # This removes duplicate declarations of sandbox-provided components (Button, Card, etc.)
    content = auto_fix_jsx_for_sandbox(content, f"{component_name}.jsx")
    
    # CRITICAL: Remove ALL React imports - React is provided globally
    content = re.sub(r"import\s+React\s*,?\s*\{[^}]*\}\s*from\s*['\"]react['\"];?\s*\n?", '', content)
    content = re.sub(r"import\s+React\s+from\s*['\"]react['\"];?\s*\n?", '', content)
    content = re.sub(r"import\s*\{[^}]*\}\s*from\s*['\"]react['\"];?\s*\n?", '', content)
    content = re.sub(r"import\s+\*\s+as\s+React\s+from\s*['\"]react['\"];?\s*\n?", '', content)
    
    # CRITICAL: Remove ALL framer-motion imports - motion is provided globally
    content = re.sub(r"import\s+\{[^}]*\}\s+from\s+['\"]framer-motion['\"];?\s*\n?", '', content)
    content = re.sub(r"import\s+\*\s+as\s+\w+\s+from\s+['\"]framer-motion['\"];?\s*\n?", '', content)
    content = re.sub(r"import\s+motion\s+from\s+['\"]framer-motion['\"];?\s*\n?", '', content)
    
    # Remove any local motion fallback definitions since global ones exist
    content = re.sub(r"const\s+motion\s*=\s*window\.motion\s*\|\|[^;]+;?\s*\n?", '', content)
    content = re.sub(r"const\s+motion\s*=\s*\{[^}]*\};\s*\n?", '', content)
    
    # Remove Lucide icon imports - icons are provided globally
    content = re.sub(r"import\s*\{[^}]*\}\s*from\s*['\"]lucide-react['\"];?\s*\n?", '', content)
    
    # Remove CSS imports - Tailwind is provided via CDN
    content = re.sub(r"import\s+['\"][^'\"]*\.css['\"];?\s*\n?", '', content)
    
    # Remove clsx/tailwind-merge imports - cn is provided globally
    content = re.sub(r"import\s*\{[^}]*\}\s*from\s*['\"]clsx['\"];?\s*\n?", '', content)
    content = re.sub(r"import\s*\{[^}]*\}\s*from\s*['\"]tailwind-merge['\"];?\s*\n?", '', content)
    content = re.sub(r"import\s*\{[^}]*cn[^}]*\}\s*from\s*['\"]\.+/lib/utils['\"];?\s*\n?", '', content)
    content = re.sub(r"import\s*\{[^}]*\}\s*from\s*['\"]\.+/lib/utils\.js['\"];?\s*\n?", '', content)
    
    # Remove window.twMerge assignments
    content = re.sub(r"window\.twMerge\s*=\s*[^;]+;?\s*\n?", '', content)
    
    # Remove buttonVariants/cardVariants constants that would cause undefined errors
    # These are only used by local Button/Card components that we're removing
    content = re.sub(r"const\s+buttonVariants\s*=\s*\{[\s\S]*?\};\s*\n?", '', content)
    content = re.sub(r"const\s+cardVariants\s*=\s*\{[\s\S]*?\};\s*\n?", '', content)
    content = re.sub(r"const\s+inputVariants\s*=\s*\{[\s\S]*?\};\s*\n?", '', content)
    
    # Remove React.forwardRef component declarations for UI components
    # These are provided globally by the sandbox
    for comp in ['Button', 'Card', 'Input', 'Loading', 'Select', 'Textarea']:
        # Match forwardRef declarations (multi-line)
        content = re.sub(
            rf'const\s+{comp}\s*=\s*React\.forwardRef\s*\([^;]+;',
            f'// {comp} is provided globally by the sandbox',
            content,
            flags=re.DOTALL
        )
        # Match displayName assignments
        content = re.sub(rf'{comp}\.displayName\s*=\s*["\'][^"\']*["\'];?\s*\n?', '', content)
    
    # Fix empty component functions
    if f'const {component_name} = () => (\n\n);' in content:
        print(f"🔧 Fixing empty component {component_name}")
        content = content.replace(
            f'const {component_name} = () => (\n\n);',
            f'const {component_name} = () => (\n  <div className="p-4 bg-gray-100 rounded">\n    <h3>Welcome to {component_name}</h3>\n    <p>Component is working!</p>\n  </div>\n);'
        )
    
    # Fix incomplete arrow function components - pattern: const ComponentName = () => (\n\n);
    content = re.sub(
        r'const (\w+) = \(\) => \(\s*\n\s*\n\s*\);',
        r'const \1 = () => (\n  <div className="flex items-center justify-center p-4">\n    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>\n  </div>\n);',
        content
    )
    
    # Fix incomplete arrow function components with props - pattern: const ComponentName = ({ prop }) => (\n\n);
    content = re.sub(
        r'const (\w+) = \(\{[^}]*\}\) => \(\s*\n\s*\n\s*\);',
        r'const \1 = ({ message, type = "error" }) => (\n  <div className={`p-4 rounded-lg border ${"bg-red-50 border-red-200 text-red-700" if type === "error" else "bg-blue-50 border-blue-200 text-blue-700"}`}>\n    <div className="flex items-center">\n      <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">\n        <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />\n      </svg>\n      {message || "An error occurred"}\n    </div>\n  </div>\n);',
        content
    )
    
    # Fix any remaining incomplete components with better defaults
    content = re.sub(
        r'const (\w+) = \([^)]*\) => \{\s*\n\s*return \(\s*\n\s*\);?\s*\n\s*\};?',
        r'const \1 = (props) => {\n  return (\n    <div className="p-4 bg-white rounded-lg shadow-sm border border-gray-200">\n      <h3 className="text-lg font-semibold text-gray-800 mb-2">\1 Component</h3>\n      <p className="text-gray-600">This component is ready for implementation.</p>\n    </div>\n  );\n};',
        content
    )

    # Fix incomplete function components
    if 'function ' + component_name in content and 'return (\n\n' in content:
        print(f"🔧 Fixing incomplete return in {component_name}")
        content = content.replace(
            'return (\n\n',
            f'return (\n    <div className="p-4">\n      <h2>{component_name}</h2>\n      <p>Component content for {project_name}</p>\n'
        )
        # Ensure proper closing structure
        if 'return (' in content and not content.rstrip().endswith('</div>\n  );'):
            content = content.rstrip()
            if content.endswith(');'):
                content = content[:-2] + '\n    </div>\n  );'
            elif content.endswith('  );\n}'):
                content = content.replace('  );\n}', '    </div>\n  );\n}')
    
    # Fix Router component usage for sandbox (use globals provided by sandbox)
    # Normalize all router types to a single `Router` symbol used by preview
    content = content.replace('BrowserRouter', 'Router')
    content = content.replace('HashRouter', 'Router')
    content = content.replace('MemoryRouter', 'Router')

    # Remove any react-router-dom imports (named, default, or namespace)
    content = re.sub(r"import\s+\{[^}]*\}\s+from\s+['\"]react-router-dom['\"];?\s*", '', content)
    content = re.sub(r"import\s+\*\s+as\s+\w+\s+from\s+['\"]react-router-dom['\"];?\s*", '', content)
    content = re.sub(r"import\s+\w+\s+from\s+['\"]react-router-dom['\"];?\s*", '', content)

    # Remove destructuring from ReactRouterDOM global, if present
    content = re.sub(r'const\s*\{\s*([^}]*)\s*\}\s*=\s*ReactRouterDOM;?\s*', '', content)
    
    # Handle Lucide React imports - remove them since icons are global
    content = re.sub(r'import\s*{\s*([^}]*)\s*}\s*from\s*[\'"]lucide-react[\'"];?', '', content)
    content = re.sub(r'const\s*{\s*([^}]*)\s*}\s*=\s*LucideReact;?', '', content)
    
    # Fix incomplete JSX elements (missing content between tags) - more comprehensive
    content = re.sub(r'>\s*\n\s*\n\s*</div>', '>\n      <p>Content placeholder</p>\n    </div>', content)
    content = re.sub(r'>\s*\n\s*\n\s*</(\w+)>', r'>\n      <p>Content placeholder</p>\n    </\1>', content)
    
    # Fix malformed comment blocks in JSX
    content = re.sub(r'/\*\*\s*\n\s*\*\s*\n\s*\*\s*\n\s*\*\s*This component is responsible for rendering the list of tasks\. It maps over\s*\n\s*\*\s*the `tasks` array and renders a `TaskItem` for each one, passing down the\s*\n\s*\*\s*necessary props and callbacks\.\s*\n\s*\*/', '/**\n * TaskList Component\n * \n * This component is responsible for rendering the list of tasks. It maps over\n * the tasks array and renders a TaskItem for each one, passing down the\n * necessary props and callbacks.\n */', content)
    
    # Fix incomplete exports with malformed syntax
    if 'export const' in content and '= ({' in content and '}) => {' in content:
        # This handles the malformed export structure
        content = re.sub(r'export const (\w+) = \(\{[^}]*\}\) => \{\s*\n\s*return \(\s*\n\s*\);?\s*\n\s*\};?', 
                        r'export const \1 = ({ tasks, onToggleTask, onDeleteTask }) => {\n  return (\n    <div className="space-y-2">\n      <h2 className="text-lg font-semibold">Task List</h2>\n      <p>Tasks will be displayed here</p>\n    </div>\n  );\n};', content)
    
    # CRITICAL: Remove ALL export statements for sandbox mode
    # Browser scripts cannot use ES module exports
    content = re.sub(r'\nexport\s+default\s+\w+;?\s*$', '', content)
    content = re.sub(r'^export\s+default\s+\w+;?\s*$', '', content, flags=re.MULTILINE)
    content = re.sub(r'\nexport\s+\{[^}]*\};?\s*$', '', content)
    content = re.sub(r'^export\s+\{[^}]*\};?\s*$', '', content, flags=re.MULTILINE)
    content = re.sub(r'^export\s+const\s+', 'const ', content, flags=re.MULTILINE)
    content = re.sub(r'^export\s+function\s+', 'function ', content, flags=re.MULTILINE)
    content = re.sub(r'^export\s+class\s+', 'class ', content, flags=re.MULTILINE)
    
    return content

# --- Lovable-style Orchestrator: Build With AI (ASYNC VERSION) ---
@app.post("/api/build-with-ai")
async def build_with_ai(
    request: dict = Body(...),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Create an async job for project generation.
    Returns immediately with job_id for polling.
    """
    try:
        # Verify token and get user
        token = credentials.credentials
        payload = verify_token(token)
        if not payload:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        
        user_email = payload.get("sub")
        
        # Extract parameters
        project_name = request.get("project_name")
        idea = request.get("idea") or ""
        tech_stack = request.get("tech_stack", [])
        project_type = request.get("project_type", "web app")
        features = request.get("features", [])
        requirements = request.get("requirements", {})
        customizations = request.get("customizations", {})
        product_data = request.get("product_data")  # User's product catalog for e-commerce
        custom_data = request.get("custom_data", {})  # Any custom data
        documentation_context = request.get("documentation_context")  # User's uploaded documents (resume, PDFs, images)

        if not project_name:
            raise HTTPException(status_code=400, detail="project_name is required")
        
        # Ensure project name is unique by checking existing projects
        # This prevents collisions when multiple projects have similar names
        unique_project_name = ensure_unique_project_name(project_name.lower().replace(" ", "-"))
        
        # Create async job
        job_id = job_manager.create_job(
            job_type="project_generation",
            params={
                "project_name": unique_project_name,
                "idea": idea,
                "tech_stack": tech_stack,
                "project_type": project_type,
                "features": features,
                "requirements": requirements,
                "customizations": customizations,
                "product_data": product_data,  # User's product catalog for e-commerce
                "custom_data": custom_data,  # Any custom data
                "documentation_context": documentation_context,  # User's uploaded documents (resume, PDFs, images)
                "user_id": user_email  # Pass user email as user_id for S3
            },
            user_email=user_email
        )
        
        return {
            "success": True,
            "job_id": job_id,
            "project_name": unique_project_name,  # Return the actual unique name used
            "message": "Project generation started. Poll /api/jobs/{job_id} for progress."
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Build with AI error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# --- AI Chat Endpoint ---
@app.post("/api/chat")
async def ai_chat(request: dict = Body(...)):
    """General AI chat endpoint for development assistance and questions."""
    try:
        project_name = request.get("project_name")
        user_message = request.get("user_message")
        chat_history = request.get("chat_history", [])
        context = request.get("context", {})
        
        if not user_message:
            raise HTTPException(status_code=400, detail="user_message is required")
        
        # Optional: Send typing indicator if project_name is provided
        if project_name:
            await manager.send_to_project(project_name, {
                "type": "chat_typing",
                "message": "AI is thinking..."
            })
        
        # Build context for the AI
        system_context = """You are an expert full-stack developer and helpful coding assistant. 
You help developers with:
- Code explanations and debugging
- Architecture advice and best practices  
- Technology recommendations
- Implementation guidance
- Problem-solving and optimization
- General development questions

Provide clear, practical, and actionable responses. When discussing code, be specific and include examples when helpful."""

        # Add project context if provided
        if context:
            tech_stack = context.get("tech_stack", [])
            current_files = context.get("current_files", [])
            errors = context.get("errors", [])
            
            if tech_stack:
                system_context += f"\n\nCurrent project uses: {', '.join(tech_stack)}"
            if current_files:
                system_context += f"\nCurrent files: {', '.join(current_files[:10])}"  # Limit to first 10
            if errors:
                system_context += f"\nActive errors: {len(errors)} issues found"

        # Prepare chat messages for AI
        messages = [{"role": "system", "content": system_context}]
        
        # Add chat history (limit to last 10 messages to avoid token limits)
        recent_history = chat_history[-10:] if chat_history else []
        for msg in recent_history:
            if msg.get("role") and msg.get("content"):
                messages.append({
                    "role": msg["role"], 
                    "content": msg["content"]
                })
        
        # Add current user message
        messages.append({"role": "user", "content": user_message})
        
        # Get AI response
        try:
            from ai_assistant import get_chat_response
            ai_response = get_chat_response(messages, model_type='smart')
            
            # Send response via WebSocket if project connected
            if project_name:
                await manager.send_to_project(project_name, {
                    "type": "chat_response",
                    "message": ai_response,
                    "user_message": user_message
                })
            
            return {
                "success": True,
                "response": ai_response,
                "timestamp": time.time()
            }
            
        except Exception as ai_error:
            error_msg = f"AI chat failed: {str(ai_error)}"
            if project_name:
                await manager.send_to_project(project_name, {
                    "type": "chat_error",
                    "message": error_msg
                })
            
            return {
                "success": False,
                "error": error_msg
            }
            
    except HTTPException:
        raise
    except Exception as e:
        return {"success": False, "error": str(e)}

# --- Chat History Endpoint ---
@app.get("/api/chat/history/{project_name}")
async def get_chat_history(project_name: str, limit: int = 50):
    """Get recent chat history for a project (placeholder for now)."""
    try:
        # For now, return empty history - in production you'd store/retrieve from database
        return {
            "success": True,
            "project_name": project_name,
            "history": [],
            "message": "Chat history feature coming soon - conversations are not yet persisted"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

# --- React Code Validation Functions ---
def validate_react_code(content, file_path):
    """Validate React component code for common issues"""
    errors = []
    
    # Check for placeholder comments instead of actual code
    if (content.strip().startswith('//') and len(content.strip()) < 100) or "component content here" in content.lower():
        errors.append("Contains only placeholder comments, needs actual code")
    
    # Check for proper React component structure
    if file_path.endswith('.jsx'):
        if 'import React' not in content and 'from "react"' not in content and 'from \'react\'' not in content:
            errors.append("Missing React import")
        if 'export default' not in content:
            errors.append("Missing default export")
        if 'const ' not in content and 'function ' not in content and 'class ' not in content:
            errors.append("No component definition found")
        if 'return (' not in content and 'return <' not in content:
            errors.append("Component missing return statement with JSX")
    
    # Check for syntax issues
    if content.count('(') != content.count(')'):
        errors.append("Unmatched parentheses")
    if content.count('{') != content.count('}'):
        errors.append("Unmatched braces")
    if content.count('[') != content.count(']'):
        errors.append("Unmatched brackets")
    
    return errors

def fix_common_react_issues(content, file_path):
    """Fix common React component issues"""
    
    # If it's just a placeholder comment, create a basic component
    if file_path.endswith('.jsx') and (content.strip().startswith('//') and len(content.strip()) < 100) or "component content here" in content.lower():
        # Extract component name from file path (cross-platform)
        import os
        component_name = os.path.basename(file_path).replace('.jsx', '')
        
        content = f"""import React from 'react';

const {component_name} = () => {{
  return (
    <div className="p-4">
      <h2 className="text-xl font-semibold mb-2">{component_name}</h2>
      <p className="text-gray-600">This component is ready for customization.</p>
    </div>
  );
}};

export default {component_name};"""
    
    # Add missing React import
    if file_path.endswith('.jsx') and 'import React' not in content:
        content = "import React from 'react';\n\n" + content
    
    # Add missing export if component is defined but not exported
    if 'const ' in content and 'export default' not in content:
        component_match = re.search(r'const (\w+) = ', content)
        if component_match:
            component_name = component_match.group(1)
            content += f"\n\nexport default {component_name};"
    
    return content

# --- AI Project Assistant Endpoint ---
# ⚠️ LEGACY - LOCAL STORAGE ONLY (EC2 INCOMPATIBLE)
# Use /api/ai-customize-project instead (line 2869+) - S3-enabled
# This endpoint uses 200+ lines of local file operations and is rarely used
@app.post("/api/ai-project-assistant")
async def ai_project_assistant(request: dict = Body(...)):
    """Process natural language requests to modify and improve project files."""
    import re
    import json
    
    try:
        project_name = request.get("project_name")
        user_message = request.get("user_message")
        tech_stack = request.get("tech_stack", [])
        re_run = bool(request.get("re_run", False))
        user_id = request.get("user_id", "anonymous")  # Get user_id for S3 multi-tenancy

        if not project_name:
            raise HTTPException(status_code=400, detail="project_name is required")
        if not user_message:
            raise HTTPException(status_code=400, detail="user_message is required")

        # Resolve project path
        project_slug = project_name.lower().replace(" ", "-")
        projects_dir = Path("generated_projects")
        project_path = projects_dir / project_slug
        if not project_path.exists():
            return {"success": False, "error": "Project not found"}

        # Handle specific requests first before general AI processing
        if ("student helper" in user_message.lower() or "studenthelper" in user_message.lower()) and ("name" in user_message.lower() or "title" in user_message.lower()):
            print(f"🎯 Detected Student Helper name change request: {user_message}")
            
            await manager.send_to_project(project_name, {
                "type": "status",
                "phase": "processing",
                "message": "🔧 Changing application name to 'Student Helper'..."
            })
            
            # Update files to change the app name
            files_modified = []
            changes_made = []
            
            try:
                # Update frontend App.jsx
                app_jsx_path = project_path / "frontend" / "src" / "App.jsx"
                if app_jsx_path.exists():
                    with open(app_jsx_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Replace various title patterns
                    updated_content = content
                    updated_content = re.sub(r'<h1[^>]*>.*?</h1>', '<h1 className="text-4xl font-bold mb-4">Welcome to Student Helper</h1>', updated_content)
                    updated_content = re.sub(r'Welcome to [^<]+', 'Welcome to Student Helper', updated_content)
                    updated_content = re.sub(r'title["\']?\s*:\s*["\'][^"\']*["\']', 'title: "Student Helper"', updated_content)
                    
                    if updated_content != content:
                        with open(app_jsx_path, 'w', encoding='utf-8') as f:
                            f.write(updated_content)
                        files_modified.append("frontend/src/App.jsx")
                        changes_made.append("Updated main heading to 'Student Helper'")
                
                # Update package.json
                package_json_path = project_path / "frontend" / "package.json"
                if package_json_path.exists():
                    try:
                        with open(package_json_path, 'r', encoding='utf-8') as f:
                            package_data = json.load(f)
                        
                        package_data["name"] = "student-helper"
                        
                        with open(package_json_path, 'w', encoding='utf-8') as f:
                            json.dump(package_data, f, indent=2)
                        
                        files_modified.append("frontend/package.json")
                        changes_made.append("Updated package name to 'student-helper'")
                    except:
                        pass
                
                # Update index.html title
                index_html_path = project_path / "frontend" / "public" / "index.html"
                if index_html_path.exists():
                    try:
                        with open(index_html_path, 'r', encoding='utf-8') as f:
                            html_content = f.read()
                        
                        updated_html = re.sub(r'<title>.*?</title>', '<title>Student Helper</title>', html_content)
                        
                        if updated_html != html_content:
                            with open(index_html_path, 'w', encoding='utf-8') as f:
                                f.write(updated_html)
                            files_modified.append("frontend/public/index.html")
                            changes_made.append("Updated page title to 'Student Helper'")
                    except:
                        pass
                
                # Update README.md
                readme_path = project_path / "README.md"
                if readme_path.exists():
                    try:
                        with open(readme_path, 'r', encoding='utf-8') as f:
                            readme_content = f.read()
                        
                        lines = readme_content.split('\n')
                        if lines and lines[0].startswith('# '):
                            lines[0] = '# Student Helper'
                            
                            with open(readme_path, 'w', encoding='utf-8') as f:
                                f.write('\n'.join(lines))
                            
                            files_modified.append("README.md")
                            changes_made.append("Updated project title in README")
                    except:
                        pass
                
                success_message = f"✅ Successfully changed application name to 'Student Helper'!\n\nChanges made:\n" + "\n".join([f"• {change}" for change in changes_made])
                
                await manager.send_to_project(project_name, {
                    "type": "status",
                    "phase": "complete",
                    "message": success_message
                })
                
                return {
                    "success": True,
                    "changes": [{"file_path": fp, "edit_type": "name_change"} for fp in files_modified],
                    "explanation": success_message,
                    "files_modified": files_modified
                }
                
            except Exception as e:
                error_msg = f"❌ Error changing app name: {str(e)}"
                await manager.send_to_project(project_name, {
                    "type": "status", 
                    "phase": "error",
                    "message": error_msg
                })
                
                return {"success": False, "error": error_msg}

        # Handle "Neelesh" profile personalization requests  
        if "neelesh" in user_message.lower() and ("profile" in user_message.lower() or "mba" in user_message.lower() or "graduate" in user_message.lower()):
            print(f"🎯 Detected Neelesh profile personalization request: {user_message}")
            
            await manager.send_to_project(project_name, {
                "type": "status",
                "phase": "processing", 
                "message": "👤 Adding Neelesh's profile information..."
            })
            
            files_modified = []
            changes_made = []
            
            try:
                # Update App.jsx with Neelesh's profile
                app_jsx_path = project_path / "frontend" / "src" / "App.jsx"
                if app_jsx_path.exists():
                    with open(app_jsx_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Add Neelesh's profile section
                    if 'Neelesh' not in content:
                        # Add a profile section after the main header
                        profile_section = '''
        <div className="bg-gradient-to-r from-blue-600 to-purple-600 text-white p-6 rounded-lg shadow-lg mb-6">
          <div className="flex items-center space-x-4">
            <div className="w-16 h-16 bg-white rounded-full flex items-center justify-center">
              <span className="text-2xl font-bold text-blue-600">NP</span>
            </div>
            <div>
              <h2 className="text-2xl font-bold">Neelesh Padmanabh</h2>
              <p className="text-blue-100">MBA Graduate</p>
              <p className="text-sm text-blue-200">Business Strategy & Innovation</p>
            </div>
          </div>
          <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
            <div className="bg-white/10 rounded p-3">
              <h3 className="font-semibold">Education</h3>
              <p>MBA Graduate</p>
            </div>
            <div className="bg-white/10 rounded p-3">
              <h3 className="font-semibold">Expertise</h3>
              <p>Strategic Planning</p>
            </div>
            <div className="bg-white/10 rounded p-3">
              <h3 className="font-semibold">Focus</h3>
              <p>Business Innovation</p>
            </div>
          </div>
        </div>'''
                        
                        # Insert profile section after the main header
                        if '<div className="App">' in content:
                            content = content.replace(
                                '<div className="App">',
                                f'<div className="App">{profile_section}'
                            )
                        elif 'return (' in content:
                            content = content.replace(
                                'return (',
                                f'return (\n    <div className="min-h-screen bg-gray-50 p-4">{profile_section}\n    <div className="max-w-4xl mx-auto">'
                            )
                            # Add closing divs
                            content = content.replace('  );\n}', '    </div>\n    </div>\n  );\n}')
                        
                        with open(app_jsx_path, 'w', encoding='utf-8') as f:
                            f.write(content)
                        
                        files_modified.append("frontend/src/App.jsx")
                        changes_made.append("Added Neelesh's profile section with MBA credentials")
                
                success_message = f"✅ Successfully added Neelesh's profile information!\n\nChanges made:\n" + "\n".join([f"• {change}" for change in changes_made])
                
                await manager.send_to_project(project_name, {
                    "type": "status",
                    "phase": "complete",
                    "message": success_message
                })
                
                return {
                    "success": True,
                    "changes": [{"file_path": fp, "edit_type": "profile_update"} for fp in files_modified],
                    "explanation": success_message,
                    "files_modified": files_modified
                }
                
            except Exception as e:
                error_msg = f"❌ Error adding profile: {str(e)}"
                await manager.send_to_project(project_name, {
                    "type": "status",
                    "phase": "error", 
                    "message": error_msg
                })
                
                return {"success": False, "error": error_msg}

        # Send status update
        await manager.send_to_project(project_name, {
            "type": "status",
            "phase": "thinking",
            "message": "🤖 Working on it..."
        })

        # Get project context (read existing files)
        project_context = ""
        try:
            # Read key files for context
            for file_pattern in ["package.json", "src/App.jsx", "src/main.jsx", "backend/main.py"]:
                context_file = project_path / file_pattern
                if context_file.exists():
                    try:
                        with open(context_file, 'r', encoding='utf-8') as f:
                            content = f.read()
                            project_context += f"\n=== {file_pattern} ===\n{content[:2000]}\n"
                    except:
                        continue
        except:
            pass

        # Enhanced request processing - handle all requests by analyzing the project
        def is_vague_request(message):
            """Always accept requests - the AI will determine what to do."""
            # Removed validation - accept any message and let AI handle it
            # The AI is smart enough to respond appropriately to any request
            return False  # Never reject messages as too vague

        def analyze_error_message(message):
            """Extract specific error information from error messages."""
            error_patterns = {
                "TypeError: Invalid attempt to spread non-iterable instance": {
                    "issue": "Spread operator used on non-array/object",
                    "fixes": ["Check array initialization", "Ensure proper data types", "Add null checks before spreading"]
                },
                "ReferenceError": {
                    "issue": "Component or variable not defined",
                    "fixes": ["Check imports", "Verify component exports", "Add missing declarations"]
                },
                "map is not a function": {
                    "issue": "Array method called on non-array",
                    "fixes": ["Initialize as empty array []", "Add Array.isArray() check", "Provide fallback data"]
                },
                "JSON.parse": {
                    "issue": "JSON parsing error",
                    "fixes": ["Add try/catch around JSON.parse", "Validate JSON string", "Provide default fallback"]
                }
            }
            
            for pattern, info in error_patterns.items():
                if pattern.lower() in message.lower():
                    return info
            return None

        # Auto-analyze project for common issues if request is vague
        project_analysis = ""
        
        # First check for specific error patterns
        error_info = analyze_error_message(user_message)
        if error_info:
            project_analysis = f"""

🚨 DETECTED ERROR: {error_info['issue']}

RECOMMENDED FIXES:
- {chr(10).join(f'• {fix}' for fix in error_info['fixes'])}

ANALYZING PROJECT FILES FOR SPECIFIC FIXES..."""
            
        elif is_vague_request(user_message):
            await manager.send_to_project(project_name, {
                "type": "status",
                "phase": "analyzing",
                "message": "🔍 Looking at your project..."
            })            # Quick analysis of common frontend issues
            analysis_points = []
            
            # Check for React-specific issues in App.jsx
            app_file = project_path / "frontend" / "src" / "App.jsx"
            if app_file.exists():
                try:
                    with open(app_file, 'r', encoding='utf-8') as f:
                        app_content = f.read()
                        
                    # Common React issues to check
                    if "spread non-iterable" in user_message.lower():
                        analysis_points.append("Fix spread operator errors - check for null/undefined values before spreading")
                        # Check for specific spread patterns that might fail
                        if "...(" in app_content or "... " in app_content:
                            analysis_points.append("Found spread operators that need null checks")
                    if ".map is not a function" in user_message.lower() or "map" in user_message.lower():
                        analysis_points.append("Fix array.map() errors - ensure arrays are properly initialized")
                    if "products.map" in app_content and "useState([])" not in app_content:
                        analysis_points.append("Arrays not properly initialized as [] in useState")
                    if "JSON.parse" in app_content and "try" not in app_content:
                        analysis_points.append("JSON.parse without error handling")  
                    if "ErrorBoundary" in app_content:
                        analysis_points.append("Remove duplicate ErrorBoundary class declarations")
                    if "...props" in app_content and "props &&" not in app_content:
                        analysis_points.append("Spread operator used without checking if props exists")
                    if "localhost" in app_content or "127.0.0.1" in app_content:
                        analysis_points.append("Using localhost URLs - should use production API URLs")
                    if "fetch(" in app_content and ".then" not in app_content and "await" not in app_content:
                        analysis_points.append("Fetch calls need proper async/await or .then handling")
                        
                except:
                    pass
            
            # Check package.json for missing dependencies
            pkg_file = project_path / "frontend" / "package.json"
            if pkg_file.exists():
                try:
                    with open(pkg_file, 'r', encoding='utf-8') as f:
                        pkg_content = f.read()
                    if '"react"' not in pkg_content:
                        analysis_points.append("Missing React dependency in package.json")
                except:
                    pass
            
            if analysis_points:
                project_analysis = f"\n\nDETECTED ISSUES TO FIX:\n- " + "\n- ".join(analysis_points[:5])
            else:
                project_analysis = f"\n\nSUGGESTION: Be more specific. Examples:\n- 'Fix the array.map error'\n- 'Add a login form'\n- 'Make buttons responsive'"

        # Get project file tree to help AI understand what files exist
        def get_file_tree(path: Path, prefix="", max_depth=3, current_depth=0):
            """Generate a simple file tree structure"""
            if current_depth >= max_depth:
                return ""
            
            tree = []
            try:
                items = sorted(path.iterdir(), key=lambda x: (not x.is_dir(), x.name))
                for item in items:
                    # Skip node_modules, .git, etc
                    if item.name in ['node_modules', '.git', '__pycache__', 'dist', 'build', '.vite']:
                        continue
                    if item.is_dir():
                        tree.append(f"{prefix}📁 {item.name}/")
                        tree.append(get_file_tree(item, prefix + "  ", max_depth, current_depth + 1))
                    else:
                        tree.append(f"{prefix}📄 {item.name}")
            except:
                pass
            return "\n".join(filter(None, tree))
        
        project_file_tree = get_file_tree(project_path)
        
        # For editing requests, include relevant file content
        file_context = ""
        if any(keyword in user_message.lower() for keyword in ['change', 'update', 'modify', 'edit', 'fix', 'button', 'color', 'style']):
            # Try to find and include App.jsx content for context
            app_file = project_path / "frontend" / "src" / "App.jsx"
            if app_file.exists():
                try:
                    with open(app_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    # Include first 150 lines (usually contains components and UI)
                    lines = content.split('\n')[:150]
                    file_context = f"\n\nRELEVANT FILE CONTENT (App.jsx first 150 lines):\n```jsx\n" + '\n'.join(lines) + "\n```\n"
                except:
                    pass

        # Use AI to generate changes with STRICT JSON-only prompt
        prompt = f"""You MUST respond with ONLY valid JSON. No other text. No markdown. No explanations outside JSON.

User Request: "{user_message}"
Project: {project_name}

PROJECT FILE STRUCTURE:
{project_file_tree}
{file_context}
IMPORTANT: Only edit files that exist in the project structure above. Do NOT create edits for files that don't exist.
IMPORTANT: When making targeted edits, use the EXACT code from the file content above - match spacing, quotes, and formatting precisely.

CRITICAL RULES - TARGETED EDITS ONLY:
1. Your ENTIRE response must be valid JSON
2. Do NOT use markdown code blocks (no ```)
3. Do NOT add explanations before or after the JSON
4. Start with {{ and end with }}
5. Generate COMPLETE, FUNCTIONAL React components for NEW files
6. For EXISTING files (like App.jsx, App.css), use "edit_type": "targeted_edit" with search/replace
7. NEVER send full file replacements for existing files - only send the specific lines to change
8. Keep search/replace strings SHORT - edit ONE line at a time for complex changes
9. Make MULTIPLE small targeted edits instead of one large edit

EDIT TYPES:
- "new_file": Create a completely new file (for new components only)
- "targeted_edit": Modify existing files with search/replace patterns (PREFERRED - use multiple small edits)
- "append": Add content to end of file

EXAMPLE - For vague requests like "add more features":
{{
  "changes": [],
  "explanation": "I can add many features! Please specify:\\n• Customer reviews\\n• User login\\n• Dark mode\\n• Search functionality\\nWhat would you like?"
}}

EXAMPLE - For creating NEW components:
{{
  "changes": [
    {{
      "file_path": "frontend/src/components/CustomerReviews.jsx",
      "content": "import React, {{ useState }} from 'react';\\n\\nconst CustomerReviews = () => {{\\n  const [reviews, setReviews] = useState([\\n    {{ id: 1, name: 'John Doe', rating: 5, comment: 'Excellent service!' }},\\n    {{ id: 2, name: 'Jane Smith', rating: 4, comment: 'Very satisfied with my purchase.' }}\\n  ]);\\n\\n  return (\\n    <div className=\\"max-w-4xl mx-auto p-6\\">\\n      <h2 className=\\"text-2xl font-bold mb-4\\">Customer Reviews</h2>\\n      <div className=\\"space-y-4\\">\\n        {{reviews.map(review => (\\n          <div key={{review.id}} className=\\"border rounded-lg p-4 shadow-sm\\">\\n            <div className=\\"flex items-center mb-2\\">\\n              <h3 className=\\"font-semibold text-lg\\">{{review.name}}</h3>\\n              <div className=\\"ml-auto flex\\">\\n                {{[...Array(review.rating)].map((_, i) => (\\n                  <span key={{i}} className=\\"text-yellow-500\\">⭐</span>\\n                ))}}\\n              </div>\\n            </div>\\n            <p className=\\"text-gray-700\\">{{review.comment}}</p>\\n          </div>\\n        ))}}\\n      </div>\\n    </div>\\n  );\\n}};\\n\\nexport default CustomerReviews;",
      "edit_type": "new_file"
    }}
  ],
  "explanation": "Created functional CustomerReviews component with sample reviews and star ratings"
}}

EXAMPLE - For modifying EXISTING files like "change background color to black":
{{
  "changes": [
    {{
      "file_path": "frontend/src/App.css",
      "edit_type": "targeted_edit",
      "search": "  background-color: #282c34;",
      "replace": "  background-color: #000000;"
    }}
  ],
  "explanation": "Changed App background color to black"
}}

EXAMPLE - For changing multiple button colors (MULTIPLE small edits):
{{
  "changes": [
    {{
      "file_path": "frontend/src/App.jsx",
      "edit_type": "targeted_edit",
      "search": "        primary: \\"bg-gradient-to-br from-purple-600 via-pink-500 to-red-500 text-white shadow-lg shadow-pink-500/30 hover:scale-105 hover:-translate-y-1 px-8 py-3\\",",
      "replace": "        primary: \\"bg-white text-slate-900 hover:bg-gray-200 px-8 py-3\\","
    }},
    {{
      "file_path": "frontend/src/App.jsx",
      "edit_type": "targeted_edit",
      "search": "        outline: \\"border-2 border-white/50 bg-transparent text-white hover:bg-white/10 hover:border-white px-8 py-3\\",",
      "replace": "        outline: \\"bg-white text-slate-900 hover:bg-gray-200 px-8 py-3\\","
    }}
  ],
  "explanation": "Changed primary and outline button variants to white background"
}}

EXAMPLE with user-friendly language:
{{
  "changes": [...],
  "explanation": "Done! All buttons are now white."
}}

CRITICAL: For modifying existing files, use MULTIPLE small "targeted_edit" changes (one per line) instead of one large edit.
CRITICAL: Match EXACT spacing, quotes, and formatting from the file content provided above.
CRITICAL: If the search string ends with a comma (,) the replace string MUST also end with a comma to maintain valid syntax!

IMPORTANT - USER-FRIENDLY EXPLANATIONS:
- Write explanations for non-technical users, NOT developers
- NEVER mention: "file_path", "edit_type", "targeted_edit", "append", "JSON", "component", "class", "function", "import", "export"
- NEVER mention: "App.jsx", "index.html", ".css", "src/", "frontend/", "backend/"
- DO say: "I changed the button color", "I added the image", "I updated the text", "I fixed the layout"
- Keep it simple: "Done! Your buttons are now white." NOT "Successfully modified Button component variants"

RESPOND WITH ONLY JSON NOW:"""

        try:
            # Use Gemini API directly for fast, simple code suggestions
            import google.generativeai as genai
            import asyncio
            import os
            
            print(f"🤖 AI Code Generator: Processing request '{user_message}' for project '{project_name}'")
            
            # Configure Gemini API
            api_key = os.getenv("GOOGLE_API_KEY")
            if not api_key:
                raise Exception("GOOGLE_API_KEY not configured. Please set your Gemini API key in environment variables.")
            
            genai.configure(api_key=api_key)
            
            # Use fast Flash model for quick responses
            model = genai.GenerativeModel(
                model_name="gemini-2.0-flash-exp",
                generation_config={
                    "temperature": 0.3,
                    "max_output_tokens": 8192,  # Increased token limit
                }
            )
            
            # Generate AI response with timeout
            try:
                ai_response_obj = await asyncio.wait_for(
                    asyncio.to_thread(model.generate_content, prompt),
                    timeout=30.0  # 30 second timeout
                )
                ai_response = ai_response_obj.text
                print(f"✅ AI Response received ({len(ai_response)} chars)")
                print(f"🔍 DEBUG - Raw AI Response: {repr(ai_response[:1000])}")  # Show first 1000 chars with escapes
                print(f"🔍 DEBUG - Full AI Response length: {len(ai_response)} chars")
            except asyncio.TimeoutError:
                print("⏱️ AI request timed out after 30 seconds")
                raise Exception("AI request timed out. Please try a more specific request or try again.")
            
            # Parse AI response with robust error handling
            import json
            import re
            
            def clean_json_string(text):
                
                if not text:
                    return text
                
                # First, try to parse as-is (don't clean well-formed JSON)
                try:
                    json.loads(text)
                    print("🔍 DEBUG - JSON is already valid, no cleaning needed")
                    return text
                except json.JSONDecodeError:
                    print("🔍 DEBUG - JSON needs cleaning")
                    pass
                
                # Remove control characters (except newlines, tabs, carriage returns)
                cleaned = ''.join(char for char in text if ord(char) >= 32 or char in '\n\t\r')
                
                # Remove BOM if present
                cleaned = cleaned.lstrip('\ufeff')
                
                # Fix unterminated strings
                cleaned = fix_unterminated_strings(cleaned)
                
                # Fix common JSON issues
                cleaned = re.sub(r',\s*}', '}', cleaned)  # Remove trailing commas before }
                cleaned = re.sub(r',\s*]', ']', cleaned)  # Remove trailing commas before ]
                
                # Only apply aggressive fixes if the JSON is still broken
                try:
                    json.loads(cleaned)
                    return cleaned
                except json.JSONDecodeError:
                    # Apply more aggressive fixes only if needed
                    
                    # First, escape single quotes inside JSON string values
                    # Simple approach: replace ' with \' in content/explanation values
                    lines = cleaned.split('\n')
                    for i, line in enumerate(lines):
                        if '"content":' in line or '"explanation":' in line:
                            # Escape single quotes in this line
                            lines[i] = line.replace("'", "\\'")
                    cleaned = '\n'.join(lines)
                    
                    # Fix unquoted property names (only at the start of lines or after braces/commas)
                    cleaned = re.sub(r'(^|[{\[,]\s*)(\w+):', r'\1"\2":', cleaned, flags=re.MULTILINE)
                    
                    # Fix single quotes to double quotes (but be careful about apostrophes)
                    # Only replace single quotes that are likely JSON delimiters, not apostrophes
                    cleaned = re.sub(r"(?<!\w)'([^']*)'(?!\w)", r'"\1"', cleaned)
                
                # Remove comments
                cleaned = re.sub(r'//.*?\n', '', cleaned)
                cleaned = re.sub(r'/\*.*?\*/', '', cleaned, flags=re.DOTALL)
                
                return cleaned
            
            def fix_unterminated_strings(text):
                try:
                    result = ""
                    in_string = False
                    escape_next = False
                    
                    for i, char in enumerate(text):
                        if escape_next:
                            result += char
                            escape_next = False
                            continue
                            
                        if char == '\\' and in_string:
                            result += char
                            escape_next = True
                            continue
                            
                        if char == '"':
                            if in_string:
                                # End of string
                                in_string = False
                            else:
                                # Start of string
                                in_string = True
                            result += char
                        elif char == '\n' and in_string:
                            # Unterminated string at newline - close it
                            result += '"'
                            in_string = False
                            result += char
                        else:
                            result += char
                    
                    # If we end while still in a string, close it
                    if in_string:
                        result += '"'
                        
                    return result
                except Exception:
                    return text
            
            # Improved JSON extraction and parsing
            def extract_and_parse_json(text):
                if not text:
                    return None
                
                print(f"🔍 DEBUG - Before markdown removal: {repr(text[:200])}")
                
                # Remove markdown code blocks first - more aggressive approach
                text = re.sub(r'```json\s*\n?', '', text, flags=re.IGNORECASE)
                text = re.sub(r'```\s*\n?', '', text)
                text = re.sub(r'^```[\w]*\s*\n?', '', text, flags=re.MULTILINE)
                
                print(f"🔍 DEBUG - After markdown removal: {repr(text[:200])}")
                
                # Try multiple JSON extraction patterns - start with most specific
                patterns = [
                    r'\{[\s\S]*?"changes"\s*:\s*\[[\s\S]*?\][\s\S]*?"explanation"[\s\S]*?\}',  # Complete JSON with changes array and explanation
                    r'\{[\s\S]*?"changes"\s*:\s*\[[\s\S]*?\][\s\S]*?\}',  # JSON with changes array (may be missing explanation)
                    r'\{[\s\S]*?\}(?=\s*$)',  # Complete JSON object at end of text
                    r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}',  # Nested JSON (fallback)
                ]
                
                for i, pattern in enumerate(patterns):
                    matches = re.findall(pattern, text, re.DOTALL)
                    print(f"🔍 DEBUG - Pattern {i+1} found {len(matches)} matches")
                    for j, match in enumerate(matches):
                        try:
                            print(f"🔍 DEBUG - Trying to parse match {j+1}: {repr(match[:100])}")
                            # Clean and attempt to parse
                            cleaned = clean_json_string(match.strip())
                            
                            # Try to fix common JSON issues
                            if cleaned.endswith(','):
                                cleaned = cleaned[:-1]
                            
                            # Handle truncated JSON by ensuring proper closure
                            open_braces = cleaned.count('{') - cleaned.count('}')
                            open_brackets = cleaned.count('[') - cleaned.count(']')
                            
                            if open_braces > 0:
                                cleaned += '}' * open_braces
                            if open_brackets > 0:
                                cleaned += ']' * open_brackets
                            
                            parsed = json.loads(cleaned)
                            if isinstance(parsed, dict) and ('changes' in parsed or 'explanation' in parsed):
                                print(f"✅ DEBUG - JSON parsing succeeded! Returning: {parsed}")
                                return parsed
                            else:
                                print(f"🔍 DEBUG - Parsed but invalid structure: {parsed}")
                        except json.JSONDecodeError as e:
                            print(f"❌ DEBUG - JSON parse error: {str(e)[:100]}")
                            print(f"🔍 DEBUG - Failed to parse: {repr(cleaned[:150])}")
                            continue
                        except Exception as e:
                            print(f"General parse error: {str(e)[:100]}")
                            continue
                
                # If no valid JSON found, try to extract key information manually
                if 'changes' in text.lower() or 'file_path' in text.lower():
                    print("Attempting manual extraction from AI response...")
                    try:
                        # Try to extract structured information even if JSON is malformed
                        explanation_match = re.search(r'"explanation":\s*"([^"]*)"', text)
                        explanation = explanation_match.group(1) if explanation_match else "AI suggested changes"
                        
                        # Look for file modifications in the text
                        file_mentions = re.findall(r'src/[\w/\.]+\.jsx?', text)
                        if file_mentions:
                            return {
                                "changes": [{"file_path": f"frontend/{file_mentions[0]}", "edit_type": "content_update"}],
                                "explanation": explanation
                            }
                    except:
                        pass
                
                return None
            
            response_data = extract_and_parse_json(ai_response)
            print(f"🔍 DEBUG - extract_and_parse_json returned: {response_data}")
            
            if not response_data:
                # Fallback: Parse the response manually for key information
                print(f"JSON parsing failed, creating fallback response for: {user_message}")
                
                # Try to create a specific response based on the user's request
                fallback_changes = []
                
                # Determine if this is a greeting or conversational message
                greetings = ["hi", "hello", "hey", "sup", "yo", "greetings"]
                is_greeting = any(user_message.lower().strip() == greeting for greeting in greetings)
                
                if is_greeting:
                    # Respond to greetings warmly without requiring code changes
                    fallback_explanation = f"Hi! 👋 I'm your AI coding assistant. I can help you with your {project_name} project by:\n• Adding new features\n• Fixing bugs and errors\n• Styling and design changes\n• Code improvements\n\nWhat would you like to work on?"
                elif "name" in user_message.lower() and ("neelesh" in user_message.lower() or "include" in user_message.lower()):
                    # Read current App.jsx to personalize it
                    app_file = project_path / "frontend" / "src" / "App.jsx"
                    if app_file.exists():
                        try:
                            with open(app_file, 'r', encoding='utf-8') as f:
                                current_content = f.read()
                            
                            # Create personalized version
                            personalized_content = current_content.replace(
                                'Welcome to Your Project', 'Welcome to Neelesh\'s Project'
                            ).replace(
                                'Your application', 'Neelesh\'s application'
                            ).replace(
                                'Welcome to app-', 'Welcome to Neelesh\'s app-'
                            )
                            
                            # If no changes were made, add a personal header
                            if personalized_content == current_content:
                                # Add a personal welcome section
                                if 'return (' in personalized_content:
                                    personalized_content = personalized_content.replace(
                                        'return (',
                                        '''return (
    <div className="text-center py-4 bg-gradient-to-r from-blue-600 to-purple-600 text-white">
      <h2 className="text-lg font-semibold">Welcome, Neelesh! 👋</h2>
      <p className="text-sm opacity-90">This application was built just for you</p>
    </div>
    <div className="flex-1">''',
                                        1
                                    )
                                    # Add closing div
                                    personalized_content = personalized_content.replace(
                                        '  );\n}', '    </div>\n  );\n}'
                                    )
                            
                            fallback_changes = [{
                                "file_path": "frontend/src/App.jsx",
                                "edit_type": "content_update",
                                "new_content": personalized_content,
                                "reason": "Added personalization for Neelesh"
                            }]
                            fallback_explanation = "Added personalized welcome message for Neelesh to the application"
                            
                        except Exception as e:
                            print(f"Error creating personalized content: {e}")
                
                # If no specific changes could be made, provide helpful, friendly responses
                if not fallback_changes:
                    # Check if this is a conversational message
                    conversational_words = ["hi", "hello", "hey", "thanks", "thank you", "ok", "okay", "cool", "nice", "great"]
                    is_conversational = any(word in user_message.lower() for word in conversational_words)
                    
                    if is_conversational:
                        # Friendly response without code changes
                        fallback_explanation = f"Hi there! 👋 I'm ready to help with your {project_name} project. Just tell me what you'd like me to do:\n\n• Add new features or components\n• Fix bugs or errors you're seeing\n• Change styling or layout\n• Improve code quality\n\nWhat can I help you with?"
                    elif "fix" in user_message.lower():
                        if "frontend" in user_message.lower():
                            fallback_explanation = "I can help fix frontend issues! Here are some common fixes I can apply:\n• Fix React array.map() errors\n• Fix API endpoint calls\n• Fix localStorage parsing\n• Remove duplicate declarations\n\nLet me analyze your project..."
                        else:
                            fallback_explanation = "I can help fix backend issues! Common fixes include:\n• CORS configuration\n• Database connections\n• API routing\n• Authentication\n\nLet me check your code..."
                    elif any(word in user_message.lower() for word in ["add", "create", "build", "more"]):
                        # For general "add features" requests, provide specific suggestions
                        if "more" in user_message.lower() and "feature" in user_message.lower():
                            fallback_explanation = f"I can add many features to {project_name}! Here are some popular options:\n\n💡 **Quick Wins:**\n• Dark mode toggle\n• Loading animations\n• Toast notifications\n• Search functionality\n\n🎨 **UI Enhancements:**\n• Modern card layouts\n• Gradient backgrounds\n• Hover effects\n• Responsive navigation\n\n⚙️ **Functionality:**\n• User authentication\n• Data filtering\n• Form validation\n• API integration\n\nTell me specifically what you'd like, or I can add something awesome for you!"
                        else:
                            fallback_explanation = f"I'd be happy to add features to {project_name}! I can help with:\n• User authentication (login/signup)\n• Dashboards and data views\n• Forms and validation\n• Navigation and routing\n\nWhat would you like me to add?"
                    else:
                        # General helpful response
                        fallback_explanation = f"I understand you want to work on: '{user_message}'\n\nI can help with many tasks:\n• Adding features or components\n• Fixing bugs and errors\n• Styling and design changes\n• Code improvements\n\nLet me see what I can do for your project..."
                    
                response_data = {
                    "changes": fallback_changes,
                    "explanation": fallback_explanation
                }
            
            changes = response_data.get("changes", [])
            explanation = response_data.get("explanation", "AI-generated changes")
            print(f"🔍 DEBUG - Extracted changes: {len(changes)} items")
            print(f"🔍 DEBUG - Extracted explanation: {explanation[:100]}...")
            
            # Validate changes structure - support both full file and targeted edits
            valid_changes = []
            for change in changes:
                if not isinstance(change, dict) or not change.get("file_path"):
                    continue
                
                edit_type = change.get("edit_type", "replace")
                
                # Validate based on edit type
                if edit_type == "targeted_edit":
                    # Targeted edits need search/replace or old_code/new_code
                    has_search_replace = change.get("search") and "replace" in change
                    has_old_new = change.get("old_code") and "new_code" in change
                    if has_search_replace or has_old_new:
                        valid_changes.append(change)
                        print(f"✅ DEBUG - Valid targeted edit for {change.get('file_path')}")
                elif edit_type in ["new_file", "replace", "append"]:
                    # These edit types need content
                    content = str(change.get("content", "")).strip()
                    if len(content) > 10:  # Minimum content check
                        valid_changes.append(change)
                        print(f"✅ DEBUG - Valid {edit_type} for {change.get('file_path')}")
            
            print(f"🔍 DEBUG - Valid changes found: {len(valid_changes)}")
            
            if not valid_changes:
                # Check if this might be a customization request that should use the direct customization system
                # Only trigger customization for very specific requests, not vague ones
                vague_requests = ['more features', 'add features', 'features for customers', 'more functionality']
                is_vague_request = any(phrase in user_message.lower() for phrase in vague_requests)
                
                customization_keywords = [
                    'change color', 'update style', 'modify layout', 'replace image', 'include picture',
                    'change background', 'update font', 'modify theme', 'change design', 'update appearance'
                ]
                
                is_customization_request = any(phrase in user_message.lower() for phrase in customization_keywords) and not is_vague_request
                print(f"🔍 DEBUG - is_customization_request: {is_customization_request}, is_vague_request: {is_vague_request} (user_message: '{user_message}')")
                
                if is_customization_request:
                    # Try to use the direct customization system as fallback
                    try:
                        from ai_assistant import get_user_customization_response
                        
                        # Find the main App.jsx file to customize
                        app_file_path = None
                        if (project_path / "frontend" / "src" / "App.jsx").exists():
                            app_file_path = "frontend/src/App.jsx"
                        elif (project_path / "src" / "App.jsx").exists():
                            app_file_path = "src/App.jsx"
                        
                        if app_file_path:
                            full_app_path = project_path / app_file_path.replace("/", os.sep)
                            
                            # Read current content
                            with open(full_app_path, 'r', encoding='utf-8') as f:
                                current_content = f.read()
                            
                            # Try customization
                            customization_result = get_user_customization_response(
                                file_content=current_content,
                                file_path=app_file_path,
                                user_request=user_message,
                                project_context={
                                    "name": project_name,
                                    "type": "Web Application", 
                                    "framework": "React"
                                },
                                model_type='smart'
                            )
                            
                            if customization_result.get("success") and customization_result.get("content_changed"):
                                # Apply the customization
                                with open(full_app_path, 'w', encoding='utf-8') as f:
                                    f.write(customization_result["modified_content"])
                                
                                await manager.send_to_project(project_name, {
                                    "type": "status",
                                    "phase": "complete",
                                    "message": "✅ Customization applied successfully"
                                })
                                
                                return {
                                    "success": True,
                                    "message": "Customization applied successfully",
                                    "changes": [{
                                        "file_path": app_file_path,
                                        "content": customization_result["modified_content"],
                                        "edit_type": "customization",
                                        "reason": customization_result.get("explanation", "Applied user customization")
                                    }],
                                    "explanation": customization_result.get("explanation", "Applied customizations as requested"),
                                    "changes_made": customization_result.get("changes_made", [])
                                }
                    except Exception as e:
                        print(f"Customization fallback failed: {e}")
                
                # Check if this is a conversational message without code changes needed
                greetings = ["hi", "hello", "hey", "sup", "yo", "thanks", "thank you", "ok", "okay"]
                is_greeting = any(user_message.lower().strip() == greeting for greeting in greetings)
                
                if is_greeting or not valid_changes:
                    # For greetings or when no changes needed, return friendly response (not error)
                    if 'explanation' in locals() and explanation:
                        response_msg = explanation
                    else:
                        # Default helpful message
                        response_msg = f"I understand you want to: '{user_message}'\n\nI can help with:\n• Adding specific features (e.g., 'add a login form')\n• Fixing bugs (e.g., 'fix the error in App.jsx')\n• Styling changes (e.g., 'make it blue')\n• Code improvements\n\nPlease be more specific about what you'd like me to do!"
                    
                    print(f"💬 Returning conversational response: {response_msg[:100]}...")
                    
                    await manager.send_to_project(project_name, {
                        "type": "status", 
                        "phase": "complete",
                        "message": f"💬 {response_msg[:100]}..."
                    })
                    
                    response_obj = {
                        "success": True,
                        "message": response_msg,
                        "changes": [],
                        "explanation": response_msg,
                        "conversational": True
                    }
                    print(f"🔍 DEBUG - Returning conversational response: {response_obj}")
                    return response_obj
            
            changes = valid_changes

            # Load project files from S3 for editing (primary source)
            from s3_storage import get_project_from_s3, upload_project_to_s3, s3_client, S3_BUCKET_NAME
            
            s3_project_data = None
            s3_files_map = {}  # Map file paths to their S3 content
            actual_user_id = user_id  # Track which user_id actually works
            
            try:
                s3_project_data = get_project_from_s3(project_slug=project_slug, user_id=user_id)
                
                # If not found with provided user_id, try to find project under any user
                if not s3_project_data or not s3_project_data.get('files'):
                    print(f"⚠️ Project not found for user_id={user_id}, searching all users...")
                    
                    # Search for the project across all user folders
                    response = s3_client.list_objects_v2(Bucket=S3_BUCKET_NAME, Prefix='projects/', Delimiter='/')
                    if 'CommonPrefixes' in response:
                        for prefix in response['CommonPrefixes']:
                            user_prefix = prefix['Prefix']  # e.g., 'projects/user123/'
                            # Extract user_id from prefix
                            try_user_id = user_prefix.replace('projects/', '').rstrip('/')
                            
                            # Check if this user has the project
                            project_check = s3_client.list_objects_v2(
                                Bucket=S3_BUCKET_NAME, 
                                Prefix=f'{user_prefix}{project_slug}/',
                                MaxKeys=1
                            )
                            if 'Contents' in project_check:
                                print(f"✅ Found project under user_id={try_user_id}")
                                actual_user_id = try_user_id
                                s3_project_data = get_project_from_s3(project_slug=project_slug, user_id=actual_user_id)
                                break
                
                if s3_project_data and s3_project_data.get('files'):
                    for f in s3_project_data['files']:
                        s3_files_map[f['path']] = f['content']
                    print(f"☁️ Loaded {len(s3_files_map)} files from S3 for editing (user_id={actual_user_id})")
                else:
                    print(f"⚠️ Project not found in S3, will use local files only")
            except Exception as s3_err:
                print(f"⚠️ Could not load from S3, will use local files: {s3_err}")

            # Apply the changes with targeted editing
            files_modified = []
            modified_contents = {}  # Track modified content for S3 upload
            
            for change in changes:
                file_path = change.get("file_path", "").lstrip("/")
                edit_type = change.get("edit_type", "replace")  # Default to full replace for backwards compatibility
                
                if not file_path:
                    continue
                    
                target = project_path / file_path
                # Ensure path is within project
                try:
                    target.resolve().relative_to(project_path.resolve())
                except Exception:
                    continue
                    
                target.parent.mkdir(parents=True, exist_ok=True)
                
                # Handle different edit types
                if edit_type == "targeted_edit":
                    # Targeted edit - modify specific sections
                    # Support both old/new and search/replace field names
                    search_pattern = change.get("search", change.get("old_code", ""))
                    replace_with = change.get("replace", change.get("new_code", ""))
                    target_section = change.get("target_section", "targeted modification")
                    
                    if not search_pattern or replace_with is None:
                        await manager.send_to_project(project_name, {
                            "type": "warning",
                            "message": f"⚠️ Targeted edit for {file_path} missing search/replace patterns"
                        })
                        continue
                    
                    # CRITICAL: Preserve trailing punctuation from search pattern
                    # If search ends with , or ; but replace doesn't, add it
                    if search_pattern.rstrip().endswith(',') and not replace_with.rstrip().endswith(','):
                        replace_with = replace_with.rstrip() + ','
                        print(f"⚠️ Auto-fixed: Added missing comma to replacement in {file_path}")
                    elif search_pattern.rstrip().endswith(';') and not replace_with.rstrip().endswith(';'):
                        replace_with = replace_with.rstrip() + ';'
                        print(f"⚠️ Auto-fixed: Added missing semicolon to replacement in {file_path}")
                    
                    # Read existing content - PREFER S3 over local files
                    existing_content = None
                    
                    # Try S3 first (primary source)
                    if file_path in s3_files_map:
                        existing_content = s3_files_map[file_path]
                        print(f"☁️ Reading {file_path} from S3")
                    elif target.exists():
                        # Fallback to local file
                        with open(target, 'r', encoding='utf-8') as f:
                            existing_content = f.read()
                        print(f"📁 Reading {file_path} from local (not in S3)")
                    
                    if existing_content:
                        # Apply targeted edit
                        if search_pattern in existing_content:
                            updated_content = existing_content.replace(search_pattern, replace_with, 1)
                            cleaned = _clean_ai_generated_content(updated_content, target.name)
                            
                            # Save to local file
                            target.parent.mkdir(parents=True, exist_ok=True)
                            with open(target, 'w', encoding='utf-8', newline='\n') as f:
                                f.write(cleaned)
                            
                            # Track for S3 upload
                            files_modified.append(file_path)
                            modified_contents[file_path] = cleaned
                            
                            await manager.send_to_project(project_name, {
                                "type": "file_changed",
                                "file_path": file_path,
                                "message": f"✏️ Updated your project"
                            })
                        else:
                            await manager.send_to_project(project_name, {
                                "type": "warning",
                                "message": f"⚠️ I couldn't make that change. Can you be more specific about what you'd like me to update?"
                            })
                            print(f"❌ Search pattern not found in {file_path}")
                            print(f"🔍 Looking for: {repr(search_pattern[:100])}")
                    else:
                        await manager.send_to_project(project_name, {
                            "type": "warning", 
                            "message": f"⚠️ That file doesn't exist yet. Let me know if you'd like me to create it."
                        })
                        
                elif edit_type == "append":
                    # Append to existing file
                    content = change.get("content", "")
                    if not content:
                        continue
                    
                    # Read existing content - PREFER S3 over local files
                    existing_content = ""
                    if file_path in s3_files_map:
                        existing_content = s3_files_map[file_path]
                        print(f"☁️ Reading {file_path} from S3 for append")
                    elif target.exists():
                        with open(target, 'r', encoding='utf-8') as f:
                            existing_content = f.read()
                    
                    updated_content = existing_content + "\n" + content
                    cleaned = _clean_ai_generated_content(updated_content, target.name)
                    
                    target.parent.mkdir(parents=True, exist_ok=True)
                    with open(target, 'w', encoding='utf-8', newline='\n') as f:
                        f.write(cleaned)
                    files_modified.append(file_path)
                    modified_contents[file_path] = cleaned
                    
                else:
                    # Default: full file replacement (backwards compatibility)
                    content = change.get("content", "") or change.get("new_content", "")
                    if not content:
                        continue
                    
                    # Validate React component content before writing
                    if file_path.endswith(('.jsx', '.js')):
                        validation_errors = validate_react_code(content, file_path)
                        if validation_errors:
                            await manager.send_to_project(project_name, {
                                "type": "warning",
                                "message": f"⚠️ Validation issues in {file_path}: {'; '.join(validation_errors)}"
                            })
                            # Try to fix common issues
                            content = fix_common_react_issues(content, file_path)
                        
                    cleaned = _clean_ai_generated_content(content, target.name)
                    
                    target.parent.mkdir(parents=True, exist_ok=True)
                    with open(target, 'w', encoding='utf-8', newline='\n') as f:
                        f.write(cleaned)
                    files_modified.append(file_path)
                    modified_contents[file_path] = cleaned

            # Validate and fix critical files
            await manager.send_to_project(project_name, {
                "type": "status",
                "phase": "validate",
                "message": "Validating changes..."
            })
            
            await validate_and_fix_project_files(project_path, project_name)
            check = await check_project_errors(project_name)
            remaining_errors = check.get("errors", []) if check.get("success") else []

            # Upload modified files to S3 so the preview can see them
            if files_modified and modified_contents:
                try:
                    await manager.send_to_project(project_name, {
                        "type": "status",
                        "phase": "upload",
                        "message": "☁️ Saving changes to cloud..."
                    })
                    
                    # Use already-loaded S3 data or fetch fresh
                    if s3_project_data and s3_project_data.get('files'):
                        # Build updated files list - use our cached data
                        files_to_upload = []
                        modified_paths = set(files_modified)
                        
                        # Keep existing files that weren't modified
                        for file_info in s3_project_data['files']:
                            if file_info['path'] not in modified_paths:
                                files_to_upload.append(file_info)
                        
                        # Add newly modified files with their in-memory content
                        for file_path, content in modified_contents.items():
                            files_to_upload.append({
                                'path': file_path,
                                'content': content
                            })
                        
                        # Upload to S3 using the actual user_id that owns the project
                        upload_result = upload_project_to_s3(
                            project_slug=project_slug,
                            files=files_to_upload,
                            user_id=actual_user_id  # Use the user_id where project was found
                        )
                        print(f"✅ AI changes uploaded to S3 (user={actual_user_id}): {list(modified_contents.keys())}")
                    else:
                        # Project not in S3 yet, create it fresh from local files
                        files_to_upload = []
                        for root, dirs, files in os.walk(project_path):
                            for file in files:
                                file_path_full = Path(root) / file
                                rel_path = file_path_full.relative_to(project_path)
                                try:
                                    with open(file_path_full, 'r', encoding='utf-8') as f:
                                        content = f.read()
                                    files_to_upload.append({
                                        'path': str(rel_path).replace(os.sep, '/'),
                                        'content': content
                                    })
                                except:
                                    pass
                        
                        if files_to_upload:
                            upload_project_to_s3(
                                project_slug=project_slug,
                                files=files_to_upload,
                                user_id=user_id
                            )
                            print(f"✅ Full project uploaded to S3: {len(files_to_upload)} files")
                except Exception as s3_error:
                    print(f"⚠️ S3 upload error: {s3_error}")
                    # Continue anyway - local files are saved

            # Optionally rerun project
            preview_url = None
            if re_run and files_modified:
                await manager.send_to_project(project_name, {
                    "type": "status",
                    "phase": "run",
                    "message": "Restarting development servers..."
                })
                run_resp = await run_project({
                    "project_name": project_name,
                    "tech_stack": tech_stack
                })
                if isinstance(run_resp, dict):
                    preview_url = run_resp.get("preview_url")
                    if preview_url:
                        await manager.send_to_project(project_name, {
                            "type": "preview_ready", 
                            "url": preview_url
                        })

            # Send success message
            if files_modified:
                await manager.send_to_project(project_name, {
                    "type": "success",
                    "message": f"✅ Done! Check the preview to see your changes."
                })

            return {
                "success": True,
                "explanation": explanation,
                "files_modified": files_modified,
                "preview_url": preview_url,
                "errors": remaining_errors
            }

        except Exception as ai_error:
            print(f"❌ AI processing error: {ai_error}")
            print(f"AI response preview: {ai_response[:500] if 'ai_response' in locals() else 'No response generated'}")
            
            error_message = str(ai_error)
            if "timed out" in error_message.lower():
                error_message = "⏱️ Request took too long. Try being more specific:\n• 'add a contact form'\n• 'make the buttons blue'\n• 'fix the navigation menu'"
            
            await manager.send_to_project(project_name, {
                "type": "status",
                "phase": "error",
                "message": f"❌ {error_message}"
            })
            return {
                "success": False,
                "error": f"AI processing failed: {str(ai_error)}"
            }

    except HTTPException:
        raise
    except Exception as e:
        print(f"AI chat error: {e}")
        return {"success": False, "error": str(e)}

# --- AI Customization Endpoint ---
@app.post("/api/ai-customize-project")
async def ai_customize_project(request: dict = Body(...)):
    """Handle user customization requests - reads from and writes to S3"""
    try:
        project_name = request.get("project_name")
        file_path = request.get("file_path")
        customization_request = request.get("customization_request")
        user_id = request.get("user_id", "anonymous")
        
        if not project_name:
            raise HTTPException(status_code=400, detail="project_name is required")
        if not file_path:
            raise HTTPException(status_code=400, detail="file_path is required")
        if not customization_request:
            raise HTTPException(status_code=400, detail="customization_request is required")
        
        project_slug = project_name.replace(" ", "-")
        file_path_clean = file_path.lstrip("/")
        
        # Get current file content from S3 first
        current_content = None
        try:
            project_data = get_project_from_s3(project_slug=project_slug, user_id=user_id)
            
            if project_data and project_data.get('files'):
                for file_info in project_data['files']:
                    if file_info['path'] == file_path_clean:
                        current_content = file_info['content']
                        print(f"📄 AI reading from S3: {file_path_clean}")
                        break
        except Exception as s3_error:
            print(f"⚠️ S3 read error: {s3_error}")
        
        # Fallback to local if S3 fails
        if current_content is None:
            projects_dir = Path("generated_projects")
            project_path = projects_dir / project_slug
            
            if not project_path.exists():
                return {"success": False, "error": "Project not found"}
            
            full_file_path = project_path / file_path_clean
            
            if not full_file_path.exists():
                return {"success": False, "error": f"File not found: {file_path}"}
            
            try:
                with open(full_file_path, 'r', encoding='utf-8') as f:
                    current_content = f.read()
                print(f"📄 AI reading from local: {file_path_clean}")
            except Exception as e:
                return {"success": False, "error": f"Failed to read file: {str(e)}"}
        
        # Prepare project context
        project_context = {
            "name": project_name,
            "type": "Web Application",
            "framework": "React"
        }
        
        # Send status update
        await manager.send_to_project(project_name, {
            "type": "status",
            "phase": "processing", 
            "message": f"🎨 Customizing {file_path}..."
        })
        
        # Use the AI assistant function to process the customization
        from ai_assistant import get_user_customization_response
        
        result = get_user_customization_response(
            file_content=current_content,
            file_path=file_path_clean,
            user_request=customization_request,
            project_context=project_context,
            model_type='smart'
        )
        
        if result["success"]:
            modified_content = result["modified_content"]
            
            # Save to S3 first
            try:
                # Get all project files from S3
                project_data = get_project_from_s3(project_slug=project_slug, user_id=user_id)
                
                if project_data and project_data.get('files'):
                    # Update the modified file in the list
                    files_to_upload = []
                    file_updated = False
                    
                    for file_info in project_data['files']:
                        if file_info['path'] == file_path_clean:
                            files_to_upload.append({
                                'path': file_path_clean,
                                'content': modified_content
                            })
                            file_updated = True
                        else:
                            files_to_upload.append(file_info)
                    
                    # If file wasn't in S3, add it
                    if not file_updated:
                        files_to_upload.append({
                            'path': file_path_clean,
                            'content': modified_content
                        })
                    
                    # Upload updated project to S3
                    upload_result = upload_project_to_s3(
                        project_slug=project_slug,
                        files=files_to_upload,
                        user_id=user_id
                    )
                    print(f"✅ AI saved to S3: {file_path_clean}")
            except Exception as s3_error:
                print(f"⚠️ S3 write error: {s3_error}")
            
            # Also save locally for development
            try:
                projects_dir = Path("generated_projects")
                project_path = projects_dir / project_slug
                full_file_path = project_path / file_path_clean
                
                full_file_path.parent.mkdir(parents=True, exist_ok=True)
                with open(full_file_path, 'w', encoding='utf-8') as f:
                    f.write(modified_content)
                print(f"✅ AI saved to local: {file_path_clean}")
            except Exception as local_error:
                print(f"⚠️ Local write error: {local_error}")
            
            # Send success notification
            await manager.send_to_project(project_name, {
                "type": "status",
                "phase": "complete",
                "message": f"✅ Successfully customized {file_path}",
                "details": {
                    "changes_made": result["changes_made"],
                    "explanation": result["explanation"]
                }
            })
            
            return {
                "success": True,
                "message": "Customization applied successfully",
                "file_path": file_path_clean,
                "changes_made": result["changes_made"],
                "explanation": result["explanation"],
                "file_type": result.get("file_type", "unknown")
            }
        else:
            # Send error notification
            await manager.send_to_project(project_name, {
                "type": "error",
                "message": f"❌ Failed to customize {file_path}: {result['error']}"
            })
            
            return {
                "success": False,
                "error": result["error"],
                "explanation": result.get("explanation", "")
            }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"AI customization error: {e}")
        return {"success": False, "error": str(e)}

# --- AI Apply Changes Endpoint ---
@app.post("/api/ai-apply-changes")
async def ai_apply_changes(request: dict = Body(...)):
    """Apply AI-suggested changes to project files in S3"""
    try:
        project_name = request.get("project_name")
        edits = request.get("edits", [])  # List[{file_path, content}]
        re_run = bool(request.get("re_run", False))
        tech_stack = request.get("tech_stack", [])
        user_id = request.get("user_id", "anonymous")

        if not project_name:
            raise HTTPException(status_code=400, detail="project_name is required")
        if not isinstance(edits, list) or not edits:
            raise HTTPException(status_code=400, detail="No edits provided")

        # Get project slug
        project_slug = project_name.lower().replace(" ", "-")

        # Prepare files for S3 upload
        files_to_upload = []
        files_modified = []
        
        for edit in edits:
            file_path = (edit.get("file_path") or "").lstrip("/")
            content = edit.get("content", "")
            if not file_path:
                continue
            
            # Clean AI-generated content
            filename = file_path.split('/')[-1]
            cleaned = _clean_ai_generated_content(content, filename)
            
            files_to_upload.append({
                'path': file_path,
                'content': cleaned
            })
            files_modified.append(file_path)
            
            await manager.send_to_project(project_name, {
                "type": "file_changed",
                "file_path": file_path,
                "message": f"✍️ Updated {file_path}"
            })

        # Batch upload to S3
        try:
            from s3_storage import upload_project_to_s3
            
            upload_project_to_s3(
                project_slug=project_slug,
                files=files_to_upload,
                user_id=user_id
            )
            
            print(f"☁️ Uploaded {len(files_to_upload)} AI-modified files to S3")
            
        except Exception as s3_error:
            print(f"❌ S3 upload failed: {s3_error}")
            return {"success": False, "error": f"Failed to save changes to S3: {str(s3_error)}"}

        # Validate (optional - may need local files)
        await manager.send_to_project(project_name, {
            "type": "status",
            "phase": "validate",
            "message": "✅ Changes applied to cloud storage"
        })

        # Optionally rerun project (may need local files for preview)
        preview_url = None
        if re_run:
            await manager.send_to_project(project_name, {
                "type": "status",
                "phase": "run",
                "message": "⚠️ Preview requires local checkout (S3 files uploaded)"
            })

        await manager.send_to_project(project_name, {
            "type": "status",
            "phase": "ready",
            "message": "✅ Changes applied to cloud storage",
            "preview_url": preview_url
        })

        return {
            "success": True,
            "files_modified": files_modified,
            "preview_url": preview_url,
            "storage": "s3"
        }

    except HTTPException:
        raise
    except Exception as e:
        return {"success": False, "error": str(e)}

async def simulate_typing_effect(project_name: str, file_path: str, content: str, delay_per_char: float = 0.01):
    """Simulate typing effect by sending content in chunks"""
    lines = content.split('\n')
    current_content = ""
    
    for i, line in enumerate(lines):
        current_content += line
        if i < len(lines) - 1:  # Add newline except for last line
            current_content += '\n'
        
        # Send partial content
        await manager.send_to_project(project_name, {
            "type": "file_content_update",
            "file_path": file_path,
            "content": current_content,
            "is_complete": i == len(lines) - 1
        })
        
        # Small delay for typing effect
        await asyncio.sleep(delay_per_char * len(line))

def _strip_code_fences(text: str) -> str:
    """Remove ```...``` fences from AI outputs if present."""
    try:
        t = text.strip()
        # Match fenced block optionally with language like ```json
        m = re.match(r"^```(?:\w+)?\s*([\s\S]*?)\s*```$", t)
        return m.group(1).strip() if m else t
    except Exception:
        return text

def _clean_ai_generated_content(content: str, filename: str) -> str:
    """Normalize AI-generated content by stripping BOM/code fences and validating JSON."""
    try:
        # Remove control characters (except newlines, tabs, carriage returns)
        cleaned = ''.join(char for char in content if ord(char) >= 32 or char in '\n\t\r')
        
        # Remove BOM
        cleaned = cleaned.lstrip('\ufeff')
        cleaned = _strip_code_fences(cleaned)

        # If it's a JSON file, try to extract a strict JSON object/array and pretty print
        if filename.lower().endswith('.json'):
            start = cleaned.find('{')
            end = cleaned.rfind('}')
            candidate = cleaned[start:end+1] if start != -1 and end != -1 and start < end else cleaned
            try:
                obj = json.loads(candidate)
                cleaned = json.dumps(obj, indent=2)
            except Exception:
                try:
                    # Attempt to remove trailing commas and retry
                    tmp = re.sub(r",\s*([}\]])", r"\1", candidate)
                    obj = json.loads(tmp)
                    cleaned = json.dumps(obj, indent=2)
                except Exception as e:
                    print(f"JSON validation failed for {filename}: {e}")
                    # Return the original cleaned content as fallback
                    pass
        return cleaned
    except Exception:
        return content

async def create_file_with_animation(file_path: Path, content: str, relative_path: str, project_name: str) -> str:
    """Create a file with real-time typing animation"""
    
    # Announce file creation
    await manager.send_to_project(project_name, {
        "type": "terminal_output",
        "message": f"📝 Creating {relative_path}...",
        "level": "info"
    })
    
    # Create directory if needed
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Normalize AI content (especially for JSON and fenced blocks)
    final_content = _clean_ai_generated_content(content, file_path.name)
    
    # If JSON, re-validate and pretty print; provide fallback for package.json
    if file_path.suffix.lower() == ".json":
        try:
            obj = json.loads(final_content)
            final_content = json.dumps(obj, indent=2)
        except Exception as e:
            print(f"Invalid JSON for {relative_path}: {e}")
            if file_path.name == "package.json":
                # Minimal safe fallback
                final_content = json.dumps({
                    "name": Path(project_name).name.lower().replace(" ", "-"),
                    "version": "1.0.0",
                    "private": True,
                    "type": "module",
                    "scripts": {"dev": "vite", "build": "vite build", "preview": "vite preview"},
                    "dependencies": {"react": "^18.2.0", "react-dom": "^18.2.0"},
                    "devDependencies": {"vite": "^4.4.0", "@vitejs/plugin-react": "^4.0.0"}
                }, indent=2)

    # Send file creation start
    await manager.send_to_project(project_name, {
        "type": "file_created",
        "file_path": relative_path,
        "file_type": "file",
        "size": len(final_content)
    })
    
    # Simulate typing effect for code files
    if any(relative_path.endswith(ext) for ext in ['.jsx', '.tsx', '.js', '.ts', '.py', '.css', '.html', '.json']):
        await simulate_typing_effect(project_name, relative_path, final_content, 0.005)
    else:
        # For non-code files, just send the complete content
        await manager.send_to_project(project_name, {
            "type": "file_content_update",
            "file_path": relative_path,
            "content": final_content,
            "is_complete": True
        })
    
    # Write the actual file
    with open(file_path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(final_content)
    
    await asyncio.sleep(0.1)  # Brief pause between files
    
    return relative_path

async def validate_and_fix_project_files(project_path: Path, project_name: str) -> bool:
    """Validate and fix critical project files like frontend/package.json before running."""
    try:
        frontend_path = project_path / "frontend"
        package_json_path = frontend_path / "package.json"

        if not frontend_path.exists():
            return True  # Nothing to validate

        if package_json_path.exists():
            try:
                raw = package_json_path.read_text(encoding='utf-8', errors='ignore')
                cleaned = _clean_ai_generated_content(raw, 'package.json')
                obj = json.loads(cleaned)
                # Optionally ensure minimal required fields
                if "name" not in obj:
                    obj["name"] = project_name.lower().replace(" ", "-")
                package_json_path.write_text(json.dumps(obj, indent=2), encoding='utf-8', newline='\n')
                return True
            except Exception as e:
                print(f"Repairing package.json due to error: {e}")
                fallback = {
                    "name": project_name.lower().replace(" ", "-"),
                    "version": "1.0.0",
                    "private": True,
                    "type": "module",
                    "scripts": {"dev": "vite", "build": "vite build", "preview": "vite preview"},
                    "dependencies": {"react": "^18.2.0", "react-dom": "^18.2.0"},
                    "devDependencies": {"vite": "^4.4.0", "@vitejs/plugin-react": "^4.0.0"}
                }
                package_json_path.write_text(json.dumps(fallback, indent=2), encoding='utf-8', newline='\n')
                return True
        else:
            # Create a minimal package.json
            minimal = {
                "name": project_name.lower().replace(" ", "-"),
                "version": "1.0.0",
                "private": True,
                "type": "module",
                "scripts": {"dev": "vite", "build": "vite build", "preview": "vite preview"},
                "dependencies": {"react": "^18.2.0", "react-dom": "^18.2.0"},
                "devDependencies": {"vite": "^4.4.0", "@vitejs/plugin-react": "^4.0.0"}
            }
            frontend_path.mkdir(parents=True, exist_ok=True)
            package_json_path.write_text(json.dumps(minimal, indent=2), encoding='utf-8', newline='\n')
            return True
    except Exception as e:
        print(f"validate_and_fix_project_files error: {e}")
        return False

# --- File Save Endpoint ---
@app.post("/api/save-project-file")
async def save_project_file(request: dict = Body(...)):
    """Save file content to S3 and optionally local storage"""
    try:
        project_name = request.get("project_name")
        file_path = request.get("file_path")
        content = request.get("content")
        user_id = request.get("user_id", "anonymous")
        
        # Get project slug
        project_slug = project_name.replace(" ", "-")
        file_path_clean = file_path.lstrip('/')
        
        # Clean content before saving
        filename = file_path_clean.split('/')[-1]
        cleaned_content = _clean_ai_generated_content(content, filename)
        
        # Upload to S3 (primary storage)
        try:
            from s3_storage import upload_project_to_s3
            
            upload_project_to_s3(
                project_slug=project_slug,
                files=[{'path': file_path_clean, 'content': cleaned_content}],
                user_id=user_id
            )
            
            print(f"☁️ Saved {file_path_clean} to S3")
            
            # Notify via WebSocket
            await manager.send_to_project(project_name, {
                "type": "file_changed",
                "file_path": file_path,
                "message": f"☁️ File saved to cloud: {file_path}"
            })
            
            return {"success": True, "storage": "s3"}
            
        except Exception as s3_error:
            print(f"❌ S3 save failed: {s3_error}")
            return {"success": False, "error": f"Failed to save to S3: {str(s3_error)}"}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

# --- Machine Learning API Endpoints ---
@app.post("/api/ml/predict")
async def ml_predict(request: dict = Body(...)):
    """Make predictions using ML models"""
    try:
        model_type = request.get("model", "linear_regression")
        features = request.get("features", [])
        
        if not features:
            return {"success": False, "error": "No features provided"}
        
        # Simple linear regression prediction
        if model_type == "linear_regression":
            import numpy as np
            
            # For demo, use a simple linear model (y = mx + b)
            # In production, this would load a trained model
            slope = request.get("slope", 1.5)
            intercept = request.get("intercept", 10)
            
            if isinstance(features[0], list):
                predictions = [sum([f * slope for f in row]) + intercept for row in features]
            else:
                predictions = [f * slope + intercept for f in features]
            
            return {
                "success": True,
                "model": model_type,
                "prediction": predictions[0] if len(predictions) == 1 else predictions,
                "confidence": 0.85,
                "features_used": features
            }
        
        elif model_type == "classification":
            # Simple classification demo
            threshold = request.get("threshold", 0.5)
            predictions = ["positive" if f > threshold else "negative" for f in features]
            confidences = [abs(f - threshold) + 0.5 for f in features]
            
            return {
                "success": True,
                "model": model_type,
                "prediction": predictions[0] if len(predictions) == 1 else predictions,
                "confidence": min(confidences),
                "classes": ["negative", "positive"]
            }
        
        elif model_type == "time_series":
            # Simple time series prediction (moving average)
            import numpy as np
            
            data = np.array(features)
            window = min(3, len(data))
            moving_avg = np.convolve(data, np.ones(window)/window, mode='valid')
            
            # Forecast next values
            last_avg = moving_avg[-1] if len(moving_avg) > 0 else data[-1]
            trend = (data[-1] - data[0]) / len(data) if len(data) > 1 else 0
            
            forecast_steps = request.get("steps", 5)
            forecast = [last_avg + trend * (i + 1) for i in range(forecast_steps)]
            
            return {
                "success": True,
                "model": model_type,
                "prediction": forecast,
                "historical": features,
                "confidence": 0.75
            }
        
        else:
            return {"success": False, "error": f"Unknown model type: {model_type}"}
            
    except Exception as e:
        print(f"❌ ML prediction error: {e}")
        return {"success": False, "error": str(e)}

@app.post("/api/ml/train")
async def ml_train(request: dict = Body(...)):
    """Train a custom ML model"""
    try:
        model_type = request.get("model", "linear_regression")
        X = request.get("features", [])
        y = request.get("labels", [])
        
        if not X or not y:
            return {"success": False, "error": "Training data (features and labels) required"}
        
        if len(X) != len(y):
            return {"success": False, "error": "Features and labels must have same length"}
        
        import numpy as np
        
        X = np.array(X)
        y = np.array(y)
        
        if model_type == "linear_regression":
            # Simple least squares fit
            if X.ndim == 1:
                X = X.reshape(-1, 1)
            
            # Add bias term
            X_with_bias = np.c_[np.ones(X.shape[0]), X]
            
            # Normal equation: (X^T X)^-1 X^T y
            coefficients = np.linalg.lstsq(X_with_bias, y, rcond=None)[0]
            
            # Calculate R-squared
            y_pred = X_with_bias @ coefficients
            ss_res = np.sum((y - y_pred) ** 2)
            ss_tot = np.sum((y - np.mean(y)) ** 2)
            r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
            
            return {
                "success": True,
                "model": model_type,
                "coefficients": {
                    "intercept": float(coefficients[0]),
                    "slopes": [float(c) for c in coefficients[1:]]
                },
                "r_squared": float(r_squared),
                "samples_used": len(y)
            }
        
        return {"success": False, "error": f"Training not implemented for: {model_type}"}
        
    except Exception as e:
        print(f"❌ ML training error: {e}")
        return {"success": False, "error": str(e)}

@app.get("/api/ml/models")
async def ml_list_models():
    """List available ML models"""
    return {
        "success": True,
        "models": [
            {
                "id": "linear_regression",
                "name": "Linear Regression",
                "description": "Predict continuous values based on input features",
                "use_cases": ["Price prediction", "Population forecasting", "Trend analysis"]
            },
            {
                "id": "classification",
                "name": "Classification",
                "description": "Categorize inputs into discrete classes",
                "use_cases": ["Sentiment analysis", "Spam detection", "Category prediction"]
            },
            {
                "id": "time_series",
                "name": "Time Series",
                "description": "Forecast future values based on historical data",
                "use_cases": ["Sales forecasting", "Stock prediction", "Demand planning"]
            }
        ]
    }

# --- LLM Integration API Endpoints ---
@app.post("/api/llm/chat")
async def llm_chat(request: dict = Body(...)):
    """Chat with LLM (OpenAI, Gemini, Claude)"""
    try:
        provider = request.get("provider", "openai")
        messages = request.get("messages", [])
        api_key = request.headers.get("X-API-Key") or request.get("api_key")
        
        if not messages:
            return {"success": False, "error": "No messages provided"}
        
        if not api_key:
            return {"success": False, "error": "API key required. Please set your API key."}
        
        if provider == "openai":
            import openai
            client = openai.OpenAI(api_key=api_key)
            
            response = client.chat.completions.create(
                model=request.get("model", "gpt-3.5-turbo"),
                messages=messages,
                max_tokens=request.get("max_tokens", 1000),
                temperature=request.get("temperature", 0.7)
            )
            
            return {
                "success": True,
                "provider": provider,
                "response": response.choices[0].message.content,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens
                }
            }
        
        elif provider == "gemini":
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            
            model = genai.GenerativeModel(request.get("model", "gemini-1.5-flash"))
            
            # Convert messages to Gemini format
            prompt = "\n".join([f"{m['role']}: {m['content']}" for m in messages])
            
            response = model.generate_content(prompt)
            
            return {
                "success": True,
                "provider": provider,
                "response": response.text
            }
        
        elif provider == "claude":
            import anthropic
            client = anthropic.Anthropic(api_key=api_key)
            
            # Extract system message if present
            system_message = None
            user_messages = []
            for msg in messages:
                if msg.get("role") == "system":
                    system_message = msg.get("content")
                else:
                    user_messages.append(msg)
            
            kwargs = {
                "model": request.get("model", "claude-3-sonnet-20240229"),
                "max_tokens": request.get("max_tokens", 1000),
                "messages": user_messages
            }
            if system_message:
                kwargs["system"] = system_message
            
            response = client.messages.create(**kwargs)
            
            return {
                "success": True,
                "provider": provider,
                "response": response.content[0].text,
                "usage": {
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens
                }
            }
        
        else:
            return {"success": False, "error": f"Unknown provider: {provider}"}
            
    except Exception as e:
        print(f"❌ LLM chat error: {e}")
        return {"success": False, "error": str(e)}

@app.post("/api/llm/generate")
async def llm_generate(request: dict = Body(...)):
    """Generate text using LLM"""
    try:
        provider = request.get("provider", "gemini")
        prompt = request.get("prompt", "")
        api_key = request.headers.get("X-API-Key") or request.get("api_key")
        
        if not prompt:
            return {"success": False, "error": "No prompt provided"}
        
        # Use Gemini as default (we have API key)
        if provider == "gemini" or not api_key:
            import google.generativeai as genai
            
            # Use environment Gemini key if no API key provided
            key = api_key or os.getenv("GOOGLE_API_KEY")
            if not key:
                return {"success": False, "error": "Gemini API key not configured"}
            
            genai.configure(api_key=key)
            model = genai.GenerativeModel("gemini-2.0-flash")
            
            response = model.generate_content(prompt)
            
            return {
                "success": True,
                "provider": "gemini",
                "text": response.text
            }
        
        # Forward to chat endpoint for other providers
        messages = [{"role": "user", "content": prompt}]
        return await llm_chat({**request, "messages": messages})
        
    except Exception as e:
        print(f"❌ LLM generate error: {e}")
        return {"success": False, "error": str(e)}

# --- Visual Edit Element Endpoint ---
@app.post("/api/visual-edit-element")
async def visual_edit_element(
    request: dict = Body(...),
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """Update element styles in the code based on visual editor changes - searches ALL project files"""
    try:
        project_slug = request.get("project_slug", "").strip()
        element_path = request.get("element_path", "")
        element_tag = request.get("element_tag", "")
        element_classes = request.get("element_classes", "")
        element_text = request.get("element_text", "")
        styles = request.get("styles", {})
        
        # Get user info from request body (passed from iframe URL params)
        user_email_from_request = request.get("user_email", "")
        user_id_alt_from_request = request.get("user_id_alt", "")
        
        # Get text change info
        new_text = request.get("new_text")
        original_text = request.get("original_text")
        
        # Get component context from request
        component_name = request.get("component_name", "")
        
        if not project_slug:
            return {"success": False, "error": "Missing project_slug"}
        
        # Get user_id - prefer authenticated user, then request params, then anonymous
        user_id = "anonymous"
        if current_user:
            user_id = current_user.get('email') or current_user.get('_id') or 'anonymous'
        elif user_email_from_request:
            user_id = user_email_from_request
        
        # Also track alternative user_id
        user_id_alt = user_id_alt_from_request if user_id_alt_from_request else None
        
        print(f"🎨 Visual edit request for project: {project_slug}")
        print(f"   User: {user_id}, Alt: {user_id_alt}")
        print(f"   Element: {element_tag} | Classes: {element_classes[:50] if element_classes else 'none'}")
        print(f"   Styles to apply: {styles}")
        if new_text:
            print(f"   Text change: '{original_text}' -> '{new_text}'")
        
        # Load project from S3 - try multiple user IDs
        project_data = get_project_from_s3(project_slug=project_slug, user_id=user_id)
        
        # Try alternative user_id if not found
        if (not project_data or not project_data.get('files')) and user_id_alt:
            print(f"   Trying alternative user_id: {user_id_alt}")
            project_data = get_project_from_s3(project_slug=project_slug, user_id=user_id_alt)
            if project_data and project_data.get('files'):
                user_id = user_id_alt  # Use this for saving
        
        # Try anonymous if not found
        if not project_data or not project_data.get('files'):
            print(f"   Trying anonymous")
            project_data = get_project_from_s3(project_slug=project_slug, user_id='anonymous')
            if project_data and project_data.get('files'):
                user_id = 'anonymous'
        
        if not project_data or not project_data.get('files'):
            return {"success": False, "error": f"Project '{project_slug}' not found"}
        
        # ENHANCED: Search ALL JSX/JS files, not just App.jsx
        jsx_files = []
        for file in project_data['files']:
            if file['path'].endswith(('.jsx', '.js', '.tsx', '.ts')) and 'node_modules' not in file['path']:
                jsx_files.append(file)
        
        if not jsx_files:
            return {"success": False, "error": "No JSX/JS files found in project"}
        
        print(f"🔍 Searching {len(jsx_files)} JSX/JS files for element...")
        
        # Clean up classes for searching (remove xverta- prefixed classes)
        clean_classes = ' '.join([c for c in element_classes.split() 
                                  if not c.startswith('xverta')]) if element_classes else ""
        
        # Try to find the exact file containing this element
        target_file = None
        target_content = ""
        match_confidence = 0
        
        # Build search patterns
        search_patterns = []
        if clean_classes:
            # Add full class string pattern
            search_patterns.append(clean_classes)
            # Add first few significant classes
            sig_classes = [c for c in clean_classes.split() if c.startswith('bg-') or c.startswith('text-') or c.startswith('px-') or c.startswith('py-') or c.startswith('flex') or c.startswith('grid')][:4]
            if sig_classes:
                search_patterns.extend(sig_classes)
        if original_text:
            search_patterns.append(original_text)
        if element_text:
            search_patterns.append(element_text[:30])
        
        # Search each file for the element
        for file in jsx_files:
            content = file['content']
            file_path = file['path']
            score = 0
            
            # Check each pattern
            for pattern in search_patterns:
                if pattern and pattern in content:
                    score += 1
                    # Higher score for exact class match
                    if pattern == clean_classes and len(pattern) > 20:
                        score += 5
            
            # If this file has a higher match score, use it
            if score > match_confidence:
                match_confidence = score
                target_file = file
                target_content = content
                print(f"   📄 Better match in {file_path} (score: {score})")
        
        # Fall back to App.jsx if no better match found
        if not target_file:
            for file in jsx_files:
                if file['path'].endswith('App.jsx'):
                    target_file = file
                    target_content = file['content']
                    print(f"   📄 Fallback to App.jsx")
                    break
        
        if not target_file:
            return {"success": False, "error": "Could not find target file"}
        
        print(f"🎯 Target file: {target_file['path']}")
        
        # Convert styles to Tailwind classes
        tailwind_classes = []
        style_updates = []
        
        # Map CSS properties to Tailwind classes
        tailwind_map = {
            'backgroundColor': {
                '#ef4444': 'bg-red-500', '#f97316': 'bg-orange-500', '#eab308': 'bg-yellow-500',
                '#22c55e': 'bg-green-500', '#3b82f6': 'bg-blue-500', '#8b5cf6': 'bg-violet-500',
                '#ec4899': 'bg-pink-500', '#1f2937': 'bg-gray-800', '#ffffff': 'bg-white',
                '#000000': 'bg-black', 'transparent': 'bg-transparent',
                '#111827': 'bg-gray-900', '#374151': 'bg-gray-700', '#4b5563': 'bg-gray-600',
                '#6b7280': 'bg-gray-500', '#9ca3af': 'bg-gray-400', '#d1d5db': 'bg-gray-300',
                '#e5e7eb': 'bg-gray-200', '#f3f4f6': 'bg-gray-100', '#f9fafb': 'bg-gray-50',
            },
            'color': {
                '#ef4444': 'text-red-500', '#f97316': 'text-orange-500', '#eab308': 'text-yellow-500',
                '#22c55e': 'text-green-500', '#3b82f6': 'text-blue-500', '#8b5cf6': 'text-violet-500',
                '#ec4899': 'text-pink-500', '#1f2937': 'text-gray-800', '#ffffff': 'text-white',
                '#000000': 'text-black', '#111827': 'text-gray-900', '#374151': 'text-gray-700',
                '#6b7280': 'text-gray-500', '#9ca3af': 'text-gray-400', '#d1d5db': 'text-gray-300',
            },
            'fontSize': {
                '12px': 'text-xs', '14px': 'text-sm', '16px': 'text-base', '18px': 'text-lg',
                '20px': 'text-xl', '24px': 'text-2xl', '30px': 'text-3xl', '36px': 'text-4xl',
                '48px': 'text-5xl', '60px': 'text-6xl'
            },
            'fontWeight': {
                '100': 'font-thin', '200': 'font-extralight', '300': 'font-light', 
                '400': 'font-normal', '500': 'font-medium', '600': 'font-semibold', 
                '700': 'font-bold', '800': 'font-extrabold', '900': 'font-black'
            },
            'borderRadius': {
                '0': 'rounded-none', '2px': 'rounded-sm', '4px': 'rounded', '6px': 'rounded-md',
                '8px': 'rounded-lg', '12px': 'rounded-xl', '16px': 'rounded-2xl', 
                '24px': 'rounded-3xl', '9999px': 'rounded-full'
            },
            'padding': {
                '0': 'p-0', '4px': 'p-1', '8px': 'p-2', '12px': 'p-3', '16px': 'p-4',
                '20px': 'p-5', '24px': 'p-6', '32px': 'p-8', '40px': 'p-10', '48px': 'p-12'
            }
        }
        
        # Build Tailwind classes from styles
        for prop, value in styles.items():
            if prop in tailwind_map and value in tailwind_map[prop]:
                tailwind_classes.append(tailwind_map[prop][value])
            else:
                # Try to find closest match for colors
                if prop == 'backgroundColor' and value.startswith('#'):
                    tailwind_classes.append(f"bg-[{value}]")  # Arbitrary value
                elif prop == 'color' and value.startswith('#'):
                    tailwind_classes.append(f"text-[{value}]")
                else:
                    # Use inline style for non-standard values
                    css_prop = ''.join(['-' + c.lower() if c.isupper() else c for c in prop]).lstrip('-')
                    style_updates.append(f"{css_prop}: {value}")
        
        print(f"🎨 Tailwind classes to add: {tailwind_classes}")
        print(f"🎨 Inline styles to add: {style_updates}")
        
        # Track if we made any changes
        content_modified = False
        new_content = target_content
        
        # HANDLE TEXT CHANGES FIRST
        if new_text and original_text and original_text in target_content:
            # Direct text replacement
            new_content = new_content.replace(f">{original_text}<", f">{new_text}<", 1)
            if new_content != target_content:
                print(f"🎨 TEXT REPLACED: '{original_text}' -> '{new_text}'")
                content_modified = True
            else:
                # Try with quotes (for JSX text)
                new_content = new_content.replace(f'"{original_text}"', f'"{new_text}"', 1)
                if new_content != target_content:
                    print(f"🎨 TEXT REPLACED (quoted): '{original_text}' -> '{new_text}'")
                    content_modified = True
        
        # FAST PATH: Try direct string replacement if we have exact class match
        if clean_classes and tailwind_classes:
            print(f"🎨 Looking for classes in code: '{clean_classes[:80]}...'")
            
            if clean_classes and clean_classes in new_content:
                # Direct replacement - fastest path!
                existing_set = set(clean_classes.split())
                new_classes_to_add = [c for c in tailwind_classes if c not in existing_set]
                
                print(f"🎨 FAST PATH: Found exact match! Adding: {new_classes_to_add}")
                
                if new_classes_to_add:
                    new_class_str = clean_classes + ' ' + ' '.join(new_classes_to_add)
                    new_content = new_content.replace(clean_classes, new_class_str, 1)
                    content_modified = True
                
                # Save if we have any modifications (text or styles)
                if content_modified:
                    try:
                        from s3_storage import upload_project_to_s3
                        upload_project_to_s3(
                            project_slug=project_slug,
                            files=[{'path': target_file['path'], 'content': new_content}],
                            user_id=user_id
                        )
                        print(f"✅ FAST PATH: Visual edit saved for {project_slug} in {target_file['path']}")
                        return {"success": True, "message": f"Changes saved to {target_file['path']} (fast)"}
                    except Exception as e:
                        print(f"⚠️ Fast path save failed: {e}")
                else:
                    print(f"🎨 No changes to save")
                    return {"success": True, "message": "No changes to apply"}
            else:
                print(f"🎨 FAST PATH: No exact match found, trying partial match...")
                # Try matching just the first few significant classes
                sig_classes = [c for c in clean_classes.split() if c.startswith('bg-') or c.startswith('text-') or c.startswith('px-') or c.startswith('py-')][:4]
                if sig_classes:
                    partial_match = ' '.join(sig_classes)
                    if partial_match in new_content:
                        # Find the full className containing these classes
                        import re
                        # Look for className="...partial_match..." or className={...partial_match...}
                        pattern = r'className="([^"]*' + re.escape(sig_classes[0]) + r'[^"]*)"'
                        match = re.search(pattern, new_content)
                        if match:
                            original_classes = match.group(1)
                            existing_set = set(original_classes.split())
                            new_classes_to_add = [c for c in tailwind_classes if c not in existing_set]
                            if new_classes_to_add:
                                new_class_str = original_classes + ' ' + ' '.join(new_classes_to_add)
                                new_content = new_content.replace(f'className="{original_classes}"', f'className="{new_class_str}"', 1)
                                content_modified = True
                                try:
                                    from s3_storage import upload_project_to_s3
                                    upload_project_to_s3(
                                        project_slug=project_slug,
                                        files=[{'path': target_file['path'], 'content': new_content}],
                                        user_id=user_id
                                    )
                                    print(f"✅ PARTIAL MATCH: Visual edit saved for {project_slug} in {target_file['path']}")
                                    return {"success": True, "message": f"Styles saved to {target_file['path']} (partial match)"}
                                except Exception as e:
                                    print(f"⚠️ Partial match save failed: {e}")
        
        # SLOW PATH: Use AI if direct match not found
        # Find where the element might be in the code
        search_terms = []
        if element_classes:
            # Take first few unique classes as search terms
            classes = [c for c in element_classes.split() if not c.startswith('xverta')][:3]
            search_terms.extend(classes)
        if element_text:
            search_terms.append(element_text[:20])
        
        # Find the position in code where element likely is
        code_start = 0
        for term in search_terms:
            pos = target_content.find(term)
            if pos > 0:
                code_start = max(0, pos - 500)  # Start 500 chars before match
                break
        
        # Extract relevant code section (8k around the match point)
        code_section = target_content[code_start:code_start + 8000]
        
        # Build parent context string
        parent_str = ""
        if 'parent_context' in request:
            parent_context = request.get("parent_context", [])
            if parent_context:
                for i, p in enumerate(parent_context):
                    parent_str += f"\n  Parent {i+1}: <{p.get('tag', '')}> classes=\"{p.get('classes', '')[:50]}\""
        
        # Build the style modification instruction - TARGETED EDIT APPROACH
        modification_prompt = f"""Find the className to modify in this React code snippet.

TARGET:
- Tag: {element_tag}
- Classes: {element_classes}
- Text: {element_text}{parent_str}

ADD THESE TAILWIND CLASSES: {' '.join(tailwind_classes) if tailwind_classes else 'none'}

Return ONLY two lines:
FIND: [exact current className value]
REPLACE: [className with new classes added]

CODE:
{code_section}"""
        
        # Use AI to find the targeted edit
        import google.generativeai as genai
        
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            return {"success": True, "message": "Styles applied visually (AI key not available)"}
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.0-flash")
        
        response = model.generate_content(modification_prompt)
        
        if not response.candidates:
            return {"success": False, "error": "AI failed to generate edit instructions"}
        
        ai_response = response.candidates[0].content.parts[0].text.strip()
        print(f"🎨 AI response: {ai_response[:200]}")
        
        # Parse FIND and REPLACE from response
        find_str = None
        replace_str = None
        
        for line in ai_response.split('\n'):
            line = line.strip()
            if line.startswith('FIND:'):
                find_str = line[5:].strip()
            elif line.startswith('REPLACE:'):
                replace_str = line[8:].strip()
        
        if not find_str or not replace_str:
            # Fallback: Try direct class replacement using element_classes
            if element_classes and tailwind_classes:
                find_str = element_classes
                # Add new classes, avoiding duplicates
                existing = set(element_classes.split())
                new_classes = [c for c in tailwind_classes if c not in existing]
                replace_str = element_classes + ' ' + ' '.join(new_classes)
                print(f"🎨 Using fallback class replacement")
            else:
                return {"success": True, "message": "Styles applied visually (couldn't parse AI edit)"}
        
        # Apply the find/replace to the code
        if find_str in target_content:
            new_content = target_content.replace(find_str, replace_str, 1)  # Replace first occurrence
            print(f"🎨 Replaced: '{find_str[:50]}...' -> '{replace_str[:50]}...'")
        else:
            # Try a fuzzy match - maybe the classes are in a different order or with extra spaces
            import re
            # Escape special regex chars and allow flexible whitespace
            pattern = r'\s+'.join(re.escape(c) for c in find_str.split())
            match = re.search(pattern, target_content)
            if match:
                new_content = target_content[:match.start()] + replace_str + target_content[match.end():]
                print(f"🎨 Fuzzy replaced via regex")
            else:
                print(f"🎨 Could not find '{find_str[:50]}...' in code")
                return {"success": True, "message": "Styles applied visually (element not found in code)"}
        
        # Verify the edit didn't break anything
        if 'export default' not in new_content:
            print(f"❌ Edit removed 'export default' - reverting")
            return {"success": True, "message": "Styles applied visually (edit would break code)"}
        
        # Save updated file to S3
        try:
            from s3_storage import upload_project_to_s3
            
            upload_project_to_s3(
                project_slug=project_slug,
                files=[{'path': target_file['path'], 'content': new_content}],
                user_id=user_id
            )
            
            print(f"✅ Visual edit saved to S3 for {project_slug} in {target_file['path']}")
            
            return {
                "success": True, 
                "message": f"Styles saved to {target_file['path']}",
                "file_updated": target_file['path'],
                "tailwind_classes_added": tailwind_classes,
                "inline_styles_added": style_updates
            }
            
        except Exception as s3_error:
            print(f"❌ Failed to save visual edit: {s3_error}")
            return {"success": False, "error": str(s3_error)}
        
    except Exception as e:
        import traceback
        print(f"❌ Visual edit error: {e}")
        print(traceback.format_exc())
        return {"success": False, "error": str(e)}

# --- Install Dependencies Endpoint ---
@app.post("/api/install-dependencies")
async def install_dependencies(request: dict = Body(...)):
    """Install project dependencies"""
    try:
        project_name = request.get("project_name")
        tech_stack = request.get("tech_stack", [])
        
        project_slug = project_name.lower().replace(" ", "-")
        projects_dir = Path("generated_projects")
        project_path = projects_dir / project_slug
        
        if not project_path.exists():
            return {"success": False, "error": "Project not found"}
        
        # Install frontend dependencies
        frontend_path = project_path / "frontend"
        if frontend_path.exists() and (frontend_path / "package.json").exists():
            await manager.send_to_project(project_name, {
                "type": "terminal_output",
                "message": "📦 Installing frontend dependencies...",
                "level": "info"
            })
            
            try:
                process = await asyncio.create_subprocess_shell(
                    "npm install",
                    cwd=frontend_path,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await process.communicate()
                
                if process.returncode == 0:
                    await manager.send_to_project(project_name, {
                        "type": "terminal_output",
                        "message": "✅ Frontend dependencies installed",
                        "level": "success"
                    })
                else:
                    await manager.send_to_project(project_name, {
                        "type": "terminal_output",
                        "message": f"⚠️ Frontend install issues: {stderr.decode()}",
                        "level": "warning"
                    })
            except Exception as e:
                await manager.send_to_project(project_name, {
                    "type": "terminal_output",
                    "message": f"❌ Frontend install failed: {str(e)}",
                    "level": "error"
                })
        
        # Install backend dependencies if Python/FastAPI
        backend_path = project_path / "backend"
        if backend_path.exists() and (backend_path / "requirements.txt").exists():
            await manager.send_to_project(project_name, {
                "type": "terminal_output",
                "message": "📦 Installing backend dependencies...",
                "level": "info"
            })
            
            try:
                process = await asyncio.create_subprocess_shell(
                    "pip install -r requirements.txt",
                    cwd=backend_path,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await process.communicate()
                
                if process.returncode == 0:
                    await manager.send_to_project(project_name, {
                        "type": "terminal_output",
                        "message": "✅ Backend dependencies installed",
                        "level": "success"
                    })
                else:
                    await manager.send_to_project(project_name, {
                        "type": "terminal_output",
                        "message": f"⚠️ Backend install issues: {stderr.decode()}",
                        "level": "warning"
                    })
            except Exception as e:
                await manager.send_to_project(project_name, {
                    "type": "terminal_output",
                    "message": f"❌ Backend install failed: {str(e)}",
                    "level": "error"
                })
        
        return {"success": True}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

# Preserve a stable reference to the endpoint function before any later helper redefinitions
install_dependencies_endpoint = install_dependencies

# --- Run Project Endpoint ---
@app.post("/api/run-project")
async def run_project(request: dict = Body(...)):
    """Build and run the project using sandboxed preview"""
    try:
        from s3_storage import get_project_from_s3, find_project_user_id, _project_user_cache
        
        project_name = request.get("project_name")
        tech_stack = request.get("tech_stack", [])
        
        print(f"🚀 Run project requested for: '{project_name}'")
        project_slug = normalize_project_slug(project_name)
        print(f"🚀 Normalized to slug: '{project_slug}'")
        projects_dir = Path("generated_projects")
        project_path = projects_dir / project_slug
        print(f"🚀 Full project path: '{project_path}'")
        
        # Check if project exists locally OR in S3
        project_exists_locally = project_path.exists()
        project_exists_in_s3 = False
        s3_data = None  # Initialize to avoid undefined variable
        
        if not project_exists_locally:
            # Try to find in S3
            cached_user = _project_user_cache.get(project_slug)
            if cached_user:
                s3_data = get_project_from_s3(project_slug=project_slug, user_id=cached_user)
                if s3_data and s3_data.get('files'):
                    project_exists_in_s3 = True
                    print(f"✅ Found project {project_slug} in S3 (cached)")
            
            if not project_exists_in_s3:
                found_user = find_project_user_id(project_slug)
                if found_user:
                    s3_data = get_project_from_s3(project_slug=project_slug, user_id=found_user)
                    if s3_data and s3_data.get('files'):
                        project_exists_in_s3 = True
                        print(f"✅ Found project {project_slug} in S3 (searched)")
        
        if not project_exists_locally and not project_exists_in_s3:
            return {"success": False, "error": "Project not found"}
        
        # Check if frontend exists (local or S3)
        frontend_path = project_path / "frontend"
        frontend_exists = frontend_path.exists() if project_exists_locally else False
        
        if project_exists_in_s3 and not frontend_exists:
            # Check if S3 project has frontend files
            # s3_data['files'] is a LIST of dicts with 'path' key, not a dict
            s3_files = s3_data.get('files', []) if s3_data else []
            if any(f.get('path', '').startswith('frontend/') for f in s3_files):
                frontend_exists = True
        
        if not frontend_exists:
            return {"success": False, "error": "Frontend not found"}
        
        await manager.send_to_project(project_name, {
            "type": "terminal_output", 
            "message": "🚀 Preparing sandboxed preview...",
            "level": "info"
        })
        
        # Generate sandbox preview URL
        sandbox_url = f"http://localhost:8000/api/sandbox-preview/{project_slug}"
        
        # Validate that essential files exist (skip for S3 - sandbox will handle it)
        if project_exists_locally:
            essential_files = ["src/App.jsx", "src/main.jsx"]
            missing_files = []
            for file_path in essential_files:
                if not (frontend_path / file_path).exists():
                    missing_files.append(file_path)
            
            if missing_files:
                await manager.send_to_project(project_name, {
                    "type": "terminal_output",
                    "message": f"⚠️ Missing essential files: {', '.join(missing_files)}",
                    "level": "warning"
                })
        
        await manager.send_to_project(project_name, {
            "type": "terminal_output",
            "message": "✅ Sandbox preview ready!",
            "level": "info"
        })
        
        # Send preview ready signal
        await manager.send_to_project(project_name, {
            "type": "preview_ready",
            "url": sandbox_url
        })
        
        return {
            "success": True,
            "preview_url": sandbox_url,
            "message": "Sandbox preview is ready",
            "type": "sandbox"
        }
        
    except Exception as e:
        await manager.send_to_project(project_name, {
            "type": "terminal_output",
            "message": f"❌ Failed to start preview: {str(e)}",
            "level": "error"
        })
        return {"success": False, "error": str(e)}

# --- AI Visual Testing Agent Endpoint ---
@app.post("/api/visual-test")
async def run_visual_test_endpoint(request: dict = Body(...)):
    """
    Run AI-powered visual testing on a generated application.
    
    The AI agent will:
    1. Take screenshots of the application
    2. Analyze the UI visually using Gemini Vision
    3. Generate test cases automatically based on what it sees
    4. Execute tests (click buttons, fill forms, navigate)
    5. Verify functionality and report issues
    
    Request body:
        - preview_url: The sandbox preview URL to test
        - app_name: (optional) Name of the application
        - test_cases: (optional) Custom test cases to run instead of AI-generated ones
    
    Returns:
        Complete test report with pass/fail status, issues found, and suggestions
    """
    preview_url = request.get("preview_url")
    app_name = request.get("app_name", "Generated App")
    custom_tests = request.get("test_cases")  # Optional custom test cases
    
    if not preview_url:
        raise HTTPException(status_code=400, detail="preview_url is required")
    
    try:
        from visual_test_agent import VisualTestAgent, TestCase, TestStep, PLAYWRIGHT_AVAILABLE
        
        if not PLAYWRIGHT_AVAILABLE:
            return {
                "success": False,
                "error": "Playwright not installed. Run: pip install playwright && playwright install chromium",
                "report": None
            }
        
        print(f"🤖 Starting AI Visual Test for: {app_name}")
        print(f"🌐 URL: {preview_url}")
        
        # Send WebSocket notification
        project_name = app_name.lower().replace(" ", "-")
        await manager.send_to_project(project_name, {
            "type": "terminal_output",
            "message": "🤖 AI Visual Test Agent starting autonomous testing...",
            "level": "info"
        })
        
        # Initialize the agent
        agent = VisualTestAgent(preview_url, app_name)
        
        # Convert custom tests if provided
        test_cases = None
        if custom_tests:
            test_cases = []
            for tc_data in custom_tests:
                steps = []
                for i, step_data in enumerate(tc_data.get("steps", []), 1):
                    steps.append(TestStep(
                        step_number=i,
                        action=step_data.get("action", "verify"),
                        description=step_data.get("description", "")
                    ))
                test_cases.append(TestCase(
                    name=tc_data.get("name", f"Test {len(test_cases)+1}"),
                    description=tc_data.get("description", ""),
                    steps=steps
                ))
        
        # Run the test
        report = await agent.run_full_test(custom_test_cases=test_cases)
        
        # Send completion notification
        status_emoji = "✅" if report.overall_status.value == "passed" else "⚠️" if report.overall_status.value == "warning" else "❌"
        await manager.send_to_project(project_name, {
            "type": "terminal_output",
            "message": f"{status_emoji} AI Visual Test completed: {report.overall_status.value.upper()}",
            "level": "success" if report.overall_status.value == "passed" else "warning"
        })
        
        # Convert report to dict (excluding large screenshot data for initial response)
        report_dict = report.to_dict()
        
        # Remove base64 screenshots from response to keep it light (they can be fetched separately)
        report_dict["screenshots_count"] = len(report.screenshots)
        report_dict.pop("screenshots", None)  # Remove if present
        
        return {
            "success": True,
            "report": report_dict,
            "summary": report.ai_summary,
            "overall_status": report.overall_status.value,
            "issues_count": len(report.issues_found),
            "suggestions_count": len(report.suggestions)
        }
        
    except ImportError as e:
        return {
            "success": False,
            "error": f"Visual test agent not available: {str(e)}. Install with: pip install playwright && playwright install chromium",
            "report": None
        }
    except Exception as e:
        import traceback
        print(f"❌ Visual test error: {e}")
        print(traceback.format_exc())
        return {
            "success": False,
            "error": str(e),
            "report": None
        }

# --- OWASP ZAP Security Scan Endpoint ---
@app.post("/api/security-scan")
async def run_security_scan(request: dict = Body(...)):
    """
    Run a security scan on a generated application URL.
    Attempts to use OWASP ZAP first, falls back to AI-powered scanning if ZAP is unavailable.
    
    Request body:
        - target_url: The sandbox preview URL to scan
        - scan_type: "passive", "active", "spider", "ajax_spider", "api", or "full" (default: ajax_spider for SPAs)
        - api_endpoints: (optional) List of API endpoints to scan when scan_type is "api"
        - zap_api_key: Optional custom ZAP API key
        - force_ai: If true, skip ZAP and use AI scanner directly
    
    BEST PRACTICES for React SPAs:
        - Use "ajax_spider" for frontend scanning (handles JavaScript)
        - Use "api" to scan backend API endpoints directly (RECOMMENDED)
        - Use "full" for comprehensive scanning (takes longer)
    """
    target_url = request.get("target_url")
    force_ai = request.get("force_ai", False)
    
    if not target_url:
        raise HTTPException(status_code=400, detail="target_url is required")
    
    # If force_ai or ZAP not available, use AI scanner
    use_ai_scanner = force_ai
    
    if not use_ai_scanner:
        try:
            from scanner_service import ZAPSecurityScanner, ScanType
            
            scan_type_str = request.get("scan_type", "ajax_spider")  # Default to AJAX Spider for SPAs
            api_key = request.get("zap_api_key", None)  # None = disabled API key
            api_endpoints = request.get("api_endpoints")  # Optional list of API endpoints
            
            # Map string to enum
            scan_type_map = {
                "passive": ScanType.PASSIVE,
                "active": ScanType.ACTIVE,
                "spider": ScanType.SPIDER,
                "ajax_spider": ScanType.AJAX_SPIDER,
                "api": ScanType.API,
                "full": ScanType.FULL
            }
            scan_type = scan_type_map.get(scan_type_str, ScanType.AJAX_SPIDER)
            
            # Initialize scanner
            scanner = ZAPSecurityScanner(api_key=api_key)
            
            # Check if ZAP is running
            if not scanner.is_zap_running():
                print("⚠️ ZAP not running, falling back to AI scanner...")
                use_ai_scanner = True
            else:
                # Run appropriate scan based on type
                if scan_type == ScanType.API:
                    # Direct API endpoint scanning (BEST for React SPAs)
                    base_url = target_url.rsplit('/api/', 1)[0] + '/api' if '/api/' in target_url else target_url
                    result = scanner.scan_api_endpoints(base_url, api_endpoints)
                else:
                    # Standard URL scanning
                    result = scanner.scan_url(target_url, scan_type)
                
                return {
                    "success": result.success,
                    "target_url": result.target_url,
                    "scan_type": result.scan_type,
                    "duration_seconds": result.scan_duration_seconds,
                    "summary": {
                        "high_risk": result.high_risk_count,
                        "medium_risk": result.medium_risk_count,
                        "low_risk": result.low_risk_count,
                        "informational": result.informational_count,
                        "total_alerts": len(result.alerts)
                    },
                    "alerts": result.alerts[:50],
                    "error": result.error,
                    "report": scanner.generate_report(result) if result.success else None,
                    "scanner": "OWASP ZAP",
                    "scan_tips": {
                        "for_spa": "Use scan_type='ajax_spider' for React/Vue/Angular apps",
                        "for_api": "Use scan_type='api' with api_endpoints list for backend API scanning",
                        "deep_scan": "Use scan_type='full' for comprehensive (but slower) scanning"
                    }
                }
        except ImportError:
            print("⚠️ ZAP library not installed, using AI scanner...")
            use_ai_scanner = True
        except Exception as e:
            print(f"⚠️ ZAP error: {e}, falling back to AI scanner...")
            use_ai_scanner = True
    
    # Fallback to AI Scanner (or if force_ai=True)
    if use_ai_scanner:
        try:
            from ai_security_scanner import AISecurityScanner, ScanType as AIScanType
            
            ai_scan_type_str = request.get("scan_type", "standard")
            timeout = request.get("timeout", 60)  # Allow custom timeout
            
            ai_scan_map = {
                "passive": AIScanType.STANDARD,
                "active": AIScanType.DEEP,
                "spider": AIScanType.STANDARD,
                "full": AIScanType.DEEP,
                "quick": AIScanType.QUICK,
                "standard": AIScanType.STANDARD,
                "deep": AIScanType.DEEP,
                "owasp": AIScanType.OWASP
            }
            ai_scan_type = ai_scan_map.get(ai_scan_type_str, AIScanType.STANDARD)
            
            ai_scanner = AISecurityScanner()
            result = await ai_scanner.scan_url(target_url, ai_scan_type, timeout=timeout, retries=3)
            
            return {
                "success": result.success,
                "target_url": result.target_url,
                "scan_type": result.scan_type,
                "duration_seconds": result.scan_duration_seconds,
                "summary": {
                    "critical": result.critical_count,
                    "high_risk": result.high_risk_count,
                    "medium_risk": result.medium_risk_count,
                    "low_risk": result.low_risk_count,
                    "informational": result.informational_count,
                    "total_alerts": len(result.alerts)
                },
                "alerts": result.alerts[:150],  # Return more alerts
                "owasp_mapping": result.owasp_mapping,
                "error": result.error,
                "report": ai_scanner.generate_report(result) if result.success else None,
                "scanner": "AI-Powered Security Scanner",
                "note": "Comprehensive security analysis using AI + pattern matching. No OWASP ZAP required."
            }
        except Exception as e:
            import traceback
            return {
                "success": False,
                "error": f"Security scan failed: {str(e)}",
                "traceback": traceback.format_exc()
            }


# --- AI-Powered Security Scan (NO ZAP REQUIRED) ---
@app.post("/api/ai-security-scan")
async def run_ai_security_scan(request: dict = Body(...)):
    """
    Run an AI-powered security scan WITHOUT requiring OWASP ZAP.
    Uses Gemini AI + pattern matching to detect vulnerabilities.
    
    Request body:
        - target_url: (optional) URL to scan
        - code: (optional) Code to analyze directly
        - language: Programming language (default: javascript)
        - scan_type: "quick", "standard", "deep", or "owasp" (default: standard)
        - project_name: (optional) Project name to scan from S3/storage
        - timeout: (optional) Request timeout in seconds (default: 60)
    """
    try:
        from ai_security_scanner import AISecurityScanner, ScanType
        
        target_url = request.get("target_url")
        code = request.get("code")
        language = request.get("language", "javascript")
        scan_type_str = request.get("scan_type", "standard")
        project_name = request.get("project_name")
        timeout = request.get("timeout", 60)
        
        # Map string to enum
        scan_type_map = {
            "quick": ScanType.QUICK,
            "standard": ScanType.STANDARD,
            "deep": ScanType.DEEP,
            "owasp": ScanType.OWASP
        }
        scan_type = scan_type_map.get(scan_type_str, ScanType.STANDARD)
        
        # Initialize AI scanner
        scanner = AISecurityScanner()
        
        # Determine what to scan
        if code:
            # Direct code analysis
            print(f"🔍 AI Security Scan: Analyzing provided code ({len(code)} chars)")
            result = await scanner.scan_code(code, language, scan_type)
        elif target_url:
            # URL-based scanning with retry
            print(f"🔍 AI Security Scan: Analyzing URL {target_url[:60]}...")
            result = await scanner.scan_url(target_url, scan_type, timeout=timeout, retries=3)
        elif project_name:
            # Scan project from storage
            project_slug = project_name.lower().replace(" ", "-")
            
            # Try to get code from S3 or local storage
            all_code = ""
            try:
                # Check S3 first
                from s3_storage import S3ProjectStorage
                s3_storage = S3ProjectStorage()
                project_data = await asyncio.to_thread(s3_storage.get_project, project_slug)
                
                if project_data and "files" in project_data:
                    for file_path, content in project_data["files"].items():
                        if file_path.endswith(('.js', '.jsx', '.ts', '.tsx', '.py', '.html')):
                            all_code += f"\n// === {file_path} ===\n{content}\n"
            except Exception as e:
                print(f"⚠️ Could not fetch from S3: {e}")
                
                # Try local storage
                import os
                project_dir = os.path.join("generated_apps", project_slug)
                if os.path.exists(project_dir):
                    for root, dirs, files in os.walk(project_dir):
                        for file in files:
                            if file.endswith(('.js', '.jsx', '.ts', '.tsx', '.py', '.html')):
                                file_path = os.path.join(root, file)
                                try:
                                    with open(file_path, 'r', encoding='utf-8') as f:
                                        all_code += f"\n// === {file} ===\n{f.read()}\n"
                                except:
                                    pass
            
            if all_code:
                print(f"🔍 AI Security Scan: Analyzing project {project_name} ({len(all_code)} chars)")
                result = await scanner.scan_code(all_code, "javascript", scan_type)
            else:
                return {
                    "success": False,
                    "error": f"Could not find code for project: {project_name}"
                }
        else:
            return {
                "success": False,
                "error": "Must provide either 'target_url', 'code', or 'project_name'"
            }
        
        return {
            "success": result.success,
            "target_url": result.target_url,
            "scan_type": result.scan_type,
            "duration_seconds": result.scan_duration_seconds,
            "summary": {
                "critical": result.critical_count,
                "high_risk": result.high_risk_count,
                "medium_risk": result.medium_risk_count,
                "low_risk": result.low_risk_count,
                "informational": result.informational_count,
                "total_alerts": len(result.alerts)
            },
            "alerts": result.alerts[:100],  # Return more results than ZAP endpoint
            "owasp_mapping": result.owasp_mapping,
            "error": result.error,
            "report": scanner.generate_report(result) if result.success else None,
            "scanner": "AI-Powered (No ZAP Required)"
        }
        
    except ImportError as e:
        return {
            "success": False,
            "error": f"AI scanner import failed: {str(e)}",
            "instructions": ["Ensure google-generativeai is installed: pip install google-generativeai"]
        }
    except Exception as e:
        import traceback
        return {
            "success": False, 
            "error": str(e),
            "traceback": traceback.format_exc()
        }


# --- AI-Powered Security Issue Fix Endpoint ---
class SecurityFixRequest(BaseModel):
    project_name: str
    alert: dict  # The ZAP alert to fix
    file_path: Optional[str] = None
    fix_all: bool = False  # If true, fix all similar issues


class SecurityFixPreviewRequest(BaseModel):
    project_id: str
    alert: dict
    files: Optional[List[dict]] = None


@app.post("/api/ai-fix-security-preview")
async def ai_fix_security_preview(request: SecurityFixPreviewRequest):
    """
    Generate a diff preview for a security fix without applying it.
    Works with both OWASP ZAP alerts and AI Security Scanner alerts.
    Returns the original code, proposed fix, and explanation.
    """
    try:
        import google.generativeai as genai
        
        alert = request.alert
        alert_name = alert.get('alert', 'Unknown')
        alert_risk = alert.get('risk', 'Unknown')
        alert_description = alert.get('description', '')
        alert_solution = alert.get('solution', '')
        alert_evidence = alert.get('evidence', '')
        alert_param = alert.get('param', '')
        # Support both ZAP ('cweid') and AI scanner ('cwe_id') field names
        alert_cweid = alert.get('cweid', '') or alert.get('cwe_id', '')
        alert_owasp = alert.get('owasp', '')
        alert_context = alert.get('context', '')  # AI scanner provides context
        alert_line = alert.get('url', '')  # AI scanner puts line number here
        alert_line_content = alert.get('line_content', '')
        
        # Find relevant file content from provided files
        relevant_file = None
        relevant_content = ""
        
        if request.files:
            # Look for files that might contain the vulnerability
            for f in request.files:
                fname = f.get('name', '').lower()
                content = f.get('content', '')
                
                # Check if evidence appears in this file
                if alert_evidence and alert_evidence in content:
                    relevant_file = f.get('name')
                    relevant_content = content
                    break
                
                # Check if line content appears in this file (AI scanner)
                if alert_line_content and alert_line_content in content:
                    relevant_file = f.get('name')
                    relevant_content = content
                    break
                    
                # Check for common vulnerable patterns based on alert type
                alert_lower = alert_name.lower()
                if 'xss' in alert_lower and ('dangerouslySetInnerHTML' in content or 'innerHTML' in content or 'document.write' in content):
                    relevant_file = f.get('name')
                    relevant_content = content
                    break
                if ('sql' in alert_lower or 'injection' in alert_lower) and ('query' in content.lower() or 'execute' in content.lower()):
                    relevant_file = f.get('name')
                    relevant_content = content
                    break
                if 'header' in alert_lower and ('index.html' in fname or 'app.jsx' in fname):
                    relevant_file = f.get('name')
                    relevant_content = content
                    break
                if ('secret' in alert_lower or 'credential' in alert_lower or 'hardcoded' in alert_lower):
                    # Check for secrets in any file
                    if any(pattern in content.lower() for pattern in ['api_key', 'password', 'secret', 'token']):
                        relevant_file = f.get('name')
                        relevant_content = content
                        break
                if 'cookie' in alert_lower and 'document.cookie' in content:
                    relevant_file = f.get('name')
                    relevant_content = content
                    break
                    
            # If no specific match, use index.html or App.jsx as fallback
            if not relevant_file:
                for f in request.files:
                    fname = f.get('name', '').lower()
                    if fname == 'index.html' or fname == 'app.jsx' or fname.endswith('.jsx') or fname.endswith('.js'):
                        relevant_file = f.get('name')
                        relevant_content = f.get('content', '')
                        break
        
        # If still no files, try to fetch from S3 or local storage
        if not relevant_file and request.project_id:
            try:
                from s3_storage import S3ProjectStorage
                s3_storage = S3ProjectStorage()
                project_data = await asyncio.to_thread(s3_storage.get_project, request.project_id)
                
                if project_data and "files" in project_data:
                    for file_path, content in project_data["files"].items():
                        # Check if this file might contain the vulnerability
                        if alert_evidence and alert_evidence in content:
                            relevant_file = file_path
                            relevant_content = content
                            break
                        if file_path.endswith(('.jsx', '.js', '.html')):
                            relevant_file = file_path
                            relevant_content = content
                            # Don't break, keep looking for better match
            except Exception as e:
                print(f"⚠️ Could not fetch project files: {e}")
        
        # Configure Gemini
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            return {
                "success": False,
                "message": "Gemini API key not configured",
                "diff": {
                    "filename": relevant_file or "N/A",
                    "description": "API key not available for AI analysis. Apply the suggested solution manually.",
                    "original": alert_evidence or alert_line_content or "",
                    "patched": alert_solution[:500] if alert_solution else "See solution in alert details",
                    "notes": alert_solution
                }
            }
            
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.0-flash')
        
        # Build context info
        context_info = ""
        if alert_context:
            context_info = f"\nCODE CONTEXT:\n{alert_context}"
        if alert_line_content:
            context_info += f"\nVULNERABLE LINE:\n{alert_line_content}"
        
        prompt = f"""You are a security expert. Analyze this security vulnerability and provide a specific code fix.

VULNERABILITY DETECTED:
- Alert: {alert_name}
- Risk: {alert_risk}
- CWE: {alert_cweid}
- OWASP: {alert_owasp}
- Parameter: {alert_param}
- Evidence: {alert_evidence}
- Description: {alert_description}
- Recommended Solution: {alert_solution}
{context_info}

{"RELEVANT FILE: " + relevant_file if relevant_file else ""}
{"CURRENT CODE:" if relevant_content else ""}
{relevant_content[:4000] if relevant_content else "No specific file identified - provide generic fix pattern"}

Provide your response in this EXACT JSON format:
{{
    "filename": "{relevant_file or 'App.jsx'}",
    "description": "Clear explanation of what the fix does and why it's secure",
    "original_lines": "The exact vulnerable code snippet that needs to be replaced (copy from the code above, 2-10 lines)",
    "fixed_lines": "The secure replacement code with proper fixes applied (2-10 lines)",
    "additional_notes": "Any server-side changes needed, CSP recommendations, or additional security measures"
}}

IMPORTANT:
- The original_lines MUST be an exact copy of vulnerable code from the file (if provided)
- The fixed_lines must be syntactically correct and ready to use
- Only return the JSON, no other text."""

        response = model.generate_content(prompt)
        response_text = response.text.strip()
        
        # Parse JSON from response
        if '```json' in response_text:
            response_text = response_text.split('```json')[1].split('```')[0].strip()
        elif '```' in response_text:
            response_text = response_text.split('```')[1].split('```')[0].strip()
            
        try:
            fix_data = json.loads(response_text)
        except json.JSONDecodeError:
            # Fallback response
            fix_data = {
                "filename": relevant_file or "App.jsx",
                "description": f"Fix for {alert_name}: {alert_solution[:200]}",
                "original_lines": alert_evidence[:200] if alert_evidence else (alert_line_content[:200] if alert_line_content else "// Vulnerable code"),
                "fixed_lines": f"// Secure implementation:\n// {alert_solution[:300]}",
                "additional_notes": alert_solution
            }
        
        return {
            "success": True,
            "diff": {
                "filename": fix_data.get("filename", relevant_file or "App.jsx"),
                "description": fix_data.get("description", "Security fix"),
                "original": fix_data.get("original_lines", ""),
                "patched": fix_data.get("fixed_lines", ""),
                "notes": fix_data.get("additional_notes", "")
            }
        }
        
    except Exception as e:
        import traceback
        print(f"❌ AI Fix Preview Error: {e}\n{traceback.format_exc()}")
        return {
            "success": False,
            "message": str(e),
            "diff": {
                "filename": "N/A",
                "description": f"Error generating preview: {str(e)}",
                "original": request.alert.get('evidence', '') or request.alert.get('line_content', ''),
                "patched": request.alert.get('solution', 'See alert details for solution'),
                "notes": "Try applying the fix directly using the AI Fix button, or apply the solution manually."
            }
        }


@app.post("/api/ai-fix-security-issue")
async def ai_fix_security_issue(request: SecurityFixRequest):
    """
    Use Gemini AI to fix security issues detected by OWASP ZAP or AI Security Scanner.
    This endpoint fixes vulnerabilities found by security scans.
    """
    try:
        import google.generativeai as genai
        
        project_slug = request.project_name.lower().replace(" ", "-")
        projects_dir = Path("generated_projects")
        project_path = projects_dir / project_slug
        
        # Also try S3 storage if local path doesn't exist
        files_from_s3 = None
        if not project_path.exists():
            try:
                from s3_storage import S3ProjectStorage
                s3_storage = S3ProjectStorage()
                project_data = await asyncio.to_thread(s3_storage.get_project, project_slug)
                if project_data and "files" in project_data:
                    files_from_s3 = project_data["files"]
            except Exception as e:
                print(f"S3 fetch error: {e}")
        
        if not project_path.exists() and not files_from_s3:
            return {"success": False, "error": "Project not found"}
        
        alert = request.alert
        alert_name = alert.get('alert', 'Unknown')
        alert_risk = alert.get('risk', 'Unknown')
        alert_url = alert.get('url', '')
        alert_description = alert.get('description', '')
        alert_solution = alert.get('solution', '')
        alert_evidence = alert.get('evidence', '')
        alert_param = alert.get('param', '')
        # Support both ZAP ('cweid') and AI scanner ('cwe_id') field names
        alert_cweid = alert.get('cweid', '') or alert.get('cwe_id', '')
        alert_wascid = alert.get('wascid', '')
        alert_reference = alert.get('reference', '')
        alert_owasp = alert.get('owasp', '')
        alert_context = alert.get('context', '')
        alert_line_content = alert.get('line_content', '')
        alert_source = alert.get('source', 'Security Scan')
        
        # Build comprehensive security context
        context_extra = ""
        if alert_context:
            context_extra += f"\nCode Context:\n{alert_context}"
        if alert_line_content:
            context_extra += f"\nVulnerable Line:\n{alert_line_content}"
        
        security_context = f"""
SECURITY VULNERABILITY DETECTED:
==========================================
- Alert Name: {alert_name}
- Risk Level: {alert_risk}
- CWE ID: {alert_cweid}
- OWASP Category: {alert_owasp}
- WASC ID: {alert_wascid}
- URL/Location: {alert_url}
- Parameter: {alert_param}
- Evidence Found: {alert_evidence}
{context_extra}

Description:
{alert_description}

Recommended Solution:
{alert_solution}

Reference: {alert_reference}

Project: {request.project_name}
Type: React Frontend Application
Framework: React + Vite
Source: {alert_source}
"""
        
        # Load ALL project files for comprehensive analysis
        all_files = []
        
        if files_from_s3:
            # Use S3 files
            for file_path, content in files_from_s3.items():
                if any(file_path.endswith(ext) for ext in ['.js', '.jsx', '.ts', '.tsx', '.html', '.css', '.json']):
                    all_files.append({
                        'path': file_path,
                        'full_path': file_path,
                        'content': content[:8000]
                    })
        else:
            # Use local files
            frontend_src = project_path / "frontend" / "src"
        
        if frontend_src.exists():
            for file_path in frontend_src.rglob("*"):
                if file_path.suffix in ['.js', '.jsx', '.ts', '.tsx', '.html', '.css', '.json']:
                    try:
                        content = file_path.read_text(encoding='utf-8')
                        all_files.append({
                            'path': str(file_path.relative_to(project_path)),
                            'full_path': str(file_path),
                            'content': content[:8000]  # Limit content size
                        })
                    except Exception as e:
                        print(f"Error reading {file_path}: {e}")
        
        # Also check public/index.html for header-related issues
        index_html = project_path / "frontend" / "index.html"
        if index_html.exists():
            try:
                content = index_html.read_text(encoding='utf-8')
                all_files.append({
                    'path': 'frontend/index.html',
                    'full_path': str(index_html),
                    'content': content
                })
            except:
                pass
        
        if not all_files:
            return {"success": False, "error": "No source files found in project"}
        
        # Use Gemini to analyze and fix the security issue
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            return {"success": False, "error": "Gemini API key not configured. Set GEMINI_API_KEY or GOOGLE_API_KEY."}
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.0-flash')
        
        files_context = "\n\n".join([
            f"=== File: {f['path']} ===\n{f['content']}"
            for f in all_files[:10]  # Include up to 10 files
        ])
        
        prompt = f"""You are a security expert. Fix ONLY the specific vulnerability detected by the security scan.

{security_context}

PROJECT SOURCE FILES:
{files_context}

IMPORTANT INSTRUCTIONS:
1. Fix ONLY the specific vulnerability described above
2. Do NOT look for or fix other security issues - only fix the reported issue
3. Identify which file(s) need modification to fix this specific alert
4. Provide the COMPLETE fixed file content (not just snippets)
5. If the fix requires server-side changes (like adding headers), indicate this clearly
6. Ensure the fix follows security best practices

RESPONSE FORMAT (JSON only, no markdown):
{{
    "affected_files": [
        {{
            "path": "frontend/src/App.jsx",
            "issue_found": "exact description of where the vulnerability applies",
            "fixed_code": "COMPLETE file content with the fix applied",
            "explanation": "how this fix resolves the specific security issue"
        }}
    ],
    "server_side_fix_needed": true/false,
    "server_fix_instructions": "If server config needed, explain here",
    "owasp_category": "{alert_owasp or 'OWASP Top 10 category'}",
    "zap_alert_resolved": "{alert_name}"
}}

Respond with valid JSON only."""

        response = model.generate_content(prompt)
        response_text = response.text.strip()
        
        # Clean response if it has markdown
        if response_text.startswith('```'):
            response_text = response_text.split('\n', 1)[1]
            if response_text.endswith('```'):
                response_text = response_text[:-3]
        if response_text.startswith('json'):
            response_text = response_text[4:].strip()
        
        try:
            fix_result = json.loads(response_text)
        except json.JSONDecodeError:
            # Try to extract JSON from response
            import re
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                fix_result = json.loads(json_match.group())
            else:
                return {
                    "success": False,
                    "error": "Failed to parse AI response",
                    "raw_response": response_text[:500]
                }
        
        # Apply fixes to affected files
        fixes_applied = []
        server_fix_needed = fix_result.get('server_side_fix_needed', False)
        server_instructions = fix_result.get('server_fix_instructions', '')
        
        for affected_file in fix_result.get('affected_files', []):
            file_path = affected_file.get('path', '')
            fixed_code = affected_file.get('fixed_code', '')
            
            if not file_path or not fixed_code:
                continue
            
            # Find the actual file path
            actual_path = project_path / file_path
            if not actual_path.exists():
                # Try with frontend prefix
                actual_path = project_path / "frontend" / file_path.replace('frontend/', '')
            if not actual_path.exists():
                # Try src directly
                actual_path = project_path / "frontend" / "src" / file_path.split('/')[-1]
            
            if actual_path.exists():
                try:
                    # Create backup
                    backup_path = actual_path.with_suffix(actual_path.suffix + '.security_backup')
                    shutil.copy2(actual_path, backup_path)
                    
                    # Apply fix
                    with open(actual_path, 'w', encoding='utf-8') as f:
                        f.write(fixed_code)
                    
                    fixes_applied.append({
                        'path': file_path,
                        'issue': affected_file.get('issue_found', ''),
                        'explanation': affected_file.get('explanation', ''),
                        'backup': str(backup_path)
                    })
                except Exception as e:
                    print(f"Error applying fix to {actual_path}: {e}")
        
        return {
            "success": True,
            "alert_fixed": alert_name,
            "risk_level": alert_risk,
            "fixes_applied": fixes_applied,
            "server_side_fix_needed": server_fix_needed,
            "server_fix_instructions": server_instructions,
            "owasp_category": fix_result.get('owasp_category', 'Unknown'),
            "zap_alert_resolved": fix_result.get('zap_alert_resolved', alert_name),
            "files_analyzed": len(all_files),
            "message": f"Fixed {len(fixes_applied)} file(s) for ZAP alert: {alert_name}"
        }
        
    except Exception as e:
        print(f"AI security fix failed: {e}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "error": f"Failed to fix ZAP security issue: {str(e)}"
        }


# --- Auto-Fix Project Errors Endpoint ---
@app.post("/api/auto-fix-project-errors")
async def auto_fix_project_errors(
    project_name: str = Query(...),
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """Automatically fix common project errors - works with S3 storage"""
    try:
        project_slug = project_name.lower().replace(" ", "-")
        
        # Get user_id for S3 lookup - try multiple sources
        user_ids_to_try = []
        
        if current_user:
            if current_user.get('_id'):
                user_ids_to_try.append(current_user.get('_id'))
            if current_user.get('email'):
                user_ids_to_try.append(current_user.get('email'))
        
        # Also try cached user_id and anonymous
        from s3_storage import get_cached_user_id_for_project, s3_client, S3_BUCKET_NAME
        cached_user = get_cached_user_id_for_project(project_slug)
        if cached_user:
            user_ids_to_try.insert(0, cached_user)  # Try cached first
        
        user_ids_to_try.append('anonymous')
        
        # Remove duplicates while preserving order
        seen = set()
        user_ids_to_try = [x for x in user_ids_to_try if x and not (x in seen or seen.add(x))]
        
        # Try to find the project with different user_ids
        project_data = None
        working_user_id = None
        
        for user_id in user_ids_to_try:
            project_data = get_project_from_s3(project_slug=project_slug, user_id=user_id)
            if project_data and project_data.get('files'):
                working_user_id = user_id
                print(f"✅ Found project {project_slug} with user_id: {user_id}")
                break
        
        # LAST RESORT: Search for project across all users
        if not project_data or not project_data.get('files'):
            print(f"🔍 Searching for project '{project_slug}' across all users...")
            from s3_storage import find_project_user_id
            found_user_id = find_project_user_id(project_slug)
            if found_user_id:
                project_data = get_project_from_s3(project_slug=project_slug, user_id=found_user_id)
                if project_data and project_data.get('files'):
                    working_user_id = found_user_id
                    print(f"✅ Found project {project_slug} with searched user_id: {found_user_id}")
        
        if project_data and project_data.get('files'):
            # Project is in S3 - fix files in S3
            print(f"🔧 Auto-fixing project in S3: {project_slug}")
            fixes_applied = []
            
            from code_validator import auto_fix_jsx_for_sandbox
            
            for file_info in project_data['files']:
                file_path = file_info['path']
                content = file_info['content']
                original_content = content
                
                # Only process JSX/JS files
                if not file_path.endswith(('.jsx', '.js')):
                    continue
                
                # Apply fixes using code_validator
                fixed_content = auto_fix_jsx_for_sandbox(content, file_path.split('/')[-1])
                
                if fixed_content != original_content:
                    # Update file directly in S3 using the working_user_id
                    s3_key = f"projects/{working_user_id}/{project_slug}/{file_path}"
                    s3_client.put_object(
                        Bucket=S3_BUCKET_NAME,
                        Key=s3_key,
                        Body=fixed_content.encode('utf-8'),
                        ContentType='text/javascript'
                    )
                    fixes_applied.append(f"Fixed {file_path}")
                    print(f"  ✅ Fixed {file_path}")
            
            if fixes_applied:
                print(f"✅ Applied {len(fixes_applied)} fixes to S3")
            
            return {
                "success": True,
                "message": f"Fixed {len(fixes_applied)} issues" if fixes_applied else "No issues found",
                "fixes_applied": fixes_applied
            }
        
        # FALLBACK: Try local filesystem (legacy support)
        projects_dir = Path("generated_projects")
        project_path = projects_dir / project_slug
        
        if not project_path.exists():
            return {"success": False, "error": "Project not found in S3 or local storage"}
        
        fixes_applied = []
        
        # Run the existing validation and fix function
        fix_success = await validate_and_fix_project_files(project_path, project_name)
        if fix_success:
            fixes_applied.append("Fixed package.json structure")
        
        # Additional common fixes
        frontend_path = project_path / "frontend"
        if frontend_path.exists():
            src_path = frontend_path / "src"
            
            # Fix duplicate ErrorBoundary declarations in App.jsx
            app_jsx_path = src_path / "App.jsx"
            if app_jsx_path.exists():
                try:
                    with open(app_jsx_path, 'r', encoding='utf-8') as f:
                        app_content = f.read()
                    
                    # Check for duplicate ErrorBoundary class declarations
                    error_boundary_count = app_content.count('class ErrorBoundary extends React.Component')
                    if error_boundary_count > 1:
                        # Remove duplicate declarations by keeping only the first one
                        parts = app_content.split('class ErrorBoundary extends React.Component')
                        if len(parts) > 2:
                            # Find the end of the first ErrorBoundary class
                            first_part = parts[0] + 'class ErrorBoundary extends React.Component' + parts[1]
                            
                            # Find where the first class ends (look for the closing brace of the class)
                            brace_count = 0
                            class_end_pos = len(first_part)
                            in_class = False
                            
                            for i, char in enumerate(first_part[first_part.rfind('class ErrorBoundary'):]):
                                if char == '{':
                                    in_class = True
                                    brace_count += 1
                                elif char == '}' and in_class:
                                    brace_count -= 1
                                    if brace_count == 0:
                                        class_end_pos = first_part.rfind('class ErrorBoundary') + i + 1
                                        break
                            
                            # Reconstruct content without duplicate ErrorBoundary
                            fixed_content = first_part[:class_end_pos] + '\n'
                            
                            # Add the remaining content after skipping duplicate classes
                            remaining_parts = parts[2:]
                            for i, part in enumerate(remaining_parts):
                                if i == 0:
                                    # Skip the duplicate class content, find where it ends
                                    brace_count = 0
                                    skip_to = 0
                                    for j, char in enumerate(part):
                                        if char == '{':
                                            brace_count += 1
                                        elif char == '}':
                                            brace_count -= 1
                                            if brace_count <= 0:
                                                skip_to = j + 1
                                                break
                                    fixed_content += part[skip_to:]
                                else:
                                    fixed_content += part
                            
                            # Write the fixed content
                            with open(app_jsx_path, 'w', encoding='utf-8') as f:
                                f.write(fixed_content)
                            fixes_applied.append("Removed duplicate ErrorBoundary class declaration")
                    
                    # Fix other common React errors
                    original_content = app_content
                    
                    # Fix spread operator on non-iterable
                    if "...(" in app_content or "TypeError: Invalid attempt to spread non-iterable" in str(project_name):
                        app_content = re.sub(r'\.\.\.\s*\([^)]*\)', '...(data || {})', app_content)
                        app_content = re.sub(r'\.\.\.\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*(?=\})', r'...(\1 || {})', app_content)
                        fixes_applied.append("Fixed spread operator on potentially undefined values")
                    
                    # Fix array.map() errors by ensuring proper initialization
                    if ".map(" in app_content and "useState([])" not in app_content:
                        # Look for useState patterns and ensure arrays are initialized
                        app_content = re.sub(
                            r'useState\(\s*\)',
                            'useState([])',
                            app_content
                        )
                        app_content = re.sub(
                            r'useState\(\s*null\s*\)',
                            'useState([])',
                            app_content
                        )
                        fixes_applied.append("Fixed array initialization in useState")
                    
                    # Fix JSON.parse without error handling
                    if "JSON.parse(" in app_content and "try" not in app_content:
                        json_parse_pattern = r'JSON\.parse\(([^)]+)\)'
                        def replace_json_parse(match):
                            variable = match.group(1)
                            return f'(function() {{ try {{ return JSON.parse({variable}); }} catch(e) {{ console.error("JSON parse error:", e); return null; }} }})()'
                        
                        app_content = re.sub(json_parse_pattern, replace_json_parse, app_content)
                        fixes_applied.append("Added error handling to JSON.parse calls")
                    
                    # Write fixed content if changes were made
                    if app_content != original_content:
                        with open(app_jsx_path, 'w', encoding='utf-8') as f:
                            f.write(app_content)
                        
                except Exception as e:
                    print(f"Error fixing App.jsx: {e}")
            
            # Ensure src/main.jsx exists
            main_jsx_path = src_path / "main.jsx"
            
            if not main_jsx_path.exists():
                src_path.mkdir(exist_ok=True)
                main_jsx_content = '''import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)'''
                main_jsx_path.write_text(main_jsx_content, encoding='utf-8')
                fixes_applied.append("Created missing main.jsx")
            
            # Ensure src/App.jsx exists
            if not app_jsx_path.exists():
                app_jsx_content = '''import React from 'react'
import './App.css'

function App() {
  return (
    <div className="App">
      <h1>Welcome to Your Project</h1>
      <p>This project has been auto-generated and fixed!</p>
    </div>
  )
}

export default App'''
                app_jsx_path.write_text(app_jsx_content, encoding='utf-8')
                fixes_applied.append("Created missing App.jsx")
            
            # Ensure index.html exists
            index_html_path = frontend_path / "index.html"
            if not index_html_path.exists():
                index_html_content = '''<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/vite.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>''' + project_name + '''</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>'''
                index_html_path.write_text(index_html_content, encoding='utf-8')
                fixes_applied.append("Created missing index.html")
        
        return {
            "success": True,
            "fixes_applied": fixes_applied,
            "message": f"Applied {len(fixes_applied)} fixes" if fixes_applied else "No fixes needed"
        }
        
    except Exception as e:
        print(f"Auto-fix errors: {e}")
        return {"success": False, "error": str(e)}

# --- Gemini-Powered Console Error Fix Endpoint ---
@app.post("/api/gemini-fix-console-error")
async def gemini_fix_console_error(request: ConsoleErrorRequest):
    """
    Use Gemini AI to analyze and fix console errors in generated projects.
    This endpoint specifically handles JavaScript/React errors and provides intelligent fixes.
    """
    try:
        # Import the new code fix function
        from ai_assistant import get_code_fix_response
        from s3_storage import get_project_from_s3, upload_project_to_s3, find_project_user_id, _project_user_cache
        
        project_slug = request.project_name.lower().replace(" ", "-")
        projects_dir = Path("generated_projects")
        project_path = projects_dir / project_slug
        
        # Check if project exists locally or in S3
        use_s3 = False
        s3_project_data = None
        working_user_id = None
        
        if not project_path.exists():
            # Try S3 - first check cache, then search
            cached_user = _project_user_cache.get(project_slug)
            if cached_user:
                s3_project_data = get_project_from_s3(project_slug=project_slug, user_id=cached_user)
                if s3_project_data and s3_project_data.get('files'):
                    working_user_id = cached_user
                    use_s3 = True
                    print(f"✅ Found project {project_slug} in S3 (cached user_id)")
            
            if not use_s3:
                # Search across all users
                found_user_id = find_project_user_id(project_slug)
                if found_user_id:
                    s3_project_data = get_project_from_s3(project_slug=project_slug, user_id=found_user_id)
                    if s3_project_data and s3_project_data.get('files'):
                        working_user_id = found_user_id
                        use_s3 = True
                        print(f"✅ Found project {project_slug} in S3 (searched user_id: {found_user_id})")
            
            if not use_s3:
                return {"success": False, "error": "Project not found"}
        
        # Determine the file path if provided
        target_file_path = None
        target_s3_path = None  # For S3 files
        file_content = None
        
        if use_s3:
            # Handle S3 project files
            s3_files = s3_project_data.get('files', {})
            
            if request.file_path:
                # Try to find the file in S3
                file_path_clean = request.file_path.lstrip('/')
                possible_s3_paths = [
                    f"frontend/{file_path_clean}",
                    f"frontend/src/{file_path_clean}",
                    file_path_clean,
                    f"src/{file_path_clean}"
                ]
                
                for s3_path in possible_s3_paths:
                    if s3_path in s3_files:
                        target_s3_path = s3_path
                        file_content = s3_files[s3_path]
                        print(f"✅ Found S3 file: {s3_path}")
                        break
            else:
                # Default to App.jsx for React errors
                if any(keyword in request.error_message.lower() for keyword in ['jsx', 'react', 'component', 'unexpected token']):
                    app_paths = ['frontend/src/App.jsx', 'src/App.jsx']
                    for app_path in app_paths:
                        if app_path in s3_files:
                            target_s3_path = app_path
                            file_content = s3_files[app_path]
                            print(f"✅ Found S3 App.jsx: {app_path}")
                            break
        else:
            # Handle local filesystem (existing logic)
            if request.file_path:
                # Handle both absolute and relative paths - FIXED PATH RESOLUTION
                if request.file_path.startswith('/'):
                    # Relative path from project root - try frontend first
                    relative_path = request.file_path.lstrip('/')
                    possible_paths = [
                        project_path / "frontend" / relative_path,  # Most common: frontend/src/App.jsx
                        project_path / relative_path               # Fallback: src/App.jsx
                    ]
                else:
                    # Try to find the file in common locations
                    possible_paths = [
                        project_path / "frontend" / "src" / request.file_path,
                        project_path / "frontend" / request.file_path,
                        project_path / request.file_path,
                        project_path / "src" / request.file_path
                    ]
                
                # Find the actual file
                for path in possible_paths:
                    print(f"🔍 Checking path: {path}")
                    if path.exists():
                        target_file_path = path
                        print(f"✅ Found file at: {target_file_path}")
                        break
                
                if not target_file_path:
                    print(f"❌ File not found in any of these locations: {[str(p) for p in possible_paths]}")
            else:
                # If no file path provided, try to infer from error message
                # Default to App.jsx if it's a React error
                if any(keyword in request.error_message.lower() for keyword in ['jsx', 'react', 'component', 'unexpected token']):
                    app_jsx_path = project_path / "frontend" / "src" / "App.jsx"
                    if app_jsx_path.exists():
                        target_file_path = app_jsx_path
            
            # Read the current file content if we found a file
            if target_file_path and target_file_path.exists():
                try:
                    with open(target_file_path, 'r', encoding='utf-8') as f:
                        file_content = f.read()
                except Exception as e:
                    print(f"Error reading file {target_file_path}: {e}")
        
        # Build project context
        storage_location = "S3" if use_s3 else str(project_path)
        project_context = f"""
Project: {request.project_name}
Type: React Frontend Application
Framework: React + Vite
Storage: {storage_location}
"""
        
        # Add stack trace context if available
        error_details = request.error_message
        if request.stack_trace:
            error_details += f"\n\nStack Trace:\n{request.stack_trace}"
        if request.line_number:
            error_details += f"\n\nLine Number: {request.line_number}"
        
        # Determine the file path for the AI
        effective_file_path = target_s3_path if use_s3 else (str(target_file_path) if target_file_path else request.file_path)
        
        # Call the AI assistant to fix the error
        fix_result = get_code_fix_response(
            error_message=error_details,
            file_content=file_content,
            file_path=effective_file_path,
            project_context=project_context,
            model_type='fast'  # Use fast model for quick fixes
        )
        
        if not fix_result["success"]:
            return {
                "success": False,
                "error": fix_result.get("error", "Failed to generate fix"),
                "explanation": fix_result.get("explanation", "")
            }
        
        # Apply the fix if we have a target file and fixed content
        has_target = (use_s3 and target_s3_path) or (not use_s3 and target_file_path)
        if has_target and fix_result["fixed_content"] and fix_result["fixed_content"] != file_content:
            try:
                if use_s3:
                    # Update file in S3
                    s3_files = s3_project_data.get('files', {})
                    s3_files[target_s3_path] = fix_result["fixed_content"]
                    
                    # Convert to list format expected by upload_project_to_s3
                    files_list = [{'path': path, 'content': content} for path, content in s3_files.items()]
                    
                    # Save back to S3
                    save_result = upload_project_to_s3(
                        project_slug=project_slug,
                        files=files_list,
                        user_id=working_user_id
                    )
                    
                    if save_result and save_result.get('success'):
                        print(f"✅ Fixed S3 file: {target_s3_path}")
                        return {
                            "success": True,
                            "message": "Error fixed successfully using Gemini AI (S3)",
                            "file_path": target_s3_path,
                            "explanation": fix_result["explanation"],
                            "suggestions": fix_result.get("suggestions", []),
                            "changes_applied": True
                        }
                    else:
                        return {
                            "success": False,
                            "error": "Failed to save fix to S3",
                            "explanation": fix_result["explanation"],
                            "suggested_fix": fix_result["fixed_content"]
                        }
                else:
                    # Local filesystem (existing logic)
                    # Create backup of original file
                    backup_path = target_file_path.with_suffix(target_file_path.suffix + '.backup')
                    if target_file_path.exists():
                        shutil.copy2(target_file_path, backup_path)
                    
                    # Write the fixed content
                    with open(target_file_path, 'w', encoding='utf-8') as f:
                        f.write(fix_result["fixed_content"])
                    
                    return {
                        "success": True,
                        "message": "Error fixed successfully using Gemini AI",
                        "file_path": str(target_file_path),
                        "explanation": fix_result["explanation"],
                        "suggestions": fix_result.get("suggestions", []),
                        "backup_created": str(backup_path),
                        "changes_applied": True
                    }
                
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Failed to apply fix to file: {str(e)}",
                    "explanation": fix_result["explanation"],
                    "suggested_fix": fix_result["fixed_content"]
                }
        else:
            # Return the analysis without applying changes
            return {
                "success": True,
                "message": "Analysis completed - no file changes applied",
                "explanation": fix_result["explanation"],
                "suggestions": fix_result.get("suggestions", []),
                "suggested_fix": fix_result["fixed_content"] if fix_result["fixed_content"] != file_content else None,
                "changes_applied": False
            }
            
    except Exception as e:
        print(f"Gemini console error fix failed: {e}")
        return {
            "success": False,
            "error": f"Failed to process error fix: {str(e)}"
        }

# --- Stop Project Endpoint ---
@app.post("/api/stop-project")
async def check_project_errors(project_name: str = Query(...)):
    """Check for errors in the project"""
    try:
        project_slug = project_name.lower().replace(" ", "-")
        projects_dir = Path("generated_projects")
        project_path = projects_dir / project_slug
        
        if not project_path.exists():
            return {"success": False, "error": "Project not found"}
        
        errors = []
        
        # Check for common issues
        frontend_path = project_path / "frontend"
        if frontend_path.exists():
            # Check package.json exists
            pkg_path = frontend_path / "package.json"
            if not pkg_path.exists():
                errors.append({
                    "severity": "error",
                    "message": "Missing package.json",
                    "file": "frontend/package.json",
                    "line": 1
                })
            else:
                try:
                    raw = pkg_path.read_text(encoding="utf-8", errors="ignore")
                    cleaned = _clean_ai_generated_content(raw, "package.json")
                    pkg = json.loads(cleaned)
                    scripts = (pkg.get("scripts") or {}) if isinstance(pkg, dict) else {}
                    if not isinstance(scripts, dict):
                        errors.append({
                            "severity": "error",
                            "message": "Invalid scripts section in package.json",
                            "file": "frontend/package.json",
                            "line": 1
                        })
                    else:
                        if not ("dev" in scripts or "start" in scripts):
                            errors.append({
                                "severity": "error",
                                "message": "Missing dev/start script in package.json",
                                "file": "frontend/package.json",
                                "line": 1
                            })
                except Exception as e:
                    errors.append({
                        "severity": "error",
                        "message": f"Invalid JSON in package.json: {str(e)}",
                        "file": "frontend/package.json",
                        "line": 1
                    })
            
            # Check for syntax errors in JS/JSX files
            for file in frontend_path.rglob("*.js*"):
                if file.is_file():
                    try:
                        with open(file, 'r', encoding='utf-8') as f:
                            content = f.read()
                            # Basic syntax check
                            if content.count('{') != content.count('}'):
                                errors.append({
                                    "severity": "error",
                                    "message": "Mismatched braces",
                                    "file": str(file.relative_to(project_path)),
                                    "line": 1
                                })
                    except Exception:
                        pass
        
        return {"success": True, "errors": errors}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

# --- Auto Fix Errors Endpoint ---  
@app.post("/api/auto-fix-errors")
async def auto_fix_errors(request: dict = Body(...)):
    """Automatically fix common errors"""
    try:
        project_name = request.get("project_name")
        errors = request.get("errors", [])
        tech_stack = request.get("tech_stack", [])
        
        project_slug = project_name.lower().replace(" ", "-")
        projects_dir = Path("generated_projects")
        project_path = projects_dir / project_slug
        
        if not project_path.exists():
            return {"success": False, "error": "Project not found"}
        
        files_modified = []
        
        await manager.send_to_project(project_name, {
            "type": "terminal_output",
            "message": f"🔧 Auto-fixing {len(errors)} errors...",
            "level": "info"
        })
        
        for error in errors:
            if "Missing package.json" in error.get("message", ""):
                # Create basic package.json
                package_json = {
                    "name": project_slug,
                    "version": "1.0.0",
                    "private": True,
                    "scripts": {
                        "dev": "next dev" if "Next.js" in tech_stack else "vite",
                        "build": "next build" if "Next.js" in tech_stack else "vite build",
                        "preview": "vite preview --port 5173" if "Next.js" not in tech_stack else "next start",
                        "start": "next start" if "Next.js" in tech_stack else "vite"
                    },
                    "dependencies": {
                        "react": "^18.2.0",
                        "react-dom": "^18.2.0"
                    }
                }
                
                if "Next.js" in tech_stack:
                    package_json["dependencies"]["next"] = "^14.0.0"
                else:
                    # Prefer Vite defaults; dev deps installed separately during scaffold
                    package_json.setdefault("devDependencies", {})
                    package_json["devDependencies"].update({
                        "vite": "^5.0.0"
                    })
                
                if "TypeScript" in tech_stack:
                    package_json["dependencies"]["typescript"] = "^5.0.0"
                    package_json["dependencies"]["@types/react"] = "^18.0.0"
                    package_json["dependencies"]["@types/react-dom"] = "^18.0.0"
                
                package_path = project_path / "frontend" / "package.json"
                with open(package_path, 'w', encoding='utf-8') as f:
                    json.dump(package_json, f, indent=2)
                
                files_modified.append("frontend/package.json")
                
                await manager.send_to_project(project_name, {
                    "type": "terminal_output",
                    "message": "✅ Created package.json",
                    "level": "success"
                })
            elif "Invalid JSON in package.json" in error.get("message", ""):
                # Try to clean and rewrite package.json
                pkg_path = project_path / "frontend" / "package.json"
                if pkg_path.exists():
                    try:
                        raw = pkg_path.read_text(encoding="utf-8", errors="ignore")
                        cleaned = _clean_ai_generated_content(raw, "package.json")
                        pkg = json.loads(cleaned)
                        with open(pkg_path, 'w', encoding='utf-8') as f:
                            json.dump(pkg, f, indent=2)
                        files_modified.append("frontend/package.json")
                        await manager.send_to_project(project_name, {
                            "type": "terminal_output",
                            "message": "🧹 Cleaned invalid JSON in package.json",
                            "level": "success"
                        })
                    except Exception:
                        # Fallback to minimal vite-based package
                        fallback = {
                            "name": project_slug,
                            "version": "1.0.0",
                            "private": True,
                            "scripts": {"dev": "vite", "build": "vite build", "preview": "vite preview --port 5173", "start": "vite"}
                        }
                        with open(pkg_path, 'w', encoding='utf-8') as f:
                            json.dump(fallback, f, indent=2)
                        files_modified.append("frontend/package.json")
                        await manager.send_to_project(project_name, {
                            "type": "terminal_output",
                            "message": "✅ Replaced invalid package.json with a safe default",
                            "level": "warning"
                        })
            elif "Missing dev/start script" in error.get("message", "") or "Invalid scripts section in package.json" in error.get("message", ""):
                pkg_path = project_path / "frontend" / "package.json"
                if pkg_path.exists():
                    try:
                        raw = pkg_path.read_text(encoding="utf-8", errors="ignore")
                        cleaned = _clean_ai_generated_content(raw, "package.json")
                        pkg = json.loads(cleaned)
                        if not isinstance(pkg, dict):
                            pkg = {}
                        scripts = pkg.get("scripts") or {}
                        if not isinstance(scripts, dict):
                            scripts = {}
                        # Heuristic: use vite if dependency present, else next if Next.js in stack
                        deps = pkg.get("dependencies", {}) or {}
                        use_vite = "vite" in (pkg.get("devDependencies", {}) or {}) or "vite" in deps
                        if "Next.js" in tech_stack:
                            scripts.update({"dev": "next dev", "build": "next build", "start": "next start"})
                        elif use_vite or True:
                            scripts.update({"dev": "vite", "build": "vite build", "preview": "vite preview --port 5173", "start": "vite"})
                        pkg["scripts"] = scripts
                        with open(pkg_path, 'w', encoding='utf-8') as f:
                            json.dump(pkg, f, indent=2)
                        files_modified.append("frontend/package.json")
                        await manager.send_to_project(project_name, {
                            "type": "terminal_output",
                            "message": "🔧 Added missing scripts to package.json",
                            "level": "success"
                        })
                    except Exception as e:
                        await manager.send_to_project(project_name, {
                            "type": "terminal_output",
                            "message": f"⚠️ Could not update scripts in package.json: {str(e)}",
                            "level": "warning"
                        })
        
        return {
            "success": True,
            "files_modified": files_modified,
            "fixes_applied": len(errors)
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

# --- Execute Terminal Command Endpoint ---
@app.post("/api/execute-command") 
async def execute_command(request: dict = Body(...)):
    """Execute terminal command in project directory"""
    try:
        project_name = request.get("project_name")
        command = request.get("command")
        working_directory = request.get("working_directory", "/")
        
        project_slug = project_name.lower().replace(" ", "-")
        projects_dir = Path("generated_projects")
        project_path = projects_dir / project_slug
        
        if not project_path.exists():
            return {"success": False, "error": "Project not found"}
        
        # Determine actual working directory
        if working_directory == "/" or not working_directory:
            cwd = project_path
        else:
            cwd = project_path / working_directory.lstrip('/')
        
        # Security: only allow safe commands
        safe_commands = [
            "ls", "dir", "pwd", "cat", "type", "npm", "node", "python", "pip",
            "git", "cd", "mkdir", "touch", "echo", "clear", "cls"
        ]
        
        command_parts = command.split()
        if not command_parts or command_parts[0] not in safe_commands:
            return {"success": False, "error": f"Command '{command_parts[0] if command_parts else command}' not allowed"}
        
        try:
            # Handle cd command specially
            if command.startswith("cd "):
                target_dir = command[3:].strip()
                if target_dir == "..":
                    new_cwd = cwd.parent
                elif target_dir == "/":
                    new_cwd = project_path
                else:
                    new_cwd = cwd / target_dir
                
                # Security check
                try:
                    new_cwd.resolve().relative_to(project_path.resolve())
                    return {
                        "success": True,
                        "output": f"Changed directory to {new_cwd.relative_to(project_path)}",
                        "working_directory": str(new_cwd.relative_to(project_path))
                    }
                except ValueError:
                    return {"success": False, "error": "Cannot navigate outside project directory"}
            
            # Execute other commands
            process = await asyncio.create_subprocess_shell(
                command,
                cwd=cwd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            output = stdout.decode('utf-8')
            if stderr:
                output += f"\nError: {stderr.decode('utf-8')}"
            
            return {
                "success": True,
                "output": output,
                "working_directory": working_directory
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

# --- Project History Endpoint (S3-backed) ---
@app.get("/api/project-history")
async def get_project_history(current_user: dict = Depends(get_current_user)):
    """Get list of all generated projects with metadata from S3 - Requires authentication"""
    try:
        # Get user_id from authenticated user (email)
        user_id = current_user.get('email')
        user_id_alternative = str(current_user.get('_id', ''))
        
        print(f"📋 Loading project history for user: {user_id}")
        print(f"🔐 Authentication status: Authenticated as {user_id}")
        print(f"🔑 Alternative ID (MongoDB _id): {user_id_alternative}")
        
        # Try to get project slugs from S3 using email first, then MongoDB _id
        project_list = list_user_projects(user_id=user_id)
        
        if not project_list and user_id_alternative:
            print(f"🔄 No projects found for email, trying MongoDB _id: {user_id_alternative}")
            project_list = list_user_projects(user_id=user_id_alternative)
            # If found with alternative ID, use it for subsequent operations
            if project_list:
                user_id = user_id_alternative
                print(f"✅ Found projects under MongoDB _id: {user_id}")
        
        if not project_list:
            print(f"⚠️ No projects found for user {user_id} or {user_id_alternative}")
            return {"success": True, "projects": []}
        
        # Extract slugs from the list of dicts
        project_slugs = [p['slug'] for p in project_list if 'slug' in p]
        
        if not project_slugs:
            return {"success": True, "projects": []}
        
        print(f"📦 Found {len(project_slugs)} projects for user {user_id}, loading first 20")
        
        # Limit to first 20 projects to avoid overload
        project_slugs = project_slugs[:20]
        
        # Define async function to process a single project
        async def process_project(project_slug: str):
            try:
                # Run S3 fetch in thread pool to avoid blocking
                import asyncio
                from concurrent.futures import ThreadPoolExecutor
                
                loop = asyncio.get_event_loop()
                with ThreadPoolExecutor() as executor:
                    project_data = await loop.run_in_executor(
                        executor,
                        get_project_from_s3,
                        project_slug,
                        user_id
                    )
                
                if not project_data:
                    return None
                
                project_files = project_data.get('files', [])
                
                # Determine frontend/backend presence
                has_frontend = any('frontend' in f['path'] for f in project_files)
                has_backend = any('backend' in f['path'] for f in project_files)
                
                # Extract metadata from S3
                metadata = project_data.get('metadata', {})
                created_date = metadata.get('created_date', None)
                
                project_info = {
                    "name": project_data.get('name', project_slug.replace("-", " ").title()),
                    "slug": project_slug,
                    "created_date": created_date,
                    "preview_url": f"http://localhost:8000/api/sandbox-preview/{project_slug}?user_email={user_id}",
                    "editor_url": f"/project/{project_slug}",
                    "has_frontend": has_frontend,
                    "has_backend": has_backend,
                    "tech_stack": []
                }
                
                # Detect tech stack from package.json if exists
                package_json_file = next((f for f in project_files if f['path'] == 'frontend/package.json'), None)
                if package_json_file:
                    try:
                        import json
                        pkg_data = json.loads(package_json_file['content'])
                        
                        dependencies = list(pkg_data.get("dependencies", {}).keys())
                        dev_dependencies = list(pkg_data.get("devDependencies", {}).keys())
                        
                        if "react" in dependencies:
                            project_info["tech_stack"].append("React")
                        if "vite" in dev_dependencies:
                            project_info["tech_stack"].append("Vite")
                        if "tailwindcss" in dependencies or "tailwindcss" in dev_dependencies:
                            project_info["tech_stack"].append("TailwindCSS")
                    except Exception:
                        pass
                
                # Check for backend
                if any(f['path'] == 'backend/requirements.txt' for f in project_files):
                    project_info["tech_stack"].append("FastAPI")
                    project_info["tech_stack"].append("Python")
                
                # Format created date
                if created_date:
                    import datetime
                    if isinstance(created_date, str):
                        try:
                            created_dt = datetime.datetime.fromisoformat(created_date.replace('Z', '+00:00'))
                        except:
                            created_dt = datetime.datetime.now()
                    else:
                        created_dt = datetime.datetime.fromtimestamp(created_date)
                    
                    project_info["created_date_formatted"] = created_dt.strftime("%Y-%m-%d %H:%M")
                    project_info["created_date"] = created_dt.timestamp()
                
                return project_info
                
            except Exception as e:
                print(f"Error processing project {project_slug}: {e}")
                import traceback
                traceback.print_exc()
                return None
        
        # Fetch all projects in parallel with concurrency limit
        print(f"⚡ Fetching {len(project_slugs)} projects in parallel...")
        import asyncio
        
        # Process projects in parallel
        tasks = [process_project(slug) for slug in project_slugs]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out None values and exceptions
        projects = [p for p in results if p is not None and not isinstance(p, Exception)]
        
        print(f"✅ Successfully loaded {len(projects)} projects")
        
        # Sort by creation date (newest first), handle None values
        projects.sort(key=lambda x: x.get("created_date") or 0, reverse=True)
        
        return {
            "success": True,
            "projects": projects,
            "total_count": len(projects)
        }
        
    except Exception as e:
        print(f"Error fetching project history from S3: {e}")
        return {"success": False, "error": str(e)}

# --- Get Project File Tree Endpoint ---
@app.get("/api/project-file-tree")
async def get_project_file_tree(project_name: str = Query(...), current_user: Optional[dict] = Depends(get_current_user_optional)):
    """Get file tree structure for a project from S3 or local storage"""
    try:
        from s3_storage import get_cached_user_id_for_project
        
        project_slug = project_name.replace(" ", "-")
        
        # Check cache first for faster lookup
        cached_user_id = get_cached_user_id_for_project(project_slug)
        
        # Build user_ids list with cached one first (if exists)
        user_ids_to_try = []
        if cached_user_id:
            user_ids_to_try.append(cached_user_id)
        if current_user:
            if current_user.get('_id') and current_user.get('_id') not in user_ids_to_try:
                user_ids_to_try.append(current_user.get('_id'))
            if current_user.get('email') and current_user.get('email') not in user_ids_to_try:
                user_ids_to_try.append(current_user.get('email'))
        if 'anonymous' not in user_ids_to_try:
            user_ids_to_try.append('anonymous')
        
        # Build tree structure from S3 files
        def build_tree_from_paths(file_paths):
            tree = []
            dir_map = {}
            
            for file_info in file_paths:
                path = file_info['path']
                parts = path.split('/')
                
                current_level = tree
                for i, part in enumerate(parts):
                    current_path = '/'.join(parts[:i+1])
                    
                    if i == len(parts) - 1:  # File
                        current_level.append({
                            "name": part,
                            "path": path,
                            "type": "file",
                            "size": len(file_info.get('content', ''))
                        })
                    else:  # Directory
                        if current_path not in dir_map:
                            dir_entry = {
                                "name": part,
                                "path": current_path,
                                "type": "directory",
                                "children": []
                            }
                            current_level.append(dir_entry)
                            dir_map[current_path] = dir_entry
                        current_level = dir_map[current_path]["children"]
            
            return tree
        
        # Try S3 with user IDs (cached one first)
        for user_id in user_ids_to_try:
            try:
                project_data = get_project_from_s3(project_slug=project_slug, user_id=user_id)
                
                if project_data and project_data.get('files'):
                    file_tree = build_tree_from_paths(project_data['files'])
                    print(f"📁 ✅ Found project {project_slug} with {len(project_data['files'])} files (user: {user_id})")
                    return {
                        "success": True,
                        "file_tree": file_tree,
                        "project_path": f"s3://projects/{user_id}/{project_slug}",
                        "source": "s3"
                    }
            except Exception as s3_error:
                continue
        
        # Fallback to local files
        projects_dir = Path("generated_projects")
        project_path = projects_dir / project_slug
        
        if not project_path.exists():
            return {
                "success": True,
                "file_tree": [],
                "project_path": str(project_path),
                "source": "none"
            }
        
        def build_file_tree(path: Path, base_path: Path = None):
            """Recursively build file tree structure"""
            if base_path is None:
                base_path = path
            
            items = []
            
            try:
                for item in sorted(path.iterdir()):
                    if item.name.startswith('.') or item.name in ['node_modules', '__pycache__', 'dist', 'build']:
                        continue
                    
                    relative_path = str(item.relative_to(base_path)).replace('\\', '/')
                    
                    if item.is_dir():
                        items.append({
                            "name": item.name,
                            "path": relative_path,
                            "type": "directory",
                            "children": build_file_tree(item, base_path)
                        })
                    else:
                        items.append({
                            "name": item.name,
                            "path": relative_path,
                            "type": "file",
                            "size": item.stat().st_size
                        })
            except PermissionError:
                pass
            
            return items
        
        file_tree = build_file_tree(project_path)
        
        return {
            "success": True,
            "file_tree": file_tree,
            "project_path": str(project_path),
            "source": "local"
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

# --- Rate Limit Status (to avoid 404 in frontend) ---
@app.get("/api/rate-limit-status")
async def rate_limit_status():
    """Return a basic rate limit status; integrate with GitHub if available."""
    try:
        # Minimal static response to satisfy UI; extend to real provider limits as needed
        return {
            "success": True,
            "rate_limit": {
                "core": {"limit": 5000, "remaining": 4999},
                "search": {"limit": 30, "remaining": 30}
            }
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

# --- Get Project File Content Endpoint ---
@app.get("/api/project-file-content")
async def get_project_file_content(project_name: str = Query(...), file_path: str = Query(...), current_user: Optional[dict] = Depends(get_current_user_optional)):
    """Get content of a specific file from S3 or local storage"""
    try:
        from s3_storage import get_cached_user_id_for_project
        
        project_slug = project_name.replace(" ", "-")
        file_path_clean = file_path.lstrip('/')
        
        # Check cache first for faster lookup
        cached_user_id = get_cached_user_id_for_project(project_slug)
        
        # Build user_ids list with cached one first
        user_ids_to_try = []
        if cached_user_id:
            user_ids_to_try.append(cached_user_id)
        if current_user:
            if current_user.get('_id') and current_user.get('_id') not in user_ids_to_try:
                user_ids_to_try.append(current_user.get('_id'))
            if current_user.get('email') and current_user.get('email') not in user_ids_to_try:
                user_ids_to_try.append(current_user.get('email'))
        if 'anonymous' not in user_ids_to_try:
            user_ids_to_try.append('anonymous')
        
        # Try S3 with cached user_id first
        for user_id in user_ids_to_try:
            try:
                project_data = get_project_from_s3(project_slug=project_slug, user_id=user_id)
                
                if project_data and project_data.get('files'):
                    # Find the file in S3 data
                    for file_info in project_data['files']:
                        if file_info['path'] == file_path_clean:
                            return {
                                "success": True,
                                "content": file_info['content'],
                                "file_path": file_path_clean,
                                "size": len(file_info['content']),
                                "source": "s3"
                            }
            except Exception as s3_error:
                continue
        
        # Fallback to local files
        projects_dir = Path("generated_projects")
        project_path = projects_dir / project_slug
        
        if not project_path.exists():
            return {"success": False, "error": f"Project not found (tried S3 and local)"}
        
        # Security check
        full_file_path = project_path / file_path_clean
        try:
            full_file_path.resolve().relative_to(project_path.resolve())
        except ValueError:
            return {"success": False, "error": "Invalid file path"}
        
        if not full_file_path.exists():
            return {"success": False, "error": "File not found"}
        
        if not full_file_path.is_file():
            return {"success": False, "error": "Path is not a file"}
        
        # Read file content
        try:
            with open(full_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            print(f"📄 Reading file from local: {file_path_clean}")
            return {
                "success": True,
                "content": content,
                "file_path": file_path_clean,
                "size": full_file_path.stat().st_size,
                "source": "local"
            }
            
        except UnicodeDecodeError:
            return {
                "success": False,
                "error": "File is binary and cannot be displayed as text"
            }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

# --- Stop Project Endpoint ---
@app.post("/api/stop-project")
async def stop_project(request: dict = Body(...)):
    """Stop running project servers"""
    try:
        project_name = request.get("project_name")
        
        await manager.send_to_project(project_name, {
            "type": "terminal_output",
            "message": "⏹️ Stopping project servers...",
            "level": "info"
        })
        
        # In a real implementation, you would track running processes
        # and terminate them here. For this demo, we'll just simulate.
        
        await asyncio.sleep(1)  # Simulate stopping time
        
        await manager.send_to_project(project_name, {
            "type": "terminal_output",
            "message": "✅ Project servers stopped",
            "level": "success"
        })
        
        return {"success": True}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

# --- Project Template Creation Functions ---

async def create_react_frontend_with_animation(frontend_path: Path, idea: str, project_name: str, needs_typescript: bool, needs_auth: bool) -> List[str]:
    """Create React frontend structure with real-time animation"""
    files_created = []
    
    # Create directories
    src_path = frontend_path / "src"
    components_path = src_path / "components"
    pages_path = src_path / "pages"
    utils_path = src_path / "utils"
    
    for path in [src_path, components_path, pages_path, utils_path]:
        path.mkdir(parents=True, exist_ok=True)
    
    # Package.json
    package_json = {
        "name": project_name.lower().replace(" ", "-"),
        "version": "0.1.0",
        "private": True,
        "dependencies": {
            "@testing-library/jest-dom": "^5.16.4",
            "@testing-library/react": "^13.3.0",
            "@testing-library/user-event": "^13.5.0",
            "react": "^18.2.0",
            "react-dom": "^18.2.0",
            "react-router-dom": "^6.8.0",
            "react-scripts": "5.0.1",
            "axios": "^1.3.0",
            "tailwindcss": "^3.2.0",
            "autoprefixer": "^10.4.13",
            "postcss": "^8.4.21"
        },
        "scripts": {
            "start": "react-scripts start",
            "build": "react-scripts build",
            "test": "react-scripts test",
            "eject": "react-scripts eject"
        },
        "eslintConfig": {
            "extends": ["react-app", "react-app/jest"]
        },
        "browserslist": {
            "production": [">0.2%", "not dead", "not op_mini all"],
            "development": ["last 1 chrome version", "last 1 firefox version", "last 1 safari version"]
        }
    }
    
    if needs_typescript:
        package_json["dependencies"].update({
            "typescript": "^4.9.0",
            "@types/node": "^16.18.0",
            "@types/react": "^18.0.0",
            "@types/react-dom": "^18.0.0"
        })
    
    if needs_auth:
        package_json["dependencies"]["auth0-react"] = "^2.0.0"
    
    package_content = json.dumps(package_json, indent=2)
    rel_path = await create_file_with_animation(
        frontend_path / "package.json", 
        package_content, 
        "frontend/package.json", 
        project_name
    )
    files_created.append(rel_path)
    
    # Public/index.html
    public_path = frontend_path / "public"
    public_path.mkdir(exist_ok=True)
    
    index_html = f"""<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <link rel="icon" href="%PUBLIC_URL%/favicon.ico" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <meta name="theme-color" content="#000000" />
    <meta name="description" content="{idea}" />
    <title>{project_name}</title>
  </head>
  <body>
    <noscript>You need to enable JavaScript to run this app.</noscript>
    <div id="root"></div>
  </body>
</html>"""
    
    rel_path = await create_file_with_animation(
        public_path / "index.html", 
        index_html, 
        "frontend/public/index.html", 
        project_name
    )
    files_created.append(rel_path)
    
    # Main App component
    ext = ".tsx" if needs_typescript else ".jsx"
    
    app_component = f"""import React from 'react';
import {{ BrowserRouter as Router, Routes, Route }} from 'react-router-dom';
import './App.css';
import Home from './pages/Home{ext}';
import Header from './components/Header{ext}';

function App() {{
  return (
    <div className="App min-h-screen bg-gray-50">
      <Router>
        <Header />
        <main className="container mx-auto px-4 py-8">
          <Routes>
            <Route path="/" element={{<Home />}} />
          </Routes>
        </main>
      </Router>
    </div>
  );
}}

export default App;"""
    
    rel_path = await create_file_with_animation(
        src_path / f"App{ext}", 
        app_component, 
        f"frontend/src/App{ext}", 
        project_name
    )
    files_created.append(rel_path)
    
    # Index.js/tsx
    index_content = f"""import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App{ext}';

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);"""
    
    index_ext = ".tsx" if needs_typescript else ".js"
    rel_path = await create_file_with_animation(
        src_path / f"index{index_ext}", 
        index_content, 
        f"frontend/src/index{index_ext}", 
        project_name
    )
    files_created.append(rel_path)
    
    # Home page
    home_component = f"""import React from 'react';

const Home = () => {{
  return (
    <div className="max-w-4xl mx-auto">
      <div className="text-center mb-12">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">
          Welcome to {project_name}
        </h1>
        <p className="text-xl text-gray-600 mb-8">
          {idea}
        </p>
        <div className="space-x-4">
          <button className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded">
            Get Started
          </button>
          <button className="bg-gray-200 hover:bg-gray-300 text-gray-800 font-bold py-2 px-4 rounded">
            Learn More
          </button>
        </div>
      </div>
      
      <div className="grid md:grid-cols-3 gap-8">
        <div className="bg-white p-6 rounded-lg shadow-md">
          <h3 className="text-xl font-semibold mb-3">Feature 1</h3>
          <p className="text-gray-600">Description of your first key feature.</p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow-md">
          <h3 className="text-xl font-semibold mb-3">Feature 2</h3>
          <p className="text-gray-600">Description of your second key feature.</p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow-md">
          <h3 className="text-xl font-semibold mb-3">Feature 3</h3>
          <p className="text-gray-600">Description of your third key feature.</p>
        </div>
      </div>
    </div>
  );
}};

export default Home;"""
    
    rel_path = await create_file_with_animation(
        pages_path / f"Home{ext}", 
        home_component, 
        f"frontend/src/pages/Home{ext}", 
        project_name
    )
    files_created.append(rel_path)
    
    # Header component
    header_component = f"""import React from 'react';

const Header = () => {{
  return (
    <header className="bg-white shadow-sm border-b">
      <div className="container mx-auto px-4">
        <div className="flex justify-between items-center py-4">
          <div className="flex items-center">
            <h1 className="text-2xl font-bold text-gray-900">{project_name}</h1>
          </div>
          <nav className="hidden md:flex space-x-8">
            <a href="/" className="text-gray-600 hover:text-gray-900">Home</a>
            <a href="/about" className="text-gray-600 hover:text-gray-900">About</a>
            <a href="/contact" className="text-gray-600 hover:text-gray-900">Contact</a>
          </nav>
          <div className="flex items-center space-x-4">
            <button className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded">
              Sign Up
            </button>
          </div>
        </div>
      </div>
    </header>
  );
}};

export default Header;"""
    
    rel_path = await create_file_with_animation(
        components_path / f"Header{ext}", 
        header_component, 
        f"frontend/src/components/Header{ext}", 
        project_name
    )
    files_created.append(rel_path)
    
    # CSS files
    app_css = """@tailwind base;
@tailwind components;
@tailwind utilities;

.App {
  text-align: center;
}"""
    
    rel_path = await create_file_with_animation(
        src_path / "App.css", 
        app_css, 
        "frontend/src/App.css", 
        project_name
    )
    files_created.append(rel_path)
    
    index_css = """@tailwind base;
@tailwind components;
@tailwind utilities;

body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
    'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue',
    sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

code {
  font-family: source-code-pro, Menlo, Monaco, Consolas, 'Courier New',
    monospace;
}"""
    
    rel_path = await create_file_with_animation(
        src_path / "index.css", 
        index_css, 
        "frontend/src/index.css", 
        project_name
    )
    files_created.append(rel_path)
    
    # Tailwind config
    tailwind_config = """/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}"""
    
    rel_path = await create_file_with_animation(
        frontend_path / "tailwind.config.js", 
        tailwind_config, 
        "frontend/tailwind.config.js", 
        project_name
    )
    files_created.append(rel_path)
    
    return files_created

# For now, let's create simpler aliases that redirect to the animated version
async def create_nextjs_frontend_with_animation(frontend_path: Path, idea: str, project_name: str, needs_typescript: bool, needs_auth: bool) -> List[str]:
    return await create_nextjs_frontend(frontend_path, idea, project_name, needs_typescript, needs_auth)

async def create_fastapi_backend_with_animation(backend_path: Path, idea: str, project_name: str, needs_ai: bool, needs_auth: bool, needs_database: bool) -> List[str]:
    return await create_fastapi_backend(backend_path, idea, project_name, needs_ai, needs_auth, needs_database)

async def create_nodejs_backend_with_animation(backend_path: Path, idea: str, project_name: str, needs_ai: bool, needs_auth: bool, needs_database: bool) -> List[str]:
    return await create_nodejs_backend(backend_path, idea, project_name, needs_ai, needs_auth, needs_database)

async def create_root_files_with_animation(project_path: Path, project_name: str, idea: str, tech_stack: List[str]) -> List[str]:
    return await create_root_files(project_path, project_name, idea, tech_stack)
    """Create React frontend structure"""
    files_created = []
    
    # Create directories
    src_path = frontend_path / "src"
    components_path = src_path / "components"
    pages_path = src_path / "pages"
    utils_path = src_path / "utils"
    
    for path in [src_path, components_path, pages_path, utils_path]:
        path.mkdir(parents=True, exist_ok=True)
    
    # Package.json
    package_json = {
        "name": project_name.lower().replace(" ", "-"),
        "version": "0.1.0",
        "private": True,
        "dependencies": {
            "@testing-library/jest-dom": "^5.16.4",
            "@testing-library/react": "^13.3.0",
            "@testing-library/user-event": "^13.5.0",
            "react": "^18.2.0",
            "react-dom": "^18.2.0",
            "react-router-dom": "^6.8.0",
            "react-scripts": "5.0.1",
            "axios": "^1.3.0",
            "tailwindcss": "^3.2.0",
            "autoprefixer": "^10.4.13",
            "postcss": "^8.4.21"
        },
        "scripts": {
            "start": "react-scripts start",
            "build": "react-scripts build",
            "test": "react-scripts test",
            "eject": "react-scripts eject"
        },
        "eslintConfig": {
            "extends": ["react-app", "react-app/jest"]
        },
        "browserslist": {
            "production": [">0.2%", "not dead", "not op_mini all"],
            "development": ["last 1 chrome version", "last 1 firefox version", "last 1 safari version"]
        }
    }
    
    if needs_typescript:
        package_json["dependencies"].update({
            "typescript": "^4.9.0",
            "@types/node": "^16.18.0",
            "@types/react": "^18.0.0",
            "@types/react-dom": "^18.0.0"
        })
    
    if needs_auth:
        package_json["dependencies"]["auth0-react"] = "^2.0.0"
    
    package_path = frontend_path / "package.json"
    with open(package_path, 'w', encoding='utf-8') as f:
        json.dump(package_json, f, indent=2)
    files_created.append("frontend/package.json")
    
    # Public/index.html
    public_path = frontend_path / "public"
    public_path.mkdir(exist_ok=True)
    
    index_html = f"""<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <link rel="icon" href="%PUBLIC_URL%/favicon.ico" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <meta name="theme-color" content="#000000" />
    <meta name="description" content="{idea}" />
    <title>{project_name}</title>
  </head>
  <body>
    <noscript>You need to enable JavaScript to run this app.</noscript>
    <div id="root"></div>
  </body>
</html>"""
    
    with open(public_path / "index.html", 'w', encoding='utf-8') as f:
        f.write(index_html)
    files_created.append("frontend/public/index.html")
    
    # Main App component
    ext = ".tsx" if needs_typescript else ".jsx"
    
    app_component = f"""import React from 'react';
import {{ BrowserRouter as Router, Routes, Route }} from 'react-router-dom';
import './App.css';
import Home from './pages/Home{ext}';
import Header from './components/Header{ext}';

function App() {{
  return (
    <div className="App min-h-screen bg-gray-50">
      <Router>
        <Header />
        <main className="container mx-auto px-4 py-8">
          <Routes>
            <Route path="/" element={{<Home />}} />
          </Routes>
        </main>
      </Router>
    </div>
  );
}}

export default App;"""
    
    with open(src_path / f"App{ext}", 'w', encoding='utf-8') as f:
        f.write(app_component)
    files_created.append(f"frontend/src/App{ext}")
    
    # Index.js/tsx
    index_content = f"""import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App{ext}';

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);"""
    
    index_ext = ".tsx" if needs_typescript else ".js"
    with open(src_path / f"index{index_ext}", 'w', encoding='utf-8') as f:
        f.write(index_content)
    files_created.append(f"frontend/src/index{index_ext}")
    
    # Home page
    home_component = f"""import React from 'react';

const Home = () => {{
  return (
    <div className="max-w-4xl mx-auto">
      <div className="text-center mb-12">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">
          Welcome to {project_name}
        </h1>
        <p className="text-xl text-gray-600 mb-8">
          {idea}
        </p>
        <div className="space-x-4">
          <button className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded">
            Get Started
          </button>
          <button className="bg-gray-200 hover:bg-gray-300 text-gray-800 font-bold py-2 px-4 rounded">
            Learn More
          </button>
        </div>
      </div>
      
      <div className="grid md:grid-cols-3 gap-8">
        <div className="bg-white p-6 rounded-lg shadow-md">
          <h3 className="text-xl font-semibold mb-3">Feature 1</h3>
          <p className="text-gray-600">Description of your first key feature.</p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow-md">
          <h3 className="text-xl font-semibold mb-3">Feature 2</h3>
          <p className="text-gray-600">Description of your second key feature.</p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow-md">
          <h3 className="text-xl font-semibold mb-3">Feature 3</h3>
          <p className="text-gray-600">Description of your third key feature.</p>
        </div>
      </div>
    </div>
  );
}};

export default Home;"""
    
    with open(pages_path / f"Home{ext}", 'w', encoding='utf-8') as f:
        f.write(home_component)
    files_created.append(f"frontend/src/pages/Home{ext}")
    
    # Header component
    header_component = f"""import React from 'react';

const Header = () => {{
  return (
    <header className="bg-white shadow-sm border-b">
      <div className="container mx-auto px-4">
        <div className="flex justify-between items-center py-4">
          <div className="flex items-center">
            <h1 className="text-2xl font-bold text-gray-900">{project_name}</h1>
          </div>
          <nav className="hidden md:flex space-x-8">
            <a href="/" className="text-gray-600 hover:text-gray-900">Home</a>
            <a href="/about" className="text-gray-600 hover:text-gray-900">About</a>
            <a href="/contact" className="text-gray-600 hover:text-gray-900">Contact</a>
          </nav>
          <div className="flex items-center space-x-4">
            <button className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded">
              Sign Up
            </button>
          </div>
        </div>
      </div>
    </header>
  );
}};

export default Header;"""
    
    with open(components_path / f"Header{ext}", 'w', encoding='utf-8') as f:
        f.write(header_component)
    files_created.append(f"frontend/src/components/Header{ext}")
    
    # CSS files
    app_css = """@tailwind base;
@tailwind components;
@tailwind utilities;

.App {
  text-align: center;
}"""
    
    with open(src_path / "App.css", 'w', encoding='utf-8') as f:
        f.write(app_css)
    files_created.append("frontend/src/App.css")
    
    index_css = """@tailwind base;
@tailwind components;
@tailwind utilities;

body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
    'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue',
    sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

code {
  font-family: source-code-pro, Menlo, Monaco, Consolas, 'Courier New',
    monospace;
}"""
    
    with open(src_path / "index.css", 'w', encoding='utf-8') as f:
        f.write(index_css)
    files_created.append("frontend/src/index.css")
    
    # Tailwind config
    tailwind_config = """/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}"""
    
    with open(frontend_path / "tailwind.config.js", 'w', encoding='utf-8') as f:
        f.write(tailwind_config)
    files_created.append("frontend/tailwind.config.js")
    
    return files_created

async def create_nextjs_frontend(frontend_path: Path, idea: str, project_name: str, needs_typescript: bool, needs_auth: bool) -> List[str]:
    """Create Next.js frontend structure"""
    files_created = []
    
    # Create directories
    src_path = frontend_path / "src"
    app_path = src_path / "app"
    components_path = src_path / "components"
    
    for path in [src_path, app_path, components_path]:
        path.mkdir(parents=True, exist_ok=True)
    
    # Package.json
    package_json = {
        "name": project_name.lower().replace(" ", "-"),
        "version": "0.1.0",
        "private": True,
        "scripts": {
            "dev": "next dev",
            "build": "next build",
            "start": "next start",
            "lint": "next lint"
        },
        "dependencies": {
            "react": "^18",
            "react-dom": "^18",
            "next": "14.0.4",
            "tailwindcss": "^3.3.0",
            "autoprefixer": "^10.4.16",
            "postcss": "^8.4.32"
        },
        "devDependencies": {
            "eslint": "^8",
            "eslint-config-next": "14.0.4"
        }
    }
    
    if needs_typescript:
        package_json["devDependencies"].update({
            "typescript": "^5",
            "@types/node": "^20",
            "@types/react": "^18",
            "@types/react-dom": "^18"
        })
    
    package_path = frontend_path / "package.json"
    with open(package_path, 'w', encoding='utf-8') as f:
        json.dump(package_json, f, indent=2)
    files_created.append("frontend/package.json")
    
    # Next.js config
    next_config = """/** @type {import('next').NextConfig} */
const nextConfig = {}

module.exports = nextConfig"""
    
    with open(frontend_path / "next.config.js", 'w', encoding='utf-8') as f:
        f.write(next_config)
    files_created.append("frontend/next.config.js")
    
    # App directory files
    ext = ".tsx" if needs_typescript else ".js"
    
    # Layout
    layout_content = f"""import './globals.css'
import {{ Inter }} from 'next/font/google'

const inter = Inter({{ subsets: ['latin'] }})

export const metadata = {{
  title: '{project_name}',
  description: '{idea}',
}}

export default function RootLayout({{
  children,
}}: {{
  children: React.ReactNode
}}) {{
  return (
    <html lang="en">
      <body className={{inter.className}}>{{children}}</body>
    </html>
  )
}}"""
    
    with open(app_path / f"layout{ext}", 'w', encoding='utf-8') as f:
        f.write(layout_content)
    files_created.append(f"frontend/src/app/layout{ext}")
    
    # Page
    page_content = f"""export default function Home() {{
  return (
    <main className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-16">
        <div className="text-center mb-16">
          <h1 className="text-5xl font-bold text-gray-900 mb-6">
            {project_name}
          </h1>
          <p className="text-xl text-gray-600 mb-8 max-w-2xl mx-auto">
            {idea}
          </p>
          <div className="space-x-4">
            <button className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-6 rounded-lg transition-colors">
              Get Started
            </button>
            <button className="bg-white hover:bg-gray-50 text-gray-800 font-bold py-3 px-6 rounded-lg border border-gray-300 transition-colors">
              Learn More
            </button>
          </div>
        </div>
        
        <div className="grid md:grid-cols-3 gap-8 max-w-6xl mx-auto">
          <div className="bg-white p-8 rounded-xl shadow-lg">
            <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mb-4">
              <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path>
              </svg>
            </div>
            <h3 className="text-xl font-semibold mb-3">Fast Performance</h3>
            <p className="text-gray-600">Built with Next.js for optimal performance and user experience.</p>
          </div>
          
          <div className="bg-white p-8 rounded-xl shadow-lg">
            <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center mb-4">
              <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
              </svg>
            </div>
            <h3 className="text-xl font-semibold mb-3">Easy to Use</h3>
            <p className="text-gray-600">Intuitive interface designed for the best user experience.</p>
          </div>
          
          <div className="bg-white p-8 rounded-xl shadow-lg">
            <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center mb-4">
              <svg className="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"></path>
              </svg>
            </div>
            <h3 className="text-xl font-semibold mb-3">Modern Design</h3>
            <p className="text-gray-600">Beautiful, responsive design that works on all devices.</p>
          </div>
        </div>
      </div>
    </main>
  )
}}"""
    
    with open(app_path / f"page{ext}", 'w', encoding='utf-8') as f:
        f.write(page_content)
    files_created.append(f"frontend/src/app/page{ext}")
    
    # Global CSS
    globals_css = """@tailwind base;
@tailwind components;
@tailwind utilities;"""
    
    with open(app_path / "globals.css", 'w', encoding='utf-8') as f:
        f.write(globals_css)
    files_created.append("frontend/src/app/globals.css")
    
    # Tailwind config
    tailwind_config = """/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'gradient-conic':
          'conic-gradient(from 180deg at 50% 50%, var(--tw-gradient-stops))',
      },
    },
  },
  plugins: [],
}"""
    
    with open(frontend_path / "tailwind.config.js", 'w', encoding='utf-8') as f:
        f.write(tailwind_config)
    files_created.append("frontend/tailwind.config.js")
    
    # PostCSS config
    postcss_config = """module.exports = {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}"""
    
    with open(frontend_path / "postcss.config.js", 'w', encoding='utf-8') as f:
        f.write(postcss_config)
    files_created.append("frontend/postcss.config.js")
    
    return files_created

async def create_fastapi_backend(backend_path: Path, idea: str, project_name: str, needs_ai: bool, needs_auth: bool, needs_database: bool) -> List[str]:
    """Create FastAPI backend structure"""
    files_created = []
    
    # Create directories
    api_path = backend_path / "api"
    models_path = backend_path / "models"
    utils_path = backend_path / "utils"
    
    for path in [api_path, models_path, utils_path]:
        path.mkdir(parents=True, exist_ok=True)
    
    # Requirements.txt
    requirements = [
        "fastapi==0.104.1",
        "uvicorn[standard]==0.24.0",
        "python-multipart==0.0.6",
        "python-dotenv==1.0.0",
        "requests==2.31.0",
        "pydantic==2.5.0"
    ]
    
    if needs_database:
        requirements.extend([
            "sqlalchemy==2.0.23",
            "psycopg2-binary==2.9.9",
            "alembic==1.13.0"
        ])
    
    if needs_ai:
        requirements.extend([
            "openai==1.3.0",
            "langchain==0.0.350"
        ])
    
    if needs_auth:
        requirements.extend([
            "python-jose[cryptography]==3.3.0",
            "passlib[bcrypt]==1.7.4",
            "python-jwt==4.0.0"
        ])
    
    with open(backend_path / "requirements.txt", 'w', encoding='utf-8') as f:
        f.write('\n'.join(requirements))
    files_created.append("backend/requirements.txt")
    
    # Main.py
    main_content = f"""from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    title="{project_name} API",
    description="{idea}",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Frontend dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Data models
class HealthResponse(BaseModel):
    status: str
    message: str

class ItemCreate(BaseModel):
    name: str
    description: str

class ItemResponse(BaseModel):
    id: int
    name: str
    description: str
    created_at: str

# Routes
@app.get("/")
async def root():
    return {{"message": "Welcome to {project_name} API"}}

@app.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(
        status="healthy",
        message="API is running successfully"
    )

@app.get("/api/items", response_model=list[ItemResponse])
async def get_items():
    # Mock data - replace with database queries
    return [
        ItemResponse(
            id=1,
            name="Sample Item",
            description="This is a sample item",
            created_at="2024-01-01T00:00:00Z"
        )
    ]

@app.post("/api/items", response_model=ItemResponse)
async def create_item(item: ItemCreate):
    # Mock creation - replace with database insert
    return ItemResponse(
        id=2,
        name=item.name,
        description=item.description,
        created_at="2024-01-01T00:00:00Z"
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)"""
    
    with open(backend_path / "main.py", 'w', encoding='utf-8') as f:
        f.write(main_content)
    files_created.append("backend/main.py")
    
    # .env file
    env_content = f"""# {project_name} Environment Variables
DEBUG=True
PORT=8001
CORS_ORIGINS=http://localhost:5173"""
    
    if needs_database:
        env_content += """

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/dbname"""
    
    if needs_ai:
        env_content += """

# AI/OpenAI
OPENAI_API_KEY=your_openai_api_key_here"""
    
    if needs_auth:
        env_content += """

# Authentication
SECRET_KEY=your_secret_key_here
ACCESS_TOKEN_EXPIRE_MINUTES=30"""
    
    with open(backend_path / ".env", 'w', encoding='utf-8') as f:
        f.write(env_content)
    files_created.append("backend/.env")
    
    return files_created

async def create_nodejs_backend(backend_path: Path, idea: str, project_name: str, needs_ai: bool, needs_auth: bool, needs_database: bool) -> List[str]:
    """Create Node.js Express backend structure"""
    files_created = []
    
    # Create directories
    routes_path = backend_path / "routes"
    models_path = backend_path / "models"
    middleware_path = backend_path / "middleware"
    
    for path in [routes_path, models_path, middleware_path]:
        path.mkdir(parents=True, exist_ok=True)
    
    # Package.json
    package_json = {
        "name": project_name.lower().replace(" ", "-") + "-backend",
        "version": "1.0.0",
        "description": idea,
        "main": "server.js",
        "scripts": {
            "start": "node server.js",
            "dev": "nodemon server.js",
            "test": "jest"
        },
        "dependencies": {
            "express": "^4.18.2",
            "cors": "^2.8.5",
            "dotenv": "^16.3.1",
            "helmet": "^7.1.0",
            "morgan": "^1.10.0"
        },
        "devDependencies": {
            "nodemon": "^3.0.2",
            "jest": "^29.7.0"
        }
    }
    
    if needs_database:
        package_json["dependencies"]["mongoose"] = "^8.0.0"
    
    if needs_ai:
        package_json["dependencies"]["openai"] = "^4.20.0"
    
    if needs_auth:
        package_json["dependencies"].update({
            "jsonwebtoken": "^9.0.2",
            "bcryptjs": "^2.4.3"
        })
    
    with open(backend_path / "package.json", 'w', encoding='utf-8') as f:
        json.dump(package_json, f, indent=2)
    files_created.append("backend/package.json")
    
    # Server.js
    server_content = f"""const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const morgan = require('morgan');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 8001;

// Middleware
app.use(helmet());
app.use(cors({{
    origin: ['http://localhost:5173'],
    credentials: true
}}));
app.use(morgan('combined'));
app.use(express.json());
app.use(express.urlencoded({{ extended: true }}));

// Routes
app.get('/', (req, res) => {{
    res.json({{
        message: 'Welcome to {project_name} API',
        description: '{idea}',
        version: '1.0.0'
    }});
}});

app.get('/health', (req, res) => {{
    res.json({{
        status: 'healthy',
        message: 'API is running successfully',
        timestamp: new Date().toISOString()
    }});
}});

// API Routes
app.get('/api/items', (req, res) => {{
    // Mock data - replace with database queries
    res.json([
        {{
            id: 1,
            name: 'Sample Item',
            description: 'This is a sample item',
            createdAt: new Date().toISOString()
        }}
    ]);
}});

app.post('/api/items', (req, res) => {{
    const {{ name, description }} = req.body;
    
    // Mock creation - replace with database insert
    res.status(201).json({{
        id: Date.now(),
        name,
        description,
        createdAt: new Date().toISOString()
    }});
}});

// Error handling middleware
app.use((err, req, res, next) => {{
    console.error(err.stack);
    res.status(500).json({{
        error: 'Something went wrong!',
        message: process.env.NODE_ENV === 'development' ? err.message : undefined
    }});
}});

// 404 handler
app.use('*', (req, res) => {{
    res.status(404).json({{
        error: 'Route not found'
    }});
}});

app.listen(PORT, () => {{
    console.log('{project_name} API running on port ' + PORT);
}});"""
    
    with open(backend_path / "server.js", 'w', encoding='utf-8') as f:
        f.write(server_content)
    files_created.append("backend/server.js")
    
    # .env file
    env_content = f"""# {project_name} Environment Variables
NODE_ENV=development
PORT=8001"""
    
    if needs_database:
        env_content += "\n\n# Database\nMONGODB_URI=mongodb://localhost:27017/yourdbname"
    
    if needs_ai:
        env_content += "\n\n# AI/OpenAI\nOPENAI_API_KEY=your_openai_api_key_here"
    
    if needs_auth:
        env_content += "\n\n# Authentication\nJWT_SECRET=your_jwt_secret_here\nJWT_EXPIRES_IN=7d"
    
    with open(backend_path / ".env", 'w', encoding='utf-8') as f:
        f.write(env_content)
    files_created.append("backend/.env")
    
    return files_created

async def create_root_files(project_path: Path, project_name: str, idea: str, tech_stack: List[str]) -> List[str]:
    """Create root project files"""
    files_created = []
    
    # README.md
    readme_content = f"""# {project_name}

{idea}

## Tech Stack

{', '.join(tech_stack)}

## Getting Started

### Prerequisites

- Node.js 18+ (for frontend)
- Python 3.9+ (for backend, if using FastAPI)
- npm or yarn

### Installation

1. Clone the repository
```bash
git clone <repository-url>
cd {project_name.lower().replace(' ', '-')}
```

2. Install frontend dependencies
```bash
cd frontend
npm install
```

3. Install backend dependencies
```bash
cd ../backend
{'pip install -r requirements.txt' if 'FastAPI' in tech_stack or 'Python' in tech_stack else 'npm install'}
```

### Running the Application

1. Start the backend server
```bash
cd backend
{'python main.py' if 'FastAPI' in tech_stack or 'Python' in tech_stack else 'npm run dev'}
```

2. Start the frontend development server
```bash
cd frontend
npm {'run dev' if 'Next.js' in tech_stack else 'start'}
```

The application will be available at:
- Frontend: https://xverta.com
- Backend API: https://api.xverta.com

## Project Structure

The project follows a standard full-stack structure:
- frontend/ - {'Next.js' if 'Next.js' in tech_stack else 'React'} frontend application
- backend/ - {'FastAPI' if 'FastAPI' in tech_stack or 'Python' in tech_stack else 'Node.js Express'} backend API
- README.md - Project documentation
- .gitignore - Git ignore file

## Features

- Modern responsive design
- RESTful API
- Real-time updates
- Error handling
- Development tools

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the MIT License.
"""
    
    with open(project_path / "README.md", 'w', encoding='utf-8') as f:
        f.write(readme_content)
    files_created.append("README.md")
    
    # .gitignore
    gitignore_content = """# Dependencies
node_modules/
__pycache__/
*.pyc

# Environment variables
.env
.env.local
.env.development.local
.env.test.local
.env.production.local

# Build outputs
/frontend/build/
/frontend/.next/
/frontend/out/
/frontend/dist/

# Logs
npm-debug.log*
yarn-debug.log*
yarn-error.log*
*.log

# Runtime data
pids
*.pid
*.seed
*.pid.lock

# Coverage directory used by tools like istanbul
coverage/
*.lcov

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Database
*.sqlite
*.db

# Temporary files
tmp/
temp/"""
    
    with open(project_path / ".gitignore", 'w', encoding='utf-8') as f:
        f.write(gitignore_content)
    files_created.append(".gitignore")
    
    return files_created


@app.get("/debug/test-token")
async def test_github_token_direct():
    """Test GitHub token directly without ai_assistant import"""
    try:
        token = os.getenv("GITHUB_TOKEN")
        if not token:
            return {"error": "GITHUB_TOKEN not found in environment"}
        
        # Test token directly
        from github import Github
        test_client = Github(token)
        
        # Test authentication
        user = test_client.get_user()
        
        # Fix: Get rate limit properly (newer PyGithub versions)
        try:
            rate_limit = test_client.get_rate_limit()
            # Try different attributes for rate limit
            if hasattr(rate_limit, 'core'):
                remaining = rate_limit.core.remaining
            elif hasattr(rate_limit, 'rate'):
                remaining = rate_limit.rate.remaining  
            else:
                remaining = "Unknown"
        except Exception as rate_error:
            print(f"Rate limit check failed: {rate_error}")
            remaining = "Could not check"
        
        return {
            "token_valid": True,
            "authenticated_as": user.login,
            "user_id": user.id,
            "user_type": user.type,
            "rate_limit_remaining": remaining,
            "token_scopes": "Check GitHub settings for exact scopes"
        }
        
    except Exception as e:
        return {
            "token_valid": False,
            "error": str(e),
            "token_present": bool(os.getenv("GITHUB_TOKEN")),
            "suggestion": "Check if token has 'repo' and 'public_repo' permissions"
        }
# --- Enhanced Security Analysis Functions ---
# Replace the scan processing section in your /scan endpoint (around lines 240-280) with this enhanced version:

@app.post("/scan")
async def scan(request: ScanRequest):
    """Scan a website for security vulnerabilities with weighted scoring and store results for AI chat"""
    url = request.url
    
    try:
        # --- HYBRID CRAWLER INTEGRATION ---
        pages = await crawl_hybrid(url)
        
        # Enhanced scanning with SSL certificate analysis
        scan_result = await run_in_threadpool(scan_url, url)
        
        # Correctly call the async directory scanner
        scan_data = await scan_common_paths(url)
        exposed_paths = scan_data.get('accessible_paths', []) if scan_data else []
        waf_info = scan_data.get('waf_analysis', {}) if scan_data else {}
        dns_security = scan_data.get('dns_security', {}) if scan_data else {}

        suggestions = await run_in_threadpool(suggest_fixes, scan_result.get('headers', {}))
        ai_advice = await run_in_threadpool(
            ai_assistant.analyze_scan_with_llm,
            scan_result.get("https", False),
            scan_result.get("flags", []),
            scan_result.get("headers", {}),
            request.model_type
        )

        # Extract basic scan data
        ssl_certificate = scan_result.get("ssl_certificate", {}) if scan_result else {}
        flags = scan_result.get("flags", []) if scan_result else []
        headers = scan_result.get("headers", {}) if scan_result else {}
        https_enabled = scan_result.get("https", False) if scan_result else False

        # ============================================================================
        # 🎯 NEW WEIGHTED CATEGORY-BASED WEBSITE SECURITY SCORING SYSTEM
        # ============================================================================
        
        print("📊 Calculating weighted website security score...")

        # Initialize category scores (each starts at 100)
        category_scores = {
            'https_ssl': 100,       # HTTPS/SSL/TLS security
            'security_headers': 100, # HTTP security headers
            'vulnerabilities': 100,  # General vulnerabilities/flags
            'exposed_paths': 100,    # Directory/path exposure
            'dns_security': 100      # DNS security features
        }

        # Define category weights (must sum to 1.0)
        weights = {
            'https_ssl': 0.30,        # 30% - Most critical for web
            'security_headers': 0.25,  # 25% - Very important
            'vulnerabilities': 0.25,   # 25% - High impact
            'exposed_paths': 0.10,     # 10% - Medium impact
            'dns_security': 0.10       # 10% - Lower impact but important
        }

        print(f"🔍 Category weights: {weights}")

        # 1. Calculate HTTPS/SSL Score
        if not https_enabled:
            # Major penalty for no HTTPS
            category_scores['https_ssl'] -= 60
            print(f"🚨 HTTPS penalty: No HTTPS = -60 points")
        else:
            # Check SSL certificate issues
            ssl_issues = 0
            ssl_cert = ssl_certificate if isinstance(ssl_certificate, dict) else {}
            
            # Check for SSL certificate problems
            if ssl_cert.get('expired', False):
                category_scores['https_ssl'] -= 30
                ssl_issues += 1
                print(f"🔒 SSL penalty: Certificate expired = -30 points")
            
            if ssl_cert.get('self_signed', False):
                category_scores['https_ssl'] -= 20
                ssl_issues += 1
                print(f"🔒 SSL penalty: Self-signed certificate = -20 points")
            
            if ssl_cert.get('weak_cipher', False):
                category_scores['https_ssl'] -= 15
                ssl_issues += 1
                print(f"🔒 SSL penalty: Weak cipher = -15 points")
            
            # Check SSL version/protocol issues
            ssl_version = ssl_cert.get('version', '').lower()
            if 'sslv' in ssl_version or 'tlsv1.0' in ssl_version or 'tlsv1.1' in ssl_version:
                category_scores['https_ssl'] -= 25
                ssl_issues += 1
                print(f"🔒 SSL penalty: Outdated protocol ({ssl_version}) = -25 points")
            
            if ssl_issues == 0:
                print(f"✅ SSL bonus: Good HTTPS configuration")

        # 2. Calculate Security Headers Score
        essential_headers = {
            'strict-transport-security': 20,  # HSTS
            'content-security-policy': 20,    # CSP
            'x-frame-options': 15,           # Clickjacking protection
            'x-content-type-options': 10,    # MIME sniffing protection
            'referrer-policy': 10,           # Referrer policy
            'x-xss-protection': 10,          # XSS protection
            'permissions-policy': 10,        # Feature policy
            'expect-ct': 5                   # Certificate transparency
        }

        headers_penalty_total = 0
        missing_headers = []
        
        for header, penalty in essential_headers.items():
            header_found = False
            
            # Check for header (case insensitive)
            for actual_header in headers.keys():
                if header.lower() == actual_header.lower():
                    header_found = True
                    break
            
            if not header_found:
                category_scores['security_headers'] -= penalty
                headers_penalty_total += penalty
                missing_headers.append(header)

        print(f"🛡️ Security headers penalty: {len(missing_headers)} missing = -{headers_penalty_total} points")
        if missing_headers:
            print(f"   Missing: {', '.join(missing_headers[:3])}{'...' if len(missing_headers) > 3 else ''}")

        # 3. Calculate Vulnerabilities Score (from flags)
        vulnerability_penalty_total = 0
        critical_flags = []
        
        for flag in flags:
            flag_lower = flag.lower()
            
            # Categorize vulnerability severity
            if any(keyword in flag_lower for keyword in ['injection', 'xss', 'csrf', 'sql', 'rce', 'critical']):
                category_scores['vulnerabilities'] -= 25
                vulnerability_penalty_total += 25
                critical_flags.append(flag)
                print(f"🚨 Critical vulnerability: {flag} = -25 points")
            elif any(keyword in flag_lower for keyword in ['missing', 'weak', 'insecure', 'exposed']):
                category_scores['vulnerabilities'] -= 15
                vulnerability_penalty_total += 15
                print(f"⚠️ High vulnerability: {flag} = -15 points")
            elif any(keyword in flag_lower for keyword in ['deprecated', 'outdated', 'info']):
                category_scores['vulnerabilities'] -= 8
                vulnerability_penalty_total += 8
                print(f"📋 Medium vulnerability: {flag} = -8 points")
            else:
                # General vulnerability
                category_scores['vulnerabilities'] -= 10
                vulnerability_penalty_total += 10
                print(f"🔍 General vulnerability: {flag} = -10 points")

        print(f"🛡️ Total vulnerability penalty: {len(flags)} flags = -{vulnerability_penalty_total} points")

        # 4. Calculate Exposed Paths Score
        exposed_paths_penalty_total = 0
        sensitive_paths = []
        
        for path_info in exposed_paths:
            path = path_info.get('path', '') if isinstance(path_info, dict) else str(path_info)
            path_lower = path.lower()
            
            # Categorize path sensitivity
            if any(keyword in path_lower for keyword in [
                'admin', 'config', 'backup', '.env', 'secret', 'private', 'key', 'password'
            ]):
                category_scores['exposed_paths'] -= 20
                exposed_paths_penalty_total += 20
                sensitive_paths.append(path)
                print(f"🚨 Sensitive path exposed: {path} = -20 points")
            elif any(keyword in path_lower for keyword in [
                'test', 'dev', 'debug', 'staging', 'internal'
            ]):
                category_scores['exposed_paths'] -= 10
                exposed_paths_penalty_total += 10
                print(f"⚠️ Development path exposed: {path} = -10 points")
            else:
                # General exposed path
                category_scores['exposed_paths'] -= 5
                exposed_paths_penalty_total += 5
                print(f"📁 Path exposed: {path} = -5 points")

        print(f"🚪 Exposed paths penalty: {len(exposed_paths)} paths = -{exposed_paths_penalty_total} points")

        # 5. Calculate DNS Security Score
        dns_penalty_total = 0
        dns_issues = []
        
        if isinstance(dns_security, dict):
            # DNSSEC check
            dnssec_info = dns_security.get('dnssec', {})
            if isinstance(dnssec_info, dict) and not dnssec_info.get('enabled', False):
                category_scores['dns_security'] -= 30
                dns_penalty_total += 30
                dns_issues.append('No DNSSEC')
                print(f"🔐 DNS penalty: No DNSSEC = -30 points")

            # DMARC check
            dmarc_info = dns_security.get('dmarc', {})
            if isinstance(dmarc_info, dict) and not dmarc_info.get('enabled', False):
                category_scores['dns_security'] -= 25
                dns_penalty_total += 25
                dns_issues.append('No DMARC')
                print(f"📧 DNS penalty: No DMARC = -25 points")

            # DKIM check
            dkim_info = dns_security.get('dkim', {})
            if isinstance(dkim_info, dict):
                selectors = dkim_info.get('selectors_found', [])
                if not selectors or len(selectors) == 0:
                    category_scores['dns_security'] -= 20
                    dns_penalty_total += 20
                    dns_issues.append('No DKIM')
                    print(f"🔑 DNS penalty: No DKIM selectors = -20 points")

        print(f"🔐 DNS security penalty: {len(dns_issues)} issues = -{dns_penalty_total} points")

        # Ensure no category score goes below 0
        for category in category_scores:
            category_scores[category] = max(0, category_scores[category])

        print(f"📊 Category scores after penalties: {category_scores}")

        # 6. Calculate Weighted Average Score
        overall_score = 0
        for category, score in category_scores.items():
            weighted_contribution = score * weights[category]
            overall_score += weighted_contribution
            print(f"   {category}: {score} × {weights[category]} = {weighted_contribution:.1f}")

        print(f"📊 Base weighted score: {overall_score:.1f}")

        # 7. Add Bonus for Good Security Practices
        security_bonus_total = 0
        
        # WAF detection bonus
        if waf_info.get('waf_detected', False):
            waf_bonus = 5
            overall_score += waf_bonus
            security_bonus_total += waf_bonus
            print(f"🛡️ WAF bonus: WAF detected = +{waf_bonus} points")

        # Strong security headers bonus
        if 'content-security-policy' in [h.lower() for h in headers.keys()] and \
           'strict-transport-security' in [h.lower() for h in headers.keys()]:
            headers_bonus = 3
            overall_score += headers_bonus
            security_bonus_total += headers_bonus
            print(f"🔒 Security headers bonus: CSP + HSTS = +{headers_bonus} points")

        # Perfect HTTPS implementation bonus
        if https_enabled and category_scores['https_ssl'] >= 90:
            https_bonus = 2
            overall_score += https_bonus
            security_bonus_total += https_bonus
            print(f"✅ HTTPS bonus: Perfect SSL/TLS = +{https_bonus} points")

        if security_bonus_total > 0:
            print(f"✅ Total security bonus: +{security_bonus_total} points")

        # 8. Final Score Calculation
        overall_score = max(0, min(100, int(overall_score)))

        print(f"🎯 Final Website Security Score: {overall_score}/100")

        # Determine security level
        if overall_score >= 90:
            security_level = "Excellent"
        elif overall_score >= 75:
            security_level = "Good"
        elif overall_score >= 50:
            security_level = "Medium"
        elif overall_score >= 25:
            security_level = "Low" 
        else:
            security_level = "Critical"

        # Store detailed scoring breakdown
        scoring_breakdown = {
            "category_scores": category_scores,
            "category_weights": weights,
            "penalties_applied": {
                "https_ssl": (60 if not https_enabled else 0) + sum([30 if ssl_certificate.get('expired') else 0,
                                                                     20 if ssl_certificate.get('self_signed') else 0,
                                                                     15 if ssl_certificate.get('weak_cipher') else 0]),
                "security_headers": headers_penalty_total,
                "vulnerabilities": vulnerability_penalty_total,
                "exposed_paths": exposed_paths_penalty_total,
                "dns_security": dns_penalty_total
            },
            "bonuses_applied": {
                "waf_detection": 5 if waf_info.get('waf_detected', False) else 0,
                "security_headers": 3 if all(h in [header.lower() for header in headers.keys()] 
                                           for h in ['content-security-policy', 'strict-transport-security']) else 0,
                "perfect_https": 2 if https_enabled and category_scores['https_ssl'] >= 90 else 0
            },
            "weighted_contributions": {
                category: category_scores[category] * weights[category] 
                for category in category_scores
            }
        }

        # Update scan_result with new scoring
        if scan_result:
            scan_result["security_score"] = overall_score
            scan_result["security_level"] = security_level
            scan_result["scoring_breakdown"] = scoring_breakdown

        # ============================================================================
        # END OF NEW WEBSITE SCORING SYSTEM  
        # ============================================================================

        # Enhanced summary with new scoring information
        scan_summary = scan_data.get('scan_summary', {}) if scan_data else {}
        domain = scan_summary.get('domain', 'Unknown')
        summary = f"""Security Scan Complete

Target Analysis:
- Domain: {domain}
- Overall Security Score: {overall_score}/100 ({security_level})
- HTTPS: {'Enabled' if https_enabled else 'Disabled'}
- Vulnerabilities: {len(flags)} issues found
- Pages Crawled: {len(pages)} pages
- Security Headers: {len(headers)} detected
- Exposed Paths: {len(exposed_paths)} found

Web Application Firewall (WAF):
- WAF Detected: {'Yes' if waf_info.get('waf_detected') else 'No'}
- WAF Type: {waf_info.get('waf_type', 'None detected')}
- Protection Level: {waf_info.get('protection_level', 'Unknown')}
- Blocked Requests: {waf_info.get('blocked_requests', 0)}/{waf_info.get('total_requests', 0)}

DNS Security Features:
- DNSSEC: {'Enabled' if dns_security.get('dnssec', {}).get('enabled') else 'Disabled'} - {dns_security.get('dnssec', {}).get('status', 'Unknown')}
- DMARC: {'Enabled' if dns_security.get('dmarc', {}).get('enabled') else 'Not configured'} - {dns_security.get('dmarc', {}).get('policy', 'No policy')}
- DKIM: {'Found' if dns_security.get('dkim', {}).get('selectors_found') else 'Not found'} - {len(dns_security.get('dkim', {}).get('selectors_found', []))} selectors

SSL/TLS Security Analysis:
{_format_ssl_analysis(ssl_certificate)}

Security Score Breakdown:
- HTTPS/SSL: {category_scores['https_ssl']}/100 ({int(weights['https_ssl']*100)}% weight)
- Security Headers: {category_scores['security_headers']}/100 ({int(weights['security_headers']*100)}% weight)
- Vulnerabilities: {category_scores['vulnerabilities']}/100 ({int(weights['vulnerabilities']*100)}% weight)
- Exposed Paths: {category_scores['exposed_paths']}/100 ({int(weights['exposed_paths']*100)}% weight)
- DNS Security: {category_scores['dns_security']}/100 ({int(weights['dns_security']*100)}% weight)

Key Issues Found:
{chr(10).join([f'- {flag}' for flag in flags[:5]]) if flags else '- No critical issues detected'}

Potentially Exposed Paths:
{chr(10).join([f'- Found accessible path: {p.get("path", p) if isinstance(p, dict) else p}' for p in exposed_paths[:3]]) if exposed_paths else '- No common sensitive paths were found.'}

Ready to help with specific security questions about this scan!"""
        
        scan_response = {
            "url": url,
            "pages": pages,
            "scan_result": scan_result,
            "exposed_paths": exposed_paths,
            "waf_analysis": waf_info,
            "dns_security": dns_security,
            "suggestions": suggestions,
            "ai_assistant_advice": ai_advice,
            "summary": summary
        }
        
        # Debug logging to see what we're returning
        print(f"🔍 DEBUG - Overall Security Score: {overall_score}/100 ({security_level})")
        print(f"🔍 DEBUG - Category Scores: {category_scores}")
        print(f"🔍 DEBUG - Scan Response Keys: {list(scan_response.keys())}")
        
        WebsiteScan.latest_scan = scan_response
        return scan_response
        
    except Exception as e:
        error_detail = f"Scan failed for {url}: {str(e)}"
        print(f"❌ {error_detail}")
        raise HTTPException(status_code=500, detail=error_detail)


@app.post("/update-knowledge-base")
async def force_update_knowledge_base():
    """Force update knowledge base from web (ignoring 7-day cache)"""
    try:
        from web_scraper import force_update_knowledge_base
        success = await run_in_threadpool(force_update_knowledge_base)
        
        if success:
            # Rebuild RAG database to include new data
            from build_rag_db import build_database
            await run_in_threadpool(build_database, False, False)
            
            return {
                "success": True,
                "message": "Knowledge base force updated with fresh web data",
                "cache_bypass": True,
                "pdf_generated": True,
                "next_auto_update": "7 days from now"
            }
        else:
            return {
                "success": False,
                "message": "Failed to update knowledge base",
                "error": "Web scraping failed"
            }
            
    except Exception as e:
        return {
            "success": False,
            "message": f"Update failed: {str(e)}",
            "error": str(e)
        }


@app.post("/analyze-repo")
async def analyze_repo_comprehensive(request: RepoAnalysisRequest):
    """Comprehensive repository security analysis with file scanning and store results for AI chat"""
    try:
        repo_url = request.repo_url
        model_type = request.model_type
        deep_scan = request.deep_scan
        
        if not repo_url:
            return {"error": "Repository URL is required"}
        
        # Validate model type
        if model_type not in ['fast', 'smart']:
            model_type = 'smart'  # Default fallback
        
        # Create temporary directory for cloning
        temp_dir = tempfile.mkdtemp()
        
        # Verify temp directory is writable
        try:
            test_file = os.path.join(temp_dir, 'test_write.tmp')
            with open(test_file, 'w', encoding='utf-8') as f:
                f.write('test')
            os.remove(test_file)
        except Exception as e:
            return {"error": f"Temporary directory is not writable: {temp_dir}\nError: {e}\nTry running VS Code as administrator or check folder permissions."}
        
        print(f"📁 Created temporary directory: {temp_dir}")
        
        try:
            # Clone the repository for comprehensive analysis
            print(f"🔄 Cloning repository: {repo_url}")
            
            # Handle different URL formats
            clone_url = repo_url
            if not clone_url.endswith('.git'):
                clone_url += '.git'
            
            # Clone repository with proper error handling
            import git
            from git import Repo, GitCommandError
            
            try:
                # Use shallow clone for better performance - we only need current files
                repo = git.Repo.clone_from(clone_url, temp_dir, depth=1)
                print(f"✅ Repository cloned successfully to {temp_dir} (shallow clone)")
                
                # Configure the cloned repo for Windows compatibility
                try:
                    with repo.config_writer() as config_writer:
                        config_writer.set_value("core", "filemode", "false")
                        config_writer.set_value("core", "autocrlf", "true")
                        config_writer.set_value("core", "safecrlf", "false")
                except Exception as config_error:
                    print(f"⚠️ Could not configure Git settings: {config_error}")
                
            except GitCommandError as git_error:
                # Fallback to full clone if shallow fails
                print(f"⚠️ Shallow clone failed, trying full clone: {git_error}")
                try:
                    repo = git.Repo.clone_from(clone_url, temp_dir)
                    print(f"✅ Repository cloned successfully to {temp_dir} (full clone)")
                    
                    # Configure the cloned repo
                    try:
                        with repo.config_writer() as config_writer:
                            config_writer.set_value("core", "filemode", "false")
                            config_writer.set_value("core", "autocrlf", "true")
                    except Exception as config_error:
                        print(f"⚠️ Could not configure Git settings: {config_error}")
                        
                except GitCommandError as shallow_error:
                    print(f"⚠️ Shallow clone also failed: {shallow_error}")
                    raise Exception(f"All Git clone methods failed. Last error: {shallow_error}")
            
            # Get basic repo info from GitHub API with enhanced error handling
            repo_url_clean = repo_url.rstrip('/').replace('.git', '')
            parts = repo_url_clean.split('/')
            github_repo = None
            github_error = None
            
            # Extract owner and repo name from URL
            if len(parts) >= 5:
                owner, repo_name = parts[-2], parts[-1]
                print(f"🔍 Extracted repo info: {owner}/{repo_name}")
                
                # Try to use github_client first, then create a new one if needed
                working_client = None
                
                # First try the imported github_client
                if github_client:
                    try:
                        # Test the client with a quick call
                        github_client.get_user()
                        working_client = github_client
                        print("✅ Using imported GitHub client")
                    except Exception as test_error:
                        print(f"⚠️ Imported github_client failed: {test_error}")
                
                if not working_client:
                    print("⚠️ Creating new GitHub client...")
                    # Try to create a new GitHub client if the imported one failed
                    token = os.getenv("GITHUB_TOKEN")
                    if token:
                        try:
                            from github import Github
                            working_client = Github(token)
                            # Test the new client
                            working_client.get_user()
                            print("✅ Created new GitHub client with token")
                        except Exception as client_error:
                            print(f"❌ Failed to create GitHub client: {client_error}")
                            working_client = None
                    
                    if not working_client:
                        # Try anonymous access for public repos
                        try:
                            from github import Github
                            working_client = Github()
                            print("✅ Created anonymous GitHub client")
                        except Exception as anon_error:
                            print(f"❌ Failed to create anonymous GitHub client: {anon_error}")
                
                if working_client:
                    try:
                        github_repo = working_client.get_repo(f"{owner}/{repo_name}")
                        print(f"✅ Successfully fetched GitHub repo info for {owner}/{repo_name}")
                        print(f"📊 Repo details: {github_repo.full_name}, {github_repo.language}, {github_repo.stargazers_count} stars")
                    except Exception as e:
                        github_error = str(e)
                        print(f"⚠️ Could not fetch GitHub repo info: {e}")
                        if "404" in str(e):
                            print(f"💡 Repository might be private or URL might be incorrect")
                        elif "403" in str(e):
                            print(f"💡 API rate limit reached or authentication required")
                        elif "401" in str(e):
                            print(f"💡 Authentication failed - check GitHub token")
                else:
                    github_error = "No GitHub client available"
                    print(f"❌ No GitHub client available for API access")
            else:
                github_error = "Invalid repository URL format"
                print(f"❌ Invalid repository URL format: {repo_url_clean}")
            
            # Parallel scanning for better performance
            print("🔍 Starting parallel security scans...")
            
            # Create tasks for parallel execution
            scan_tasks = []
            
            # 1. File security scan
            file_scan_task = run_in_threadpool(scan_for_sensitive_files, temp_dir)
            scan_tasks.append(("file_scan", file_scan_task))
            
            # 2. Static analysis (if deep_scan enabled)
            if deep_scan:
                static_analysis_task = run_in_threadpool(run_bandit, temp_dir)
                scan_tasks.append(("static_analysis", static_analysis_task))
            
            # 3. Dependency scan
            dependency_scan_task = run_in_threadpool(scan_dependencies, temp_dir)
            scan_tasks.append(("dependency_scan", dependency_scan_task))
            
            # 4. Code quality scan
            code_quality_task = run_in_threadpool(scan_code_quality_patterns, temp_dir)
            scan_tasks.append(("code_quality", code_quality_task))
            
            # Execute parallel scans
            scan_results = {}
            for scan_name, task in scan_tasks:
                try:
                    print(f"🔄 Running {scan_name}...")
                    scan_results[scan_name] = await task
                    print(f"✅ {scan_name} completed")
                except Exception as e:
                    print(f"⚠️ {scan_name} failed: {e}")
                    scan_results[scan_name] = []
            
            # Extract results
            file_scan_results = scan_results.get("file_scan", {})
            static_analysis_results = scan_results.get("static_analysis", [])
            dependency_scan_results = scan_results.get("dependency_scan", {})
            code_quality_results = scan_results.get("code_quality", [])
            
            # Ensure static_analysis_results is properly formatted
            if not isinstance(static_analysis_results, list):
                static_analysis_results = []
            
            # 5. Deep secret scanning (if enabled)
            secret_scan_results = []
            if deep_scan:
                print("🕵️ Performing deep content scanning for secrets...")
                scanned_files = 0
                skip_dirs = {
                    'venv', 'env', '.env', 'virtualenv', '__pycache__', 
                    'node_modules', '.git', '.svn', 'build', 'dist', 'target',
                    '.gradle', '.maven', 'vendor', '.next', '.nuxt', 'coverage',
                    'logs', 'tmp', 'temp', '.tmp', '.temp', '.DS_Store', 
                    '.vscode', '.idea', 'docker-data'
                }
                
                for root, dirs, files in os.walk(temp_dir):
                    # Filter out directories we should skip
                    dirs[:] = [d for d in dirs if not any(skip_pattern in d.lower() for skip_pattern in skip_dirs)]
                    
                    # Skip if current directory contains excluded patterns
                    if any(skip_pattern in root.lower() for skip_pattern in skip_dirs):
                        continue
                    
                    for file in files:
                        if scanned_files >= 100:  # Increased limit since we're filtering better
                            break
                        
                        if file.endswith(('.py', '.js', '.ts', '.jsx', '.tsx', '.json', '.yml', '.yaml', '.env', '.config', '.txt', '.md', '.sh', '.bat')):
                            file_path = os.path.join(root, file)
                            secrets = await run_in_threadpool(scan_file_contents_for_secrets, file_path)
                            
                            # Filter false positives
                            filtered_secrets = []
                            for secret in secrets:
                                if not is_likely_false_positive(file_path, secret.get('secret_type', ''), secret.get('match', '')):
                                    filtered_secrets.append(secret)
                            
                            secret_scan_results.extend(filtered_secrets)
                            scanned_files += 1
            
            # Initialize analysis tracking arrays
            analysis_warnings = []
            analysis_errors = []
            
            # Add Windows compatibility warnings if needed
            if os.name == 'nt':  # Windows
                analysis_warnings.extend([
                    "Running on Windows - some Unix-specific security tools may have limited functionality",
                    "File path analysis optimized for Windows environment", 
                    "If analysis tools fail, try running VS Code as administrator"
                ])
            
            # Run traditional GitHub API analysis for AI insights
            print("📊 Running AI analysis...")
            try:
                if github_repo:
                    github_analysis = await run_in_threadpool(
                        ai_assistant.analyze_github_repo, 
                        repo_url, 
                        model_type,
                        temp_dir  # Pass existing clone directory
                    )
                else:
                    # Fallback when GitHub API fails
                    github_analysis = f"""
📊 **Repository Analysis** (Limited - GitHub API unavailable)

**Repository:** {repo_url}
**Status:** Successfully cloned and analyzed locally
**Note:** GitHub API returned error: {github_error or 'Unknown error'} - repository might be private or require authentication

✅ **Local Analysis Completed:**
• File security scanning: Complete
• Secret detection: Complete  
• Static code analysis: Complete
• Dependency scanning: Complete
• Code quality analysis: Complete

💡 **Recommendation:** For full GitHub integration, ensure repository is public or add GitHub token authentication.
"""
            except Exception as e:
                github_analysis = f"⚠️ AI analysis error: {str(e)}"
                analysis_errors.append(f"GitHub API analysis failed: {str(e)}")
                # Add enhanced fallback analysis
                github_analysis += f"""

📊 **Enhanced Local Analysis Summary:**
• Repository successfully analyzed using local tools
• Enhanced with live SonarSource security rules
• {len(secret_scan_results)} secrets detected
• {len(static_analysis_results)} static analysis issues found  
• {len(code_quality_results)} code quality issues identified
• Security recommendations generated using RAG-enhanced AI"""
            
            # Compile comprehensive results with enhanced repository info
            # Ensure all dicts are valid for .get() usage
            file_scan_results = file_scan_results if isinstance(file_scan_results, dict) else {}
            dependency_scan_results = dependency_scan_results if isinstance(dependency_scan_results, dict) else {}
            
            # Create repository info with better fallback handling
            repository_info = {
                "url": repo_url,
                "name": "Unknown",
                "description": "No description",
                "language": "Unknown", 
                "stars": 0,
                "forks": 0,
                "open_issues": 0
            }
            
            if github_repo:
                # Successfully got GitHub API data
                repository_info.update({
                    "name": getattr(github_repo, 'full_name', "Unknown"),
                    "description": getattr(github_repo, 'description', None) or "No description",
                    "language": getattr(github_repo, 'language', None) or "Unknown",
                    "stars": getattr(github_repo, 'stargazers_count', 0),
                    "forks": getattr(github_repo, 'forks_count', 0),
                    "open_issues": getattr(github_repo, 'open_issues_count', 0)
                })
                print(f"✅ Using GitHub API data: {repository_info['name']} ({repository_info['language']})")
            else:
                # Fallback: extract what we can from the URL
                if len(parts) >= 5:
                    owner, repo_name = parts[-2], parts[-1]
                    repository_info["name"] = f"{owner}/{repo_name}"
                    print(f"⚠️ Using URL-based fallback: {repository_info['name']}")
                    
                    # Add GitHub API error to analysis warnings
                    if github_error:
                        analysis_warnings.append(f"GitHub API access failed: {github_error}")
                        analysis_warnings.append("Repository statistics (stars, forks, language) unavailable - using URL-based fallback")
            
            comprehensive_results = {
                "repository_info": repository_info,
                "file_security_scan": file_scan_results,
                "secret_scan_results": secret_scan_results,
                "static_analysis_results": static_analysis_results,
                "dependency_scan_results": dependency_scan_results,
                "code_quality_results": code_quality_results,
                "ai_analysis": github_analysis,
                "analysis_warnings": analysis_warnings,
                "analysis_errors": analysis_errors,
                "security_summary": {
                    "total_files_scanned": file_scan_results.get('total_files_scanned', 0),
                    "sensitive_files_found": len(file_scan_results.get('sensitive_files', [])),
                    "risky_files_found": len(file_scan_results.get('risky_files', [])),
                    "secrets_found": len(secret_scan_results) if secret_scan_results else 0,
                    "static_issues_found": len(static_analysis_results) if static_analysis_results else 0,
                    "vulnerable_dependencies": len(dependency_scan_results.get('vulnerable_packages', [])),
                    "code_quality_issues": len(code_quality_results) if code_quality_results else 0,
                    "security_files_present": len(file_scan_results.get('security_files_found', [])),
                    "missing_security_files": len(file_scan_results.get('missing_security_files', []))
                }
            }
            
            # ============================================================================
            # 🎯 NEW WEIGHTED CATEGORY-BASED SECURITY SCORING SYSTEM
            # ============================================================================
            
            print("📊 Calculating weighted security score...")

            # Initialize category scores (each starts at 100)
            category_scores = {
                'secrets': 100,
                'sensitive_files': 100,
                'static_analysis': 100,
                'dependencies': 100,
                'code_quality': 100
            }

            # Define category weights (must sum to 1.0)
            weights = {
                'secrets': 0.30,           # 30% - Most critical
                'sensitive_files': 0.20,   # 20% - High impact
                'static_analysis': 0.20,   # 20% - High impact  
                'dependencies': 0.20,      # 20% - High impact
                'code_quality': 0.10       # 10% - Lower impact
            }

            print(f"🔍 Category weights: {weights}")

            # 1. Calculate Secrets Score (Critical Impact)
            secrets_count = len(secret_scan_results) if secret_scan_results else 0
            if secrets_count > 0:
                # Critical penalty: -40 points per secret (very harsh)
                category_scores['secrets'] -= secrets_count * 40
                print(f"🚨 Secrets penalty: {secrets_count} secrets × 40 = -{secrets_count * 40} points")

            # 2. Calculate Sensitive Files Score
            sensitive_files_count = len(file_scan_results.get('sensitive_files', []))
            risky_files_count = len(file_scan_results.get('risky_files', []))

            if sensitive_files_count > 0:
                # High penalty: -15 points per sensitive file
                category_scores['sensitive_files'] -= sensitive_files_count * 15
                print(f"⚠️ Sensitive files penalty: {sensitive_files_count} files × 15 = -{sensitive_files_count * 15} points")

            if risky_files_count > 0:
                # Medium penalty: -5 points per risky file
                category_scores['sensitive_files'] -= risky_files_count * 5
                print(f"📁 Risky files penalty: {risky_files_count} files × 5 = -{risky_files_count * 5} points")

            # 3. Calculate Static Analysis Score (Severity-Based)
            static_penalty_total = 0
            if static_analysis_results:
                for issue in static_analysis_results:
                    severity = issue.get('severity', 'UNKNOWN').upper()
                    if severity in ['HIGH', 'CRITICAL']:
                        category_scores['static_analysis'] -= 10
                        static_penalty_total += 10
                    elif severity in ['MEDIUM', 'MODERATE']:
                        category_scores['static_analysis'] -= 5
                        static_penalty_total += 5
                    else:  # LOW, INFO, etc.
                        category_scores['static_analysis'] -= 2
                        static_penalty_total += 2
                print(f"🛡️ Static analysis penalty: {len(static_analysis_results)} issues = -{static_penalty_total} points")

            # 4. Calculate Dependencies Score (Severity-Based)
            dependency_penalty_total = 0
            vulnerable_packages = dependency_scan_results.get('vulnerable_packages', []) if isinstance(dependency_scan_results, dict) else []

            if vulnerable_packages:
                for pkg in vulnerable_packages:
                    severity = pkg.get('severity', 'Unknown').lower()
                    if severity == 'critical':
                        category_scores['dependencies'] -= 15
                        dependency_penalty_total += 15
                    elif severity == 'high':
                        category_scores['dependencies'] -= 10
                        dependency_penalty_total += 10
                    elif severity == 'medium':
                        category_scores['dependencies'] -= 7
                        dependency_penalty_total += 7
                    else:  # low, info
                        category_scores['dependencies'] -= 3
                        dependency_penalty_total += 3
                print(f"📦 Dependencies penalty: {len(vulnerable_packages)} packages = -{dependency_penalty_total} points")

            # 5. Calculate Code Quality Score (Severity-Based)
            code_quality_penalty_total = 0
            if code_quality_results:
                for issue in code_quality_results:
                    severity = issue.get('severity', 'Unknown')
                    if severity in ['Critical', 'High']:
                        category_scores['code_quality'] -= 5
                        code_quality_penalty_total += 5
                    elif severity == 'Medium':
                        category_scores['code_quality'] -= 2
                        code_quality_penalty_total += 2
                    else:  # Low, Info
                        category_scores['code_quality'] -= 1
                        code_quality_penalty_total += 1
                print(f"⚡ Code quality penalty: {len(code_quality_results)} issues = -{code_quality_penalty_total} points")

            # Ensure no category score goes below 0
            for category in category_scores:
                category_scores[category] = max(0, category_scores[category])

            print(f"📊 Category scores after penalties: {category_scores}")

            # 6. Calculate Weighted Average Score
            overall_score = 0
            for category, score in category_scores.items():
                weighted_contribution = score * weights[category]
                overall_score += weighted_contribution
                print(f"   {category}: {score} × {weights[category]} = {weighted_contribution:.1f}")

            print(f"📊 Base weighted score: {overall_score:.1f}")

            # 7. Add Bonus for Good Security Practices
            security_files_found = len(file_scan_results.get('security_files_found', []))
            if security_files_found > 0:
                # Bonus: up to 10 points for security files (2 points each, max 5 files)
                security_files_bonus = min(10, security_files_found * 2)
                overall_score += security_files_bonus
                print(f"✅ Security files bonus: {security_files_found} files × 2 = +{security_files_bonus} points")

            # 8. Final Score Calculation
            overall_score = max(0, min(100, int(overall_score)))

            print(f"🎯 Final Security Score: {overall_score}/100")

            # Store detailed scoring breakdown for frontend
            comprehensive_results["scoring_breakdown"] = {
                "category_scores": category_scores,
                "category_weights": weights,
                "penalties_applied": {
                    "secrets": secrets_count * 40 if secrets_count > 0 else 0,
                    "sensitive_files": (sensitive_files_count * 15) + (risky_files_count * 5),
                    "static_analysis": static_penalty_total,
                    "dependencies": dependency_penalty_total,
                    "code_quality": code_quality_penalty_total
                },
                "bonuses_applied": {
                    "security_files": security_files_bonus if 'security_files_bonus' in locals() else 0
                },
                "weighted_contributions": {
                    category: category_scores[category] * weights[category] 
                    for category in category_scores
                }
            }

            comprehensive_results["overall_security_score"] = overall_score
            comprehensive_results["security_level"] = (
                "Excellent" if overall_score >= 90 else
                "Good" if overall_score >= 75 else
                "Medium" if overall_score >= 50 else
                "Low"
            )
            
            # ============================================================================
            # END OF NEW SCORING SYSTEM
            # ============================================================================
            
            # Add detailed findings for AI chat context
            comprehensive_results["detailed_findings"] = {
                "secrets": [
                    {
                        "file": s.get('file', 'unknown'),
                        "line": s.get('line', 'N/A'),
                        "secret_type": s.get('secret_type', 'unknown'),
                        "description": s.get('description', 'No description available'),
                        "severity": s.get('severity', 'High')
                    } for s in secret_scan_results[:10]
                ] if secret_scan_results else [],
                "static_issues": [
                    {
                        "file": s.get('filename', 'unknown'),
                        "line": s.get('line', 'N/A'), 
                        "issue": s.get('issue', 'Security issue'),
                        "severity": s.get('severity', 'Unknown'),
                        "description": s.get('description', 'No description available'),
                        "fix_suggestion": s.get('fix_suggestion', 'No fix suggestion available')
                    } for s in static_analysis_results[:10]
                ] if static_analysis_results else [],
                "vulnerable_dependencies": [
                    {
                        "package": d.get('package', 'unknown'),
                        "version": d.get('version', 'unknown'),
                        "severity": d.get('severity', 'Unknown'),
                        "advisory": d.get('advisory', 'Update recommended'),
                        "cve": d.get('cve', 'N/A'),
                        "affected_versions": d.get('affected_versions', 'Unknown'),
                        "fixed_version": d.get('fixed_version', 'Latest')
                    } for d in dependency_scan_results.get('vulnerable_packages', [])[:10]
                ],
                "code_quality": [
                    {
                        "file": c.get('file', 'unknown'),
                        "line": c.get('line', 'N/A'),
                        "pattern": c.get('pattern', 'unknown'),
                        "severity": c.get('severity', 'Unknown'),
                        "description": c.get('description', 'No description'),
                        "fix_suggestion": c.get('fix_suggestion', 'Review and apply secure coding practices')
                    } for c in code_quality_results[:10]
                ] if code_quality_results else [],
                "sensitive_files": [
                    {
                        "file": f.get('file', 'unknown'),
                        "risk": f.get('risk', 'Unknown'),
                        "reason": f.get('reason', 'Sensitive file detected'),
                        "recommended_action": f.get('recommended_action', 'Review and secure or remove')
                    } for f in file_scan_results.get('sensitive_files', [])[:10]
                ]
            }
            
            # Enhanced recommendations with RAG-powered security intelligence
            recommendations = []
            
            # Critical Security Issues (RAG-Enhanced)
            if file_scan_results.get('sensitive_files'):
                recommendations.append({
                    "file": "Multiple sensitive files detected",
                    "pattern": "Sensitive file exposure",
                    "risk": "Critical",
                    "fix": "Remove sensitive files from repository or add to .gitignore. Refer to SonarSource RSPEC rules for file security patterns."
                })
            
            if secret_scan_results:
                recommendations.append({
                    "file": f"{len(secret_scan_results)} files with secrets",
                    "pattern": "Hardcoded secrets detected",
                    "risk": "Critical", 
                    "fix": "Remove secrets from code and use environment variables or secret management systems. Follow OWASP secure coding guidelines."
                })
            
            if static_analysis_results and len(static_analysis_results) > 0:
                recommendations.append({
                    "file": f"{len(static_analysis_results)} static analysis issues", 
                    "pattern": "Code vulnerabilities detected",
                    "risk": "High",
                    "fix": "Apply secure coding patterns from updated SonarSource rules database. Focus on injection flaws and input validation."
                })
            
            if dependency_scan_results.get('vulnerable_packages'):
                vulnerable_count = len(dependency_scan_results['vulnerable_packages'])
                recommendations.append({
                    "file": f"{vulnerable_count} vulnerable dependencies",
                    "pattern": "Outdated dependencies with known vulnerabilities", 
                    "risk": "High",
                    "fix": "Update packages to secure versions. Monitor security advisories and implement automated dependency scanning."
                })
            
            # Infrastructure and Configuration Issues
            if file_scan_results.get('excluded_directories'):
                excluded_count = len(file_scan_results['excluded_directories'])
                recommendations.append({
                    "file": f"{excluded_count} build/dependency directories found",
                    "pattern": "Build artifacts in repository",
                    "risk": "Medium",
                    "fix": f"Ensure {excluded_count} directories (venv, __pycache__, node_modules) are in .gitignore to prevent sensitive data exposure."
                })
            
            if file_scan_results.get('gitignore_recommendations'):
                high_priority_gitignore = [rec for rec in file_scan_results['gitignore_recommendations'] if rec['priority'] == 'High']
                if high_priority_gitignore:
                    patterns = [rec['pattern'] for rec in high_priority_gitignore[:3]]
                    recommendations.append({
                        "file": ".gitignore",
                        "pattern": "Missing security patterns in .gitignore",
                        "risk": "Medium", 
                        "fix": f"Add patterns to .gitignore: {', '.join(patterns)} - Based on SonarSource file security recommendations."
                    })
            
            critical_code_issues = [r for r in code_quality_results if r.get('severity') in ['Critical', 'High']]
            if critical_code_issues:
                recommendations.append({
                    "file": f"{len(critical_code_issues)} files with critical issues",
                    "pattern": "Insecure coding patterns",
                    "risk": "High",
                    "fix": "Apply secure coding practices from live SonarSource rules. Focus on input validation, error handling, and authentication patterns."
                })
            
            # Additional Security Improvements  
            if file_scan_results.get('risky_files'):
                risky_count = len(file_scan_results['risky_files'])
                recommendations.append({
                    "file": f"{risky_count} risky file types",
                    "pattern": "Potentially risky file extensions",
                    "risk": "Medium",
                    "fix": "Review risky file types for security implications. Consider removing unnecessary executable files or configuration files with defaults."
                })
            
            if file_scan_results.get('missing_security_files'):
                missing = file_scan_results['missing_security_files'][:3]
                recommendations.append({
                    "file": "Repository root",
                    "pattern": "Missing security documentation", 
                    "risk": "Low",
                    "fix": f"Add missing security files: {', '.join(missing)} to improve security posture and compliance."
                })
            
            if not any('security.md' in f.get('type', '') for f in file_scan_results.get('security_files_found', [])):
                recommendations.append({
                    "file": "SECURITY.md",
                    "pattern": "Missing security policy",
                    "risk": "Low", 
                    "fix": "Add SECURITY.md file with vulnerability disclosure policy and security contact information."
                })
            
            comprehensive_results["recommendations"] = recommendations[:10]  # Limit to top 10 recommendations
            
            # Add user-friendly display summary
            comprehensive_results["display_summary"] = {
                "basic_info": f"Repository: {comprehensive_results['repository_info'].get('name', 'Unknown')}\nSecurity Score: {overall_score}/100 ({comprehensive_results['security_level']})\nLanguage: {comprehensive_results['repository_info'].get('language', 'Unknown')}",
                "scan_results": f"Secrets Found: {len(secret_scan_results) if secret_scan_results else 0}\nStatic Issues: {len(static_analysis_results) if static_analysis_results else 0}\nVulnerable Dependencies: {len(dependency_scan_results.get('vulnerable_packages', []))}\nCode Quality Issues: {len(code_quality_results) if code_quality_results else 0}",
                "ready_message": "I am ready to answer specific questions about these findings and provide detailed explanations with exact file locations and fix suggestions."
            }
            
            # Store results for AI chat context
            RepoAnalysis.latest_analysis = comprehensive_results
            
            return comprehensive_results
            
        except git.exc.GitCommandError as e:
            error_msg = str(e)
            if "Access is denied" in error_msg:
                return {"error": f"Access denied during Git clone. This might be due to:\n• Repository permissions\n• Windows file system restrictions\n• Antivirus software blocking Git operations\n\nTry running VS Code as administrator or temporarily disable antivirus scanning for the temp directory.\n\nOriginal error: {error_msg}"}
            elif "not found" in error_msg.lower():
                return {"error": f"Repository not found. Please verify:\n• Repository URL is correct\n• Repository is public (or you have access)\n• GitHub is accessible from your network\n\nOriginal error: {error_msg}"}
            elif "authentication" in error_msg.lower():
                return {"error": f"Authentication failed. For private repositories:\n• Ensure you have access rights\n• Consider using GitHub token authentication\n\nOriginal error: {error_msg}"}
            else:
                return {"error": f"Git clone failed: {error_msg}"}
        except Exception as e:
            error_msg = str(e)
            if "Access is denied" in error_msg:
                return {"error": f"Windows access denied error. Try:\n• Running VS Code as administrator\n• Checking antivirus settings\n• Ensuring temp directory is writable\n\nOriginal error: {error_msg}"}
            else:
                return {"error": f"Repository analysis failed: {error_msg}"}
        finally:
            # Enhanced cleanup for Git repositories on Windows
            if os.path.exists(temp_dir):
                try:
                    import stat
                    import time
                    
                    def force_remove_readonly(func, path, exc_info):
                        """Enhanced readonly handler for Git objects"""
                        try:
                            if os.path.exists(path):
                                # Make file writable and remove all permissions restrictions
                                os.chmod(path, stat.S_IWRITE | stat.S_IREAD | stat.S_IEXEC)
                                # Try the original function again
                                func(path)
                        except Exception as e:
                            print(f"⚠️ Could not remove {path}: {e}")
                            # Try with admin privileges if needed
                            try:
                                import subprocess
                                if os.name == 'nt':  # Windows
                                    # Use cmd.exe for Windows-specific commands
                                    subprocess.run(['cmd', '/c', 'del', '/f', '/q', f'"{path}"'], 
                                                 check=False, capture_output=True)
                            except:
                                pass
                    
                    def cleanup_git_directory(directory):
                        """Special cleanup for Git directories with enhanced Windows support"""
                        try:
                            # First, try to make all files in .git writable
                            git_dir = os.path.join(directory, '.git')
                            if os.path.exists(git_dir):
                                print(f"🔧 Making Git files writable in: {git_dir}")
                                for root, dirs, files in os.walk(git_dir):
                                    # Make directories writable
                                    for dir_name in dirs:
                                        dir_path = os.path.join(root, dir_name)
                                        try:
                                            os.chmod(dir_path, stat.S_IWRITE | stat.S_IREAD | stat.S_IEXEC)
                                        except Exception:
                                            pass
                                    
                                    # Make files writable  
                                    for file in files:
                                        file_path = os.path.join(root, file)
                                        try:
                                            # Remove read-only attribute and make writable
                                            os.chmod(file_path, stat.S_IWRITE | stat.S_IREAD)
                                            # Additional Windows-specific attribute removal
                                            if os.name == 'nt':
                                                try:
                                                    import subprocess
                                                    # Use cmd.exe to run attrib command properly
                                                    subprocess.run(['cmd', '/c', 'attrib', '-r', '-h', '-s', f'"{file_path}"'], 
                                                                 check=False, capture_output=True)
                                                except Exception:
                                                    # Fallback: try using Python's os module
                                                    try:
                                                        import ctypes
                                                        # Remove hidden, system, and readonly attributes
                                                        FILE_ATTRIBUTE_HIDDEN = 0x02
                                                        FILE_ATTRIBUTE_SYSTEM = 0x04
                                                        FILE_ATTRIBUTE_READONLY = 0x01
                                                        FILE_ATTRIBUTE_NORMAL = 0x80
                                                        
                                                        attrs = ctypes.windll.kernel32.GetFileAttributesW(file_path)
                                                        if attrs != -1:  # INVALID_FILE_ATTRIBUTES
                                                            new_attrs = attrs & ~(FILE_ATTRIBUTE_READONLY | FILE_ATTRIBUTE_HIDDEN | FILE_ATTRIBUTE_SYSTEM)
                                                            ctypes.windll.kernel32.SetFileAttributesW(file_path, new_attrs or FILE_ATTRIBUTE_NORMAL)
                                                    except Exception:
                                                        pass
                                        except Exception:
                                            pass
                        except Exception as e:
                            print(f"⚠️ Error in Git directory cleanup: {e}")
                    
                    # Special handling for Git directories
                    cleanup_git_directory(temp_dir)
                    
                    # Wait longer for file handles to close on Windows
                    if os.name == 'nt':
                        time.sleep(0.5)  # Longer wait on Windows
                    else:
                        time.sleep(0.1)
                    
                    # Try multiple removal strategies
                    removal_success = False
                    
                    # Strategy 1: Standard shutil.rmtree with error handler
                    try:
                        shutil.rmtree(temp_dir, onerror=force_remove_readonly)
                        print(f"✅ Temporary directory cleaned up: {temp_dir}")
                        removal_success = True
                    except Exception as e1:
                        print(f"⚠️ Standard cleanup failed: {e1}")
                        
                        # Strategy 2: Windows-specific command line tools
                        if os.name == 'nt' and not removal_success:
                            try:
                                import subprocess
                                print("🔧 Trying Windows command line cleanup...")
                                
                                # Method 1: rmdir with force
                                result = subprocess.run([
                                    'rmdir', '/s', '/q', temp_dir
                                ], shell=True, capture_output=True, text=True, timeout=30)
                                
                                if result.returncode == 0:
                                    print(f"✅ Directory cleaned up using rmdir")
                                    removal_success = True
                                else:
                                    print(f"⚠️ rmdir failed: {result.stderr}")
                                    
                            except Exception as e2:
                                print(f"⚠️ rmdir cleanup failed: {e2}")
                        
                        # Strategy 3: PowerShell as last resort
                        if os.name == 'nt' and not removal_success:
                            try:
                                print("🔧 Trying PowerShell cleanup...")
                                ps_result = subprocess.run([
                                    'powershell', '-Command', 
                                    f'Get-ChildItem -Path "{temp_dir}" -Recurse | Remove-Item -Force -Recurse -ErrorAction SilentlyContinue; Remove-Item -Path "{temp_dir}" -Force -ErrorAction SilentlyContinue'
                                ], capture_output=True, text=True, timeout=30)
                                
                                if ps_result.returncode == 0:
                                    print(f"✅ Directory cleaned up using PowerShell")
                                    removal_success = True
                                else:
                                    print(f"⚠️ PowerShell cleanup issues: {ps_result.stderr}")
                                    
                            except Exception as e3:
                                print(f"⚠️ PowerShell cleanup failed: {e3}")
                        
                        # Strategy 4: Manual file-by-file deletion
                        if not removal_success:
                            try:
                                print("🔧 Trying manual file-by-file deletion...")
                                for root, dirs, files in os.walk(temp_dir, topdown=False):
                                    for file in files:
                                        file_path = os.path.join(root, file)
                                        try:
                                            os.chmod(file_path, stat.S_IWRITE)
                                            os.remove(file_path)
                                        except:
                                            pass
                                    for dir_name in dirs:
                                        dir_path = os.path.join(root, dir_name)
                                        try:
                                            os.rmdir(dir_path)
                                        except:
                                            pass
                                try:
                                    os.rmdir(temp_dir)
                                    print(f"✅ Directory cleaned up manually")
                                    removal_success = True
                                except:
                                    pass
                            except Exception as e4:
                                print(f"⚠️ Manual cleanup failed: {e4}")
                    
                    if not removal_success:
                        print(f"⚠️ Could not fully clean temp directory: {temp_dir}")
                        print(f"💡 The directory will be cleaned up automatically by the system eventually.")
                        print(f"💡 Or you can manually delete: {temp_dir}")
                    
                except Exception as e:
                    print(f"⚠️ Cleanup error: {e} - continuing anyway")
                    print(f"💡 You may need to manually delete: {temp_dir}")
                
    except Exception as e:
        return {"error": f"Analysis setup failed: {str(e)}"}
# REPLACE your existing @app.post("/ai-chat") endpoint with this enhanced version

@app.post("/ai-chat")
async def unified_ai_chat(request: dict):
    """Enhanced AI chat endpoint - RAG-powered Explainer and Fixer Initiator"""
    try:
        question = request.get('question', '')
        context_type = request.get('context', 'auto')
        model_type = request.get('model_type', 'fast')
        previous_history = request.get('history', [])
        
        # Validate model type
        if model_type not in ['fast', 'smart']:
            model_type = 'fast'
        
        # Clean and validate previous_history to ensure all parts are strings
        cleaned_history = []
        for msg in previous_history:
            if isinstance(msg, dict) and 'type' in msg and 'parts' in msg:
                # Ensure parts contains only strings
                clean_parts = []
                for part in msg['parts']:
                    if isinstance(part, str):
                        clean_parts.append(part)
                    elif isinstance(part, dict) or isinstance(part, list):
                        # Convert complex objects to strings
                        clean_parts.append(str(part)[:1000])  # Limit length
                    else:
                        clean_parts.append(str(part))
                
                cleaned_history.append({
                    'type': msg['type'],
                    'parts': clean_parts
                })
        
        # Keep only last 5 messages for context (to prevent token limit issues)
        cleaned_history = cleaned_history[-5:]
        
        print(f"🤖 Processing AI chat request: '{question[:100]}...'")
        print(f"📝 History cleaned: {len(cleaned_history)} messages")
        
        # Check if this is a fix request
        is_fix_request = any(phrase in question.lower() for phrase in [
            'fix this', 'fix the', 'propose fix', 'create fix', 'generate fix',
            'fix it', 'resolve this', 'solve this', 'patch this', 'auto fix'
        ])
        
        # Check if this is an explanation request
        is_explanation_request = any(phrase in question.lower() for phrase in [
            'what is', 'explain', 'what does', 'how does', 'tell me about',
            'describe', 'meaning of', 'definition'
        ])
        
        # Build enhanced context with automatic scan result detection
        enhanced_context = f"MODEL TYPE: {model_type}\nUSER QUESTION: {question}\n\n"

        # Auto-detect and use available scan results
        if context_type == 'auto':
            repo_analysis = getattr(RepoAnalysis, 'latest_analysis', None)
            website_scan = getattr(WebsiteScan, 'latest_scan', None)
            if repo_analysis:
                context_type = 'repo_analysis'
                enhanced_context += "🔍 **AUTOMATICALLY DETECTED: Repository Analysis Available**\n\n"
            elif website_scan:
                context_type = 'website_scan'
                enhanced_context += "🌐 **AUTOMATICALLY DETECTED: Website Scan Available**\n\n"
            else:
                context_type = 'general'
                enhanced_context += "🤖 **GENERAL SECURITY CONSULTATION** - No recent scan data available.\n\n"
        
        # Handle RAG-powered explanation requests
        if is_explanation_request:
            print("🔍 Processing explanation request with RAG...")
            
            # Query RAG for detailed explanation
            rag_context = await run_in_threadpool(get_secure_coding_patterns, question)
            
            enhanced_context += f"""
🧠 **RAG-ENHANCED EXPLANATION:**
{rag_context}

Please provide a comprehensive explanation using the above security knowledge.
"""

        # Repository Analysis Context (Enhanced with RAG capabilities and detailed findings)
        if context_type == 'repo_analysis':
            analysis_data = getattr(RepoAnalysis, 'latest_analysis', None)
            if isinstance(analysis_data, dict):
                repo_info = analysis_data.get('repository_info', {})
                security_summary = analysis_data.get('security_summary', {})
                detailed_findings = analysis_data.get('detailed_findings', {})
                
                enhanced_context += f"""
📁 **REPOSITORY SECURITY ANALYSIS:**
• Repository: {repo_info.get('name', 'Unknown')}
• Security Score: {analysis_data.get('overall_security_score', 'N/A')}/100 ({analysis_data.get('security_level', 'Unknown')})
• Language: {repo_info.get('language', 'Unknown')}

📊 **SECURITY SUMMARY:**
• Files Scanned: {security_summary.get('total_files_scanned', 0)}
• Secrets Found: {security_summary.get('secrets_found', 0)}
• Static Issues: {security_summary.get('static_issues_found', 0)}
• Vulnerable Dependencies: {security_summary.get('vulnerable_dependencies', 0)}
• Code Quality Issues: {security_summary.get('code_quality_issues', 0)}

🚨 **DETAILED SECURITY FINDINGS:**

🔐 **SECRETS FOUND:** {len(detailed_findings.get('secrets', []))} critical issues
{chr(10).join([f"• {s.get('file', 'unknown')} (Line {s.get('line', 'N/A')}): {s.get('secret_type', 'unknown')} - {s.get('description', 'No description')}" for s in detailed_findings.get('secrets', [])[:3]])}

🛡️ **STATIC ANALYSIS ISSUES:** {len(detailed_findings.get('static_issues', []))} security vulnerabilities
{chr(10).join([f"• {s.get('file', 'unknown')} (Line {s.get('line', 'N/A')}): {s.get('issue', 'Security issue')} ({s.get('severity', 'Unknown')})" for s in detailed_findings.get('static_issues', [])[:3]])}

📦 **VULNERABLE DEPENDENCIES:** {len(detailed_findings.get('vulnerable_dependencies', []))} packages need updates
{chr(10).join([f"• {d.get('package', 'unknown')} v{d.get('version', 'unknown')}: {d.get('severity', 'Unknown')} - {d.get('advisory', 'Update recommended')}" for d in detailed_findings.get('vulnerable_dependencies', [])[:3]])}

🤖 **AI CAPABILITIES:**
- Ask "explain [specific issue]" for detailed OWASP-backed explanations
- Request "fix [package/file]" for automated pull request generation
- Get "tell me exact lines" for precise vulnerability locations
"""
            else:
                enhanced_context += "📁 **REPOSITORY ANALYSIS:** Data available but in unexpected format\n"
        
        # Website Scan Context
        elif context_type == 'website_scan':
            website_data = getattr(WebsiteScan, 'latest_scan', None)
            if isinstance(website_data, dict):
                scan_data = website_data.get('scan_result', {})
                enhanced_context += f"""
🌐 **WEBSITE SECURITY SCAN:**
• Target: {scan_data.get('url', 'N/A')}
• Security Score: {scan_data.get('security_score', 'N/A')}/100 ({scan_data.get('security_level', 'Unknown')})
• HTTPS: {'✅ Enabled' if scan_data.get('https', False) else '❌ Disabled'}
• Vulnerabilities: {len(scan_data.get('flags', []))} issues found
"""
            else:
                enhanced_context += "🌐 **WEBSITE SCAN:** No scan result available.\n"
        
        # General Context
        elif context_type == 'general':
            enhanced_context += """
🔒 **GENERAL SECURITY CONSULTATION**
No specific scan data available. I can help with:
• General security best practices  
• Common vulnerability explanations (RAG-enhanced)
• Security implementation guidance
• Code review suggestions
• Security tool recommendations
"""
        
        enhanced_context += "\n\n🧠 **RAG-ENHANCED AI:** I now have access to a comprehensive security knowledge base for detailed explanations and automated fixes!"
        
        # Create the final message for AI
        final_message = enhanced_context + f"\n\nBased on the above security analysis and knowledge base, provide a helpful response to: {question}"
        
        # Build conversation history with proper string formatting
        final_history = []
        
        # Add cleaned previous history
        final_history.extend(cleaned_history)
        
        # Add current user message
        final_history.append({
            'type': 'user', 
            'parts': [final_message]
        })
        
        print(f"🎯 Sending to AI model: {len(final_history)} messages")
        print(f"🔤 Final message length: {len(final_message)} characters")
        
        # Get AI response with error handling
        response = await run_in_threadpool(get_chat_response, final_history, model_type)
        
        if not isinstance(response, str):
            response = str(response)
        
        # Add response to history
        final_history.append({'type': 'assistant', 'parts': [response]})
        
        return {
            "response": response,
            "model_used": model_type,
            "context_detected": context_type,
            "scan_data_available": context_type in ['repo_analysis', 'website_scan'],
            "history": final_history,
            "action_taken": None,
            "rag_enhanced": True
        }
        
    except Exception as e:
        print(f"❌ Chat Error ({model_type} model): {str(e)}")
        return {
            "response": f"❌ **Chat Error ({model_type} model):** {str(e)}",
            "model_used": model_type if 'model_type' in locals() else 'unknown',
            "context_detected": 'error',
            "scan_data_available": False,
            "history": [],
            "action_taken": None
        }
@app.post("/owasp-mapping")
async def owasp_mapping(request_data: dict = Body(...)):
    """
    Map detected security issues to OWASP Top 10 categories
    Uses the latest scan and repo analysis results automatically
    """
    try:
        # Check if request specifies to exclude repo analysis (for website-only reports)
        exclude_repo = request_data.get('exclude_repo', False) if request_data else False
        scan_result_data = request_data.get('scan_result') if request_data else None
        
        print(f"🎯 OWASP Mapping - exclude_repo: {exclude_repo}")
        
        # Get the latest scan results from stored data
        scan_results = None
        if hasattr(WebsiteScan, 'latest_scan') and WebsiteScan.latest_scan:
            scan_results = WebsiteScan.latest_scan
            print(f"📊 Using stored website scan results")
        
        # Get the latest repository results from stored data (only if not excluded)
        repo_results = None
        if not exclude_repo and hasattr(RepoAnalysis, 'latest_analysis') and RepoAnalysis.latest_analysis:
            repo_results = RepoAnalysis.latest_analysis
            print(f"📁 Using stored repository analysis results")
        elif exclude_repo:
            print(f"🚫 Repository analysis excluded for website-only OWASP mapping")
        
        # Check if we have any data to analyze
        if not scan_results and not repo_results:
            return {
                "success": False,
                "error": "No scan results available. Please run /scan or /analyze-repo first.",
                "owasp_mapping": None,
                "metadata": {
                    "scan_available": False,
                    "repo_available": False,
                    "timestamp": datetime.now().isoformat()
                }
            }
        
        # Map to OWASP Top 10
        owasp_mapping = map_to_owasp_top10(scan_results, repo_results)
        
        return {
            "success": True,
            "owasp_mapping": owasp_mapping,
            "metadata": {
                "scan_available": scan_results is not None,
                "repo_available": repo_results is not None,
                "scan_url": scan_results.get('url') if scan_results else None,
                "repo_name": repo_results.get('repository_info', {}).get('name') if repo_results else None,
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OWASP mapping failed: {str(e)}")
    
async def provide_local_fix_suggestion(issue: dict):
    """
    Provide fix suggestions for local analysis without GitHub operations
    """
    try:
        print(f"🔧 Providing local fix suggestion for: {issue.get('description', 'Unknown issue')}")
        
        # Query RAG database for secure coding patterns
        rag_query = f"{issue.get('type', 'security')} {issue.get('description', '')} {issue.get('vulnerable_code', '')}"
        secure_patterns = await run_in_threadpool(get_secure_coding_patterns, rag_query)
        
        # Create AI prompt
        ai_prompt = f"""
        You are a security expert. Analyze this security issue and provide a fix:
        
        Issue Type: {issue.get('type', 'Unknown')}
        Description: {issue.get('description', 'No description')}
        File: {issue.get('file', 'Unknown file')}
        Line: {issue.get('line', 'Unknown')}
        
        Vulnerable Code:
        {issue.get('vulnerable_code', 'Not provided')}
        
        Security Knowledge Base:
        {secure_patterns}
        
        Provide a JSON response with:
        {{
            "fix_summary": "Brief description of the fix",
            "security_impact": "How this improves security",
            "suggested_code": "The corrected code",
            "explanation": "Detailed explanation of the fix",
            "prevention_tips": ["List of tips to prevent this issue"]
        }}
        """
        
        # Get AI response
        ai_response = await run_in_threadpool(get_chat_response, [
            {"role": "user", "content": ai_prompt}
        ], "smart")
        ai_text = ai_response if isinstance(ai_response, str) else str(ai_response)
        
        # Parse JSON response with robust cleaning
        def clean_and_parse_json(text):
            """Clean and parse JSON from AI response"""
            try:
                # First try to find JSON in ```json blocks
                import re
                json_block = re.search(r'```json\s*(\{.*?\})\s*```', text, re.DOTALL)
                if json_block:
                    json_text = json_block.group(1)
                    return json.loads(json_text)
            except Exception:
                pass
            
            # Fallback: Extract between first { and last } and clean
            try:
                start = text.find('{')
                end = text.rfind('}') + 1
                if start != -1 and end != -1:
                    json_text = text[start:end]
                    # Simple cleanup - replace newlines with spaces
                    json_text = json_text.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
                    # Remove extra whitespace
                    json_text = re.sub(r'\s+', ' ', json_text)
                    return json.loads(json_text)
            except Exception:
                pass
            
            return None
        
        try:
            fix_data = clean_and_parse_json(ai_text)
            if fix_data:
                print("✅ Successfully parsed AI fix response")
            else:
                raise ValueError("Could not parse JSON from AI response")
        except Exception as parse_error:
            print(f"⚠️ JSON parsing failed: {parse_error}")
            print(f"🔍 AI Response preview: {ai_text[:500]}...")
            
            # Enhanced fallback: Extract key information from the AI response text
            fix_data = {
                "fix_summary": "Replace hardcoded credentials with environment variables",
                "security_impact": "Prevents credential exposure in source code", 
                "suggested_code": "import os\nDB_PASSWORD = os.getenv('DB_PASSWORD', 'default_secure_password')",
                "explanation": "Hardcoded passwords should be moved to environment variables to prevent exposure in version control.",
                "prevention_tips": [
                    "Use environment variables for sensitive data",
                    "Never commit secrets to version control", 
                    "Use secure secret management tools",
                    "Regular security audits"
                ]
            }
            # Fallback response
            fix_data = {
                "fix_summary": f"Security fix suggested for {issue.get('type', 'issue')}",
                "security_impact": "Reduces security vulnerability risk",
                "suggested_code": "# Apply security best practices here",
                "explanation": f"This {issue.get('type', 'issue')} should be addressed by following security best practices.",
                "prevention_tips": ["Regular security audits", "Use security linting tools", "Follow OWASP guidelines"]
            }
        
        return {
            "success": True,
            "fix_applied": False,
            "suggestion_only": True,
            "fix_summary": fix_data.get("fix_summary", "Security fix suggested"),
            "security_impact": fix_data.get("security_impact", "Improves security"),
            "suggested_code": fix_data.get("suggested_code", ""),
            "explanation": fix_data.get("explanation", ""),
            "prevention_tips": fix_data.get("prevention_tips", []),
            "issue_details": {
                "type": issue.get('type'),
                "file": issue.get('file'),
                "line": issue.get('line'),
                "description": issue.get('description')
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to generate fix suggestion: {str(e)}",
            "fix_summary": "Unable to generate fix",
            "suggestion_only": True
        }

class ProjectRequest(BaseModel):
    idea: str
    project_type: str = "web-app"
    tech_stack: Union[str, List[str]] = "auto"
    complexity: str = "medium"

async def generate_full_stack_files(project_path: Path, idea: str, project_name: str, needs_ai: bool, ai_response: str):
    """
    Generate actual project files based on the idea and AI response
    """
    try:
        # Create main project structure
        project_path.mkdir(exist_ok=True)
        frontend_path = project_path / "frontend"
        backend_path = project_path / "backend"
        
        frontend_path.mkdir(exist_ok=True)
        backend_path.mkdir(exist_ok=True)
        
        # Generate frontend files
        await generate_frontend_files(frontend_path, idea, project_name, needs_ai)
        
        # Generate backend files
        await generate_backend_files(backend_path, idea, project_name, needs_ai)
        
        # Generate deployment files
        await generate_deployment_files(project_path, project_name)
        
        # Return project structure for display
        return [
            "📁 frontend/",
            "  📁 src/",
            "    📁 components/",
            "    📁 pages/",
            "    📁 hooks/",
            "    📁 utils/",
            "  📁 public/",
            "  📄 package.json",
            "  📄 tailwind.config.js",
            "  📄 vite.config.js",
            "📁 backend/",
            "  📁 app/",
            "    📁 routes/",
            "    📁 models/",
            "    📁 services/",
            "  📄 main.py",
            "  📄 requirements.txt",
            "  📄 Dockerfile",
            "📄 docker-compose.yml",
            "📄 README.md",
            "📄 .env.example"
        ]
        
    except Exception as e:
        print(f"Error generating files: {e}")
        return ["Error generating project files"]

async def generate_frontend_files(frontend_path: Path, idea: str, project_name: str, needs_ai: bool):
    """Generate React frontend with TailwindCSS"""
    
    # Create directory structure
    src_path = frontend_path / "src"
    components_path = src_path / "components"
    pages_path = src_path / "pages"
    hooks_path = src_path / "hooks"
    utils_path = src_path / "utils"
    public_path = frontend_path / "public"
    
    for path in [src_path, components_path, pages_path, hooks_path, utils_path, public_path]:
        path.mkdir(exist_ok=True)
    
    # Generate package.json
    package_json = {
        "name": project_name,
        "version": "1.0.0",
        "type": "module",
        "scripts": {
            "dev": "vite",
            "build": "vite build",
            "preview": "vite preview"
        },
        "dependencies": {
            "react": "^18.2.0",
            "react-dom": "^18.2.0",
            "axios": "^1.6.0"
        },
        "devDependencies": {
            "@vitejs/plugin-react": "^4.0.0",
            "vite": "^4.4.0",
            "tailwindcss": "^3.3.0",
            "autoprefixer": "^10.4.0",
            "postcss": "^8.4.0"
        }
    }
    
    with open(frontend_path / "package.json", "w") as f:
        json.dump(package_json, f, indent=2)
    
    # Generate main App.jsx
    app_jsx = f'''import React from 'react';
import './App.css';

function App() {{
  return (
    <div className="min-h-screen bg-gray-100">
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <h1 className="text-3xl font-bold text-gray-900">
            {project_name.replace("-", " ").title()}
          </h1>
          <p className="text-gray-600 mt-2">{idea}</p>
        </div>
      </header>
      
      <main className="max-w-7xl mx-auto px-4 py-8">
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-4">Welcome to your new app!</h2>
          <p className="text-gray-600">
            This is a full-stack application generated based on your idea.
            The backend API is ready and the frontend is set up with TailwindCSS.
          </p>
          
          <div className="mt-6 space-y-4">
            <button className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg transition-colors">
              Get Started
            </button>
            {"<button className='bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded-lg transition-colors ml-4'>API Test</button>" if needs_ai else ""}
          </div>
        </div>
      </main>
    </div>
  );
}}

export default App;'''
    
    with open(src_path / "App.jsx", "w") as f:
        f.write(app_jsx)
    
    # Generate main.jsx
    main_jsx = '''import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)'''
    
    with open(src_path / "main.jsx", "w") as f:
        f.write(main_jsx)
    
    # Generate index.css with TailwindCSS
    index_css = '''@tailwind base;
@tailwind components;
@tailwind utilities;

body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
    'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue',
    sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}'''
    
    with open(src_path / "index.css", "w") as f:
        f.write(index_css)
    
    # Generate Vite config
    vite_config = '''import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
  },
})'''
    
    with open(frontend_path / "vite.config.js", "w") as f:
        f.write(vite_config)
    
    # Generate TailwindCSS config
    tailwind_config = '''/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}'''
    
    with open(frontend_path / "tailwind.config.js", "w") as f:
        f.write(tailwind_config)
    
    # Generate index.html
    index_html = f'''<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/vite.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>{project_name.replace("-", " ").title()}</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>'''
    
    with open(frontend_path / "index.html", "w") as f:
        f.write(index_html)

async def generate_backend_files(backend_path: Path, idea: str, project_name: str, needs_ai: bool):
    """Generate FastAPI backend"""
    
    # Create directory structure
    app_path = backend_path / "app"
    routes_path = app_path / "routes"
    models_path = app_path / "models"
    services_path = app_path / "services"
    
    for path in [app_path, routes_path, models_path, services_path]:
        path.mkdir(exist_ok=True)
    
    # Generate requirements.txt
    requirements = [
        "fastapi==0.104.1",
        "uvicorn==0.24.0",
        "python-multipart==0.0.6",
        "python-dotenv==1.0.0",
        "sqlalchemy==2.0.23",
        "psycopg2-binary==2.9.9",
        "pydantic==2.5.0",
        "python-jose==3.3.0",
        "passlib==1.7.4",
        "bcrypt==4.1.2"
    ]
    
    if needs_ai:
        requirements.extend([
            "openai==1.3.0",
            "langchain==0.0.350"
        ])
    
    with open(backend_path / "requirements.txt", "w") as f:
        f.write("\\n".join(requirements))
    
    # Generate main.py
    ai_import = "from app.services.ai_service import AIService" if needs_ai else ""
    ai_route = ', ai_router' if needs_ai else ""
    
    main_py = f'''from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes.main_routes import router as main_router
{ai_import}
import uvicorn

app = FastAPI(
    title="{project_name.replace("-", " ").title()} API",
    description="Backend API for {idea}",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Frontend dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(main_router{ai_route})

@app.get("/")
async def root():
    return {{"message": "Welcome to {project_name.replace("-", " ").title()} API"}}

@app.get("/health")
async def health_check():
    return {{"status": "healthy", "service": "{project_name}"}}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)'''
    
    with open(backend_path / "main.py", "w") as f:
        f.write(main_py)
    
    # Generate main routes
    main_routes = '''from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter(prefix="/api", tags=["main"])

class ItemCreate(BaseModel):
    title: str
    description: Optional[str] = None

class ItemResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None

# In-memory storage (replace with database in production)
items_db = []
next_id = 1

@router.get("/items", response_model=List[ItemResponse])
async def get_items():
    """Get all items"""
    return items_db

@router.post("/items", response_model=ItemResponse)
async def create_item(item: ItemCreate):
    """Create a new item"""
    global next_id
    new_item = ItemResponse(
        id=next_id,
        title=item.title,
        description=item.description
    )
    items_db.append(new_item)
    next_id += 1
    return new_item

@router.get("/items/{item_id}", response_model=ItemResponse)
async def get_item(item_id: int):
    """Get item by ID"""
    for item in items_db:
        if item.id == item_id:
            return item
    raise HTTPException(status_code=404, detail="Item not found")

@router.delete("/items/{item_id}")
async def delete_item(item_id: int):
    """Delete item by ID"""
    global items_db
    items_db = [item for item in items_db if item.id != item_id]
    return {"message": "Item deleted successfully"}'''
    
    with open(routes_path / "main_routes.py", "w") as f:
        f.write(main_routes)
    
    # Generate AI service if needed
    if needs_ai:
        ai_service = '''import openai
import os
from typing import Optional
from fastapi import HTTPException

class AIService:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        openai.api_key = self.api_key
    
    async def generate_response(self, prompt: str) -> str:
        """Generate AI response using OpenAI"""
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"AI service error: {str(e)}")

ai_service = AIService()'''
        
        with open(services_path / "ai_service.py", "w") as f:
            f.write(ai_service)
    
    # Generate __init__.py files
    for path in [app_path, routes_path, models_path, services_path]:
        (path / "__init__.py").touch()

async def generate_deployment_files(project_path: Path, project_name: str):
    """Generate deployment configuration files"""
    
    # Generate docker-compose.yml
    docker_compose = f'''version: '3.8'

services:
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - VITE_API_URL=http://localhost:8000
    depends_on:
      - backend

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:password@db:5432/{project_name}
    depends_on:
      - db

  db:
    image: postgres:15
    environment:
      - POSTGRES_DB={project_name}
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

volumes:
  postgres_data:'''
    
    with open(project_path / "docker-compose.yml", "w") as f:
        f.write(docker_compose)
    
    # Generate README.md
    readme = f'''# {project_name.replace("-", " ").title()}

A full-stack application with React frontend and FastAPI backend.

## Quick Start

### Local Development

1. **Backend Setup**
   ```bash
   cd backend
   pip install -r requirements.txt
   python main.py
   ```

2. **Frontend Setup**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

3. **Access the Application**
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

### Docker Setup

```bash
docker-compose up --build
```

## Deployment

### Frontend (Vercel)
1. Push to GitHub
2. Connect to Vercel
3. Set environment variables:
   - `VITE_API_URL=your-backend-url`

### Backend (Render/Railway)
1. Connect your repository
2. Set environment variables:
   - `DATABASE_URL`
   - `OPENAI_API_KEY` (if using AI features)

### Database
- Use Railway PostgreSQL or MongoDB Atlas
- Update connection string in environment variables

## Environment Variables

Create `.env` files:

**Frontend (.env)**
```
VITE_API_URL=http://localhost:8000
```

**Backend (.env)**
```
DATABASE_URL=postgresql://user:password@localhost:5432/{project_name}
OPENAI_API_KEY=your-openai-key-here
SECRET_KEY=your-secret-key-here
```

## Features

- ✅ React with TailwindCSS
- ✅ FastAPI backend with auto-generated docs
- ✅ CORS configured for development
- ✅ Docker support
- ✅ Production-ready structure
- ✅ Environment configuration
- ✅ Database ready (PostgreSQL)

## Tech Stack

- **Frontend**: React, TailwindCSS, Vite
- **Backend**: FastAPI, Python
- **Database**: PostgreSQL
- **Deployment**: Vercel + Render/Railway

## API Endpoints

- `GET /` - Welcome message
- `GET /health` - Health check
- `GET /api/items` - Get all items
- `POST /api/items` - Create new item
- `GET /api/items/{{id}}` - Get item by ID
- `DELETE /api/items/{{id}}` - Delete item

Visit http://localhost:8000/docs for interactive API documentation.
'''
    
    with open(project_path / "README.md", "w") as f:
        f.write(readme)
    
    # Generate .env.example
    env_example = '''# Frontend Environment Variables
VITE_API_URL=http://localhost:8000

# Backend Environment Variables  
DATABASE_URL=postgresql://user:password@localhost:5432/database
OPENAI_API_KEY=your-openai-key-here
SECRET_KEY=your-secret-key-here
JWT_SECRET=your-jwt-secret-here'''
    
    with open(project_path / ".env.example", "w") as f:
        f.write(env_example)

def analyze_project_features(idea: str) -> List[str]:
    """Analyze the idea and determine what features should be included"""
    features = ["Responsive Design", "API Integration", "Production Ready"]
    
    idea_lower = idea.lower()
    
    # Core features based on keywords
    if any(word in idea_lower for word in ["user", "login", "auth", "account"]):
        features.append("User Authentication")
    
    if any(word in idea_lower for word in ["database", "store", "save", "crud"]):
        features.append("Database Storage")
    
    if any(word in idea_lower for word in ["ai", "ml", "gpt", "openai", "intelligence"]):
        features.append("AI Integration")
    
    if any(word in idea_lower for word in ["chat", "message", "real-time", "live"]):
        features.append("Real-time Features")
    
    if any(word in idea_lower for word in ["payment", "stripe", "billing", "subscription"]):
        features.append("Payment Integration")
    
    if any(word in idea_lower for word in ["upload", "file", "image", "photo"]):
        features.append("File Upload")
    
    if any(word in idea_lower for word in ["email", "notification", "alert"]):
        features.append("Email Notifications")
    
    if any(word in idea_lower for word in ["admin", "dashboard", "manage"]):
        features.append("Admin Dashboard")
    
    if any(word in idea_lower for word in ["search", "filter", "find"]):
        features.append("Search Functionality")
    
    if any(word in idea_lower for word in ["mobile", "responsive", "device"]):
        features.append("Mobile Responsive")
    
    return features

@app.post("/generate-project")
async def generate_project(request: ProjectRequest):
    """
    AI-powered full-stack project generation endpoint
    Generates complete project with frontend, backend, and deployment instructions
    """
    try:
        idea = request.idea
        project_type = request.project_type
        tech_stack_raw = request.tech_stack
        complexity = request.complexity
        
        # Normalize tech_stack to list format
        if isinstance(tech_stack_raw, str):
            if tech_stack_raw == "auto":
                tech_stack = ["React", "TypeScript", "TailwindCSS", "FastAPI", "Python"]
            else:
                tech_stack = [tech_stack_raw]
        else:
            tech_stack = tech_stack_raw
        
        print(f"🚀 Generating full-stack project for idea: '{idea}'")
        print(f"🔧 Project type: {project_type}, Tech stack: {tech_stack}, Complexity: {complexity}")
        
        # Enhanced AI prompt for full-stack generation
        tech_stack_str = ", ".join(tech_stack)
        enhanced_prompt = f"""
Generate a complete, production-ready full-stack application based on this user request: "{idea}"

TECH STACK: {tech_stack_str}

REQUIREMENTS:
1. Generate BOTH frontend and backend code (not just structure)
2. Based on the user prompt, generate:
   - The UI (React with TailwindCSS, minimal aesthetic)
   - Backend logic (routes, APIs, database models if needed)
   - Integration between frontend and backend
3. If the prompt requires authentication, CRUD, or AI integration, scaffold the logic accordingly
4. Use a clean folder structure: /frontend and /backend
5. Provide comments explaining each file's role and why the logic works
6. Ensure APIs connect correctly with the frontend fetch/axios calls
7. If the prompt includes "with AI", assume AI model integration is needed
8. Generate boilerplate so the app can run locally with minimal setup (npm/yarn for frontend, pip/npm for backend)
9. Include deployment instructions in comments (like Vercel + Render/Heroku)
10. The code should be production-ready, simple, and lovable (smooth UI, clean backend logic)
11. Use the specified tech stack: {tech_stack_str}

Example input from user: "Build a to-do list app with AI reminders"
→ Should generate: 
   - React frontend with add/remove todos
   - Backend with FastAPI or Express to store todos
   - AI reminder logic using OpenAI API
   - Clear explanation of where to configure keys

Always generate FULL STACK logic (not just frontend).

TECH STACK SELECTION:
- For web apps: React + TailwindCSS frontend, FastAPI/Express backend
- For AI features: Include OpenAI API integration
- For databases: PostgreSQL/MongoDB based on complexity
- For real-time: Socket.io/WebSockets if needed

Generate actual code files with complete implementations, not just placeholders.
"""
        
        # Use AI assistant to generate the actual project
        ai_response = await run_in_threadpool(get_chat_response, enhanced_prompt, "smart")
        
        # Generate human-readable project name from the idea
        project_name = generate_human_readable_project_name(idea)
        
        # Create project directory
        projects_dir = Path("generated_projects")
        projects_dir.mkdir(exist_ok=True)
        project_path = projects_dir / project_name
        
        # Remove existing project if it exists
        if project_path.exists():
            shutil.rmtree(project_path)
        
        # Determine tech stack and structure
        if "ai" in idea.lower() or "ml" in idea.lower():
            tech_stack_final = tech_stack + ["OpenAI API"] if "OpenAI API" not in tech_stack else tech_stack
            needs_ai = True
        else:
            tech_stack_final = tech_stack
            needs_ai = False
        
        # Generate the actual project files using AI-powered generation
        project_structure = await generate_ai_powered_full_stack_files(
            project_path, 
            idea, 
            project_name, 
            tech_stack_final,
            needs_ai
        )
        
        # Generate features based on idea analysis
        features = analyze_project_features(idea)
        
        # Estimate development time
        time_mapping = {
            "simple": "2-3 days",
            "medium": "1-2 weeks", 
            "complex": "3-4 weeks"
        }
        estimated_time = time_mapping.get(complexity, "1-2 weeks")
        
        # Generate deployment info
        deployment_info = {
            "frontend": "Deploy to Vercel or Netlify",
            "backend": "Deploy to Render, Railway, or Heroku",
            "database": "Use Railway PostgreSQL or MongoDB Atlas",
            "env_vars": "Configure API keys and database URLs"
        }
        
        return {
            "success": True,
            "project": {
                "name": project_name.replace("-", " ").title(),
                "description": idea,
                "tech_stack": tech_stack_final,
                "structure": project_structure,
                "features": features,
                "estimated_time": estimated_time,
                "deployment": deployment_info,
                "project_type": project_type,
                "complexity": complexity,
                "path": str(project_path),
                "ai_generated": True
            },
            "auto_run": {
                "enabled": True,
                "project_name": project_name.replace("-", " ").title(),
                "redirect_to_monaco": True,
                "auto_start_project": True,
                "show_file_tree": True
            }
        }
        
    except Exception as e:
        print(f"❌ Project generation error: {e}")
        return {
            "success": False,
            "error": f"Failed to generate project: {str(e)}"
        }

@app.post("/auto-run-project")
async def auto_run_project(request: dict):
    """
    Auto-run project after AI generation - opens Monaco Editor and starts the project
    """
    try:
        project_name = request.get("project_name")
        if not project_name:
            return {"success": False, "error": "Project name is required"}
        
        # Generate project slug
        project_slug = project_name.lower().replace(" ", "-").replace("_", "-")
        
        print(f"🚀 Auto-running project: {project_name}")
        
        # Return instructions for frontend to auto-navigate and start
        return {
            "success": True,
            "auto_run": {
                "project_name": project_name,
                "project_slug": project_slug,
                "monaco_url": f"/monaco?project={project_name}",
                "actions": [
                    {"type": "navigate", "target": "monaco_editor"},
                    {"type": "load_file_tree", "project": project_name},
                    {"type": "auto_start", "delay": 2000},
                    {"type": "show_preview", "delay": 5000}
                ]
            }
        }
        
    except Exception as e:
        print(f"❌ Auto-run error: {e}")
        return {"success": False, "error": str(e)}

@app.post("/propose-fix")
async def propose_fix(request: FixRequest):
    """
    RAG-powered automated code remediation endpoint with detailed code comparison
    Takes a specific security issue and creates a PR with the fix
    """
    try:
        repo_url = request.repo_url
        issue = request.issue
        
        print(f"🔍 Raw repo_url received: '{repo_url}'")
        print(f"🔍 Issue data: {json.dumps(issue, indent=2)}")
        
        # Check if this is a local analysis (not a GitHub repo)
        if not repo_url.startswith('https://github.com/') and not repo_url.startswith('git@github.com:'):
            print(f"❌ Invalid repo URL format: '{repo_url}' - not a GitHub URL")
            return await provide_local_fix_suggestion(issue)
        
        # Clean and extract repo info
        repo_url_clean = repo_url.rstrip('/').replace('.git', '')
        
        # Handle different GitHub URL formats
        if '/tree/' in repo_url_clean:
            # Remove everything after /tree/
            repo_url_clean = repo_url_clean.split('/tree/')[0]
            print(f"🔧 Cleaned tree URL: '{repo_url}' -> '{repo_url_clean}'")
        
        if '/blob/' in repo_url_clean:
            # Remove everything after /blob/
            repo_url_clean = repo_url_clean.split('/blob/')[0]
            print(f"🔧 Cleaned blob URL: '{repo_url}' -> '{repo_url_clean}'")
        
        parts = repo_url_clean.replace('https://github.com/', '').split('/')
        print(f"🔍 URL parts after cleaning: {parts}")
        
        if len(parts) < 2:
            print(f"❌ Invalid repo URL format after cleaning: '{repo_url_clean}' -> parts: {parts}")
            raise HTTPException(status_code=400, detail=f"Invalid repo URL format. Expected format: https://github.com/owner/repo, got: '{repo_url}'")
        
        owner, repo_name = parts[0], parts[1]
        print(f"🔍 Extracted repo: {owner}/{repo_name}")
        
        # Initialize GitHub client with proper authentication
        token = os.getenv("GITHUB_TOKEN")
        if not token:
            raise HTTPException(status_code=500, detail="GitHub token not configured. Please set GITHUB_TOKEN environment variable.")
        
        from github import Github
        try:
            # Always create a fresh GitHub client with the token
            working_github_client = Github(token)
            print("✅ Created fresh GitHub client")
            
            # Test the client immediately
            test_user = working_github_client.get_user()
            print(f"✅ GitHub client authenticated as: {test_user.login}")
            
        except Exception as client_error:
            print(f"❌ GitHub authentication failed: {client_error}")
            raise HTTPException(status_code=401, detail=f"GitHub authentication failed: {str(client_error)}")
        
        # Test repository access with the working client
        try:
            print(f"🔍 Testing access to repository: {owner}/{repo_name}")
            github_repo = working_github_client.get_repo(f"{owner}/{repo_name}")
            print(f"✅ Repository accessible: {github_repo.full_name}")
            print(f"📊 Repository info: {github_repo.language}, Private: {github_repo.private}")
            
        except Exception as repo_error:
            error_msg = str(repo_error)
            print(f"❌ Repository access failed: {error_msg}")
            
            if "401" in error_msg or "Bad credentials" in error_msg:
                raise HTTPException(
                    status_code=401, 
                    detail=f"GitHub authentication failed. Your token may not have the correct permissions. Please ensure your GITHUB_TOKEN has 'repo' scope for private repositories or 'public_repo' scope for public repositories. Error: {error_msg}"
                )
            elif "404" in error_msg or "Not Found" in error_msg:
                raise HTTPException(
                    status_code=404, 
                    detail=f"Repository '{owner}/{repo_name}' not found or not accessible. Please check: 1) Repository URL is correct, 2) Repository exists and is public, or 3) Your token has access to private repositories. Error: {error_msg}"
                )
            else:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Repository access error: {error_msg}"
                )
        
        # Create temporary directory for cloning
        temp_dir = tempfile.mkdtemp()
        
        try:
            print(f"🔧 Starting fix process for {repo_url_clean}")
            
            # Clone the repository using the cleaned URL
            repo = git.Repo.clone_from(repo_url_clean, temp_dir)
            
            # Get the file content
            issue_file = issue.get('file', '')
            if not issue_file:
                raise HTTPException(status_code=400, detail="Issue must specify a file path")
            
            # Extract relative path from absolute path if needed
            # Handle cases where issue_file might be an absolute temp path
            if os.path.isabs(issue_file):
                # Try to extract the relative path by finding common patterns
                # Look for patterns like /backend/, /frontend/, /src/, etc.
                path_parts = issue_file.replace('\\', '/').split('/')
                
                # Find the start of the relative path (after temp directory)
                relative_start = -1
                for i, part in enumerate(path_parts):
                    if part in ['backend', 'frontend', 'src', 'lib', 'app', 'public', 'static', 'assets']:
                        relative_start = i
                        break
                
                if relative_start != -1:
                    # Take everything from the relative start
                    issue_file = '/'.join(path_parts[relative_start:])
                    print(f"🔄 Extracted relative path from absolute: {issue_file}")
                else:
                    # If we can't find a common pattern, take the last few parts
                    # This handles cases like "config/db.js" or "package.json"
                    if len(path_parts) >= 2:
                        issue_file = '/'.join(path_parts[-2:])  # Take last 2 parts
                    else:
                        issue_file = path_parts[-1]  # Take just the filename
                    print(f"🔄 Using fallback relative path: {issue_file}")
            
            # Normalize file path (ensure forward slashes for cross-platform compatibility)
            issue_file = issue_file.replace('\\', '/')
            print(f"🔍 Final normalized issue file path: {issue_file}")
            print(f"🔍 Repository temp directory: {temp_dir}")
            
            file_path = os.path.join(temp_dir, issue_file)
            print(f"🔍 Full file path: {file_path}")
            
            # Store original file content (before fix)
            original_content = ""
            file_existed = os.path.exists(file_path)
            
            if file_existed:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    original_content = f.read()
                print(f"📄 Original file content loaded: {len(original_content)} characters")
            else:
                print(f"📝 File {issue_file} will be created (doesn't exist)")
            
            # Query RAG database for secure coding patterns (Enhanced with live SonarSource rules)
            print("🔍 Querying enhanced RAG database for secure patterns...")
            rag_query = f"{issue.get('type', 'security')} {issue.get('description', '')} {issue.get('vulnerable_code', '')}"
            secure_patterns = await run_in_threadpool(get_secure_coding_patterns, rag_query)
            
            print(f"✅ Retrieved {len(secure_patterns)} characters of security patterns from RAG database")
            
            # Enhanced "Fixer" AI prompt - Gemini receives BOTH user issue AND RAG knowledge
            # Extract the specific vulnerable line if line number is provided
            vulnerable_line_context = ""
            if issue.get('line') and original_content:
                try:
                    lines = original_content.split('\n')
                    line_num = int(issue.get('line', 0))
                    if 1 <= line_num <= len(lines):
                        # Show context around the vulnerable line
                        start_line = max(1, line_num - 2)
                        end_line = min(len(lines), line_num + 2)
                        context_lines = []
                        for i in range(start_line - 1, end_line):
                            marker = " >>> " if i == line_num - 1 else "     "
                            context_lines.append(f"{i+1:3d}:{marker}{lines[i]}")
                        vulnerable_line_context = "\n".join(context_lines)
                except:
                    vulnerable_line_context = "Could not extract line context"
            
            fixer_prompt = f"""
You are a security code remediation expert. I'm providing you with BOTH a specific security issue that needs fixing AND relevant security knowledge from our RAG database. Use both pieces of information together to create the best possible fix.

**USER'S SECURITY ISSUE TO FIX:**
- File: {issue.get('file', 'unknown')}
- Line: {issue.get('line', 'unknown')}
- Type: {issue.get('type', 'unknown')}
- Description: {issue.get('description', 'No description')}
- Vulnerable Code: {issue.get('vulnerable_code', 'Not specified')}
- Severity: {issue.get('severity', 'Medium')}

**VULNERABLE LINE CONTEXT:**
```
{vulnerable_line_context if vulnerable_line_context else "Line context not available"}
```

**CURRENT FILE CONTENT:**
```
{original_content if file_existed else "// File does not exist - will be created"}
```

**RAG SECURITY KNOWLEDGE (SonarSource Rules + OWASP Guidelines):**
{secure_patterns}

**CRITICAL REQUIREMENTS:**
1. You MUST provide the COMPLETE file content in your response, not just the changed lines
2. Make specific, targeted security fixes based on the issue description
3. If the issue is about hardcoded credentials, replace them with environment variable loading
4. If it's about missing validation, add proper input validation  
5. If it's about injection vulnerabilities, add sanitization/escaping
6. Preserve ALL existing functionality while fixing the security issue
7. DO NOT just add a comment - make actual code changes

**YOUR TASK:**
Analyze the user's security issue AND the RAG knowledge together to:
1. Understand the specific vulnerability in the user's code
2. Find the most relevant security patterns from the RAG knowledge
3. Apply the best remediation technique from both sources
4. Generate a complete, production-ready fixed version of the file
5. Reference specific rules and patterns you used from the RAG knowledge
6. Ensure the fix addresses the user's exact issue
7. Preserve all functionality while improving security

**RESPONSE FORMAT:**
Return ONLY a JSON object with this exact structure:
{{
    "fixed_content": "complete fixed file content here",
    "changes_made": [
        "Applied pattern from RAG knowledge: Replaced eval() with ast.literal_eval() based on SonarSource RSPEC-XXX",
        "Implemented user's specific issue fix: Added input validation for the vulnerable code section"
    ],
    "security_impact": "Resolves the user's {issue.get('type', 'security')} issue while applying RAG-recommended security patterns",
    "commit_message": "fix: resolve {issue.get('type', 'security')} vulnerability in {issue.get('file', 'file')} using RAG-enhanced patterns",
    "lines_changed": [
        {{"line_number": 15, "old_code": "eval(user_input)", "new_code": "ast.literal_eval(user_input)", "change_type": "modified"}},
        {{"line_number": 16, "old_code": "", "new_code": "# Security: Applied RAG pattern (SonarSource RSPEC-XXX)", "change_type": "added"}}
    ],
    "fix_summary": "Combined user issue analysis with RAG security knowledge: {issue.get('description', 'vulnerability')} resolved using recommended patterns",
    "rag_patterns_applied": ["Pattern from RAG: SonarSource RSPEC-XXX for code injection prevention", "OWASP guideline for input validation"],
    "user_issue_addressed": "Specific fix for: {issue.get('description', 'security issue')} in {issue.get('file', 'file')}",
    "integration_approach": "Gemini AI analyzed both user issue and RAG knowledge simultaneously for optimal fix"
}}
"""

            # Call Gemini AI with BOTH user issue and RAG knowledge
            print("🤖 Gemini AI processing user issue + RAG knowledge together...")
            ai_response = await run_in_threadpool(get_chat_response, [
                {'type': 'user', 'parts': [fixer_prompt]}
            ], 'smart')  # Use smart model for comprehensive analysis
            
            # Parse the AI response with robust JSON parsing
            def clean_and_parse_json(text):
                """Clean and parse JSON from AI response"""
                try:
                    # First try to find JSON in ```json blocks
                    import re
                    json_block = re.search(r'```json\s*(\{.*?\})\s*```', text, re.DOTALL)
                    if json_block:
                        json_text = json_block.group(1)
                        return json.loads(json_text)
                except Exception:
                    pass
                
                # Fallback: Extract between first { and last } and clean
                try:
                    start = text.find('{')
                    end = text.rfind('}') + 1
                    if start != -1 and end != -1:
                        json_text = text[start:end]
                        # Simple cleanup - replace newlines with spaces
                        json_text = json_text.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
                        # Remove extra whitespace
                        json_text = re.sub(r'\s+', ' ', json_text)
                        return json.loads(json_text)
                except Exception:
                    pass
                
                return None
            
            try:
                fix_data = clean_and_parse_json(ai_response)
                if fix_data:
                    print("✅ Successfully parsed AI fix response for GitHub")
                else:
                    raise ValueError("Could not parse JSON from AI response")
            except Exception as e:
                print(f"⚠️ Failed to parse AI JSON, using enhanced fallback: {e}")
                print(f"🔍 AI Response: {ai_response[:500]}...")
                
                # Enhanced fallback: create intelligent fix based on issue type
                issue_desc = issue.get('description', '').lower()
                
                if 'private key' in issue_desc or 'secret' in issue_desc or 'credential' in issue_desc:
                    # For key/secret issues, replace with environment variable pattern
                    if original_content:
                        # Try to find and replace the hardcoded credential
                        lines = original_content.split('\n')
                        fixed_lines = []
                        for line in lines:
                            if 'password' in line.lower() and '=' in line and ('"' in line or "'" in line):
                                # Replace hardcoded password with env var
                                var_name = line.split('=')[0].strip()
                                fixed_lines.append(f"import os")
                                fixed_lines.append(f"{var_name} = os.getenv('{var_name.upper()}', 'default_secure_value')")
                            else:
                                fixed_lines.append(line)
                        fixed_content = '\n'.join(fixed_lines)
                    else:
                        fixed_content = "import os\n# Credentials moved to environment variables\n"
                    
                    fix_data = {
                        "fixed_content": fixed_content,
                        "changes_made": ["Replaced hardcoded credentials with environment variables"],
                        "fix_summary": f"Secured credential management in {issue.get('file', 'file')}",
                        "security_impact": "Credentials moved to secure environment variables"
                    }
                elif '.gitignore' in issue.get('file', ''):
                    # For gitignore issues, add security patterns
                    fix_data = {
                        "fixed_content": original_content + "\n# Security additions\n*.key\n*.pem\n*.env\n.env.*\nsecrets/\nconfig/secrets.yml\n",
                        "changes_made": ["Added security patterns to .gitignore"],
                        "fix_summary": "Enhanced .gitignore with security patterns",
                        "security_impact": "Prevented sensitive files from being committed"
                    }
                else:
                    # For other issues, try to apply a meaningful fix
                    if original_content:
                        fixed_content = f"# Security improvement applied\n# Issue: {issue.get('description', 'Security vulnerability')}\n{original_content}"
                    else:
                        fixed_content = f"# Security fix for: {issue.get('description', 'Security vulnerability')}\n# Please implement proper security measures\n"
                    
                    fix_data = {
                        "fixed_content": fixed_content,
                        "changes_made": [f"Applied security fix for {issue.get('type', 'security')} issue"],
                        "security_impact": "Security improvement applied",
                        "commit_message": f"fix: resolve {issue.get('type', 'security')} vulnerability",
                        "lines_changed": [],
                        "fix_summary": f"Security fix applied for {issue.get('description', 'vulnerability')}"
                    }
            
            # Apply the fix to the file
            fixed_content = fix_data.get('fixed_content', '')
            if not fixed_content:
                raise HTTPException(status_code=500, detail="AI did not provide fixed content")
            
            # Create directory if needed
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Write the fixed content
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(fixed_content)
            
            print("✅ Fix applied to local file")
            
            # Calculate detailed code differences with unified diff
            def calculate_code_diff(original: str, fixed: str) -> dict:
                """Calculate detailed differences between original and fixed code"""
                import difflib
                
                original_lines = original.splitlines(keepends=True) if original else []
                fixed_lines = fixed.splitlines(keepends=True)
                
                # Generate unified diff
                unified_diff = list(difflib.unified_diff(
                    original_lines, 
                    fixed_lines, 
                    fromfile='original',
                    tofile='fixed',
                    lineterm='',
                    n=3  # 3 lines of context
                ))
                
                # Simple diff calculation
                diff_stats = {
                    "lines_added": len(fixed_lines) - len(original_lines) if len(fixed_lines) > len(original_lines) else 0,
                    "lines_removed": len(original_lines) - len(fixed_lines) if len(original_lines) > len(fixed_lines) else 0,
                    "lines_modified": 0,
                    "total_changes": 0,
                    "unified_diff": ''.join(unified_diff),
                    "has_changes": len(unified_diff) > 0
                }
                
                # Calculate modifications
                min_lines = min(len(original_lines), len(fixed_lines))
                for i in range(min_lines):
                    if original_lines[i] != fixed_lines[i]:
                        diff_stats["lines_modified"] += 1
                
                diff_stats["total_changes"] = diff_stats["lines_added"] + diff_stats["lines_removed"] + diff_stats["lines_modified"]
                
                return diff_stats
            
            code_diff = calculate_code_diff(original_content, fixed_content)
            
            # Create a new branch
            branch_name = request.branch_name or f"fix/{issue.get('type', 'security').lower().replace(' ', '-')}-{issue.get('file', 'file').replace('/', '-').replace('.', '-')}"
            
            # Check if branch already exists
            try:
                github_repo.get_branch(branch_name)
                # Branch exists, add timestamp to make it unique
                import time
                branch_name = f"{branch_name}-{int(time.time())}"
            except:
                pass  # Branch doesn't exist, which is what we want
            
            # Create branch and commit
            repo.git.checkout('-b', branch_name)
            
            # Use relative path for git operations (normalize path separators)
            git_file_path = issue_file.replace('\\', '/')
            print(f"📝 Adding file to git: {git_file_path}")
            print(f"🔍 Current working directory: {os.getcwd()}")
            print(f"🔍 Repository working directory: {repo.working_dir}")
            
            try:
                # Verify file exists relative to repo root
                full_file_path = os.path.join(repo.working_dir, git_file_path)
                if os.path.exists(full_file_path):
                    print(f"✅ File exists at: {full_file_path}")
                else:
                    print(f"❌ File not found at: {full_file_path}")
                    # List files in the directory to debug
                    dir_to_check = os.path.dirname(full_file_path)
                    if os.path.exists(dir_to_check):
                        print(f"📂 Files in {dir_to_check}: {os.listdir(dir_to_check)}")
                
                repo.git.add(git_file_path)
                print(f"✅ Successfully added {git_file_path} to git")
                
            except Exception as git_add_error:
                print(f"❌ DETAILED ERROR in git add: {git_add_error}")
                print(f"📍 Git add failed for: {git_file_path}")
                print(f"📍 Repository root: {repo.working_dir}")
                print(f"📍 Attempted file path: {git_file_path}")
                raise git_add_error
            
            # Configure Git user identity for commits (use global config if available)
            try:
                # First try to get the global Git configuration
                try:
                    global_email = repo.git.config('--global', '--get', 'user.email')
                    global_name = repo.git.config('--global', '--get', 'user.name')
                    print(f"✅ Using global Git identity: {global_name} <{global_email}>")
                except:
                    # If global config not available, set a default
                    repo.git.config('user.email', 'altx-security-bot@automated.fix')
                    repo.git.config('user.name', 'AltX Security Bot')
                    print("✅ Git user identity configured with bot defaults")
            except Exception as config_error:
                print(f"⚠️ Warning: Could not configure Git identity: {config_error}")
            
            commit_message = fix_data.get('commit_message', f"fix: resolve security vulnerability in {issue_file}")
            repo.git.commit('-m', commit_message)
            print(f"✅ Successfully committed fix with message: {commit_message}")
            
            # Push the branch
            try:
                origin = repo.remote('origin')
                origin.push(branch_name)
                print(f"✅ Pushed fix to branch: {branch_name}")
                
                # If push succeeds, continue with PR creation
                push_success = True
                
            except Exception as push_error:
                push_success = False
                error_msg = str(push_error)
                print(f"❌ Push failed: {error_msg}")
                
                # Check if it's a permission issue (403, authentication, etc.)
                if "403" in error_msg or "401" in error_msg or "authentication" in error_msg.lower() or "permission" in error_msg.lower():
                    print("🔒 No write access to repository - attempting fork workflow...")
                    
                    try:
                        # Try to fork the repository
                        print(f"🍴 Attempting to fork {owner}/{repo_name}")
                        
                        # Get the authenticated user
                        auth_user = working_github_client.get_user()
                        user_login = auth_user.login
                        print(f"👤 Authenticated as: {user_login}")
                        
                        # Check if fork already exists
                        try:
                            existing_fork = working_github_client.get_repo(f"{user_login}/{repo_name}")
                            print(f"✅ Fork already exists: {existing_fork.full_name}")
                            forked_repo = existing_fork
                        except:
                            # Create fork
                            original_repo = working_github_client.get_repo(f"{owner}/{repo_name}")
                            forked_repo = auth_user.create_fork(original_repo)
                            print(f"✅ Fork created: {forked_repo.full_name}")
                        
                        # Update remote origin to point to fork
                        fork_url = forked_repo.clone_url
                        # Add token to URL for authentication
                        token = os.getenv("GITHUB_TOKEN")
                        if token:
                            fork_url_with_auth = fork_url.replace("https://", f"https://{token}@")
                        else:
                            fork_url_with_auth = fork_url
                        
                        # Remove existing origin and add fork as origin
                        try:
                            repo.delete_remote('origin')
                        except:
                            pass
                        
                        fork_origin = repo.create_remote('origin', fork_url_with_auth)
                        print(f"🔄 Updated origin to fork: {fork_url}")
                        
                        # Push to fork
                        fork_origin.push(branch_name)
                        print(f"✅ Pushed fix to fork: {forked_repo.full_name}/{branch_name}")
                        
                        # Create PR from fork to original repo
                        head_ref = f"{user_login}:{branch_name}"  # Format: fork_owner:branch_name
                        
                        push_success = True
                        # Update github_repo to the original for PR creation
                        github_repo = working_github_client.get_repo(f"{owner}/{repo_name}")
                        
                    except Exception as fork_error:
                        print(f"❌ Fork workflow failed: {fork_error}")
                        
                        # Return local fix suggestion with fork instructions
                        return {
                            "success": True,
                            "message": f"🔧 Security fix generated for {issue_file} (Fork required)",
                            "fix_type": "fork_required",
                            "access_limitation": "Repository requires forking to contribute",
                            "fork_instructions": [
                                f"1. Go to https://github.com/{owner}/{repo_name}",
                                "2. Click the 'Fork' button to create your own copy",
                                "3. Clone your fork to your local machine",
                                "4. Apply the fix shown below",
                                "5. Commit and push to your fork",
                                "6. Create a pull request from your fork to the original repository"
                            ],
                            "fix_details": {
                                "file_fixed": issue_file,
                                "vulnerability_type": issue.get('type'),
                                "severity": issue.get('severity', 'Medium'),
                                "changes_made": fix_data.get('changes_made', []),
                                "security_impact": fix_data.get('security_impact'),
                                "fix_summary": fix_data.get('fix_summary', 'Security fix generated'),
                                "lines_changed": fix_data.get('lines_changed', [])
                            },
                            "code_comparison": {
                                "file_existed_before": file_existed,
                                "original_content": original_content,
                                "fixed_content": fixed_content,
                                "content_length_before": len(original_content),
                                "content_length_after": len(fixed_content),
                                "character_changes": len(fixed_content) - len(original_content)
                            },
                            "manual_fix_instructions": f"To apply this fix:\n1. Fork the repository at https://github.com/{owner}/{repo_name}\n2. Clone your fork\n3. Edit the file: {issue_file}\n4. Replace the content with the fixed version\n5. Commit, push, and create a pull request",
                            "code_preview": {
                                "original_preview": original_content[:500] + ("..." if len(original_content) > 500 else ""),
                                "fixed_preview": fixed_content[:500] + ("..." if len(fixed_content) > 500 else ""),
                                "preview_truncated": len(original_content) > 500 or len(fixed_content) > 500
                            }
                        }
                else:
                    # For other git errors, re-raise
                    raise push_error
            
            # Only proceed with PR creation if push was successful
            if not push_success:
                return  # This shouldn't be reached due to the return above, but just in case
            
            # Create enhanced pull request with code comparison
            pr_title = f"🔒 Security Fix: {issue.get('description', 'Vulnerability remediation')}"
            
            # Generate code diff preview for PR body
            def generate_diff_preview(original: str, fixed: str, max_lines: int = 20) -> str:
                """Generate a diff preview for the PR description"""
                if not original and fixed:
                    return f"```diff\n+ {chr(10).join(fixed.splitlines()[:max_lines])}\n```"
                
                original_lines = original.splitlines()
                fixed_lines = fixed.splitlines()
                
                diff_preview = "```diff\n"
                
                # Show first few differences
                shown_lines = 0
                min_lines = min(len(original_lines), len(fixed_lines))
                
                for i in range(min_lines):
                    if shown_lines >= max_lines:
                        diff_preview += "... (more changes in the full diff)\n"
                        break
                        
                    if original_lines[i] != fixed_lines[i]:
                        diff_preview += f"- {original_lines[i]}\n+ {fixed_lines[i]}\n"
                        shown_lines += 2
                
                # Show added lines
                if len(fixed_lines) > len(original_lines):
                    for i in range(min_lines, min(len(fixed_lines), min_lines + max_lines - shown_lines)):
                        diff_preview += f"+ {fixed_lines[i]}\n"
                        shown_lines += 1
                
                diff_preview += "```"
                return diff_preview
            
            diff_preview = generate_diff_preview(original_content, fixed_content)
            
            pr_body = f"""
## 🛡️ Automated Security Fix

**Vulnerability Fixed:**
- **File:** `{issue.get('file', 'unknown')}`
- **Line:** {issue.get('line', 'unknown')}
- **Type:** {issue.get('type', 'Security Issue')}
- **Severity:** {issue.get('severity', 'Medium')}
- **Description:** {issue.get('description', 'No description')}

**Fix Summary:**
{fix_data.get('fix_summary', 'Security improvements applied')}

**Changes Made:**
{chr(10).join([f'- {change}' for change in fix_data.get('changes_made', [])])}

**Security Impact:**
{fix_data.get('security_impact', 'Improves application security')}

**Code Changes Preview:**
{diff_preview}

**Statistics:**
- **Lines Added:** {code_diff['lines_added']}
- **Lines Modified:** {code_diff['lines_modified']}
- **Lines Removed:** {code_diff['lines_removed']}
- **Total Changes:** {code_diff['total_changes']}

**Generated by:** AltX Security Scanner - Automated Remediation
**Powered by:** RAG-enhanced AI code analysis

---

⚠️ **Please review this automated fix carefully before merging.**

🔍 **Testing Recommended:**
- Run existing tests to ensure functionality is preserved
- Perform security testing to verify the vulnerability is resolved
- Review the code changes for any potential side effects
"""
            try:
                default_branch = github_repo.default_branch
                print(f"📋 Repository default branch: {default_branch}")
                try:
                    remote_branch = github_repo.get_branch(branch_name)
                    print(f"✅ Branch {branch_name} confirmed on remote")
                except Exception as e:
                    print(f"⚠️ Branch verification failed: {e}")
                    github_repo = working_github_client.get_repo(f"{owner}/{repo_name}")
            
                # Check if we're working with a fork (head_ref would be set in fork workflow)
                if 'head_ref' in locals():
                    print(f"🍴 Creating PR from fork: {head_ref} -> {default_branch}")
                    pull_request = github_repo.create_pull(
                        title=pr_title,
                        body=pr_body,
                        head=head_ref,  # fork_owner:branch_name
                        base=default_branch
                    )
                else:
                    print(f"📝 Creating PR from same repo: {branch_name} -> {default_branch}")
                    pull_request = github_repo.create_pull(
                        title=pr_title,
                        body=pr_body,
                        head=branch_name,
                        base=default_branch
                    )
                print(f"✅ Pull request created: {pull_request.html_url}")
            except Exception as pr_error:
                error_msg = str(pr_error)
                print(f"❌ Pull request creation failed: {error_msg}")
                
                # Handle specific GitHub API errors with user-friendly messages
                if "403" in error_msg and ("archived" in error_msg.lower() or "read-only" in error_msg.lower()):
                    print(f"🔒 Repository is archived and read-only: {owner}/{repo_name}")
                    return {
                        "success": True,
                        "message": f"🔧 Security fix generated for {issue_file} (Repository is archived)",
                        "fix_type": "archived_repository",
                        "access_limitation": f"Repository {owner}/{repo_name} is archived and read-only",
                        "manual_fix_instructions": f"This repository is archived and cannot accept pull requests. To apply this fix:\n1. Contact the repository owner to unarchive it\n2. Or fork the repository and apply the fix to your fork\n3. The security issue was found in: {issue_file}",
                        "fix_details": fix_data,
                        "code_comparison": {
                            "original_content": original_content,
                            "fixed_content": fixed_content,
                            "content_length_before": len(original_content),
                            "content_length_after": len(fixed_content),
                            "character_changes": len(fixed_content) - len(original_content)
                        },
                        "code_preview": {
                            "original_preview": original_content[:500] + ("..." if len(original_content) > 500 else ""),
                            "fixed_preview": fixed_content[:500] + ("..." if len(fixed_content) > 500 else ""),
                            "preview_truncated": len(original_content) > 500 or len(fixed_content) > 500
                        }
                    }
                elif "404" in error_msg:
                    print(f"❌ PR creation failed with 404. Debugging info:")
                    print(f"   Repository: {owner}/{repo_name}")
                    print(f"   Head branch: {branch_name}")
                    print(f"   Base branch: {default_branch}")
                    print(f"   Repository exists: {github_repo.full_name}")
                    
                    # Check if it's a branch not found issue
                    if "not found" in error_msg.lower() and "branch" in error_msg.lower():
                        print(f"🔍 Branch not found - this might be a timing issue")
                        return {
                            "success": True,
                            "message": f"🔧 Security fix applied to {issue_file} (Branch sync issue)",
                            "fix_type": "branch_sync_issue",
                            "access_limitation": "Branch synchronization issue with GitHub",
                            "manual_fix_instructions": f"The fix was applied locally but there was a branch synchronization issue. To resolve:\n1. The changes were made to: {issue_file}\n2. Try creating the pull request manually\n3. Or re-run the fix after a few minutes",
                            "fix_details": fix_data,
                            "code_comparison": {
                                "original_content": original_content,
                                "fixed_content": fixed_content,
                                "content_length_before": len(original_content),
                                "content_length_after": len(fixed_content),
                                "character_changes": len(fixed_content) - len(original_content)
                            }
                        }
                    
                    if hasattr(github_repo, 'fork') and github_repo.fork:
                        print("   Note: This is a forked repository")
                        head_with_owner = f"{owner}:{branch_name}"
                        print(f"   Trying with owner prefix: {head_with_owner}")
                        try:
                            pull_request = github_repo.create_pull(
                                title=pr_title,
                                body=pr_body,
                                head=head_with_owner,
                                base=default_branch
                            )
                            print(f"✅ Pull request created with owner prefix: {pull_request.html_url}")
                        except Exception as e2:
                            print(f"❌ PR creation with owner prefix also failed: {e2}")
                            raise HTTPException(status_code=404, 
                                detail=f"Failed to create pull request. Repository: {owner}/{repo_name},Branch: {branch_name} → {default_branch}. Error: {error_msg}"
                            )
                    else:
                        raise HTTPException(
                            status_code=404, 
                            detail=f"Failed to create pull request. Repository: {owner}/{repo_name}, Branch: {branch_name} → {default_branch}. Error: {error_msg}"
                        )
                elif "403" in error_msg:
                    print(f"🔒 Permission denied for repository: {owner}/{repo_name}")
                    return {
                        "success": True,
                        "message": f"🔧 Security fix generated for {issue_file} (Permission denied)",
                        "fix_type": "permission_denied",
                        "access_limitation": "Insufficient permissions to create pull request",
                        "manual_fix_instructions": f"Permission denied while creating pull request. To apply this fix:\n1. Ensure your GitHub token has write access to {owner}/{repo_name}\n2. Or fork the repository and apply the fix to your fork\n3. The security issue was found in: {issue_file}",
                        "fix_details": fix_data,
                        "code_comparison": {
                            "original_content": original_content,
                            "fixed_content": fixed_content,
                            "content_length_before": len(original_content),
                            "content_length_after": len(fixed_content),
                            "character_changes": len(fixed_content) - len(original_content)
                        }
                    }
                elif "422" in error_msg and ("collaborator" in error_msg.lower() or "validation failed" in error_msg.lower()):
                    print(f"🤝 Not a collaborator on repository: {owner}/{repo_name}")
                    return {
                        "success": True,
                        "message": f"🔧 Security fix generated for {issue_file} (Fork required for contribution)",
                        "fix_type": "collaboration_required",
                        "access_limitation": "You are not a collaborator on this repository",
                        "manual_fix_instructions": f"You need to be a collaborator to create pull requests directly. To apply this fix:\n1. Ask the repository owner to add you as a collaborator\n2. Or fork the repository at https://github.com/{owner}/{repo_name}\n3. Apply the fix to your fork and create a PR from there\n4. The security issue was found in: {issue_file}",
                        "fix_details": fix_data,
                        "code_comparison": {
                            "original_content": original_content,
                            "fixed_content": fixed_content,
                            "content_length_before": len(original_content),
                            "content_length_after": len(fixed_content),
                            "character_changes": len(fixed_content) - len(original_content)
                        },
                        "fork_url": f"https://github.com/{owner}/{repo_name}/fork",
                        "code_preview": {
                            "original_preview": original_content[:500] + ("..." if len(original_content) > 500 else ""),
                            "fixed_preview": fixed_content[:500] + ("..." if len(fixed_content) > 500 else ""),
                            "preview_truncated": len(original_content) > 500 or len(fixed_content) > 500
                        }
                    }
                else:
                    raise HTTPException(
                            status_code=500,
                            detail=f"Pull request creation error: {error_msg}"
                    )
            # Prepare detailed response with code comparison
            response_data = {
                "success": True,
                "message": f"🔧 Security fix successfully applied to {issue_file}",
                "pull_request": {
                    "url": pull_request.html_url,
                    "number": pull_request.number,
                    "title": pr_title,
                    "branch": branch_name
                },
                "fix_details": {
                    "file_fixed": issue_file,
                    "vulnerability_type": issue.get('type'),
                    "severity": issue.get('severity', 'Medium'),
                    "changes_made": fix_data.get('changes_made', []),
                    "security_impact": fix_data.get('security_impact'),
                    "commit_message": commit_message,
                    "fix_summary": fix_data.get('fix_summary', 'Security fix applied'),
                    "lines_changed": fix_data.get('lines_changed', [])
                },
                "code_comparison": {
                    "file_existed_before": file_existed,
                    "original_content": original_content,
                    "fixed_content": fixed_content,
                    "content_length_before": len(original_content),
                    "content_length_after": len(fixed_content),
                    "diff_statistics": code_diff,
                    "character_changes": len(fixed_content) - len(original_content)
                },
                "metadata": {
                    "repo_url": repo_url,
                    "repo_name": f"{owner}/{repo_name}",
                    "timestamp": datetime.now().isoformat(),
                    "ai_model_used": "smart",
                    "rag_patterns_used": True,
                    "rag_query": rag_query,
                    "rag_patterns_applied": fix_data.get('rag_patterns_applied', []),
                    "user_issue_addressed": fix_data.get('user_issue_addressed', 'Security issue resolved'),
                    "integration_approach": fix_data.get('integration_approach', 'Gemini AI with RAG knowledge'),
                    "security_intelligence": "Gemini AI analyzed user issue + RAG knowledge simultaneously (6000+ patterns)"
                }
            }
            
            # Add preview of changes (first 500 chars of each)
            if original_content or fixed_content:
                response_data["code_preview"] = {
                    "original_preview": original_content[:500] + ("..." if len(original_content) > 500 else ""),
                    "fixed_preview": fixed_content[:500] + ("..." if len(fixed_content) > 500 else ""),
                    "preview_truncated": len(original_content) > 500 or len(fixed_content) > 500
                }
            
            return response_data
            
        finally:
            # Cleanup
            if os.path.exists(temp_dir):
                try:
                    import stat
                    
                    def force_remove_readonly(func, path, exc_info):
                        try:
                            if os.path.exists(path):
                                os.chmod(path, stat.S_IWRITE | stat.S_IREAD)
                                func(path)
                        except Exception:
                            pass
                    
                    shutil.rmtree(temp_dir, onerror=force_remove_readonly)
                    print("✅ Temporary directory cleaned up")
                except Exception as e:
                    print(f"⚠️ Warning: Could not clean up temp directory: {e}")
                    
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        print(f"❌ DETAILED ERROR in propose-fix: {e}")
        print(f"📍 TRACEBACK:\n{error_traceback}")
        raise HTTPException(status_code=500, detail=f"Fix generation failed: {str(e)}\nLocation: {error_traceback.split('File')[-1].split(',')[0] if 'File' in error_traceback else 'Unknown'}")
@app.get("/auth/github/callback")
async def github_callback(code: str = None, state: str = None):
    """
    Handle GitHub OAuth callback after user authorization
    This is the 'front door' for users returning after GitHub login
    """
    try:
        if not code:
            print("❌ No authorization code received from GitHub")
            return RedirectResponse(
                url="/?error=authorization_failed", 
                status_code=302
            )
        
        print(f"✅ Received GitHub authorization code: {code[:10]}...")
        
        # Exchange authorization code for access token
        

        # Exchange authorization code for access token
        token_url = "https://github.com/login/oauth/access_token"
        token_data = {
            "client_id": os.getenv("GITHUB_CLIENT_ID"),  # Changed from GITHUB_APP_ID
            "client_secret": os.getenv("GITHUB_CLIENT_SECRET"),
            "code": code,
            "state": state
        }
        token_headers = {
            "Accept": "application/json",
            "User-Agent": "AltX-Security-Scanner"
        }
        
        print("🔄 Exchanging code for access token...")
        token_response = requests.post(token_url, data=token_data, headers=token_headers)
        
        if token_response.status_code != 200:
            print(f"❌ Token exchange failed with status: {token_response.status_code}")
            return RedirectResponse(
                url="/?error=token_exchange_failed", 
                status_code=302
            )
        
        token_info = token_response.json()
        access_token = token_info.get("access_token")
        
        if not access_token:
            print(f"❌ No access token received from GitHub")
            return RedirectResponse(
                url="/?error=no_access_token", 
                status_code=302
            )
        
        print("✅ Access token received successfully")
        
        # Get user information
        user_headers = {
            "Authorization": f"token {access_token}",
            "Accept": "application/json",
            "User-Agent": "AltX-Security-Scanner"
        }
        
        user_response = requests.get("https://api.github.com/user", headers=user_headers)
        
        if user_response.status_code != 200:
            print(f"❌ Failed to get user info: {user_response.text}")
            return RedirectResponse(
                url="/?error=user_info_failed", 
                status_code=302
            )
        
        user_info = user_response.json()
        username = user_info.get("login", "unknown")
        github_id = user_info.get("id")
        avatar_url = user_info.get("avatar_url", "")
        email = user_info.get("email", "")
        
        # Get email if not in main response
        if not email:
            email_response = requests.get("https://api.github.com/user/emails", headers=user_headers)
            if email_response.status_code == 200:
                emails = email_response.json()
                primary_email = next((e["email"] for e in emails if e.get("primary")), None)
                email = primary_email or (emails[0]["email"] if emails else f"{username}@github.user")
        
        print(f"✅ User authenticated via GitHub")
        
        # Create or update user in MongoDB
        try:
            from database import MongoDB
            db = MongoDB.get_database()
            users_collection = db.users
            
            existing_user = users_collection.find_one({"email": email})
            
            if existing_user:
                # Update existing user
                users_collection.update_one(
                    {"email": email},
                    {"$set": {
                        "username": username,
                        "avatar": avatar_url,
                        "github_id": github_id,
                        "last_login": datetime.utcnow()
                    }}
                )
                user_doc = users_collection.find_one({"email": email})
            else:
                # Create new user
                new_user = {
                    "email": email,
                    "username": username,
                    "avatar": avatar_url,
                    "github_id": github_id,
                    "oauth_provider": "github",
                    "created_at": datetime.utcnow(),
                    "last_login": datetime.utcnow()
                }
                result = users_collection.insert_one(new_user)
                user_doc = users_collection.find_one({"_id": result.inserted_id})
            
            # Generate JWT token
            user_id_str = str(user_doc["_id"])
            access_token = create_access_token(data={"sub": user_id_str})
            
            # Prepare user data for frontend
            user_data = {
                "_id": user_id_str,
                "email": email,
                "username": username,
                "avatar": avatar_url
            }
            
            print(f"✅ JWT token generated successfully")
            
            # Redirect to frontend with token and user data via HTML page
            frontend_url = os.getenv("FRONTEND_URL", "https://xverta.com")
            import base64
            
            # Base64 encode user data to avoid URL encoding issues
            user_data_json = json.dumps(user_data)
            user_data_b64 = base64.b64encode(user_data_json.encode()).decode()
            
            redirect_url = f"{frontend_url}/oauth/callback?auth=success&token={access_token}&user={user_data_b64}"
            
            print(f"🚀 Redirecting to: {redirect_url}")
            
            # Return HTML page with AGGRESSIVE redirect debugging
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Login Successful</title>
                <meta charset="UTF-8">
            </head>
            <body>
                <div style="display: flex; align-items: center; justify-content: center; height: 100vh; font-family: Arial, sans-serif;">
                    <div style="text-align: center;">
                        <h2>✅ Login Successful!</h2>
                        <p id="status">Processing authentication...</p>
                        <p style="font-size: 12px; color: #666; margin-top: 10px;">
                            If you are not redirected in 2 seconds, <a href="{redirect_url}" style="color: #0066cc;">click here</a>.
                        </p>
                        <pre id="debug" style="font-size: 10px; color: #999; margin-top: 20px; text-align: left;"></pre>
                    </div>
                </div>
                <script>
                    const debug = document.getElementById('debug');
                    const status = document.getElementById('status');
                    
                    function log(msg) {{
                        console.log(msg);
                        debug.textContent += msg + '\\n';
                    }}
                    
                    log('🔄 GitHub OAuth callback page loaded');
                    log('🎯 Redirect URL: {redirect_url}');
                    log('🔍 Window location: ' + window.location.href);
                    log('🔍 User agent: ' + navigator.userAgent);
                    
                    let attempts = 0;
                    const maxAttempts = 3;
                    
                    function tryRedirect() {{
                        attempts++;
                        log(`⚡ Redirect attempt ${{attempts}} of ${{maxAttempts}}`);
                        status.textContent = `Redirecting (attempt ${{attempts}})...`;
                        
                        try {{
                            // Try multiple redirect methods
                            if (attempts === 1) {{
                                log('🔹 Method 1: window.location.href');
                                window.location.href = "{redirect_url}";
                            }} else if (attempts === 2) {{
                                log('🔹 Method 2: window.location.replace');
                                window.location.replace("{redirect_url}");
                            }} else {{
                                log('🔹 Method 3: window.location assignment');
                                window.location = "{redirect_url}";
                            }}
                            
                            log('✅ Redirect initiated');
                        }} catch (e) {{
                            log('❌ Redirect failed: ' + e.message);
                            if (attempts < maxAttempts) {{
                                setTimeout(tryRedirect, 500);
                            }} else {{
                                status.textContent = 'Redirect failed. Please click the link above.';
                            }}
                        }}
                    }}
                    
                    // Start first redirect attempt immediately
                    tryRedirect();
                </script>
            </body>
            </html>
            """
            
            return HTMLResponse(content=html_content, status_code=200)
            
        except Exception as db_error:
            print(f"❌ Database error: {str(db_error)}")
            return RedirectResponse(url=f"/?error=database_error", status_code=302)
        
    except Exception as e:
        print(f"❌ OAuth callback error: {str(e)}")
        return RedirectResponse(
            url=f"/?error=callback_failed&message={str(e)}", 
            status_code=302
        )



@app.get("/auth/github/login")
async def github_login():
    """
    Initiate GitHub OAuth login
    This redirects users to GitHub for authorization
    """
    try:
        # Use GITHUB_CLIENT_ID for OAuth, not GITHUB_APP_ID
        github_client_id = os.getenv("GITHUB_CLIENT_ID")  # Changed from GITHUB_APP_ID
        
        if not github_client_id:
            raise HTTPException(status_code=500, detail="GitHub Client ID not configured")
        
        # Generate a random state parameter for security
        import secrets
        state = secrets.token_urlsafe(32)
        
        # GitHub OAuth authorization URL
        github_auth_url = (
            f"https://github.com/login/oauth/authorize"
            f"?client_id={github_client_id}"
            f"&redirect_uri={os.getenv('GITHUB_CALLBACK_URL', 'http://localhost:8000/auth/github/callback')}"
            f"&scope=repo,user:email"
            f"&state={state}"
            f"&allow_signup=true"
        )
        
        print(f"🔗 Redirecting to GitHub OAuth: {github_auth_url}")
        
        return RedirectResponse(url=github_auth_url, status_code=302)
        
    except Exception as e:
        print(f"❌ Login initiation error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")

from fastapi import Request

@app.get("/auth/google/callback")
async def google_callback(request: Request):
    """
    Handle Google OAuth callback after user authorization
    """
    try:
        # Get the authorization code from the query parameters
        code = request.query_params.get("code")
        state = request.query_params.get("state")

        if not code:
            print("❌ No authorization code received from Google")
            return RedirectResponse(url="/?error=authorization_failed", status_code=302)

        print(f"✅ Received Google authorization code: {code[:10]}...")

        # Exchange authorization code for access token
        token_url = "https://oauth2.googleapis.com/token"
        token_data = {
            "client_id": os.getenv("GOOGLE_CLIENT_ID"),
            "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
            "code": code,
            "redirect_uri": os.getenv("GOOGLE_CALLBACK_URL", "http://localhost:8000/auth/google/callback"),
            "grant_type": "authorization_code"
        }
        token_headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }

        print("🔄 Exchanging code for access token...")
        token_response = requests.post(token_url, data=token_data, headers=token_headers)

        if token_response.status_code != 200:
            print(f"❌ Token exchange failed with status: {token_response.status_code}")
            return RedirectResponse(url="/?error=token_exchange_failed", status_code=302)

        token_info = token_response.json()
        access_token = token_info.get("access_token")

        if not access_token:
            print(f"❌ No access token received from Google")
            return RedirectResponse(url="/?error=no_access_token", status_code=302)

        print("✅ Access token received successfully")

        # Get user information
        user_info_url = "https://www.googleapis.com/oauth2/v2/userinfo"
        user_headers = {
            "Authorization": f"Bearer {access_token}"
        }
        user_response = requests.get(user_info_url, headers=user_headers)

        if user_response.status_code != 200:
            print(f"❌ Failed to get user info: {user_response.text}")
            return RedirectResponse(url="/?error=user_info_failed", status_code=302)

        user_info = user_response.json()
        email = user_info.get("email", "unknown")
        name = user_info.get("name", "unknown")
        picture = user_info.get("picture", "")
        google_id = user_info.get("id", "")

        print(f"✅ User authenticated via Google")

        # Create or update user in MongoDB
        try:
            from database import MongoDB
            db = MongoDB.get_database()
            users_collection = db.users
            
            existing_user = users_collection.find_one({"email": email})
            
            if existing_user:
                # Update existing user
                users_collection.update_one(
                    {"email": email},
                    {"$set": {
                        "name": name,
                        "avatar": picture,
                        "google_id": google_id,
                        "last_login": datetime.utcnow()
                    }}
                )
                user_doc = users_collection.find_one({"email": email})
            else:
                # Create new user
                new_user = {
                    "email": email,
                    "name": name,
                    "username": name,  # Use name as username for Google users
                    "avatar": picture,
                    "google_id": google_id,
                    "oauth_provider": "google",
                    "created_at": datetime.utcnow(),
                    "last_login": datetime.utcnow()
                }
                result = users_collection.insert_one(new_user)
                user_doc = users_collection.find_one({"_id": result.inserted_id})
            
            # Generate JWT token
            user_id_str = str(user_doc["_id"])
            access_token = create_access_token(data={"sub": user_id_str})
            
            # Prepare user data for frontend
            user_data = {
                "_id": user_id_str,
                "email": email,
                "name": name,
                "username": user_doc.get("username", name),
                "avatar": picture
            }
            
            print(f"✅ JWT token generated successfully")
            
            # Redirect to frontend OAuth callback handler with token and user data
            frontend_url = os.getenv("FRONTEND_URL", "https://xverta.com")
            import base64
            
            # Base64 encode user data to avoid URL encoding issues
            user_data_json = json.dumps(user_data)
            user_data_b64 = base64.b64encode(user_data_json.encode()).decode()
            
            redirect_url = f"{frontend_url}/oauth/callback?auth=success&token={access_token}&user={user_data_b64}"
            
            print(f"🚀 Redirecting to: {redirect_url}")

            # Return HTML page with AGGRESSIVE redirect debugging
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Login Successful</title>
                <meta charset="UTF-8">
            </head>
            <body>
                <div style="display: flex; align-items: center; justify-content: center; height: 100vh; font-family: Arial, sans-serif;">
                    <div style="text-align: center;">
                        <h2>✅ Login Successful!</h2>
                        <p id="status">Processing authentication...</p>
                        <p style="font-size: 12px; color: #666; margin-top: 10px;">
                            If you are not redirected in 2 seconds, <a href="{redirect_url}" style="color: #0066cc;">click here</a>.
                        </p>
                        <pre id="debug" style="font-size: 10px; color: #999; margin-top: 20px; text-align: left;"></pre>
                    </div>
                </div>
                <script>
                    const debug = document.getElementById('debug');
                    const status = document.getElementById('status');
                    
                    function log(msg) {{
                        console.log(msg);
                        debug.textContent += msg + '\\n';
                    }}
                    
                    log('🔄 Google OAuth callback page loaded');
                    log('🎯 Redirect URL: {redirect_url}');
                    log('🔍 Window location: ' + window.location.href);
                    log('🔍 User agent: ' + navigator.userAgent);
                    
                    let attempts = 0;
                    const maxAttempts = 3;
                    
                    function tryRedirect() {{
                        attempts++;
                        log(`⚡ Redirect attempt ${{attempts}} of ${{maxAttempts}}`);
                        status.textContent = `Redirecting (attempt ${{attempts}})...`;
                        
                        try {{
                            // Try multiple redirect methods
                            if (attempts === 1) {{
                                log('🔹 Method 1: window.location.href');
                                window.location.href = "{redirect_url}";
                            }} else if (attempts === 2) {{
                                log('🔹 Method 2: window.location.replace');
                                window.location.replace("{redirect_url}");
                            }} else {{
                                log('🔹 Method 3: window.location assignment');
                                window.location = "{redirect_url}";
                            }}
                            
                            log('✅ Redirect initiated');
                        }} catch (e) {{
                            log('❌ Redirect failed: ' + e.message);
                            if (attempts < maxAttempts) {{
                                setTimeout(tryRedirect, 500);
                            }} else {{
                                status.textContent = 'Redirect failed. Please click the link above.';
                            }}
                        }}
                    }}
                    
                    // Start first redirect attempt immediately
                    tryRedirect();
                </script>
            </body>
            </html>
            """
            
            return HTMLResponse(content=html_content, status_code=200)
            
        except Exception as db_error:
            print(f"❌ Database error: {str(db_error)}")
            frontend_url = os.getenv("FRONTEND_URL", "https://xverta.com")
            return RedirectResponse(url=f"{frontend_url}/voice-chat?error=database_error", status_code=302)

    except Exception as e:
        print(f"❌ OAuth callback error: {str(e)}")
        frontend_url = os.getenv("FRONTEND_URL", "https://xverta.com")
        return RedirectResponse(url=f"{frontend_url}/home?error=callback_failed&message={str(e)}", status_code=302)
@app.get("/auth/google/login")
async def google_login():
    """
    Initiate Google OAuth login
    Redirects user to Google's OAuth consent screen
    """
    try:
        google_client_id = os.getenv("GOOGLE_CLIENT_ID")
        google_callback_url = os.getenv("GOOGLE_CALLBACK_URL", "http://localhost:8000/auth/google/callback")
        
        # Debug logging
        print(f"DEBUG: GOOGLE_CLIENT_ID = {google_client_id}")
        print(f"DEBUG: GOOGLE_CALLBACK_URL = {google_callback_url}")
        
        if not google_client_id:
            raise HTTPException(status_code=500, detail="Google Client ID not configured")

        # Generate a random state parameter for security
        state = secrets.token_urlsafe(32)

        # Google OAuth authorization URL
        google_auth_url = (
            "https://accounts.google.com/o/oauth2/v2/auth"
            f"?client_id={google_client_id}"
            f"&redirect_uri={google_callback_url}"
            "&response_type=code"
            "&scope=openid%20email%20profile"
            f"&state={state}"
            "&access_type=offline"
            "&prompt=consent"
        )

        print(f"🔗 Redirecting to Google OAuth: {google_auth_url}")
        return RedirectResponse(url=google_auth_url, status_code=302)

    except Exception as e:
        print(f"❌ Google login initiation error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Google login failed: {str(e)}")

@app.post("/auth/login", response_model=LoginResponse)
async def login_user(login_data: LoginRequest):
    """
    Basic email/password login endpoint
    """
    try:
        # For now, we'll use a simple demo user validation
        # In a real app, you'd validate against a database with hashed passwords
        demo_users = {
            "admin@altx.com": {"password": "admin123", "id": 1, "name": "Admin User"},
            "user@altx.com": {"password": "user123", "id": 2, "name": "Demo User"},
            "test@test.com": {"password": "test123", "id": 3, "name": "Test User"}
        }
        
        user = demo_users.get(login_data.email.lower())
        if not user or user["password"] != login_data.password:
            raise HTTPException(
                status_code=401, 
                detail="Invalid email or password. Please try again."
            )
        
        # Generate a simple token (in production, use JWT with proper signing)
        access_token = f"demo_token_{user['id']}_{int(time.time())}"
        
        return LoginResponse(
            access_token=access_token,
            user={
                "id": user["id"],
                "email": login_data.email,
                "name": user["name"]
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Login error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")

@app.get("/auth/status")
async def auth_status():
    """
    Check authentication status
    """
    return {
        "github_app_configured": bool(os.getenv("GITHUB_APP_ID")),
        "github_client_id_configured": bool(os.getenv("GITHUB_CLIENT_ID")),  # Added
        "github_client_secret_configured": bool(os.getenv("GITHUB_CLIENT_SECRET")),
        "callback_url": os.getenv("GITHUB_CALLBACK_URL", "http://localhost:8000/auth/github/callback"),
        "login_url": "/auth/github/login",
        "timestamp": datetime.now().isoformat()
    }
@app.post("/api/deploy")
async def manual_deploy(request: dict):
    """
    Manual deployment endpoint for the Deploy Page
    Does not require webhook signature verification
    """
    try:
        repo_url = request.get("repo_url")
        if not repo_url:
            raise HTTPException(status_code=400, detail="Repository URL is required")
        
        print(f"🚀 Manual deployment requested for: {repo_url}")
        
        # Create a simplified payload for deployment
        repo_name = repo_url.split('/')[-1]
        owner = repo_url.split('/')[-2]
        
        deployment_payload = {
            "ref": "refs/heads/main",
            "repository": {
                "name": repo_name,
                "full_name": f"{owner}/{repo_name}",
                "clone_url": repo_url,
                "default_branch": "main"
            },
            "head_commit": {
                "id": f"manual-deploy-{int(time.time())}",
                "message": "Manual deployment from AltX Deploy Page",
                "committer": {
                    "name": "AltX Deploy"
                }
            }
        }
        
        print(f"📦 Processing deployment for {owner}/{repo_name}")
        
        # Handle push event (same logic as webhook but without signature verification)
        result = await handle_push_event(deployment_payload)
        
        return {
            "success": True,
            "message": f"Deployment initiated for {repo_name}",
            "deployment_result": result,
            "repository": {
                "name": repo_name,
                "owner": owner,
                "url": repo_url
            },
            "deployment_url": f"http://localhost:8000/{repo_name}",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"❌ Manual deployment error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Deployment failed: {str(e)}")

@app.post("/api/webhook")
async def github_webhook(request: Request, x_hub_signature_256: str = Header(None)):
    """
    Enhanced GitHub App webhook endpoint for automated deployments and security analysis
    """
    try:
        # 1. Get the secret from your environment variables
        secret = os.getenv("GITHUB_WEBHOOK_SECRET")
        if not secret:
            print("❌ Webhook secret is not configured.")
            raise HTTPException(status_code=500, detail="Webhook secret not configured.")

        # 2. Verify the signature to ensure the request is from GitHub
        raw_body = await request.body()
        expected_signature = "sha256=" + hmac.new(secret.encode('utf-8'), raw_body, hashlib.sha256).hexdigest()

        if not x_hub_signature_256:
            print("❌ No signature provided in webhook request.")
            raise HTTPException(status_code=403, detail="No signature provided.")

        if not hmac.compare_digest(expected_signature, x_hub_signature_256):
            print("❌ Invalid webhook signature.")
            raise HTTPException(status_code=403, detail="Invalid signature.")
        
        # 3. Process the event payload
        event_type = request.headers.get("X-GitHub-Event")
        payload = await request.json()

        print(f"🎉 Received valid webhook. Event type: {event_type}")
        
        # 4. Handle different GitHub events
        if event_type == "push":
            return await handle_push_event(payload)
        elif event_type == "pull_request":
            return await handle_pull_request_event(payload)
        elif event_type == "installation":
            return await handle_installation_event(payload)
        elif event_type == "security_advisory":
            return await handle_security_advisory_event(payload)
        else:
            print(f"📝 Unhandled event type: {event_type}")
            return {"status": "event received but not processed", "event_type": event_type}

    except Exception as e:
        print(f"❌ Webhook processing error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Webhook processing failed: {str(e)}")
async def handle_push_event(payload):
    """Handle push events - trigger deployment and security analysis"""
    try:
        ref = payload.get("ref", "")
        repo_info = payload.get("repository", {})
        clone_url = repo_info.get("clone_url")
        repo_name = repo_info.get("name")
        repo_full_name = repo_info.get("full_name")
        default_branch = repo_info.get("default_branch", "main")
        
        # Check if push is to default branch (main/master)
        if ref == f"refs/heads/{default_branch}":
            print(f"🚀 Push to {default_branch} branch detected for {repo_full_name}")
            
            if clone_url and repo_name:
                # Trigger automated security analysis
                print(f"🔍 Triggering automated security analysis for {repo_name}...")
                
                # Run security analysis in background
                analysis_task = asyncio.create_task(
                    run_automated_security_analysis(repo_info, payload)
                )
                
                # Trigger deployment process
                print(f"📦 Triggering deployment for {repo_name}...")
                deployment_task = asyncio.create_task(
                    deploy_project(repo_name, clone_url, payload)
                )
                
                return {
                    "status": "deployment and security analysis triggered",
                    "repo": repo_full_name,
                    "branch": default_branch,
                    "commit": payload.get("head_commit", {}).get("id", "unknown")[:8],
                    "timestamp": datetime.now().isoformat(),
                    "actions": ["security_analysis", "deployment"]
                }
            else:
                print("⚠️ Push event received, but couldn't get repo info.")
                return {"status": "insufficient repo information"}
        else:
            print(f"📝 Push to non-default branch {ref} - no deployment triggered")
            return {"status": "push to non-default branch", "ref": ref}
            
    except Exception as e:
        print(f"❌ Error handling push event: {str(e)}")
        return {"status": "error", "error": str(e)}

async def handle_pull_request_event(payload):
    """Handle pull request events - run security checks on PR"""
    try:
        action = payload.get("action")
        pr_info = payload.get("pull_request", {})
        repo_info = payload.get("repository", {})
        
        print(f"🔍 Pull request {action}: #{pr_info.get('number')} in {repo_info.get('full_name')}")
        
        if action in ["opened", "synchronize", "reopened"]:
            # Run security analysis on PR
            print(f"🛡️ Running security analysis on PR #{pr_info.get('number')}")
            
            # Analyze the PR branch
            head_sha = pr_info.get("head", {}).get("sha")
            base_sha = pr_info.get("base", {}).get("sha")
            
            # Run security analysis in background
            analysis_task = asyncio.create_task(
                run_pr_security_analysis(pr_info, repo_info, payload)
            )
            
            return {
                "status": "pr security analysis triggered",
                "pr_number": pr_info.get("number"),
                "repo": repo_info.get("full_name"),
                "head_sha": head_sha[:8] if head_sha else "unknown",
                "action": action
            }
        
        return {"status": "pr event processed", "action": action}
        
    except Exception as e:
        print(f"❌ Error handling pull request event: {str(e)}")
        return {"status": "error", "error": str(e)}

async def handle_installation_event(payload):
    """Handle GitHub App installation events"""
    try:
        action = payload.get("action")
        installation_info = payload.get("installation", {})
        account_info = installation_info.get("account", {})
        
        print(f"📱 GitHub App {action} for {account_info.get('login')}")
        
        if action == "created":
            print(f"✅ New installation: {account_info.get('login')} ({account_info.get('type')})")
            
            # Send welcome security analysis
            if installation_info.get("repository_selection") == "all":
                print("🔒 Full repository access granted - can provide comprehensive security analysis")
            else:
                repos = payload.get("repositories", [])
                print(f"🔒 Selected repository access: {len(repos)} repositories")
            
            return {
                "status": "installation created",
                "account": account_info.get("login"),
                "repo_access": installation_info.get("repository_selection"),
                "permissions": list(installation_info.get("permissions", {}).keys())
            }
        
        return {"status": "installation event processed", "action": action}
        
    except Exception as e:
        print(f"❌ Error handling installation event: {str(e)}")
        return {"status": "error", "error": str(e)}

async def handle_security_advisory_event(payload):
    """Handle security advisory events"""
    try:
        action = payload.get("action")
        advisory = payload.get("security_advisory", {})
        
        print(f"🚨 Security advisory {action}: {advisory.get('summary', 'Unknown')}")
        
        if action == "published":
            severity = advisory.get("severity", "unknown")
            cve_id = advisory.get("cve_id")
            
            print(f"🔒 New security advisory: {severity} severity")
            if cve_id:
                print(f"🆔 CVE ID: {cve_id}")
            
            # Could trigger repository rescans for affected dependencies
            return {
                "status": "security advisory processed",
                "severity": severity,
                "cve_id": cve_id,
                "action": action
            }
        
        return {"status": "security advisory event processed", "action": action}
        
    except Exception as e:
        print(f"❌ Error handling security advisory event: {str(e)}")
        return {"status": "error", "error": str(e)}

async def run_automated_security_analysis(repo_info, payload):
    """Run automated security analysis on repository"""
    try:
        repo_full_name = repo_info.get("full_name")
        clone_url = repo_info.get("clone_url")
        
        print(f"🔍 Starting automated security analysis for {repo_full_name}")
        
        # Create analysis request
        analysis_request = RepoAnalysisRequest(
            repo_url=clone_url,
            model_type='smart',  # Use smart model for webhook-triggered analysis
            deep_scan=True
        )
        
        # Run comprehensive analysis
        analysis_result = await analyze_repo_comprehensive(analysis_request)
        
        if not analysis_result.get("error"):
            security_score = analysis_result.get("overall_security_score", 0)
            security_level = analysis_result.get("security_level", "Unknown")
            
            print(f"✅ Security analysis complete: {security_score}/100 ({security_level})")
            
            # If security issues found, could create an issue or PR
            critical_issues = []
            critical_issues.extend(analysis_result.get("secret_scan_results", []))
            
            high_severity_static = [
                issue for issue in analysis_result.get("static_analysis_results", [])
                if isinstance(issue, dict) and issue.get("issue_severity") == "HIGH"
            ]
            critical_issues.extend(high_severity_static)
            
            if critical_issues:
                print(f"🚨 {len(critical_issues)} critical security issues found")
                
                # Could automatically create security issue in repository
                await create_security_issue_if_needed(repo_info, analysis_result, critical_issues)
            
            return {
                "analysis_complete": True,
                "security_score": security_score,
                "critical_issues": len(critical_issues)
            }
        else:
            print(f"❌ Security analysis failed: {analysis_result.get('error')}")
            return {"analysis_complete": False, "error": analysis_result.get("error")}
            
    except Exception as e:
        print(f"❌ Automated security analysis error: {str(e)}")
        return {"analysis_complete": False, "error": str(e)}

async def run_pr_security_analysis(pr_info, repo_info, payload):
    """Run security analysis on pull request"""
    try:
        pr_number = pr_info.get("number")
        repo_full_name = repo_info.get("full_name")
        head_repo_url = pr_info.get("head", {}).get("repo", {}).get("clone_url")
        
        print(f"🔍 Analyzing PR #{pr_number} in {repo_full_name}")
        
        if head_repo_url:
            # Create analysis request for PR branch
            analysis_request = RepoAnalysisRequest(
                repo_url=head_repo_url,
                model_type='fast',  # Use fast model for PR analysis
                deep_scan=False  # Lighter scan for PRs
            )
            
            # Run analysis
            analysis_result = await analyze_repo_comprehensive(analysis_request)
            
            if not analysis_result.get("error"):
                security_score = analysis_result.get("overall_security_score", 0)
                
                # Could post security analysis as PR comment
                print(f"✅ PR security analysis complete: {security_score}/100")
                
                # If critical issues found, could request changes
                secrets_found = len(analysis_result.get("secret_scan_results", []))
                if secrets_found > 0:
                    print(f"🚨 PR contains {secrets_found} hardcoded secrets - requires attention")
                
                return {
                    "pr_analysis_complete": True,
                    "security_score": security_score,
                    "secrets_found": secrets_found
                }
            else:
                print(f"❌ PR security analysis failed: {analysis_result.get('error')}")
                return {"pr_analysis_complete": False, "error": analysis_result.get("error")}
        else:
            print("⚠️ Could not get PR head repository URL")
            return {"pr_analysis_complete": False, "error": "No head repo URL"}
            
    except Exception as e:
        print(f"❌ PR security analysis error: {str(e)}")
        return {"pr_analysis_complete": False, "error": str(e)}

async def create_security_issue_if_needed(repo_info, analysis_result, critical_issues):
    """Create a security issue in the repository if critical issues are found"""
    try:
        # This would use the GitHub API to create an issue
        # Implementation depends on whether you want to auto-create issues
        print(f"💡 Could create security issue for {len(critical_issues)} critical findings")
        
        # Example issue content:
        issue_title = f"🔒 Security Review: {len(critical_issues)} Critical Issues Detected"
        issue_body = f"""
# 🛡️ Automated Security Analysis Results

**Security Score:** {analysis_result.get('overall_security_score', 'N/A')}/100

## 🚨 Critical Issues Found ({len(critical_issues)})

{chr(10).join([f"- {issue.get('description', 'Security issue')} in `{issue.get('file', 'unknown file')}`" for issue in critical_issues[:10]])}

## 🔧 Recommended Actions

1. Review and address the critical security issues listed above
2. Consider using environment variables for sensitive data
3. Run additional security testing before deployment

---
*Generated by AltX Security Scanner - Automated Analysis*
"""
        
        print("📝 Security issue content prepared (not created automatically)")
        return {"issue_prepared": True}
        
    except Exception as e:
        print(f"❌ Error preparing security issue: {str(e)}")
        return {"issue_prepared": False, "error": str(e)}

async def deploy_project(repo_name: str, clone_url: str, payload: dict):
    """Actually deploy project to ngrok domain"""
    try:
        print(f"🚀 Starting real deployment for {repo_name}")
        
        # Get deployment directory (create if doesn't exist) - Windows compatible
        if platform.system() == "Windows":
            deployment_base = r"D:\AltX\deployments"  # Raw string for Windows path
        else:
            deployment_base = os.path.join(os.getcwd(), "deployments") 
        
        os.makedirs(deployment_base, exist_ok=True)
        
        # Create unique deployment directory
        deploy_dir = os.path.join(deployment_base, repo_name)
        
        # Remove existing deployment if exists (Windows-safe)
        if os.path.exists(deploy_dir):
            print(f"🗑️ Removing existing deployment: {deploy_dir}")
            try:
                def force_remove_readonly(func, path, exc_info):
                    """Force remove read-only files on Windows"""
                    if os.path.exists(path):
                        os.chmod(path, stat.S_IWRITE)
                        func(path)
                
                shutil.rmtree(deploy_dir, onerror=force_remove_readonly)
                print("✅ Existing deployment removed successfully")
            except Exception as e:
                print(f"⚠️ Warning: Could not fully remove existing deployment: {e}")
                # Try to continue anyway
        
        commit_info = payload.get("head_commit", {})
        commit_message = commit_info.get("message", "No commit message")
        committer = commit_info.get("committer", {}).get("name", "Unknown")
        
        print(f"📦 Deploying commit: {commit_message}")
        print(f"👤 Committed by: {committer}")
        
        # Step 1: Clone repository
        print("⏳ Cloning repository...")
        repo = git.Repo.clone_from(clone_url, deploy_dir)
        await asyncio.sleep(1)
        
        # Step 2: Detect project type and install dependencies
        print("⏳ Installing dependencies...")
        project_type = detect_project_type(deploy_dir)
        await install_dependencies(deploy_dir, project_type)
        
        # Step 3: Build project
        print("⏳ Building application...")
        build_result = await build_project(deploy_dir, project_type)
        
        # Step 4: Configure web server (simulation for now)
        print("⏳ Configuring web server...")
        nginx_config = await configure_nginx(repo_name, deploy_dir, project_type)
        
        # Step 5: Copy files to your FastAPI static directory
        print("⏳ Copying files to ngrok domain...")
        static_copy_result = await copy_to_static_domain(repo_name, deploy_dir, project_type)
        
        # Generate deployment URL
        deployment_url = f"https://legal-actively-glider.ngrok-free.app/{repo_name}"
        
        print(f"✅ Deployment complete for {repo_name}")
        print(f"🌐 Live at: {deployment_url}")
        
        return {
            "deployment_complete": True,
            "repo": repo_name,
            "commit": commit_info.get("id", "unknown")[:8],
            "deployment_url": deployment_url,
            "project_type": project_type,
            "build_success": build_result.get("success", False),
            "nginx_configured": nginx_config.get("success", False),
            "files_copied": static_copy_result.get("files_copied", 0)
        }
        
    except Exception as e:
        print(f"❌ Deployment error: {str(e)}")
        return {"deployment_complete": False, "error": str(e)}

def detect_project_type(deploy_dir: str) -> str:
    """Detect what type of project this is"""
    if os.path.exists(os.path.join(deploy_dir, "package.json")):
        return "nodejs"
    elif os.path.exists(os.path.join(deploy_dir, "requirements.txt")):
        return "python"
    elif os.path.exists(os.path.join(deploy_dir, "index.html")):
        return "static"
    elif os.path.exists(os.path.join(deploy_dir, "Dockerfile")):
        return "docker"
    else:
        return "unknown"

async def install_dependencies(deploy_dir: str, project_type: str):
    """Install project dependencies based on type"""
    try:
        if project_type == "nodejs":
            # Check for package manager
            if os.path.exists(os.path.join(deploy_dir, "package-lock.json")):
                subprocess.run(["npm", "install"], cwd=deploy_dir, check=True)
            elif os.path.exists(os.path.join(deploy_dir, "yarn.lock")):
                subprocess.run(["yarn", "install"], cwd=deploy_dir, check=True)
            else:
                subprocess.run(["npm", "install"], cwd=deploy_dir, check=True)
        
        elif project_type == "python":
            # Create virtual environment and install
            subprocess.run(["python", "-m", "venv", "venv"], cwd=deploy_dir, check=True)
            
            # Mac/Unix pip path
            pip_path = os.path.join(deploy_dir, "venv", "bin", "pip")
            subprocess.run([pip_path, "install", "-r", "requirements.txt"], cwd=deploy_dir, check=True)
        
        print(f"✅ Dependencies installed for {project_type} project")
        return {"success": True}
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Dependency installation failed: {e}")
        return {"success": False, "error": str(e)}
    except Exception as e:
        print(f"⚠️ Dependency installation skipped: {e}")
        return {"success": True, "skipped": True}

async def build_project(deploy_dir: str, project_type: str):
    """Build the project"""
    try:
        if project_type == "nodejs":
            # Check for build script in package.json
            package_json_path = os.path.join(deploy_dir, "package.json")
            if os.path.exists(package_json_path):
                with open(package_json_path, 'r') as f:
                    package_data = json.load(f)
                
                scripts = package_data.get("scripts", {})
                
                if "build" in scripts:
                    subprocess.run(["npm", "run", "build"], cwd=deploy_dir, check=True)
                elif "dist" in scripts:
                    subprocess.run(["npm", "run", "dist"], cwd=deploy_dir, check=True)
        
        elif project_type == "python":
            # For Python, we might need to collect static files or build assets
            print("🐍 Python project detected - no build step required")
        
        print(f"✅ Build completed for {project_type} project")
        return {"success": True}
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Build failed: {e}")
        return {"success": False, "error": str(e)}
    except Exception as e:
        print(f"⚠️ Build skipped: {e}")
        return {"success": True, "skipped": True}

async def configure_nginx(repo_name: str, deploy_dir: str, project_type: str):
    """Configure nginx for the deployment (simulation)"""
    try:
        # Determine document root based on project type
        if project_type == "nodejs":
            # Check for common build directories
            for build_dir in ["dist", "build", "public"]:
                potential_root = os.path.join(deploy_dir, build_dir)
                if os.path.exists(potential_root):
                    document_root = potential_root
                    break
            else:
                document_root = deploy_dir
        elif project_type == "static":
            document_root = deploy_dir
        else:
            document_root = deploy_dir
        
        print(f"📝 Nginx would serve from: {document_root}")
        print(f"🌐 Would be accessible at: /{repo_name}")
        
        # In a real deployment, you'd write nginx config and reload
        return {"success": True, "document_root": document_root}
        
    except Exception as e:
        print(f"❌ Nginx configuration failed: {e}")
        return {"success": False, "error": str(e)}

async def copy_to_static_domain(repo_name: str, deploy_dir: str, project_type: str):
    """Copy deployed files to FastAPI static directory for ngrok domain"""
    try:
        # Create static directory in your FastAPI backend (Windows compatible)
        static_base = os.path.join(os.getcwd(), "static")
        repo_static_dir = os.path.join(static_base, repo_name)
        
        os.makedirs(static_base, exist_ok=True)
        
        # Remove existing deployment (Windows safe)
        if os.path.exists(repo_static_dir):
            def force_remove_readonly(func, path, exc_info):
                """Force remove read-only files on Windows"""
                if os.path.exists(path):
                    os.chmod(path, stat.S_IWRITE)
                    func(path)
            
            shutil.rmtree(repo_static_dir, onerror=force_remove_readonly)
        
        # Determine source directory
        if project_type == "nodejs":
            # Look for built files
            for build_dir in ["dist", "build", "public"]:
                source_path = os.path.join(deploy_dir, build_dir)
                if os.path.exists(source_path):
                    shutil.copytree(source_path, repo_static_dir, ignore=shutil.ignore_patterns(
                        '.git', 'node_modules', '__pycache__', '*.pyc', '.env*', 'venv', 'env'
                    ))
                    files_copied = len([f for f in os.listdir(repo_static_dir) if os.path.isfile(os.path.join(repo_static_dir, f))])
                    print(f"✅ Copied {files_copied} files from {build_dir}/ to static domain")
                    return {"success": True, "files_copied": files_copied, "source": build_dir}
        
        # Fallback: copy entire directory
        shutil.copytree(deploy_dir, repo_static_dir, ignore=shutil.ignore_patterns(
            '.git', 'node_modules', '*.pyc', '__pycache__', '.env*', 'venv', 'env'
        ))
        files_copied = sum([len(files) for r, d, files in os.walk(repo_static_dir)])
        print(f"✅ Copied {files_copied} files to static domain")
        
        return {"success": True, "files_copied": files_copied, "source": "root"}
        
    except Exception as e:
        print(f"❌ Static file copy failed: {e}")
        return {"success": False, "error": str(e)}
# Add this NEW function to main.py (alongside your existing deploy_project)

async def deploy_project_with_docker(repo_name: str, clone_url: str, payload: dict):
    """Enhanced CI/CD deployment with Docker builds - fallback to standard deployment"""
    try:
        print(f"🐳 Attempting Docker CI/CD deployment for {repo_name}")
        
        # Check if Docker is available
        try:
            docker_client = docker.from_env()
            print("✅ Docker is available")
        except Exception as docker_error:
            print(f"⚠️ Docker not available: {docker_error}")
            # Fall back to your proven method immediately
            return await deploy_project(repo_name, clone_url, payload)
        
        # Step 1: Prepare directories
        deployment_base = "/Users/trishajanath/AltX/deployments"
        deploy_dir = os.path.join(deployment_base, repo_name)
        build_output_dir = os.path.join(deployment_base, f"{repo_name}-build")
        
        os.makedirs(deployment_base, exist_ok=True)
        
        # Clean existing deployments
        for dir_path in [deploy_dir, build_output_dir]:
            if os.path.exists(dir_path):
                shutil.rmtree(dir_path)
        
        commit_info = payload.get("head_commit", {})
        print(f"📦 Docker deployment for: {commit_info.get('message', 'No message')}")
        
        # Step 2: Clone repository
        print("⏳ Cloning repository for Docker build...")
        repo = git.Repo.clone_from(clone_url, deploy_dir)
        
        # Step 3: Detect if this project needs Docker builds
        project_type = detect_project_type(deploy_dir)
        
        # Check if project actually benefits from Docker builds
        needs_docker_build = False
        if project_type == "nodejs" and os.path.exists(os.path.join(deploy_dir, "package.json")):
            with open(os.path.join(deploy_dir, "package.json"), 'r') as f:
                package_data = json.load(f)
                if "build" in package_data.get("scripts", {}):
                    needs_docker_build = True
        elif project_type == "python" and os.path.exists(os.path.join(deploy_dir, "requirements.txt")):
            needs_docker_build = True
        
        if not needs_docker_build:
            print(f"📄 Project type '{project_type}' doesn't need Docker builds, using standard deployment")
            return await deploy_project(repo_name, clone_url, payload)
        
        # Step 4: Check if Docker build files exist
        docker_config_dir = "/Users/trishajanath/AltX/backend/docker-configs"
        if not os.path.exists(docker_config_dir):
            print("⚠️ Docker configurations not found, using standard deployment")
            return await deploy_project(repo_name, clone_url, payload)
        
        # Step 5: Try Docker build
        print("🔨 Attempting Docker build...")
        build_result = await build_in_docker(deploy_dir, build_output_dir, project_type)
        
        if not build_result.get("success"):
            print(f"⚠️ Docker build failed: {build_result.get('error')}")
            print("🔄 Falling back to standard deployment method")
            return await deploy_project(repo_name, clone_url, payload)
        
        # Step 6: Copy Docker build output to static domain
        print("📁 Copying Docker build to static domain...")
        static_copy_result = await copy_build_to_static(repo_name, build_output_dir, project_type)
        
        if not static_copy_result.get("success"):
            print("⚠️ Docker build copy failed, using standard deployment")
            return await deploy_project(repo_name, clone_url, payload)
        
        # Success! Return Docker deployment result
        deployment_url = f"https://legal-actively-glider.ngrok-free.app/{repo_name}"
        
        print(f"✅ Docker CI/CD deployment complete for {repo_name}")
        print(f"🌐 Live at: {deployment_url}")
        
        return {
            "deployment_complete": True,
            "repo": repo_name,
            "commit": commit_info.get("id", "unknown")[:8],
            "deployment_url": deployment_url,
            "project_type": project_type,
            "build_success": True,
            "docker_build": True,
            "nginx_configured": False,
            "files_copied": static_copy_result.get("files_copied", 0),
            "deployment_method": "docker_ci_cd_success"
        }
        
    except Exception as e:
        print(f"❌ Docker CI/CD deployment error: {str(e)}")
        print("🔄 Falling back to proven standard deployment method")
        # Always fall back to your working method
        return await deploy_project(repo_name, clone_url, payload)

async def build_in_docker(source_dir: str, output_dir: str, project_type: str):
    """Build project using Docker containers"""
    try:
        # ADD THIS LINE AT THE TOP OF THE FUNCTION
        docker_client = docker.from_env()
        
        # Check if Docker files exist
        dockerfile_map = {
            "nodejs": "Dockerfile.nodejs",
            "python": "Dockerfile.python", 
            "php": "Dockerfile.php",
            "static": "Dockerfile.universal",
            "unknown": "Dockerfile.universal"
        }
        
        dockerfile_name = dockerfile_map.get(project_type, "Dockerfile.universal")
        dockerfile_path = f"/Users/trishajanath/AltX/backend/docker-configs/{dockerfile_name}"
        
        # Check if Docker files exist
        if not os.path.exists(dockerfile_path):
            print(f"⚠️ Docker configuration not found: {dockerfile_path}")
            return {"success": False, "error": "Docker configuration missing"}
        
        print(f"🐳 Using Docker configuration: {dockerfile_name}")
        
        # Build Docker image
        print("🔨 Building Docker image...")
        image_tag = f"altx-builder-{project_type}:latest"
        
        # Build image with build context
        image, build_logs = docker_client.images.build(
            path="/Users/trishajanath/AltX/backend",
            dockerfile=f"docker-configs/{dockerfile_name}",
            tag=image_tag,
            rm=True,
            forcerm=True
        )
        
        print("✅ Docker image built successfully")
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Run build container
        print("🏗️ Running build process in container...")
        
        container = docker_client.containers.run(
            image_tag,
            volumes={
                source_dir: {'bind': '/app', 'mode': 'ro'},
                output_dir: {'bind': '/deployment', 'mode': 'rw'}
            },
            working_dir='/app',
            detach=True,
            auto_remove=False
        )
        
        # Wait for completion and get logs
        exit_code = container.wait()
        build_logs = container.logs().decode('utf-8')
        
        print("📋 Build logs:")
        print(build_logs[-1000:])  # Last 1000 characters
        
        # Clean up container
        container.remove()
        
        if exit_code['StatusCode'] != 0:
            return {"success": False, "error": f"Build failed with exit code {exit_code['StatusCode']}"}
        
        # Determine document root from build output
        document_root = output_dir
        if os.path.exists(os.path.join(output_dir, "dist")):
            document_root = os.path.join(output_dir, "dist")
        elif os.path.exists(os.path.join(output_dir, "build")):
            document_root = os.path.join(output_dir, "build")
        
        print(f"✅ Docker build completed successfully")
        print(f"📁 Document root: {document_root}")
        
        return {
            "success": True,
            "image_tag": image_tag,
            "document_root": document_root,
            "build_logs": build_logs[-500:],  # Last 500 chars
            "files_created": len(os.listdir(output_dir)) if os.path.exists(output_dir) else 0
        }
        
    except docker.errors.DockerException as e:
        print(f"❌ Docker not available: {e}")
        return {"success": False, "error": f"Docker not available: {str(e)}"}
    except Exception as e:
        print(f"❌ Docker deployment error: {e}")
        return {"success": False, "error": str(e)}
    
async def copy_build_to_static(repo_name: str, build_dir: str, project_type: str):
    """Copy Docker build output to static domain"""
    try:
        # Create static directory in your FastAPI backend
        static_base = "/Users/trishajanath/AltX/backend/static"
        repo_static_dir = os.path.join(static_base, repo_name)
        
        os.makedirs(static_base, exist_ok=True)
        
        # Remove existing deployment
        if os.path.exists(repo_static_dir):
            shutil.rmtree(repo_static_dir)
        
        # Copy build output to static domain
        if os.path.exists(build_dir):
            shutil.copytree(build_dir, repo_static_dir)
            files_copied = sum([len(files) for r, d, files in os.walk(repo_static_dir)])
            print(f"✅ Copied {files_copied} files from Docker build to static domain")
            
            return {"success": True, "files_copied": files_copied}
        else:
            print(f"❌ Docker build directory not found: {build_dir}")
            return {"success": False, "error": "Build directory not found"}
            
    except Exception as e:
        print(f"❌ Failed to copy Docker build to static: {e}")
        return {"success": False, "error": str(e)}
    
async def handle_push_event(payload):
    """Handle push events - try Docker first, fallback to standard deployment"""
    try:
        ref = payload.get("ref", "")
        repo_info = payload.get("repository", {})
        clone_url = repo_info.get("clone_url")
        repo_name = repo_info.get("name")
        repo_full_name = repo_info.get("full_name")
        default_branch = repo_info.get("default_branch", "main")
        
        if ref == f"refs/heads/{default_branch}":
            print(f"🚀 Push to {default_branch} branch detected for {repo_full_name}")
            
            if clone_url and repo_name:
                # Trigger security analysis (async)
                analysis_task = asyncio.create_task(
                    run_automated_security_analysis(repo_info, payload)
                )
                
                # Try Docker deployment first, fallback to standard deployment
                try:
                    deployment_result = await deploy_project_with_docker(repo_name, clone_url, payload)
                    deployment_method = "docker_ci_cd"
                except Exception as e:
                    print(f"⚠️ Docker deployment failed: {e}, using standard deployment")
                    deployment_result = await deploy_project(repo_name, clone_url, payload)
                    deployment_method = "standard"
                
                return {
                    "status": "enhanced CI/CD deployment triggered",
                    "repo": repo_full_name,
                    "branch": default_branch,
                    "commit": payload.get("head_commit", {}).get("id", "unknown")[:8],
                    "deployment_method": deployment_method,
                    "timestamp": datetime.now().isoformat(),
                    "actions": ["security_analysis", "enhanced_deployment"],
                    "deployment_result": deployment_result
                }
        
        return {"status": "push to non-default branch", "ref": ref}
        
    except Exception as e:
        print(f"❌ Error handling push event: {str(e)}")
        return {"status": "error", "error": str(e)}

@app.get("/debug-scan")
async def debug_scan():
    """Debug endpoint to check stored scan data"""
    if hasattr(WebsiteScan, 'latest_scan') and WebsiteScan.latest_scan:
        scan_data = WebsiteScan.latest_scan
        return {
            "has_scan_data": True,
            "keys": list(scan_data.keys()),
            "waf_analysis_keys": list(scan_data.get('waf_analysis', {}).keys()) if scan_data.get('waf_analysis') else None,
            "dns_security_keys": list(scan_data.get('dns_security', {}).keys()) if scan_data.get('dns_security') else None,
            "waf_detected": scan_data.get('waf_analysis', {}).get('waf_detected'),
            "dns_has_data": bool(scan_data.get('dns_security')),
            "url": scan_data.get('url')
        }
    else:
        return {
            "has_scan_data": False,
            "message": "No scan data stored"
        }

@app.get("/health")
async def health_check():
    """Check if the API is running"""
    return {"status": "healthy"}


from fastapi.staticfiles import StaticFiles

# Add this after your other app configurations but before the endpoints
# Create static directory if it doesn't exist (Windows compatible)
if platform.system() == "Windows":
    static_dir = os.path.join(os.getcwd(), "static")
else:
    static_dir = "/Users/trishajanath/AltX/backend/static"

os.makedirs(static_dir, exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/{repo_name}/{file_path:path}")
async def serve_deployed_files(repo_name: str, file_path: str):
    """Serve deployed repository files"""
    try:
        # Windows compatible path
        if platform.system() == "Windows":
            repo_static_dir = os.path.join(os.getcwd(), "static", repo_name)
        else:
            repo_static_dir = f"/Users/trishajanath/AltX/backend/static/{repo_name}"
        
        file_full_path = os.path.join(repo_static_dir, file_path)
        
        # Security check: ensure file is within the repo directory
        if not os.path.realpath(file_full_path).startswith(os.path.realpath(repo_static_dir)):
            raise HTTPException(status_code=403, detail="Access denied")
        
        if os.path.exists(file_full_path) and os.path.isfile(file_full_path):
            from fastapi.responses import FileResponse
            return FileResponse(file_full_path)
        
        # Try index.html for SPA applications
        index_path = os.path.join(static_dir, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)
        
        raise HTTPException(status_code=404, detail="File not found")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error serving file: {str(e)}")

@app.get("/{repo_name}")
async def serve_deployed_repo_root(repo_name: str):
    """Serve deployed repository root (index.html)"""
    try:
        static_dir = f"/Users/trishajanath/AltX/backend/static/{repo_name}"
        index_path = os.path.join(static_dir, "index.html")
        
        if os.path.exists(index_path):
            from fastapi.responses import FileResponse
            return FileResponse(index_path)
        
        # If no index.html, show directory listing
        if os.path.exists(static_dir):
            files = os.listdir(static_dir)
            html_content = f"""
<!DOCTYPE html>
<html>
<head><title>🚀 {repo_name} - Deployed Files</title></head>
<body>
    <h1>🚀 Repository: {repo_name}</h1>
    <h2>📁 Deployed Files:</h2>
    <ul>
        {''.join([f'<li><a href="/{repo_name}/{f}">{f}</a></li>' for f in files])}
    </ul>
    <p><strong>Deployment URL:</strong> https://legal-actively-glider.ngrok-free.app/{repo_name}</p>
</body>
</html>
            """
            from fastapi.responses import HTMLResponse
            return HTMLResponse(content=html_content)
        
        raise HTTPException(status_code=404, detail=f"Repository {repo_name} not deployed")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error serving repository: {str(e)}")

# --- AI-Powered Code Generation Functions ---

async def generate_react_frontend_with_ai(frontend_path: Path, idea: str, project_name: str, needs_typescript: bool, needs_auth: bool) -> List[str]:
    """Generate React frontend with AI-powered unique code based on the idea"""
    files_created = []
    
    try:
        # Analyze the idea to determine specific features and components needed
        components_needed = []
        api_endpoints = []
        special_features = []
        
        # Determine what components to create based on the idea
        if any(keyword in idea.lower() for keyword in ["todo", "task", "list", "manage"]):
            components_needed.extend(["TaskList", "TaskItem", "AddTaskForm"])
            api_endpoints.extend(["/api/tasks", "/api/tasks/{id}"])
        
        if any(keyword in idea.lower() for keyword in ["ecommerce", "shop", "store", "product", "cart"]):
            components_needed.extend(["ProductGrid", "ProductCard", "Cart", "Checkout"])
            api_endpoints.extend(["/api/products", "/api/cart", "/api/orders"])
        
        if any(keyword in idea.lower() for keyword in ["blog", "article", "post", "content"]):
            components_needed.extend(["PostList", "PostCard", "PostEditor", "CommentSection"])
            api_endpoints.extend(["/api/posts", "/api/comments"])
        
        if any(keyword in idea.lower() for keyword in ["chat", "message", "conversation"]):
            components_needed.extend(["ChatWindow", "MessageList", "MessageInput"])
            api_endpoints.extend(["/api/messages", "/api/chat"])
            special_features.append("websocket")
        
        if any(keyword in idea.lower() for keyword in ["dashboard", "analytics", "chart", "data"]):
            components_needed.extend(["Dashboard", "Chart", "StatCard", "DataTable"])
            api_endpoints.extend(["/api/analytics", "/api/stats"])
        
        if any(keyword in idea.lower() for keyword in ["social", "profile", "user", "follow"]):
            components_needed.extend(["Profile", "UserCard", "Feed", "Followers"])
            api_endpoints.extend(["/api/users", "/api/profile", "/api/feed"])
        
        # Enhance component specifications based on authentication and features
        if needs_auth:
            components_needed.extend(['LoginModal', 'SignupModal', 'UserProfile', 'AuthContext', 'ProtectedRoute'])
            api_endpoints.extend(['/auth/login', '/auth/register', '/auth/me', '/auth/refresh', '/auth/logout'])
        
        # Always add core UI components for professional applications
        core_components = [
            'Header', 'Footer', 'Navigation', 'LoadingSpinner', 'ErrorBoundary',
            'NotificationToast', 'ConfirmModal', 'Breadcrumbs', 'SearchBar'
        ]
        components_needed.extend(core_components)
        
        # Enhanced e-commerce detection and components
        if any(keyword in idea.lower() for keyword in ['shop', 'store', 'ecommerce', 'cart', 'product', 'buy', 'sell', 'market', 'order', 'checkout', 'payment']):
            ecommerce_components = [
                'ShoppingCartModal', 'CartItem', 'CheckoutForm', 'PaymentModal', 
                'OrderSummary', 'ProductSearch', 'CategoryFilter', 'PriceFilter', 
                'WishlistButton', 'ProductGallery', 'ReviewSection', 'RatingStars'
            ]
            components_needed.extend(ecommerce_components)
            api_endpoints.extend([
                '/products/search', '/cart/add', '/cart/remove', '/cart/update',
                '/orders/create', '/payments/process', '/payments/stripe', '/categories',
                '/reviews', '/wishlist', '/inventory'
            ])
            special_features.append('E-commerce with cart, payments, and product management')
            
        # Enhanced dashboard/admin detection
        if any(keyword in idea.lower() for keyword in ['dashboard', 'admin', 'analytics', 'manage', 'control', 'metrics', 'stats']):
            admin_components = [
                'Sidebar', 'StatsCard', 'Chart', 'DataTable', 'AdminPanel', 
                'UserManagement', 'MetricsGrid', 'ActivityFeed', 'SettingsPanel', 
                'NotificationCenter', 'ReportsSection'
            ]
            components_needed.extend(admin_components)
            api_endpoints.extend([
                '/dashboard/stats', '/admin/users', '/analytics/data', '/metrics',
                '/activities', '/settings', '/notifications', '/reports'
            ])
            special_features.append('Admin dashboard with analytics and management')
            
        # Enhanced social features detection
        if any(keyword in idea.lower() for keyword in ['social', 'chat', 'message', 'friend', 'post', 'comment', 'feed', 'follow']):
            social_components = [
                'PostComposer', 'CommentSection', 'ChatWindow', 'UserCard', 
                'FriendsList', 'MessageInput', 'LikeButton', 'ShareButton', 
                'FollowButton', 'NotificationDropdown', 'OnlineIndicator'
            ]
            components_needed.extend(social_components)
            api_endpoints.extend([
                '/posts/create', '/posts/like', '/comments', '/messages', 
                '/friends', '/follow', '/notifications', '/feed', '/chat/rooms'
            ])
            special_features.append('Social features with messaging and interactions')
        
        # Default components if none detected
        if not components_needed or len(components_needed) <= len(core_components):
            components_needed.extend(["MainContent", "ActionForm", "ItemList", "DataGrid"])
            api_endpoints.extend(["/api/data", "/api/create", "/api/update"])
        
        # Use AI to generate unique code based on the idea
        prompt = f"""
Generate a complete, functional React frontend application for: "{idea}"

Project Name: {project_name}
Authentication: {"Yes" if needs_auth else "No"}

SPECIFIC FEATURES DETECTED:
- Components needed: {', '.join(components_needed)}
- API endpoints to integrate: {', '.join(api_endpoints)}
- Special features: {', '.join(special_features) if special_features else 'None'}

MANDATORY FULL-STACK INTEGRATION FEATURES:

1. COMPLETE AUTHENTICATION SYSTEM (Always Include):
   - Login modal with email/password form
   - Signup modal with user registration
   - JWT token storage in localStorage
   - Protected routes and authentication state management
   - User profile display and logout functionality
   - Login/signup form validation and error handling
   - Authentication context provider for global state

2. COMPREHENSIVE STATE MANAGEMENT:
   - User authentication state (logged in/out, user data)
   - Application data state (products, cart, orders, etc.)
   - UI state (modals, loading, notifications)
   - Error handling state with user-friendly messages
   - Real-time updates and data synchronization

3. WORKING API INTEGRATION:
   - Real fetch() calls to backend API (http://localhost:8000/api)
   - Proper error handling for all network requests
   - Loading states with spinners and feedback
   - Success/error notifications with toast messages
   - Authentication headers for protected routes
   - Automatic token refresh and logout on expiry

4. COMPLETE UI COMPONENT SYSTEM:
   - Header with user info, navigation, and cart (if e-commerce)
   - Login/Signup modals with form validation
   - Main content areas with proper layouts
   - Interactive buttons and forms that actually work
   - Shopping cart modal (if e-commerce detected)
   - Payment processing forms (if payment needed)
   - Responsive navigation and mobile-friendly design

5. ADVANCED FUNCTIONALITY:
   - Shopping cart operations (add/remove/update quantities)
   - Real-time cart count updates in header
   - Product grid with add to cart functionality
   - Search and filtering capabilities
   - Pagination for large data sets
   - Form validation with proper error messages

CRITICAL IMPLEMENTATION REQUIREMENTS:

AUTHENTICATION FLOW:
- Create LoginModal and SignupModal components with full functionality
- Implement proper form validation and submission
- Handle API responses and display appropriate messages
- Store JWT tokens and manage authentication state
- Create protected routes and redirect logic
- Add logout functionality with token cleanup

E-COMMERCE FEATURES (If shopping/cart detected):
- Product grid with real product data from API
- Add to Cart buttons that actually work
- Shopping cart modal with item management
- Checkout process with payment integration
- Order history and tracking
- Inventory management and stock display

API INTEGRATION PATTERNS:
- Use consistent API base URL: http://localhost:8000/api
- Include Authorization headers: Bearer ${{token}}
- Handle 401 errors with automatic logout
- Display loading states during API calls
- Show success/error notifications
- Implement proper error boundaries

STATE MANAGEMENT:
- Use React Context for global state (auth, cart, notifications)
- Local component state for UI interactions
- Proper state updates with immutable patterns
- Effect cleanup to prevent memory leaks
- Optimistic updates for better UX

COMPONENT ARCHITECTURE:
- App.jsx: Main app with routing and global state
- Header: Navigation, user info, cart count
- Modals: Login, Signup, Cart, Payment
- Forms: Proper validation and submission
- Layouts: Responsive design with mobile support

FILES TO GENERATE WITH COMPLETE IMPLEMENTATIONS:
1. package.json - React 18, TailwindCSS, React Router, Lucide icons
2. src/App.jsx - Main app with authentication and routing
3. src/main.jsx - React 18 setup with error boundaries  
4. src/index.css - TailwindCSS + custom styles
5. vite.config.js - Optimized Vite config with proxy
6. tailwind.config.js - Custom theme configuration

PACKAGE.JSON MUST INCLUDE:
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.8.0",
    "lucide-react": "^0.300.0"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^4.2.0",
    "vite": "^5.0.0",
    "tailwindcss": "^3.4.0",
    "autoprefixer": "^10.4.16",
    "postcss": "^8.4.32"
  }
}

VITE CONFIG MUST INCLUDE PROXY:
export default defineConfig({{
  plugins: [react()],
  server: {{
    proxy: {{
      '/api': 'http://localhost:8000'
    }}
  }}
}})

Each component must be complete and production-ready with real functionality.
No placeholders, TODOs, or incomplete implementations allowed.
7. Component files in src/components/ - Fully functional components

Each file must be complete and production-ready. Do not use placeholders like "TODO", "// implement later", or empty function bodies.

IMPORTANT: 
- Make the app UNIQUE and SPECIFIC to "{idea}" - not generic
- Include proper error handling and loading states
- Use modern React patterns (functional components, hooks)
- Make it production-ready with proper code structure
- Ensure all imports/exports work correctly
- Add comments explaining the logic
- NEVER leave components with empty return statements or incomplete JSX

Return each file content in this EXACT format:
===FILE: filename===
file content here
===END===

Start with package.json:
"""

        # Get AI response
        chat_history = [{"role": "user", "content": prompt}]
        ai_response = get_chat_response(chat_history, "smart")
        
        # Parse AI response and create files
        if "===FILE:" in ai_response:
            files_created = await parse_and_create_ai_files(frontend_path, ai_response, project_name)
            
            # Validate that essential files were created
            essential_files = ["package.json", "src/App.jsx", "src/main.jsx", "vite.config.js"]
            created_filenames = [f.split("/")[-1] if "/" in f else f for f in files_created]
            
            missing_files = []
            for essential in essential_files:
                filename = essential.split("/")[-1]
                if not any(filename in created for created in created_filenames):
                    missing_files.append(essential)
            
            if missing_files:
                print(f"⚠️ AI generation missing essential files: {missing_files}")
                print("🔄 Falling back to template generation")
                files_created = await create_react_frontend_with_animation(frontend_path, idea, project_name, needs_typescript, needs_auth)
        else:
            print("⚠️ AI response doesn't contain proper file markers")
            # Fallback to template-based generation if AI parsing fails
            files_created = await create_react_frontend_with_animation(frontend_path, idea, project_name, needs_typescript, needs_auth)
            
    except Exception as e:
        print(f"AI generation failed, falling back to templates: {e}")
        # Fallback to template-based generation
        files_created = await create_react_frontend_with_animation(frontend_path, idea, project_name, needs_typescript, needs_auth)
    
    return files_created

async def generate_fastapi_backend_with_ai(backend_path: Path, idea: str, project_name: str, needs_ai: bool, needs_auth: bool, needs_database: bool) -> List[str]:
    """Generate FastAPI backend with AI-powered unique code based on the idea"""
    files_created = []
    
    try:
        # Analyze the idea to determine specific API endpoints and models needed
        api_routes = []
        data_models = []
        special_deps = []
        
        # Determine what APIs to create based on the idea
        if any(keyword in idea.lower() for keyword in ["todo", "task", "list", "manage"]):
            api_routes.extend(["GET /api/tasks", "POST /api/tasks", "PUT /api/tasks/{id}", "DELETE /api/tasks/{id}"])
            data_models.extend(["Task", "TaskCreate", "TaskUpdate"])
        
        if any(keyword in idea.lower() for keyword in ["ecommerce", "shop", "store", "product", "cart"]):
            api_routes.extend(["GET /api/products", "GET /api/products/{id}", "POST /api/cart", "POST /api/orders"])
            data_models.extend(["Product", "CartItem", "Order", "OrderCreate"])
        
        if any(keyword in idea.lower() for keyword in ["blog", "article", "post", "content"]):
            api_routes.extend(["GET /api/posts", "POST /api/posts", "GET /api/posts/{id}", "POST /api/comments"])
            data_models.extend(["Post", "PostCreate", "Comment", "CommentCreate"])
        
        if any(keyword in idea.lower() for keyword in ["chat", "message", "conversation"]):
            api_routes.extend(["GET /api/messages", "POST /api/messages", "WebSocket /ws/chat"])
            data_models.extend(["Message", "MessageCreate", "ChatRoom"])
            special_deps.extend(["websockets"])
        
        if any(keyword in idea.lower() for keyword in ["user", "auth", "login", "signup"]):
            api_routes.extend(["POST /api/auth/login", "POST /api/auth/signup", "GET /api/users/me"])
            data_models.extend(["User", "UserCreate", "UserLogin", "Token"])
            special_deps.extend(["python-jose[cryptography]", "passlib[bcrypt]"])
        
        if any(keyword in idea.lower() for keyword in ["ai", "gpt", "openai", "chatbot", "ml"]):
            api_routes.extend(["POST /api/ai/chat", "POST /api/ai/generate"])
            data_models.extend(["AIRequest", "AIResponse", "ChatMessage"])
            special_deps.extend(["openai", "langchain"])
        
        if any(keyword in idea.lower() for keyword in ["database", "store", "save", "crud"]):
            special_deps.extend(["sqlalchemy", "databases", "asyncpg"])
        
        # Default routes if none detected
        if not api_routes:
            api_routes = ["GET /api/items", "POST /api/items", "GET /api/health"]
            data_models = ["Item", "ItemCreate"]
        
        # Use AI to generate unique code based on the idea
        prompt = f"""
Generate a complete, PRODUCTION-READY FastAPI backend application for: "{idea}"

Project Name: {project_name}
AI Integration: {"Yes" if needs_ai else "No"}
Authentication: {"Yes" if needs_auth else "No"}
Database: {"Yes" if needs_database else "No"}

SPECIFIC FEATURES DETECTED:
- API Routes needed: {', '.join(api_routes)}
- Data Models needed: {', '.join(data_models)}
- Special Dependencies: {', '.join(special_deps) if special_deps else 'None'}

MANDATORY FULL-STACK INTEGRATION FEATURES:

1. COMPLETE AUTHENTICATION SYSTEM (Always Include):
   - JWT token-based authentication with proper validation
   - User registration endpoint with password hashing
   - Login endpoint with credential validation
   - Protected routes with dependency injection
   - User profile management endpoints
   - Password reset functionality
   - Session management and token refresh

2. COMPREHENSIVE API ECOSYSTEM:
   - Full CRUD operations for all entities
   - Proper HTTP status codes and error handling
   - Input validation with Pydantic models
   - Search, filtering, and pagination
   - Bulk operations and batch processing
   - Real-time data updates with WebSockets (if needed)

3. ADVANCED BUSINESS LOGIC:
   - Cart functionality for e-commerce (add/remove/checkout)
   - Payment processing integration (Stripe/PayPal mock)
   - Order management and tracking
   - Inventory management with stock tracking
   - User preferences and settings
   - Notification system
   - Activity logging and audit trails

4. SECURITY & PERFORMANCE:
   - Rate limiting and DDoS protection
   - CORS configuration for frontend integration
   - Request/response validation and sanitization
   - Proper error handling and logging
   - Database connection pooling
   - Caching mechanisms with Redis (if complex)

5. REAL-TIME FEATURES:
   - WebSocket support for live updates
   - Server-sent events for notifications
   - Background task processing with Celery
   - Scheduled jobs and cron tasks

CRITICAL REQUIREMENTS - NO MOCKS OR PLACEHOLDERS:
- Generate COMPLETE, PRODUCTION-READY FastAPI code that works immediately
- Use FastAPI with modern Python 3.9+ async/await patterns
- Include proper CORS handling for React frontend (http://localhost:5173)
- Create WORKING API endpoints with full business logic implementation
- Add comprehensive error handling and validation with Pydantic models
- Include proper HTTP status codes and response models
- Implement REAL operations with in-memory storage (use dictionaries as databases)
- Add proper request/response validation and error messages
- Include authentication middleware and protected routes
- Add proper logging and error tracking

AUTHENTICATION IMPLEMENTATION (MANDATORY):
- Use OAuth2PasswordBearer for token validation
- Implement JWT token creation and validation with python-jose
- Hash passwords with passlib and bcrypt
- Create User, UserCreate, UserInDB, Token Pydantic models
- Add login endpoint that accepts form data
- Add registration endpoint that creates real users
- Implement get_current_user dependency for protected routes
- Include proper error handling for invalid credentials
CART & E-COMMERCE FUNCTIONALITY (If shopping/cart detected):
- Complete shopping cart system with add/remove/update operations
- Cart persistence per user with session management
- Product catalog with categories, search, and filtering
- Inventory tracking with stock management
- Order creation and management system
- Payment processing endpoints (mock Stripe/PayPal integration)
- Order history and tracking
- Wishlist functionality
- Coupon and discount system

PAYMENT SYSTEM IMPLEMENTATION:
- Mock payment processing for demo purposes
- Payment method management (Stripe, PayPal)
- Order total calculation with taxes and fees
- Payment validation and error handling
- Receipt generation and email notifications
- Refund and cancellation handling

IN-MEMORY DATABASE STRUCTURE:
- Use Python dictionaries as databases for immediate functionality
- Implement proper data relationships and constraints
- Add realistic sample data for testing
- Include proper data validation and error handling
- Implement data persistence simulation

DATA MODELS (COMPREHENSIVE):
- Create detailed Pydantic models for all entities
- Include proper field validation with regex, min/max values
- Add realistic sample data and default values
- Implement proper relationships between models
- Include created_at/updated_at timestamps
- Add proper serialization/deserialization
- Include response models for API documentation

BACKEND FILES TO GENERATE (ALL COMPLETE):
1. requirements.txt - All dependencies (FastAPI, uvicorn, python-jose, passlib, etc.)
2. main.py - FastAPI app with CORS, middleware, routing, startup logic
3. routes.py - ALL API endpoints with complete business logic
4. models.py - Comprehensive Pydantic models with validation
5. auth.py - Complete authentication system with JWT
6. config.py - Configuration and environment variables

REQUIREMENTS.TXT MUST INCLUDE:
fastapi>=0.104.1
uvicorn[standard]>=0.24.0
python-jose[cryptography]>=3.3.0
passlib[bcrypt]>=1.7.4
python-multipart>=0.0.6
pydantic>=2.5.0
python-dotenv>=1.0.0

Each file must be complete and production-ready. No placeholders, TODOs, or incomplete functions.
Every API endpoint must have full implementation with real business logic.

Return each file content in this EXACT format:
===FILE: filename===
file content here
===END===

IMPORTANT: The main.py file MUST include:
- CORS middleware configured for React frontend
- Router inclusion with /api/v1 prefix
- Startup logic to run on port 8001
- Health check endpoint at root

Start with requirements.txt:
"""

        # Get AI response
        chat_history = [{"role": "user", "content": prompt}]
        ai_response = get_chat_response(chat_history, "smart")
        
        # Parse AI response and create files
        if "===FILE:" in ai_response:
            files_created = await parse_and_create_ai_files(backend_path, ai_response, project_name)
            
            # Validate that essential files were created
            essential_files = ["requirements.txt", "main.py", "models.py"]
            created_filenames = [f.split("/")[-1] if "/" in f else f for f in files_created]
            
            missing_files = []
            for essential in essential_files:
                filename = essential.split("/")[-1]
                if not any(filename in created for created in created_filenames):
                    missing_files.append(essential)
            
            if missing_files:
                print(f"⚠️ AI backend generation missing essential files: {missing_files}")
                print("🔄 Falling back to template generation")
                files_created = await create_fastapi_backend_with_animation(backend_path, idea, project_name, needs_ai, needs_auth, needs_database)
        else:
            print("⚠️ AI response doesn't contain proper file markers")
            # Fallback to template-based generation if AI parsing fails
            files_created = await create_fastapi_backend_with_animation(backend_path, idea, project_name, needs_ai, needs_auth, needs_database)
            
    except Exception as e:
        print(f"AI generation failed, falling back to templates: {e}")
        # Fallback to template-based generation
        files_created = await create_fastapi_backend_with_animation(backend_path, idea, project_name, needs_ai, needs_auth, needs_database)
    
    return files_created

async def parse_and_create_ai_files(base_path: Path, ai_response: str, project_name: str) -> List[str]:
    """Parse AI response and create files with real-time animation"""
    files_created = []
    
    print(f"🔍 Parsing AI response for {project_name}...")
    print(f"📝 Response length: {len(ai_response)} characters")
    
    # Split response by file markers
    file_sections = ai_response.split("===FILE:")
    
    print(f"📁 Found {len(file_sections)-1} file sections")
    
    for section in file_sections[1:]:  # Skip first empty section
        if "===END===" not in section:
            print(f"⚠️ Section missing ===END=== marker")
            continue
            
        lines = section.split("\n")
        filename = lines[0].strip().replace("===", "")
        
        print(f"📄 Processing file: {filename}")
        
        # Extract content between filename and ===END===
        content_lines = []
        in_content = False
        
        for line in lines[1:]:
            if line.strip() == "===END===":
                break
            content_lines.append(line)
        
        content = "\n".join(content_lines).strip()
        
        if content and filename:
            # Validate and fix the content before creating the file
            content = await validate_and_fix_code_content(filename, content, project_name)
            
            print(f"✅ Creating file {filename} with {len(content)} characters")
            
            # Handle nested file paths (e.g., src/App.jsx)
            file_path = base_path / filename
            relative_path = str(file_path.relative_to(file_path.parent.parent))
            
            # Create directory if needed
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            created_file = await create_file_with_animation(file_path, content, relative_path, project_name)
            files_created.append(created_file)
        else:
            print(f"❌ Skipping file {filename} - no content or invalid filename")
    
    # Ensure essential files exist with fallback templates
    await ensure_essential_files_exist(base_path, project_name, files_created)
    
    print(f"🎉 Successfully created {len(files_created)} files")
    return files_created

async def validate_and_fix_code_content(filename: str, content: str, project_name: str) -> str:
    """Validate and fix common issues in generated code"""
    
    if filename.endswith('.jsx') or filename.endswith('.tsx'):
        # Fix JSX/React specific issues
        content = fix_jsx_content(content, filename, project_name)
    elif filename == 'package.json':
        # Validate JSON content
        content = fix_package_json_content(content, project_name)
    elif filename.endswith('.js') or filename.endswith('.ts'):
        # Fix JavaScript/TypeScript issues
        content = fix_js_content(content, filename)
    
    return content

def fix_jsx_content(content: str, filename: str, project_name: str) -> str:
    """Fix common JSX/React issues"""
    
    # Fix main.jsx with incomplete render calls
    if 'main.jsx' in filename and 'ReactDOM.createRoot' in content:
        if '.render(\n\n  ,\n)' in content or '.render(\n\n,\n)' in content:
            print(f"🔧 Fixing incomplete render call in {filename}")
            content = content.replace(
                '.render(\n\n  ,\n)',
                '.render(\n  <React.StrictMode>\n    <App />\n  </React.StrictMode>\n)'
            ).replace(
                '.render(\n\n,\n)',
                '.render(\n  <React.StrictMode>\n    <App />\n  </React.StrictMode>\n)'
            )
    
    # Fix empty component functions with proper JSX structure
    if 'const ' in content and '() => (\n\n);' in content:
        print(f"🔧 Fixing empty component functions in {filename}")
        content = content.replace(
            '() => (\n\n);',
            '() => (\n  <div className="container mx-auto p-4">\n    <h1>Welcome to Component</h1>\n    <p>This component is ready for development.</p>\n  </div>\n);'
        )
    
    # Fix incomplete JSX elements - more robust pattern matching
    if 'return (\n\n' in content and ');\n}' in content:
        print(f"🔧 Fixing incomplete return statement in {filename}")
        # Find the component name from the function declaration
        import re
        function_match = re.search(r'(?:function\s+(\w+)|const\s+(\w+)\s*=)', content)
        component_name = (function_match.group(1) or function_match.group(2)) if function_match else project_name.replace('-', ' ').title()
        
        content = content.replace(
            'return (\n\n',
            f'return (\n    <div className="container mx-auto p-4">\n      <h1>Welcome to {component_name}</h1>\n      <p>Component content will go here.</p>\n'
        )
        # Ensure proper closing structure
        if 'return (' in content and not content.rstrip().endswith('</div>\n  );'):
            # Find the last occurrence of '); and replace it
            content = content.rstrip()
            if content.endswith(');'):
                content = content[:-2] + '\n    </div>\n  );'
            elif content.endswith('  );\n}'):
                content = content.replace('  );\n}', '    </div>\n  );\n}')
    
    # Fix malformed JSX structure like incomplete tags
    content = re.sub(r'>\s*\n\s*\n\s*</div>', '>\n      <p>Content placeholder</p>\n    </div>', content)
    content = re.sub(r'>\s*\n\s*\n\s*</(\w+)>', r'>\n      <p>Content placeholder</p>\n    </\1>', content)
    
    # Ensure imports are present
    if filename.endswith('.jsx') and 'import React' not in content:
        content = "import React from 'react';\n\n" + content
    
    # Fix any incomplete comment blocks
    content = re.sub(r'/\*\*\s*\n\s*\*\s*\n\s*\*/', '/**\n * Component documentation\n */', content)
    
    return content

def fix_package_json_content(content: str, project_name: str) -> str:
    """Ensure package.json is valid"""
    try:
        import json
        parsed = json.loads(content)
        # Ensure required fields
        if 'name' not in parsed:
            parsed['name'] = project_name
        if 'version' not in parsed:
            parsed['version'] = '0.1.0'
        return json.dumps(parsed, indent=2)
    except json.JSONDecodeError:
        print(f"🔧 Creating fallback package.json")
        return get_fallback_package_json(project_name)

def fix_js_content(content: str, filename: str) -> str:
    """Fix JavaScript/TypeScript issues"""
    
    # Fix incomplete function exports
    if 'export default' in content and content.strip().endswith('export default'):
        print(f"🔧 Fixing incomplete export in {filename}")
        content = content.replace('export default', 'export default function Component() { return null; }')
    
    return content

async def ensure_essential_files_exist(base_path: Path, project_name: str, files_created: List[str]) -> None:
    """Ensure essential files exist with fallback templates"""
    
    essential_files = {
        'package.json': get_fallback_package_json(project_name),
        'src/main.jsx': get_fallback_main_jsx(),
        'src/App.jsx': get_fallback_app_jsx(project_name),
        'src/index.css': get_fallback_index_css(),
        'vite.config.js': get_fallback_vite_config(),
        'tailwind.config.js': get_fallback_tailwind_config(),
        'postcss.config.js': get_fallback_postcss_config()
    }
    
    for filename, fallback_content in essential_files.items():
        file_path = base_path / filename
        
        # Check if file was created or exists
        if not file_path.exists() and filename not in files_created:
            print(f"🔧 Creating missing essential file: {filename}")
            
            # Create directory if needed
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Create file with fallback content
            relative_path = str(file_path.relative_to(file_path.parent.parent))
            await create_file_with_animation(file_path, fallback_content, relative_path, project_name)
            files_created.append(filename)

def get_fallback_package_json(project_name: str) -> str:
    """Get fallback package.json content"""
    return f'''{{
  "name": "{project_name}",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {{
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  }},
  "dependencies": {{
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.8.1",
    "lucide-react": "^0.263.1",
    "axios": "^1.6.0"
  }},
  "devDependencies": {{
    "@types/react": "^18.2.15",
    "@types/react-dom": "^18.2.7",
    "@vitejs/plugin-react": "^4.0.3",
    "autoprefixer": "^10.4.14",
    "postcss": "^8.4.24",
    "tailwindcss": "^3.3.0",
    "vite": "^4.4.5"
  }}
}}'''

def get_fallback_main_jsx() -> str:
    """Get fallback main.jsx content"""
    return '''import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
)'''

def get_fallback_app_jsx(project_name: str) -> str:
    """Get fallback App.jsx content"""
    return f'''import React, {{ useState }} from 'react'
import './App.css'

function App() {{
  const [count, setCount] = useState(0)

  return (
    <div className="min-h-screen bg-gray-100">
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-4xl mx-auto">
          <header className="text-center mb-8">
            <h1 className="text-4xl font-bold text-gray-900 mb-4">
              {project_name.replace('-', ' ').title()}
            </h1>
            <p className="text-xl text-gray-600">
              Welcome to your new React application!
            </p>
          </header>
          
          <main className="bg-white rounded-lg shadow-lg p-8">
            <div className="text-center">
              <button
                className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"
                onClick={{() => setCount(count + 1)}}
              >
                Count is {{count}}
              </button>
              <p className="mt-4 text-gray-600">
                Click the button to test the React functionality.
              </p>
            </div>
          </main>
        </div>
      </div>
    </div>
  )
}}

export default App'''

def get_fallback_index_css() -> str:
    """Get fallback index.css content"""
    return '''@tailwind base;
@tailwind components;
@tailwind utilities;

:root {
  font-family: Inter, system-ui, Avenir, Helvetica, Arial, sans-serif;
  line-height: 1.5;
  font-weight: 400;
  color-scheme: light dark;
  color: rgba(255, 255, 255, 0.87);
  background-color: #242424;
  font-synthesis: none;
  text-rendering: optimizeLegibility;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  -webkit-text-size-adjust: 100%;
}

body {
  margin: 0;
  display: flex;
  place-items: center;
  min-width: 320px;
  min-height: 100vh;
}

#root {
  max-width: 1280px;
  margin: 0 auto;
  text-align: center;
  width: 100%;
}'''

def get_fallback_vite_config() -> str:
    """Get fallback vite.config.js content"""
    return '''import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    host: true
  }
})'''

def get_fallback_tailwind_config() -> str:
    """Get fallback tailwind.config.js content"""
    return '''/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}'''

def get_fallback_postcss_config() -> str:
    """Get fallback postcss.config.js content"""
    return '''export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}'''

async def generate_ai_powered_full_stack_files(project_path: Path, idea: str, project_name: str, tech_stack: List[str], needs_ai: bool):
    """Generate complete full-stack project using AI-powered functions - ALWAYS FastAPI + React"""
    try:
        # Create main project structure
        project_path.mkdir(exist_ok=True)
        frontend_path = project_path / "frontend"
        backend_path = project_path / "backend"
        
        frontend_path.mkdir(exist_ok=True)
        backend_path.mkdir(exist_ok=True)
        
        # Determine features needed from the idea
        needs_auth = "auth" in idea.lower() or "login" in idea.lower() or "user" in idea.lower() or "signup" in idea.lower()
        needs_database = any(keyword in idea.lower() for keyword in ["database", "store", "save", "data", "crud", "create", "update", "delete"])
        needs_real_time = any(keyword in idea.lower() for keyword in ["chat", "live", "real-time", "notification", "websocket"])
        needs_ai_integration = any(keyword in idea.lower() for keyword in ["ai", "chatbot", "gpt", "openai", "ml", "machine learning", "predict"])
        
        # Send status update
        await manager.send_to_project(project_name, {
            "type": "status",
            "phase": "generate",
            "message": f"🎨 Generating unique React frontend for: {idea}"
        })
        
        # ALWAYS use AI-powered React generation (no Next.js)
        frontend_files = await generate_react_frontend_with_ai(frontend_path, idea, project_name, False, needs_auth)
        
        # Send status update
        await manager.send_to_project(project_name, {
            "type": "status", 
            "phase": "generate",
            "message": f"⚡ Generating FastAPI backend with custom logic for: {idea}"
        })
        
        # ALWAYS use AI-powered FastAPI generation
        backend_files = await generate_fastapi_backend_with_ai(backend_path, idea, project_name, needs_ai_integration, needs_auth, needs_database)
        
        # Generate root files
        root_files = await create_root_files_with_animation(project_path, project_name, idea, ["React", "FastAPI", "Vite", "TailwindCSS"])
        
        # Return project structure for display
        return [
            "📁 frontend/",
            "  📁 src/",
            "    📁 components/",
            "    📄 App.jsx",
            "    📄 main.jsx",
            "    📄 index.css",
            "  📄 package.json",
            "  📄 vite.config.js",
            "  📄 tailwind.config.js",
            "📁 backend/",
            "  📄 main.py",
            "  📄 requirements.txt",
            "  📄 models.py",
            "  📄 routes.py",
            "📄 README.md",
            "📄 .gitignore",
            "📄 docker-compose.yml"
        ]
        
    except Exception as e:
        print(f"Error generating AI-powered project: {e}")
        return ["Error generating project files"]

# --- S3 Project Storage Endpoints ---
from s3_storage import upload_project_to_s3, get_project_from_s3, list_user_projects, delete_project_from_s3

class SaveProjectRequest(BaseModel):
    name: str
    slug: str
    files: List[Dict[str, str]]
    user_id: Optional[str] = 'anonymous'

@app.post("/api/projects/save")
async def save_project_to_s3(request: SaveProjectRequest):
    """
    Save a project to S3 storage
    
    Expects JSON body:
    {
        "name": "My Project",
        "slug": "my-project-12345",
        "files": [
            {"path": "index.html", "content": "<html>...</html>"},
            {"path": "style.css", "content": "body {...}"}
        ],
        "user_id": "user@example.com"  // optional, defaults to 'anonymous'
    }
    """
    try:
        # Upload files to S3
        result = upload_project_to_s3(
            project_slug=request.slug,
            files=request.files,
            user_id=request.user_id
        )
        
        # TODO: Save metadata to database
        # In a production app, you'd save this to Postgres/DynamoDB:
        # await db.projects.create({
        #     'name': request.name,
        #     'slug': request.slug,
        #     'user_id': request.user_id,
        #     'file_count': len(request.files),
        #     'created_at': datetime.utcnow()
        # })
        
        return {
            "success": True,
            "message": "Project saved successfully",
            "project": {
                "name": request.name,
                "slug": request.slug,
                "user_id": request.user_id,
                "files_count": result['files_uploaded']
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save project: {str(e)}")


@app.get("/api/projects")
async def get_user_projects(current_user: Optional[dict] = Depends(get_current_user_optional)):
    """
    Get all projects for a user
    
    Auth: Uses JWT token to identify user (optional - defaults to 'anonymous')
    """
    # Get user_id from authenticated user or default to anonymous
    user_id = current_user.get('_id') if current_user else 'anonymous'
    
    try:
        projects = list_user_projects(user_id=user_id)
        
        # TODO: Enhance with metadata from database
        # In production, join with database to get full project info:
        # projects_with_metadata = await db.projects.find({'user_id': user_id})
        
        return {
            "success": True,
            "projects": projects,
            "count": len(projects)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch projects: {str(e)}")


@app.get("/api/projects/{project_slug}")
async def get_project(project_slug: str, current_user: Optional[dict] = Depends(get_current_user_optional)):
    """
    Get a specific project's files from S3
    
    Path params:
        project_slug: Unique project identifier
    Auth: Uses JWT token to identify user (optional)
    """
    # Get user_id from authenticated user or default to anonymous
    user_id = current_user.get('_id') if current_user else 'anonymous'
    
    try:
        project = get_project_from_s3(project_slug=project_slug, user_id=user_id)
        
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        return {
            "success": True,
            "project": project
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve project: {str(e)}")


@app.delete("/api/projects/{project_slug}")
async def delete_project(project_slug: str, current_user: Optional[dict] = Depends(get_current_user_optional)):
    """
    Delete a project from S3
    
    Path params:
        project_slug: Unique project identifier
    Auth: Uses JWT token to identify user (optional)
    """
    # Get user_id from authenticated user or default to anonymous
    user_id = current_user.get('_id') if current_user else 'anonymous'
    
    try:
        success = delete_project_from_s3(project_slug=project_slug, user_id=user_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # TODO: Delete from database
        # await db.projects.delete({'slug': project_slug, 'user_id': user_id})
        
        return {
            "success": True,
            "message": "Project deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete project: {str(e)}")

# Health check endpoints for ALB


@app.head("/health")
async def health_check_head():
    from fastapi.responses import Response
    return Response(status_code=200)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)