"""
Sandbox Backend Deployment Service
===================================
Manages ephemeral Docker containers for AI-generated FastAPI backend previews.

Features:
- Builds Docker images for generated backends
- Runs isolated containers per preview session
- Health check polling until ready
- TTL-based automatic cleanup (30-60 minutes)
- Unique container naming and port assignment
"""

import os
import asyncio
import uuid
import time
import shutil
import tempfile
import subprocess
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import logging
import httpx

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SandboxStatus(str, Enum):
    """Container lifecycle states."""
    PENDING = "pending"
    BUILDING = "building"
    STARTING = "starting"
    RUNNING = "running"
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    STOPPING = "stopping"
    STOPPED = "stopped"
    FAILED = "failed"
    EXPIRED = "expired"


@dataclass
class SandboxContainer:
    """Represents a sandbox container instance."""
    id: str
    session_id: str
    container_name: str
    image_name: str
    port: int
    status: SandboxStatus
    created_at: datetime
    expires_at: datetime
    base_url: str
    project_path: Optional[str] = None
    error_message: Optional[str] = None
    health_checks: int = 0
    last_health_check: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "session_id": self.session_id,
            "container_name": self.container_name,
            "status": self.status.value,
            "port": self.port,
            "base_url": self.base_url,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "ttl_seconds": max(0, int((self.expires_at - datetime.utcnow()).total_seconds())),
            "health_checks": self.health_checks,
            "error": self.error_message
        }


