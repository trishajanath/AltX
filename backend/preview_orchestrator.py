"""
Preview Orchestration Service
=============================
Coordinates the full preview flow for AI-generated projects:

1. Generate FastAPI backend code
2. Build Docker image
3. Deploy sandbox container
4. Poll /health until backend is ready
5. Return backend URL for frontend injection
6. Launch frontend preview (frontend-side responsibility)

Key Principles:
- Frontend MUST NOT load before backend is ready
- Errors are surfaced clearly at each stage
- No mocked APIs in normal flow (real HTTP always)
- Fallback to mocks ONLY if backend startup fails
"""

import os
import asyncio
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import logging
import httpx

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# =============================================================================
# ORCHESTRATION STATES AND MODELS
# =============================================================================

class OrchestrationStage(str, Enum):
    """Stages in the preview orchestration pipeline."""
    PENDING = "pending"
    GENERATING_BACKEND = "generating_backend"
    BUILDING_IMAGE = "building_image"
    DEPLOYING_CONTAINER = "deploying_container"
    WAITING_FOR_HEALTH = "waiting_for_health"
    BACKEND_READY = "backend_ready"
    PREPARING_FRONTEND = "preparing_frontend"
    READY = "ready"
    FAILED = "failed"


@dataclass
class OrchestrationProgress:
    """Tracks progress through the orchestration pipeline."""
    session_id: str
    stage: OrchestrationStage
    stage_progress: int = 0  # 0-100 within current stage
    overall_progress: int = 0  # 0-100 overall
    message: str = ""
    error: Optional[str] = None
    started_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    # URLs (set when ready)
    backend_url: Optional[str] = None
    frontend_preview_url: Optional[str] = None
    health_check_url: Optional[str] = None
    
    # Timing metrics
    stage_times: Dict[str, float] = field(default_factory=dict)
    
    # Backend configuration
    backend_config: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "stage": self.stage.value,
            "stage_progress": self.stage_progress,
            "overall_progress": self.overall_progress,
            "message": self.message,
            "error": self.error,
            "started_at": self.started_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "backend_url": self.backend_url,
            "frontend_preview_url": self.frontend_preview_url,
            "health_check_url": self.health_check_url,
            "stage_times": self.stage_times,
            "backend_config": self.backend_config
        }


class PreviewRequest(BaseModel):
    """Request to start a preview orchestration."""
    project_name: str = Field(..., description="Project slug/name")
    project_files: Dict[str, str] = Field(..., description="Project files (filename -> content)")
    backend_files: Optional[Dict[str, str]] = Field(None, description="Backend-specific files to deploy")
    user_id: Optional[str] = Field(None, description="User identifier")
    ttl_minutes: int = Field(45, ge=30, le=60, description="Container TTL in minutes")
    generate_backend: bool = Field(True, description="Whether to generate backend code if not provided")


class PreviewResponse(BaseModel):
    """Response from preview orchestration."""
    success: bool
    session_id: str
    status: str
    backend_url: Optional[str] = None
    frontend_preview_url: Optional[str] = None
    message: str
    mock_mode: bool = False
    backend_config: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class HealthCheckResponse(BaseModel):
    """Response from backend health check."""
    healthy: bool
    backend_url: str
    response_time_ms: float
    auth_config: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


# =============================================================================
# BACKEND CODE GENERATOR
# =============================================================================

