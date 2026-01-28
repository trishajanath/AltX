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
    """
    
    # Port range for sandbox containers
    PORT_RANGE_START = 9000
    PORT_RANGE_END = 9999
    
    # Default TTL (45 minutes)
    DEFAULT_TTL_MINUTES = 45
    MIN_TTL_MINUTES = 30
    MAX_TTL_MINUTES = 60
    
    # Health check configuration
    HEALTH_CHECK_INTERVAL = 2  # seconds
    HEALTH_CHECK_TIMEOUT = 5   # seconds
    HEALTH_CHECK_RETRIES = 30  # max attempts (60 seconds total)
    
    # Cleanup interval
    CLEANUP_INTERVAL = 60  # seconds
    
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
        self.host_url = host_url.rstrip("/")
        self.network_name = network_name
        
        # Active containers registry
        self._containers: Dict[str, SandboxContainer] = {}
        
        # Port allocation tracking
        self._used_ports: set = set()
        
        # Background cleanup task
        self._cleanup_task: Optional[asyncio.Task] = None
        self._running = False
        
        # Ensure Docker network exists
        self._ensure_network()
    
    def _ensure_network(self):
        """Create Docker network if it doesn't exist."""
        try:
            result = subprocess.run(
                ["docker", "network", "inspect", self.network_name],
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                subprocess.run(
                    ["docker", "network", "create", self.network_name],
                    capture_output=True,
                    check=True
                )
                logger.info(f"Created Docker network: {self.network_name}")
        except subprocess.CalledProcessError as e:
            logger.warning(f"Could not create network: {e}")
    
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
    
    def _generate_container_name(self, session_id: str) -> str:
        """Generate a unique container name."""
        short_id = session_id[:8] if len(session_id) > 8 else session_id
        timestamp = int(time.time()) % 10000
        return f"sandbox-{short_id}-{timestamp}"
    
    def _generate_image_name(self, session_id: str) -> str:
        """Generate a unique image name."""
        short_id = session_id[:8] if len(session_id) > 8 else session_id
        return f"sandbox-backend-{short_id}:latest"
    
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
        """Build Docker image and run container."""
        
        # Create temporary build context
        build_dir = tempfile.mkdtemp(prefix="sandbox-build-")
        container.project_path = build_dir
        
        try:
            # Copy sandbox template files
            template_files = ["sandbox.Dockerfile", "sandbox_requirements.txt", "sandbox_main.py"]
            for fname in template_files:
                src = Path(self.docker_configs_path) / fname
                if src.exists():
                    shutil.copy(src, build_dir)
            
            # Write project-specific files (can override defaults)
            for filename, content in project_files.items():
                filepath = Path(build_dir) / filename
                filepath.parent.mkdir(parents=True, exist_ok=True)
                filepath.write_text(content)
            
            # Ensure we have a main.py (use sandbox_main.py as fallback)
            main_py = Path(build_dir) / "sandbox_main.py"
            if not (Path(build_dir) / "main.py").exists() and main_py.exists():
                shutil.copy(main_py, Path(build_dir) / "main.py")
            
            # Create .dockerignore
            dockerignore = Path(build_dir) / ".dockerignore"
            if not dockerignore.exists():
                dockerignore.write_text("__pycache__\n*.pyc\n.git\n.env\n")
            
            # Build image
            container.status = SandboxStatus.BUILDING
            logger.info(f"Building image: {container.image_name}")
            
            build_result = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: subprocess.run(
                    [
                        "docker", "build",
                        "-f", "sandbox.Dockerfile",
                        "-t", container.image_name,
                        "."
                    ],
                    cwd=build_dir,
                    capture_output=True,
                    text=True,
                    timeout=300  # 5 minute build timeout
                )
            )
            
            if build_result.returncode != 0:
                raise RuntimeError(f"Build failed: {build_result.stderr}")
            
            # Run container
            container.status = SandboxStatus.STARTING
            logger.info(f"Starting container: {container.container_name} on port {container.port}")
            
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
                        "--memory", "512m",  # Memory limit
                        "--cpus", "0.5",     # CPU limit
                        "--restart", "no",   # No auto-restart
                        container.image_name
                    ],
                    capture_output=True,
                    text=True
                )
            )
            
            if run_result.returncode != 0:
                raise RuntimeError(f"Run failed: {run_result.stderr}")
            
            container.status = SandboxStatus.RUNNING
            
            # Wait for health check
            await self._wait_for_healthy(container)
            
        except Exception as e:
            container.status = SandboxStatus.FAILED
            container.error_message = str(e)
            # Cleanup on failure
            await self._cleanup_container(container)
            raise
        
        finally:
            # Cleanup build directory
            if build_dir and Path(build_dir).exists():
                shutil.rmtree(build_dir, ignore_errors=True)
    
    async def _wait_for_healthy(self, container: SandboxContainer):
        """Poll health endpoint until ready."""
        health_url = f"{container.base_url}/health"
        
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
                            logger.info(
                                f"Container {container.container_name} healthy "
                                f"after {attempt + 1} checks"
                            )
                            return
                except (httpx.RequestError, httpx.TimeoutException):
                    pass
                
                await asyncio.sleep(self.HEALTH_CHECK_INTERVAL)
        
        # Failed health checks
        container.status = SandboxStatus.UNHEALTHY
        container.error_message = f"Health check failed after {self.HEALTH_CHECK_RETRIES} attempts"
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
                text=True
            )
        )
        
        return result.stdout + result.stderr
    
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