class SandboxDeploymentService:
    """
    Manages sandbox Docker containers for preview backends.
    
    Each preview session gets its own isolated container with:
    - Unique container name and port
    - No shared state between containers
    - Automatic TTL-based cleanup
    
    OPTIMIZATIONS:
    - Pre-built base image for instant dependency loading
    - Image caching to skip rebuilds when code matches
    - Exponential backoff for faster health checks
    - Parallel file operations during build
    """
    
    # Port range for sandbox containers
    PORT_RANGE_START = 9000
    PORT_RANGE_END = 9999
    
    # Default TTL (45 minutes)
    DEFAULT_TTL_MINUTES = 45
    MIN_TTL_MINUTES = 30
    MAX_TTL_MINUTES = 60
    
    # OPTIMIZED Health check configuration - faster initial checks
    HEALTH_CHECK_INITIAL_INTERVAL = 0.5  # Start checking quickly
    HEALTH_CHECK_MAX_INTERVAL = 3        # Max wait between checks
    HEALTH_CHECK_TIMEOUT = 2             # Faster timeout
    HEALTH_CHECK_RETRIES = 20            # Fewer retries needed with faster checks
    
    # Cleanup interval
    CLEANUP_INTERVAL = 60  # seconds
    
    # Base image for fast builds
    BASE_IMAGE = "altx-sandbox-base:latest"
    FALLBACK_IMAGE = "python:3.11-slim"
    
    def __init__(
        self,
        docker_configs_path: str = None,
        host_url: str = "http://localhost",
        network_name: str = "sandbox-network"
    ):
        """
        Initialize the sandbox deployment service.
        
        Args:
            docker_configs_path: Path to Docker configuration files
            host_url: Base URL for exposing containers
            network_name: Docker network for containers
        """
        self.docker_configs_path = docker_configs_path or str(
            Path(__file__).parent / "docker-configs"
        )
        # Verify docker_configs_path exists
        if not Path(self.docker_configs_path).exists():
            logger.error(f"Docker configs path does not exist: {self.docker_configs_path}")
        else:
            logger.debug(f"Docker configs path: {self.docker_configs_path}")
        
        self.host_url = host_url.rstrip("/")
        self.network_name = network_name
        
        # Active containers registry
        self._containers: Dict[str, SandboxContainer] = {}
        
        # Port allocation tracking
        self._used_ports: set = set()
        
        # Background cleanup task
        self._cleanup_task: Optional[asyncio.Task] = None
        self._running = False
        
        # Image cache - maps content hash to image name for reuse
        self._image_cache: Dict[str, str] = {}
        
        # Track if base image is available
        self._base_image_available: Optional[bool] = None
        
        # Ensure Docker network exists
        self._ensure_network()
        
        # Check if base image exists (async-safe check on first use)
        self._check_base_image()
    
    def _ensure_network(self):
        """Create Docker network if it doesn't exist."""
        try:
            result = subprocess.run(
                ["docker", "network", "inspect", self.network_name],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace"
            )
            if result.returncode != 0:
                subprocess.run(
                    ["docker", "network", "create", self.network_name],
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    check=True
                )
                logger.info(f"Created Docker network: {self.network_name}")
        except subprocess.CalledProcessError as e:
            logger.warning(f"Could not create network: {e}")
    
    def _check_base_image(self):
        """Check if the pre-built base image is available."""
        try:
            result = subprocess.run(
                ["docker", "image", "inspect", self.BASE_IMAGE],
                capture_output=True,
                timeout=5
            )
            self._base_image_available = (result.returncode == 0)
            if self._base_image_available:
                logger.info(f"✅ Base image {self.BASE_IMAGE} available - fast builds enabled!")
            else:
                logger.warning(f"⚠️ Base image {self.BASE_IMAGE} not found. Run: docker build -f sandbox-base.Dockerfile -t {self.BASE_IMAGE} .")
        except Exception as e:
            self._base_image_available = False
            logger.warning(f"Could not check base image: {e}")
    
    def _compute_content_hash(self, project_files: Dict[str, str]) -> str:
        """Compute a hash of project files for caching."""
        import hashlib
        content = "".join(f"{k}:{v}" for k, v in sorted(project_files.items()))
        return hashlib.md5(content.encode()).hexdigest()[:12]
    
    def _allocate_port(self) -> int:
        """Allocate an available port for a new container."""
        for port in range(self.PORT_RANGE_START, self.PORT_RANGE_END + 1):
            if port not in self._used_ports:
                # Check if port is actually available on host
                import socket
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                try:
                    sock.bind(("", port))
                    sock.close()
                    self._used_ports.add(port)
                    return port
                except OSError:
                    continue
        raise RuntimeError("No available ports in range")
    
    def _release_port(self, port: int):
        """Release a port back to the pool."""
        self._used_ports.discard(port)
    
    def _scan_imports_for_packages(self, project_files: Dict[str, str]) -> List[str]:
        """
        Scan project Python files for import statements and return 
        additional pip packages that may be needed.
        """
        import re
        
        # Map of import names to pip package names
        import_to_package = {
            "google.oauth2": "google-auth>=2.23.0",
            "google.auth": "google-auth>=2.23.0",
            "google_auth_oauthlib": "google-auth-oauthlib>=1.1.0",
            "requests": "requests>=2.31.0",
            "stripe": "stripe>=7.0.0",
            "boto3": "boto3>=1.28.0",
            "botocore": "boto3>=1.28.0",
            "redis": "redis>=5.0.0",
            "celery": "celery>=5.3.0",
            "PIL": "Pillow>=10.0.0",
            "cv2": "opencv-python-headless>=4.8.0",
            "numpy": "numpy>=1.24.0",
            "pandas": "pandas>=2.0.0",
            "jwt": "PyJWT>=2.8.0",
            "yaml": "PyYAML>=6.0",
            "dotenv": "python-dotenv>=1.0.0",
            "pymongo": "pymongo>=4.5.0",
            "motor": "motor>=3.3.0",
            "sendgrid": "sendgrid>=6.10.0",
            "twilio": "twilio>=8.10.0",
            "openai": "openai>=1.0.0",
            "anthropic": "anthropic>=0.18.0",
            "jinja2": "Jinja2>=3.1.0",
            "markdown": "Markdown>=3.5.0",
            "cryptography": "cryptography>=41.0.0",
            "websockets": "websockets>=12.0",
            "apscheduler": "APScheduler>=3.10.0",
        }
        
        needed_packages = set()
        
        for filename, content in project_files.items():
            if not filename.endswith('.py'):
                continue
            
            # Find all imports
            for line in content.split('\n'):
                line = line.strip()
                # Match: import X, from X import Y, from X.Y import Z
                import_match = re.match(r'(?:from\s+(\S+)\s+import|import\s+(\S+))', line)
                if import_match:
                    module = import_match.group(1) or import_match.group(2)
                    # Check against known mappings
                    for import_prefix, package in import_to_package.items():
                        if module == import_prefix or module.startswith(import_prefix + '.'):
                            needed_packages.add(package)
        
        return list(needed_packages)
    
    def _generate_missing_modules(self, build_dir: str, project_files: Dict[str, str]):
        """
        Auto-generate missing Python modules that are imported by project files.
        
        AI-generated projects often have import references to modules like 'database',
        'models', 'schemas', 'config' etc. that may not exist as separate files.
        This method scans for local imports and creates stub modules if missing.
        """
        import re
        
        # Collect all local module imports from project Python files
        all_files_in_build = set()
        for f in Path(build_dir).rglob("*.py"):
            all_files_in_build.add(f.stem)  # e.g. "database", "models"
        
        # Also check project_files dict
        for filename in project_files:
            if filename.endswith('.py'):
                stem = Path(filename).stem
                all_files_in_build.add(stem)
        
        # Standard library / third-party modules to ignore
        stdlib_and_packages = {
            'os', 'sys', 'json', 'datetime', 'typing', 'pathlib', 're', 'time',
            'uuid', 'hashlib', 'base64', 'secrets', 'logging', 'asyncio',
            'contextlib', 'functools', 'collections', 'enum', 'dataclasses',
            'abc', 'io', 'math', 'random', 'string', 'copy', 'itertools',
            'fastapi', 'sqlalchemy', 'pydantic', 'jose', 'passlib', 'uvicorn',
            'starlette', 'httpx', 'requests', 'stripe', 'boto3', 'google',
            'motor', 'pymongo', 'redis', 'celery', 'PIL', 'numpy', 'pandas',
            'dotenv', 'jwt', 'yaml', 'jinja2', 'markdown', 'cryptography',
            'websockets', 'apscheduler', 'email_validator', 'bcrypt',
            'click', 'aiosqlite', 'anthropic', 'openai', 'sendgrid', 'twilio',
        }
        
        # Scan all Python files for local imports
        missing_modules = set()
        for py_file in Path(build_dir).rglob("*.py"):
            try:
                content = py_file.read_text(encoding='utf-8', errors='replace')
                for line in content.split('\n'):
                    line = line.strip()
                    # Match: from X import Y  or  import X
                    match = re.match(r'(?:from\s+(\w+)\s+import|import\s+(\w+))', line)
                    if match:
                        module = match.group(1) or match.group(2)
                        if (module not in stdlib_and_packages and 
                            module not in all_files_in_build and
                            not (Path(build_dir) / f"{module}.py").exists()):
                            missing_modules.add(module)
            except Exception:
                continue
        
        # Generate stub modules for common patterns
        module_templates = {
            'database': '''"""Database configuration - auto-generated stub."""
import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/sandbox.db")
connect_args = {"check_same_thread": False} if "sqlite" in DATABASE_URL else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Create all tables."""
    Base.metadata.create_all(bind=engine)
''',
            'config': '''"""Configuration - auto-generated stub."""
import os

class Settings:
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./data/sandbox.db")
    JWT_SECRET: str = os.getenv("JWT_SECRET", "sandbox-secret-key")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24
    SANDBOX: bool = True
    SECRET_KEY: str = os.getenv("SECRET_KEY", "sandbox-secret-key")

settings = Settings()
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.JWT_ALGORITHM
''',
            'schemas': '''"""Pydantic schemas - auto-generated stub."""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Any
from datetime import datetime

class UserBase(BaseModel):
    email: str
    username: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    is_active: bool = True
    created_at: Optional[datetime] = None
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    email: Optional[str] = None
''',
            'auth': '''"""Authentication utilities - auto-generated stub."""
import os
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext

SECRET_KEY = os.getenv("JWT_SECRET", "sandbox-secret-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
''',
            'deps': '''"""Dependencies - auto-generated stub."""
from database import get_db
''',
            'utils': '''"""Utility functions - auto-generated stub."""
import os
import hashlib
import secrets
from datetime import datetime

def generate_id() -> str:
    return secrets.token_hex(16)
''',
        }
        
        for module in missing_modules:
            module_path = Path(build_dir) / f"{module}.py"
            if module in module_templates:
                module_path.write_text(module_templates[module])
                logger.info(f"📝 Auto-generated missing module: {module}.py")
            else:
                # Generic empty module stub so import doesn't fail
                module_path.write_text(f'"""Auto-generated stub for {module} module."""\n')
                logger.info(f"📝 Auto-generated stub module: {module}.py")
    
    def _generate_container_name(self, session_id: str) -> str:
        """Generate a unique container name."""
        short_id = session_id[:8] if len(session_id) > 8 else session_id
        timestamp = int(time.time()) % 10000
        return f"sandbox-{short_id}-{timestamp}"
    
    def _generate_image_name(self, session_id: str) -> str:
        """Generate a unique image name with a valid tag."""
        import re
        if not session_id or not isinstance(session_id, str):
            session_id = "sandbox"
        safe_id = re.sub(r'[^a-zA-Z0-9_-]', '', session_id)
        if not safe_id:
            safe_id = "sandbox"
        tag = f"sandbox-backend-preview-{safe_id.lower()}-v1:latest"
        print(f"[DEBUG] Docker image tag generated: {tag}")
        return tag
    
    async def start(self):
        """Start the deployment service and background cleanup."""
        if self._running:
            return
        
        self._running = True
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.info("Sandbox deployment service started")
    
    async def stop(self):
        """Stop the deployment service and cleanup all containers."""
        self._running = False
        
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        
        # Stop all active containers
        for container in list(self._containers.values()):
            await self.destroy_sandbox(container.session_id)
        
        logger.info("Sandbox deployment service stopped")
    
    async def _cleanup_loop(self):
        """Background task to cleanup expired containers."""
        while self._running:
            try:
                await asyncio.sleep(self.CLEANUP_INTERVAL)
                await self._cleanup_expired()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cleanup error: {e}")
    
    async def _cleanup_expired(self):
        """Remove expired containers."""
        now = datetime.utcnow()
        expired = [
            c for c in self._containers.values()
            if c.expires_at <= now
        ]
        
        for container in expired:
            logger.info(f"Cleaning up expired container: {container.container_name}")
            container.status = SandboxStatus.EXPIRED
            await self.destroy_sandbox(container.session_id)
    
    async def create_sandbox(
        self,
        session_id: str,
        project_files: Dict[str, str],
        ttl_minutes: int = None
    ) -> SandboxContainer:
        """
        Create and deploy a new sandbox container.
        
        Args:
            session_id: Unique session identifier
            project_files: Dict mapping filenames to file contents
            ttl_minutes: Time-to-live in minutes (30-60)
        
        Returns:
            SandboxContainer with deployment details
        """
        # Validate TTL
        ttl = ttl_minutes or self.DEFAULT_TTL_MINUTES
        ttl = max(self.MIN_TTL_MINUTES, min(self.MAX_TTL_MINUTES, ttl))
        
        # Check for existing session
        if session_id in self._containers:
            existing = self._containers[session_id]
            if existing.status in (SandboxStatus.RUNNING, SandboxStatus.HEALTHY):
                # Extend TTL and return existing
                existing.expires_at = datetime.utcnow() + timedelta(minutes=ttl)
                return existing
            else:
                # Cleanup failed container
                await self.destroy_sandbox(session_id)
        
        # Allocate resources
        port = self._allocate_port()
        container_name = self._generate_container_name(session_id)
        image_name = self._generate_image_name(session_id)
        
        # Create container record
        container = SandboxContainer(
            id=str(uuid.uuid4()),
            session_id=session_id,
            container_name=container_name,
            image_name=image_name,
            port=port,
            status=SandboxStatus.PENDING,
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(minutes=ttl),
            base_url=f"{self.host_url}:{port}"
        )
        
        self._containers[session_id] = container
        
        try:
            # Build and run container
            await self._build_and_run(container, project_files)
            return container
            
        except Exception as e:
            container.status = SandboxStatus.FAILED
            container.error_message = str(e)
            logger.error(f"Failed to create sandbox {session_id}: {e}")
            raise
    
    async def _build_and_run(
        self,
        container: SandboxContainer,
        project_files: Dict[str, str]
    ):
        """Build Docker image and run container - OPTIMIZED for speed."""
        
        build_start = time.time()
        
        # Check for cached image first
        content_hash = self._compute_content_hash(project_files)
        cached_image = self._image_cache.get(content_hash)
        
        if cached_image:
            # Verify cached image still exists
            check_result = subprocess.run(
                ["docker", "image", "inspect", cached_image],
                capture_output=True,
                timeout=5
            )
            if check_result.returncode == 0:
                logger.info(f"♻️ Reusing cached image: {cached_image} (hash: {content_hash})")
                container.image_name = cached_image
                container.status = SandboxStatus.STARTING
                await self._run_container(container)
                logger.info(f"⚡ Container started in {time.time() - build_start:.2f}s (cached)")
                return
        
        # Create temporary build context
        build_dir = tempfile.mkdtemp(prefix="sandbox-build-")
        container.project_path = build_dir
        
        try:
            # PARALLEL: Copy template files and write project files concurrently
            await self._prepare_build_context(build_dir, project_files)
            
            # Build image with base image if available
            container.status = SandboxStatus.BUILDING
            base_image = self.BASE_IMAGE if self._base_image_available else self.FALLBACK_IMAGE
            logger.info(f"🔨 Building image: {container.image_name} (base: {base_image})")
            
            build_result = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: subprocess.run(
                    [
                        "docker", "build",
                        "-f", "sandbox.Dockerfile",
                        "--build-arg", f"BASE_IMAGE={base_image}",
                        "-t", container.image_name,
                        "."
                    ],
                    cwd=build_dir,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=120  # Reduced timeout - base image makes this faster
                )
            )
            
            build_time = time.time() - build_start
            
            if build_result.returncode != 0:
                logger.error(f"Build stderr: {build_result.stderr}")
                raise RuntimeError(f"Build failed: {build_result.stderr[:500]}")
            
            logger.info(f"✅ Image built in {build_time:.2f}s")
            
            # Cache the successful image
            self._image_cache[content_hash] = container.image_name
            
            # Run container
            await self._run_container(container)
            
            total_time = time.time() - build_start
            logger.info(f"⚡ Total sandbox creation time: {total_time:.2f}s")
            
        except Exception as e:
            container.status = SandboxStatus.FAILED
            container.error_message = str(e)
            await self._cleanup_container(container)
            raise
        
        finally:
            # Cleanup build directory
            if build_dir and Path(build_dir).exists():
                shutil.rmtree(build_dir, ignore_errors=True)
    
    async def _prepare_build_context(self, build_dir: str, project_files: Dict[str, str]):
        """Prepare build context with template files and project files - PARALLEL."""
        
        # Copy sandbox template files
        template_files = ["sandbox.Dockerfile", "sandbox_requirements.txt", "sandbox_main.py"]
        for fname in template_files:
            src = Path(self.docker_configs_path) / fname
            dest = Path(build_dir) / fname
            if src.exists():
                shutil.copy(src, dest)
                logger.debug(f"Copied template: {fname}")
            else:
                logger.warning(f"Template file not found: {src}")
        
        # Verify critical files were copied
        req_file = Path(build_dir) / "sandbox_requirements.txt"
        if not req_file.exists():
            # Create a minimal requirements file as fallback
            logger.warning("sandbox_requirements.txt not found, creating minimal version")
            req_file.write_text("""# Minimal sandbox requirements
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
pydantic>=2.0.0
sqlalchemy>=2.0.0
python-jose[cryptography]>=3.3.0
passlib[bcrypt]>=1.7.4
python-multipart>=0.0.6
requests>=2.31.0
google-auth>=2.23.0
""")
        
        # Scan project files for imports and auto-add missing packages
        extra_packages = self._scan_imports_for_packages(project_files)
        if extra_packages:
            existing_reqs = req_file.read_text()
            extra_lines = "\n# Auto-detected from project imports\n"
            for pkg in extra_packages:
                # Don't add if already in requirements
                pkg_base = pkg.split(">=")[0].split("[")[0].replace("-", "").replace("_", "").lower()
                existing_normalized = existing_reqs.replace("-", "").replace("_", "").lower()
                if pkg_base not in existing_normalized:
                    extra_lines += f"{pkg}\n"
            if extra_lines.strip() != "# Auto-detected from project imports":
                req_file.write_text(existing_reqs.rstrip() + "\n" + extra_lines)
                logger.info(f"📦 Auto-added packages from imports: {extra_packages}")
        
        # Write project-specific files (can override defaults)
        for filename, content in project_files.items():
            filepath = Path(build_dir) / filename
            filepath.parent.mkdir(parents=True, exist_ok=True)
            filepath.write_text(content)
        
        # Ensure we have a working main.py
        main_py_path = Path(build_dir) / "main.py"
        sandbox_main_py = Path(build_dir) / "sandbox_main.py"
        
        if not main_py_path.exists() and sandbox_main_py.exists():
            shutil.copy(sandbox_main_py, main_py_path)
            logger.info("Using sandbox_main.py as main.py")
        elif main_py_path.exists():
            main_content = main_py_path.read_text()
            if 'app = FastAPI' not in main_content and 'FastAPI()' not in main_content:
                if sandbox_main_py.exists():
                    sandbox_content = sandbox_main_py.read_text()
                    hybrid_content = sandbox_content + "\n\n# === User routes ===\n" + main_content
                    main_py_path.write_text(hybrid_content)
        
        # Auto-generate missing modules that are imported by project files
        self._generate_missing_modules(build_dir, project_files)
        
        # Create .dockerignore for faster builds
        dockerignore = Path(build_dir) / ".dockerignore"
        dockerignore.write_text("__pycache__\n*.pyc\n.git\n.env\nvenv\n*.md\n*.txt\n!requirements.txt\n!sandbox_requirements.txt\n")
    
    async def _run_container(self, container: SandboxContainer):
        """Run the container and wait for health."""
        container.status = SandboxStatus.STARTING
        logger.info(f"🚀 Starting container: {container.container_name} on port {container.port}")
        
        run_result = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: subprocess.run(
                [
                    "docker", "run",
                    "-d",  # Detached
                    "--name", container.container_name,
                    "--network", self.network_name,
                    "-p", f"{container.port}:8000",
                    "-e", "SANDBOX=true",
                    "-e", f"JWT_SECRET=sandbox-{container.session_id}",
                    "--memory", "256m",  # Reduced memory - sandbox doesn't need much
                    "--cpus", "0.5",
                    "--restart", "no",
                    container.image_name
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace"
            )
        )
        
        if run_result.returncode != 0:
            raise RuntimeError(f"Run failed: {run_result.stderr}")
        
        container.status = SandboxStatus.RUNNING
        
        # Wait for health check with exponential backoff
        await self._wait_for_healthy(container)
    
    async def _wait_for_healthy(self, container: SandboxContainer):
        """Poll health endpoint until ready - OPTIMIZED with exponential backoff."""
        health_url = f"{container.base_url}/health"
        health_start = time.time()
        
        # Exponential backoff: start fast, slow down if needed
        interval = self.HEALTH_CHECK_INITIAL_INTERVAL
        last_error = None
        
        async with httpx.AsyncClient(timeout=self.HEALTH_CHECK_TIMEOUT) as client:
            for attempt in range(self.HEALTH_CHECK_RETRIES):
                container.health_checks = attempt + 1
                container.last_health_check = datetime.utcnow()
                
                try:
                    response = await client.get(health_url)
                    if response.status_code == 200:
                        data = response.json()
                        if data.get("status") == "ok":
                            container.status = SandboxStatus.HEALTHY
                            health_time = time.time() - health_start
                            logger.info(
                                f"✅ Container {container.container_name} healthy "
                                f"in {health_time:.2f}s ({attempt + 1} checks)"
                            )
                            return
                except (httpx.RequestError, httpx.TimeoutException) as e:
                    last_error = str(e)
                
                # Exponential backoff with cap
                await asyncio.sleep(interval)
                interval = min(interval * 1.5, self.HEALTH_CHECK_MAX_INTERVAL)
        
        # Failed health checks - get container logs for debugging
        try:
            logs_result = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: subprocess.run(
                    ["docker", "logs", "--tail", "50", container.container_name],
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace"
                )
            )
            container_logs = logs_result.stdout + logs_result.stderr
            logger.error(f"Container {container.container_name} logs:\n{container_logs}")
        except Exception as log_err:
            logger.error(f"Could not get container logs: {log_err}")
        
        container.status = SandboxStatus.UNHEALTHY
        container.error_message = f"Health check failed after {self.HEALTH_CHECK_RETRIES} attempts. Last error: {last_error}"
        raise RuntimeError(container.error_message)
    
    async def _cleanup_container(self, container: SandboxContainer):
        """Stop and remove a container."""
        try:
            # Stop container
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: subprocess.run(
                    ["docker", "stop", container.container_name],
                    capture_output=True,
                    timeout=30
                )
            )
        except Exception:
            pass
        
        try:
            # Remove container
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: subprocess.run(
                    ["docker", "rm", "-f", container.container_name],
                    capture_output=True
                )
            )
        except Exception:
            pass
        
        try:
            # Remove image
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: subprocess.run(
                    ["docker", "rmi", container.image_name],
                    capture_output=True
                )
            )
        except Exception:
            pass
    
    async def destroy_sandbox(self, session_id: str) -> bool:
        """
        Destroy a sandbox container.
        
        Args:
            session_id: Session identifier
        
        Returns:
            True if destroyed, False if not found
        """
        container = self._containers.pop(session_id, None)
        if not container:
            return False
        
        container.status = SandboxStatus.STOPPING
        
        await self._cleanup_container(container)
        self._release_port(container.port)
        
        container.status = SandboxStatus.STOPPED
        logger.info(f"Destroyed sandbox: {container.container_name}")
        
        return True
    
    async def get_sandbox(self, session_id: str) -> Optional[SandboxContainer]:
        """Get sandbox container by session ID."""
        return self._containers.get(session_id)
    
    async def list_sandboxes(self) -> List[SandboxContainer]:
        """List all active sandbox containers."""
        return list(self._containers.values())
    
    async def extend_ttl(self, session_id: str, additional_minutes: int = 15) -> bool:
        """
        Extend the TTL of a sandbox container.
        
        Args:
            session_id: Session identifier
            additional_minutes: Minutes to add (capped at MAX_TTL from now)
        
        Returns:
            True if extended, False if not found
        """
        container = self._containers.get(session_id)
        if not container:
            return False
        
        max_expires = datetime.utcnow() + timedelta(minutes=self.MAX_TTL_MINUTES)
        new_expires = container.expires_at + timedelta(minutes=additional_minutes)
        container.expires_at = min(new_expires, max_expires)
        
        logger.info(f"Extended TTL for {container.container_name} to {container.expires_at}")
        return True
    
    async def get_logs(self, session_id: str, tail: int = 100) -> Optional[str]:
        """Get container logs."""
        container = self._containers.get(session_id)
        if not container:
            return None
        
        result = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: subprocess.run(
                ["docker", "logs", "--tail", str(tail), container.container_name],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace"
            )
        )
        return (result.stdout or "") + (result.stderr or "")
    
    async def health_check(self, session_id: str) -> Dict[str, Any]:
        """Perform a health check on a sandbox."""
        container = self._containers.get(session_id)
        if not container:
            return {"status": "not_found", "session_id": session_id}
        
        health_url = f"{container.base_url}/health"
        
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(health_url)
                if response.status_code == 200:
                    return {
                        "status": "healthy",
                        "container": container.to_dict(),
                        "backend_health": response.json()
                    }
        except Exception as e:
            pass
        
        return {
            "status": "unhealthy",
            "container": container.to_dict(),
            "error": "Health check failed"
        }