class BackendCodeGenerator:
    """
    Generates FastAPI backend code based on frontend project files.
    
    Analyzes the frontend to determine:
    - Required API endpoints
    - Data models
    - Authentication needs
    """
    
    def __init__(self):
        self.template_path = Path(__file__).parent / "docker-configs"
    
    def analyze_frontend(self, project_files: Dict[str, str]) -> Dict[str, Any]:
        """
        Analyze frontend files to determine backend requirements.
        
        Returns:
            Dict with: endpoints, models, auth_required, features
        """
        analysis = {
            "endpoints": [],
            "models": [],
            "auth_required": False,
            "features": [],
            "api_calls": []
        }
        
        # Patterns to detect
        fetch_pattern = r'fetch\s*\(\s*[\'"`]([^\'"`]+)[\'"`]'
        axios_pattern = r'axios\.(get|post|put|delete|patch)\s*\(\s*[\'"`]([^\'"`]+)[\'"`]'
        model_pattern = r'(interface|type)\s+(\w+)\s*(?:extends\s+\w+)?\s*\{'
        
        import re
        
        for filename, content in project_files.items():
            if not filename.endswith(('.js', '.jsx', '.ts', '.tsx')):
                continue
            
            # Find fetch calls
            for match in re.finditer(fetch_pattern, content):
                url = match.group(1)
                if url.startswith('/api') or '/api/' in url:
                    analysis["api_calls"].append(url)
            
            # Find axios calls
            for match in re.finditer(axios_pattern, content):
                method, url = match.groups()
                if url.startswith('/api') or '/api/' in url:
                    analysis["api_calls"].append(url)
            
            # Check for auth patterns
            if any(term in content.lower() for term in ['login', 'signup', 'auth', 'token', 'password']):
                analysis["auth_required"] = True
            
            # Find TypeScript interfaces/types
            for match in re.finditer(model_pattern, content):
                analysis["models"].append(match.group(2))
        
        # Deduplicate and extract unique endpoints
        unique_calls = list(set(analysis["api_calls"]))
        analysis["endpoints"] = self._extract_endpoints(unique_calls)
        
        # Determine features
        if analysis["auth_required"]:
            analysis["features"].append("authentication")
        if any('product' in e.lower() or 'item' in e.lower() for e in unique_calls):
            analysis["features"].append("products")
        if any('cart' in e.lower() for e in unique_calls):
            analysis["features"].append("cart")
        if any('order' in e.lower() for e in unique_calls):
            analysis["features"].append("orders")
        if any('user' in e.lower() for e in unique_calls):
            analysis["features"].append("users")
        
        return analysis
    
    def _extract_endpoints(self, api_calls: List[str]) -> List[Dict[str, str]]:
        """Extract unique endpoints from API calls."""
        endpoints = []
        seen = set()
        
        for call in api_calls:
            # Clean URL
            path = call.split('?')[0]  # Remove query params
            
            # Extract base endpoint
            parts = path.split('/')
            if len(parts) >= 2:
                base = '/'.join(parts[:3])  # e.g., /api/products
                if base not in seen:
                    seen.add(base)
                    endpoints.append({
                        "path": base,
                        "methods": ["GET", "POST", "PUT", "DELETE"]
                    })
        
        return endpoints
    
    def generate_backend_code(
        self,
        project_name: str,
        analysis: Dict[str, Any]
    ) -> Dict[str, str]:
        """
        Generate FastAPI backend code based on analysis.
        
        Returns:
            Dict mapping filename -> content
        """
        files = {}
        
        # Read base template
        template_main = self.template_path / "sandbox_main.py"
        if template_main.exists():
            base_code = template_main.read_text()
        else:
            base_code = self._get_minimal_template()
        
        # Customize based on analysis
        custom_endpoints = self._generate_custom_endpoints(analysis)
        
        # Insert custom endpoints before the "if __name__" block
        if "if __name__" in base_code:
            insert_point = base_code.find("if __name__")
            base_code = (
                base_code[:insert_point] +
                "\n# =============================================================================\n"
                "# CUSTOM ENDPOINTS (Generated from frontend analysis)\n"
                "# =============================================================================\n\n" +
                custom_endpoints + "\n\n" +
                base_code[insert_point:]
            )
        
        files["main.py"] = base_code
        
        # Copy requirements
        req_file = self.template_path / "sandbox_requirements.txt"
        if req_file.exists():
            files["requirements.txt"] = req_file.read_text()
        
        return files
    
    def _generate_custom_endpoints(self, analysis: Dict[str, Any]) -> str:
        """Generate custom endpoint code based on analysis."""
        code_parts = []
        
        for endpoint in analysis.get("endpoints", []):
            path = endpoint["path"]
            
            # Generate CRUD endpoints for each resource
            resource_name = path.split('/')[-1]
            if resource_name and resource_name not in ['api', 'v1']:
                code_parts.append(self._generate_crud_endpoint(resource_name))
        
        return "\n\n".join(code_parts)
    
    def _generate_crud_endpoint(self, resource_name: str) -> str:
        """Generate CRUD endpoints for a resource."""
        singular = resource_name.rstrip('s')
        capitalized = singular.capitalize()
        
        return f'''
@app.get("/api/{resource_name}", tags=["{capitalized}s"])
async def list_{resource_name}(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List all {resource_name}."""
    # TODO: Implement actual query
    return {{"items": [], "total": 0, "skip": skip, "limit": limit}}


@app.post("/api/{resource_name}", tags=["{capitalized}s"])
async def create_{singular}(
    data: dict,
    db: Session = Depends(get_db)
):
    """Create a new {singular}."""
    # TODO: Implement creation logic
    return {{"id": 1, **data, "created_at": datetime.utcnow().isoformat()}}


@app.get("/api/{resource_name}/{{item_id}}", tags=["{capitalized}s"])
async def get_{singular}(item_id: int, db: Session = Depends(get_db)):
    """Get a specific {singular} by ID."""
    # TODO: Implement fetch logic
    return {{"id": item_id, "name": "Sample {singular}"}}
'''
    
    def _get_minimal_template(self) -> str:
        """Return a minimal FastAPI template if no template file exists."""
        return '''"""
Auto-generated FastAPI Backend
"""
from datetime import datetime
from typing import Optional, List
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="Generated API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health():
    return {"status": "ok", "sandbox": True, "timestamp": datetime.utcnow().isoformat()}

@app.get("/")
async def root():
    return {"message": "API is running", "docs": "/docs"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
'''