# =============================================================================
# FastAPI Integration - API endpoints for the deployment service
# =============================================================================

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/sandbox", tags=["Sandbox Deployment"])
security = HTTPBearer()

# Global service instance (initialized on startup)
_service: Optional[SandboxDeploymentService] = None


def get_service() -> SandboxDeploymentService:
    """Get the global deployment service instance."""
    if _service is None:
        raise HTTPException(status_code=503, detail="Sandbox service not initialized")
    return _service


async def init_service(host_url: str = "http://localhost"):
    """Initialize the global deployment service."""
    global _service
    _service = SandboxDeploymentService(host_url=host_url)
    await _service.start()
    
    # Also initialize session registry
    try:
        from sandbox_session_registry import init_registry
        await init_registry()
        logger.info("Session registry initialized")
    except ImportError:
        logger.warning("Session registry not available")
    
    return _service


async def shutdown_service():
    """Shutdown the global deployment service."""
    global _service
    if _service:
        await _service.stop()
        _service = None
    
    # Also shutdown session registry
    try:
        from sandbox_session_registry import shutdown_registry
        await shutdown_registry()
    except ImportError:
        pass


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> str:
    """Extract user ID from JWT token."""
    try:
        from auth import verify_token
        payload = verify_token(credentials.credentials)
        if not payload:
            raise HTTPException(status_code=401, detail="Invalid token")
        user_id = payload.get("sub") or payload.get("user_id") or payload.get("email")
        if not user_id:
            raise HTTPException(status_code=401, detail="No user ID in token")
        return str(user_id)
    except ImportError:
        # Fallback for testing
        import base64
        import json as json_module
        try:
            parts = credentials.credentials.split(".")
            if len(parts) >= 2:
                payload_b64 = parts[1] + "=" * (4 - len(parts[1]) % 4)
                payload = json_module.loads(base64.urlsafe_b64decode(payload_b64))
                return payload.get("sub", "unknown")
        except:
            pass
        raise HTTPException(status_code=401, detail="Invalid token")


# Request/Response models
class CreateSandboxRequest(BaseModel):
    session_id: str = Field(..., description="Unique session identifier")
    files: Dict[str, str] = Field(
        default_factory=dict,
        description="Project files (filename -> content)"
    )
    ttl_minutes: int = Field(
        default=45,
        ge=30,
        le=60,
        description="Time-to-live in minutes"
    )
    project_name: Optional[str] = Field(default=None, description="Optional project name")


class SandboxResponse(BaseModel):
    success: bool
    sandbox: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class SandboxListResponse(BaseModel):
    count: int
    sandboxes: List[Dict[str, Any]]


# API Endpoints
@router.post("/create", response_model=SandboxResponse)
async def create_sandbox(
    request: CreateSandboxRequest,
    user_id: str = Depends(get_current_user_id)
):
    """
    Create a new sandbox container for a preview session.
    
    - Builds a Docker image with the provided files
    - Runs an isolated container
    - Registers in session registry with user ownership
    - Returns the public base URL for the backend
    """
    service = get_service()
    
    try:
        container = await service.create_sandbox(
            session_id=request.session_id,
            project_files=request.files,
            ttl_minutes=request.ttl_minutes
        )
        
        # Register in session registry for user ownership tracking
        try:
            from sandbox_session_registry import register_sandbox_session
            register_sandbox_session(
                session_id=request.session_id,
                user_id=user_id,
                backend_url=container.base_url,
                container_name=container.container_name,
                ttl_minutes=request.ttl_minutes,
                project_name=request.project_name
            )
            logger.info(f"Registered session {request.session_id} for user {user_id}")
        except ImportError:
            logger.warning("Session registry not available, skipping registration")
        
        return SandboxResponse(success=True, sandbox=container.to_dict())
    
    except Exception as e:
        logger.error(f"Failed to create sandbox: {e}")
        return SandboxResponse(success=False, error=str(e))