# =============================================================================
# PREVIEW ORCHESTRATOR
# =============================================================================

class PreviewOrchestrator:
    """
    Orchestrates the complete preview deployment flow.
    
    Ensures:
    - Backend is fully ready before frontend loads
    - Clear error reporting at each stage
    - No mocked APIs unless backend fails
    """
    
    STAGE_WEIGHTS = {
        OrchestrationStage.PENDING: 0,
        OrchestrationStage.GENERATING_BACKEND: 10,
        OrchestrationStage.BUILDING_IMAGE: 30,
        OrchestrationStage.DEPLOYING_CONTAINER: 50,
        OrchestrationStage.WAITING_FOR_HEALTH: 70,
        OrchestrationStage.BACKEND_READY: 85,
        OrchestrationStage.PREPARING_FRONTEND: 95,
        OrchestrationStage.READY: 100,
        OrchestrationStage.FAILED: 0
    }
    
    # Health check configuration
    HEALTH_CHECK_TIMEOUT = 5.0
    HEALTH_CHECK_INTERVAL = 1.0
    HEALTH_CHECK_MAX_RETRIES = 30  # 30 seconds max wait
    
    def __init__(self, deployment_service=None, host_url: str = "http://localhost"):
        """
        Initialize the orchestrator.
        
        Args:
            deployment_service: SandboxDeploymentService instance
            host_url: Base URL for generated preview URLs
        """
        self._sessions: Dict[str, OrchestrationProgress] = {}
        self._deployment_service = deployment_service
        self._host_url = host_url
        self._code_generator = BackendCodeGenerator()
        
        logger.info("PreviewOrchestrator initialized")
    
    def set_deployment_service(self, service):
        """Set the deployment service (for lazy initialization)."""
        self._deployment_service = service
    
    async def start_preview(
        self,
        request: PreviewRequest
    ) -> PreviewResponse:
        """
        Start the full preview orchestration flow.
        
        Returns immediately with session_id for polling,
        or blocks until ready if wait=True in future.
        """
        session_id = f"preview-{request.project_name}-{int(time.time())}"
        
        # Initialize progress tracking
        progress = OrchestrationProgress(
            session_id=session_id,
            stage=OrchestrationStage.PENDING,
            message="Starting preview orchestration..."
        )
        self._sessions[session_id] = progress
        
        try:
            # Execute the orchestration pipeline
            result = await self._execute_pipeline(request, progress)
            return result
            
        except Exception as e:
            logger.error(f"Orchestration failed for {session_id}: {e}")
            progress.stage = OrchestrationStage.FAILED
            progress.error = str(e)
            progress.message = f"Preview failed: {e}"
            progress.updated_at = datetime.utcnow()
            
            return PreviewResponse(
                success=False,
                session_id=session_id,
                status="failed",
                message=progress.message,
                error=str(e),
                mock_mode=True  # Enable mocks as fallback
            )
    
    async def _execute_pipeline(
        self,
        request: PreviewRequest,
        progress: OrchestrationProgress
    ) -> PreviewResponse:
        """Execute the complete orchestration pipeline."""
        
        stage_start = time.time()
        
        # =================================================================
        # STAGE 1: Generate Backend Code (if needed)
        # =================================================================
        self._update_progress(
            progress,
            OrchestrationStage.GENERATING_BACKEND,
            "Analyzing frontend and generating backend code..."
        )
        
        backend_files = request.backend_files or {}
        
        if not backend_files and request.generate_backend:
            # Analyze frontend to generate appropriate backend
            analysis = self._code_generator.analyze_frontend(request.project_files)
            backend_files = self._code_generator.generate_backend_code(
                request.project_name,
                analysis
            )
            logger.info(f"Generated backend with {len(backend_files)} files, features: {analysis.get('features', [])}")
        
        if not backend_files:
            # Use default template
            template_path = Path(__file__).parent / "docker-configs" / "sandbox_main.py"
            if template_path.exists():
                backend_files["main.py"] = template_path.read_text()
        
        progress.stage_times["generating_backend"] = time.time() - stage_start
        
        # =================================================================
        # STAGE 2: Build Docker Image
        # =================================================================
        stage_start = time.time()
        self._update_progress(
            progress,
            OrchestrationStage.BUILDING_IMAGE,
            "Building Docker image for backend..."
        )
        
        if not self._deployment_service:
            raise RuntimeError("Deployment service not available")
        
        # =================================================================
        # STAGE 3: Deploy Container
        # =================================================================
        stage_start = time.time()
        self._update_progress(
            progress,
            OrchestrationStage.DEPLOYING_CONTAINER,
            "Deploying sandbox container..."
        )
        
        # Create sandbox through deployment service (handles build + deploy)
        container = await self._deployment_service.create_sandbox(
            session_id=progress.session_id,
            project_files=backend_files,
            ttl_minutes=request.ttl_minutes
        )
        
        progress.backend_url = container.base_url
        progress.health_check_url = f"{container.base_url}/health"
        progress.stage_times["deploying_container"] = time.time() - stage_start
        
        logger.info(f"Container deployed: {container.container_name} at {container.base_url}")
        
        # =================================================================
        # STAGE 4: Wait for Backend Health
        # =================================================================
        stage_start = time.time()
        self._update_progress(
            progress,
            OrchestrationStage.WAITING_FOR_HEALTH,
            "Waiting for backend to become healthy..."
        )
        
        health_result = await self._poll_health(progress)
        
        if not health_result["healthy"]:
            raise RuntimeError(f"Backend failed health checks: {health_result.get('error', 'Unknown error')}")
        
        progress.backend_config = health_result.get("auth_config", {})
        progress.stage_times["waiting_for_health"] = time.time() - stage_start
        
        logger.info(f"Backend healthy in {progress.stage_times['waiting_for_health']:.2f}s")
        
        # =================================================================
        # STAGE 5: Backend Ready
        # =================================================================
        self._update_progress(
            progress,
            OrchestrationStage.BACKEND_READY,
            "Backend is ready and healthy!"
        )
        
        # =================================================================
        # STAGE 6: Prepare Frontend
        # =================================================================
        stage_start = time.time()
        self._update_progress(
            progress,
            OrchestrationStage.PREPARING_FRONTEND,
            "Preparing frontend preview..."
        )
        
        # Generate frontend preview URL
        progress.frontend_preview_url = (
            f"{self._host_url}/api/sandbox-preview/{request.project_name}"
            f"?backend_url={container.base_url}"
            f"&session_id={progress.session_id}"
        )
        
        progress.stage_times["preparing_frontend"] = time.time() - stage_start
        
        # =================================================================
        # STAGE 7: Ready!
        # =================================================================
        self._update_progress(
            progress,
            OrchestrationStage.READY,
            "Preview is ready!"
        )
        
        total_time = sum(progress.stage_times.values())
        logger.info(f"Preview ready in {total_time:.2f}s total")
        
        return PreviewResponse(
            success=True,
            session_id=progress.session_id,
            status="ready",
            backend_url=progress.backend_url,
            frontend_preview_url=progress.frontend_preview_url,
            message=f"Preview ready! Backend deployed at {progress.backend_url}",
            mock_mode=False,  # Real APIs, no mocks
            backend_config=progress.backend_config
        )
    
    async def _poll_health(self, progress: OrchestrationProgress) -> Dict[str, Any]:
        """
        Poll the backend /health endpoint until ready.
        
        Returns:
            Dict with: healthy (bool), response_time_ms, auth_config, error
        """
        health_url = progress.health_check_url
        
        async with httpx.AsyncClient(timeout=self.HEALTH_CHECK_TIMEOUT) as client:
            for attempt in range(self.HEALTH_CHECK_MAX_RETRIES):
                progress.stage_progress = int((attempt / self.HEALTH_CHECK_MAX_RETRIES) * 100)
                progress.message = f"Health check attempt {attempt + 1}/{self.HEALTH_CHECK_MAX_RETRIES}..."
                progress.updated_at = datetime.utcnow()
                
                try:
                    start = time.time()
                    response = await client.get(health_url)
                    response_time = (time.time() - start) * 1000
                    
                    if response.status_code == 200:
                        data = response.json()
                        if data.get("status") == "ok":
                            logger.info(f"Health check passed on attempt {attempt + 1}")
                            return {
                                "healthy": True,
                                "response_time_ms": response_time,
                                "auth_config": data.get("auth_config"),
                                "error": None
                            }
                    
                except httpx.RequestError as e:
                    logger.debug(f"Health check attempt {attempt + 1} failed: {e}")
                except httpx.TimeoutException:
                    logger.debug(f"Health check attempt {attempt + 1} timed out")
                
                await asyncio.sleep(self.HEALTH_CHECK_INTERVAL)
        
        # All retries exhausted
        return {
            "healthy": False,
            "response_time_ms": 0,
            "auth_config": None,
            "error": f"Backend not healthy after {self.HEALTH_CHECK_MAX_RETRIES} attempts"
        }
    
    def _update_progress(
        self,
        progress: OrchestrationProgress,
        stage: OrchestrationStage,
        message: str
    ):
        """Update progress tracking."""
        progress.stage = stage
        progress.message = message
        progress.overall_progress = self.STAGE_WEIGHTS.get(stage, 0)
        progress.stage_progress = 0
        progress.updated_at = datetime.utcnow()
        
        logger.info(f"[{progress.session_id}] Stage: {stage.value} - {message}")
    
    def get_progress(self, session_id: str) -> Optional[OrchestrationProgress]:
        """Get progress for a session."""
        return self._sessions.get(session_id)
    
    def get_all_sessions(self) -> List[Dict[str, Any]]:
        """Get all active sessions."""
        return [p.to_dict() for p in self._sessions.values()]
    
    async def cancel_preview(self, session_id: str) -> bool:
        """Cancel a preview session and cleanup resources."""
        progress = self._sessions.get(session_id)
        if not progress:
            return False
        
        # Destroy the sandbox container
        if self._deployment_service and progress.backend_url:
            try:
                await self._deployment_service.destroy_sandbox(session_id)
            except Exception as e:
                logger.error(f"Error destroying sandbox: {e}")
        
        # Remove from tracking
        del self._sessions[session_id]
        return True