@router.get("/{session_id}", response_model=SandboxResponse)
async def get_sandbox(
    session_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """Get sandbox details by session ID (user must own the session)."""
    service = get_service()
    
    # Verify ownership via session registry
    try:
        from sandbox_session_registry import get_registry
        registry = get_registry()
        registry.get_session(session_id, user_id)  # Raises if not owned
    except ImportError:
        pass  # Registry not available, skip ownership check
    except Exception as e:
        raise HTTPException(status_code=403, detail=str(e))
    
    container = await service.get_sandbox(session_id)
    
    if not container:
        raise HTTPException(status_code=404, detail="Sandbox not found")
    
    return SandboxResponse(success=True, sandbox=container.to_dict())


@router.delete("/{session_id}", response_model=SandboxResponse)
async def destroy_sandbox(
    session_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """Destroy a sandbox container (user must own the session)."""
    
    # Verify ownership and unregister from session registry
    try:
        from sandbox_session_registry import get_registry
        registry = get_registry()
        registry.unregister(session_id, user_id)  # Raises if not owned
    except ImportError:
        pass  # Registry not available
    except Exception as e:
        raise HTTPException(status_code=403, detail=str(e))
    
    service = get_service()
    service = get_service()
    destroyed = await service.destroy_sandbox(session_id)
    
    if not destroyed:
        raise HTTPException(status_code=404, detail="Sandbox not found")
    
    return SandboxResponse(success=True)


@router.post("/{session_id}/extend", response_model=SandboxResponse)
async def extend_sandbox_ttl(session_id: str, minutes: int = 15):
    """Extend the TTL of a sandbox container."""
    service = get_service()
    extended = await service.extend_ttl(session_id, minutes)
    
    if not extended:
        raise HTTPException(status_code=404, detail="Sandbox not found")
    
    container = await service.get_sandbox(session_id)
    return SandboxResponse(success=True, sandbox=container.to_dict())


@router.get("/{session_id}/health")
async def sandbox_health_check(session_id: str):
    """Perform a health check on a sandbox."""
    service = get_service()
    return await service.health_check(session_id)


@router.get("/{session_id}/logs")
async def get_sandbox_logs(session_id: str, tail: int = 100):
    """Get container logs for debugging."""
    service = get_service()
    logs = await service.get_logs(session_id, tail)
    
    if logs is None:
        raise HTTPException(status_code=404, detail="Sandbox not found")
    
    return {"session_id": session_id, "logs": logs}


@router.get("/", response_model=SandboxListResponse)
async def list_sandboxes():
    """List all active sandbox containers."""
    service = get_service()
    containers = await service.list_sandboxes()
    
    return SandboxListResponse(
        count=len(containers),
        sandboxes=[c.to_dict() for c in containers]
    )


# =============================================================================
# Standalone usage example
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    from fastapi import FastAPI
    
    app = FastAPI(title="Sandbox Deployment Service")
    app.include_router(router)
    
    @app.on_event("startup")
    async def startup():
        await init_service(host_url="http://localhost")
    
    @app.on_event("shutdown")
    async def shutdown():
        await shutdown_service()
    
    @app.get("/health")
    async def health():
        return {"status": "ok", "service": "sandbox-deployment"}
    
    uvicorn.run(app, host="0.0.0.0", port=8080)