# =============================================================================
# FASTAPI ROUTER
# =============================================================================

router = APIRouter(prefix="/api/preview", tags=["Preview Orchestration"])
security = HTTPBearer(auto_error=False)

# Global orchestrator instance
_orchestrator: Optional[PreviewOrchestrator] = None


def get_orchestrator() -> PreviewOrchestrator:
    """Get the global orchestrator instance."""
    global _orchestrator
    if not _orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    return _orchestrator


def init_orchestrator(deployment_service=None, host_url: str = "http://localhost:8000"):
    """Initialize the global orchestrator."""
    global _orchestrator
    _orchestrator = PreviewOrchestrator(
        deployment_service=deployment_service,
        host_url=host_url
    )
    return _orchestrator


@router.post("/start", response_model=PreviewResponse)
async def start_preview(
    request: PreviewRequest,
    orchestrator: PreviewOrchestrator = Depends(get_orchestrator)
):
    """
    Start the full preview orchestration flow.
    
    This endpoint:
    1. Generates backend code (if not provided)
    2. Builds a Docker image
    3. Deploys a sandbox container
    4. Waits for the backend to be healthy
    5. Returns the backend URL for frontend injection
    
    The frontend should NOT load until this returns successfully.
    """
    return await orchestrator.start_preview(request)


@router.get("/status/{session_id}")
async def get_preview_status(
    session_id: str,
    orchestrator: PreviewOrchestrator = Depends(get_orchestrator)
):
    """Get the current status of a preview orchestration."""
    progress = orchestrator.get_progress(session_id)
    if not progress:
        raise HTTPException(status_code=404, detail="Session not found")
    return progress.to_dict()


@router.post("/cancel/{session_id}")
async def cancel_preview(
    session_id: str,
    orchestrator: PreviewOrchestrator = Depends(get_orchestrator)
):
    """Cancel a preview session and cleanup resources."""
    success = await orchestrator.cancel_preview(session_id)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"success": True, "message": f"Preview {session_id} cancelled"}


@router.get("/sessions")
async def list_sessions(
    orchestrator: PreviewOrchestrator = Depends(get_orchestrator)
):
    """List all active preview sessions."""
    return {"sessions": orchestrator.get_all_sessions()}


@router.get("/health-check/{session_id}", response_model=HealthCheckResponse)
async def check_backend_health(
    session_id: str,
    orchestrator: PreviewOrchestrator = Depends(get_orchestrator)
):
    """
    Check the health of a deployed backend.
    
    Useful for frontend to verify backend is still running
    before making API calls.
    """
    progress = orchestrator.get_progress(session_id)
    if not progress:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if not progress.backend_url:
        return HealthCheckResponse(
            healthy=False,
            backend_url="",
            response_time_ms=0,
            error="Backend not deployed"
        )
    
    health_url = f"{progress.backend_url}/health"
    
    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            start = time.time()
            response = await client.get(health_url)
            response_time = (time.time() - start) * 1000
            
            if response.status_code == 200:
                data = response.json()
                return HealthCheckResponse(
                    healthy=data.get("status") == "ok",
                    backend_url=progress.backend_url,
                    response_time_ms=response_time,
                    auth_config=data.get("auth_config")
                )
        except Exception as e:
            return HealthCheckResponse(
                healthy=False,
                backend_url=progress.backend_url,
                response_time_ms=0,
                error=str(e)
            )
    
    return HealthCheckResponse(
        healthy=False,
        backend_url=progress.backend_url,
        response_time_ms=0,
        error="Health check failed"
    )


# =============================================================================
# STANDALONE TESTING
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    from fastapi import FastAPI
    
    app = FastAPI(title="Preview Orchestration Service")
    
    # Initialize orchestrator (without deployment service for testing)
    init_orchestrator(host_url="http://localhost:8000")
    
    app.include_router(router)
    
    @app.get("/")
    async def root():
        return {"message": "Preview Orchestration Service", "docs": "/docs"}
    
    uvicorn.run(app, host="0.0.0.0", port=8001)
