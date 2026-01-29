"""
Sandbox Observability Service
==============================
Provides comprehensive observability for sandbox previews including:
- Real-time log streaming and collection
- Health and readiness status with detailed metrics
- Startup failure detection and error surfacing
- Debug context for troubleshooting preview issues

Usage:
    from sandbox_observability import init_observability, router as observability_router
    
    # In main.py
    observability = init_observability(deployment_service, orchestrator)
    app.include_router(observability_router)
"""

import os
import asyncio
import time
import re
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, AsyncGenerator
from dataclasses import dataclass, field
from enum import Enum
from collections import deque
import logging
import json
import subprocess
import httpx
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# =============================================================================
# DATA MODELS
# =============================================================================

class LogLevel(str, Enum):
    """Log severity levels."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class HealthState(str, Enum):
    """Health states for observability."""
    UNKNOWN = "unknown"
    STARTING = "starting"
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    FAILED = "failed"


class FailureCategory(str, Enum):
    """Categories of startup/runtime failures."""
    BUILD_ERROR = "build_error"
    DEPENDENCY_ERROR = "dependency_error"
    IMPORT_ERROR = "import_error"
    SYNTAX_ERROR = "syntax_error"
    RUNTIME_ERROR = "runtime_error"
    PORT_BINDING_ERROR = "port_binding_error"
    TIMEOUT_ERROR = "timeout_error"
    NETWORK_ERROR = "network_error"
    RESOURCE_ERROR = "resource_error"
    CONFIG_ERROR = "config_error"
    UNKNOWN_ERROR = "unknown_error"


@dataclass
class LogEntry:
    """Represents a single log entry."""
    timestamp: datetime
    level: LogLevel
    message: str
    source: str  # 'container', 'orchestrator', 'build'
    session_id: str
    raw_line: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "level": self.level.value,
            "message": self.message,
            "source": self.source,
            "session_id": self.session_id,
            "raw_line": self.raw_line
        }


@dataclass
class StartupFailure:
    """Represents a detected startup failure."""
    category: FailureCategory
    message: str
    details: str
    suggestion: str
    timestamp: datetime
    relevant_logs: List[str] = field(default_factory=list)
    traceback: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "category": self.category.value,
            "message": self.message,
            "details": self.details,
            "suggestion": self.suggestion,
            "timestamp": self.timestamp.isoformat(),
            "relevant_logs": self.relevant_logs,
            "traceback": self.traceback
        }


@dataclass
class HealthMetrics:
    """Detailed health metrics for a sandbox."""
    session_id: str
    state: HealthState
    uptime_seconds: float
    health_checks_total: int
    health_checks_failed: int
    last_check_time: Optional[datetime]
    last_response_time_ms: Optional[float]
    avg_response_time_ms: float
    memory_usage_mb: Optional[float]
    cpu_percent: Optional[float]
    restart_count: int
    errors: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "state": self.state.value,
            "uptime_seconds": round(self.uptime_seconds, 2),
            "health_checks": {
                "total": self.health_checks_total,
                "failed": self.health_checks_failed,
                "success_rate": round(
                    (self.health_checks_total - self.health_checks_failed) / 
                    max(self.health_checks_total, 1) * 100, 1
                )
            },
            "last_check": {
                "time": self.last_check_time.isoformat() if self.last_check_time else None,
                "response_time_ms": round(self.last_response_time_ms, 2) if self.last_response_time_ms else None
            },
            "avg_response_time_ms": round(self.avg_response_time_ms, 2),
            "resources": {
                "memory_mb": round(self.memory_usage_mb, 2) if self.memory_usage_mb else None,
                "cpu_percent": round(self.cpu_percent, 2) if self.cpu_percent else None
            },
            "restart_count": self.restart_count,
            "errors": self.errors
        }


@dataclass
class ObservabilitySnapshot:
    """Complete observability snapshot for a session."""
    session_id: str
    container_name: Optional[str]
    status: str
    health: HealthMetrics
    recent_logs: List[LogEntry]
    failures: List[StartupFailure]
    timeline: List[Dict[str, Any]]  # Ordered list of events
    debug_context: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "container_name": self.container_name,
            "status": self.status,
            "health": self.health.to_dict(),
            "recent_logs": [log.to_dict() for log in self.recent_logs],
            "failures": [f.to_dict() for f in self.failures],
            "timeline": self.timeline,
            "debug_context": self.debug_context
        }


# =============================================================================
# ERROR PATTERN DETECTION
# =============================================================================

# Patterns for detecting various error types in logs
ERROR_PATTERNS = {
    FailureCategory.IMPORT_ERROR: [
        r"ModuleNotFoundError: No module named '([^']+)'",
        r"ImportError: cannot import name '([^']+)'",
        r"ImportError: No module named ([^\s]+)",
    ],
    FailureCategory.SYNTAX_ERROR: [
        r"SyntaxError: (.+)",
        r"IndentationError: (.+)",
        r"TabError: (.+)",
    ],
    FailureCategory.DEPENDENCY_ERROR: [
        r"pkg_resources\.DistributionNotFound: (.+)",
        r"pip.*ERROR: (.+)",
        r"Could not find a version that satisfies",
    ],
    FailureCategory.PORT_BINDING_ERROR: [
        r"Address already in use",
        r"OSError: \[Errno 98\] Address already in use",
        r"bind\(\) failed",
    ],
    FailureCategory.RUNTIME_ERROR: [
        r"RuntimeError: (.+)",
        r"ValueError: (.+)",
        r"TypeError: (.+)",
        r"AttributeError: (.+)",
    ],
    FailureCategory.NETWORK_ERROR: [
        r"ConnectionRefusedError",
        r"ConnectionResetError",
        r"TimeoutError",
    ],
    FailureCategory.RESOURCE_ERROR: [
        r"MemoryError",
        r"ResourceExhausted",
        r"OOM",
        r"out of memory",
    ],
    FailureCategory.CONFIG_ERROR: [
        r"ValidationError",
        r"ConfigError",
        r"Missing required environment variable",
    ],
    FailureCategory.BUILD_ERROR: [
        r"docker build.*failed",
        r"Step \d+/\d+ : .* failed",
        r"ERROR: executor failed",
    ],
}

# Suggestions for each error category
ERROR_SUGGESTIONS = {
    FailureCategory.IMPORT_ERROR: "Check if the required package is installed. You may need to add it to requirements.txt.",
    FailureCategory.SYNTAX_ERROR: "There's a syntax error in your Python code. Check the indicated line for typos or missing characters.",
    FailureCategory.DEPENDENCY_ERROR: "A required dependency is missing. Ensure all packages are listed in requirements.txt with correct versions.",
    FailureCategory.PORT_BINDING_ERROR: "The port is already in use. This usually resolves automatically when the old container is cleaned up.",
    FailureCategory.RUNTIME_ERROR: "The code encountered a runtime error. Review the stack trace for the exact issue.",
    FailureCategory.NETWORK_ERROR: "Network connectivity issue. The backend may still be starting up - try again in a few seconds.",
    FailureCategory.RESOURCE_ERROR: "The container ran out of resources. The generated code may be too resource-intensive.",
    FailureCategory.CONFIG_ERROR: "Configuration error. Check environment variables and settings.",
    FailureCategory.BUILD_ERROR: "Docker build failed. Check the Dockerfile and build output for errors.",
    FailureCategory.TIMEOUT_ERROR: "The operation timed out. The backend may be taking too long to start.",
    FailureCategory.UNKNOWN_ERROR: "An unexpected error occurred. Check the logs for more details.",
}


def detect_failure_category(log_text: str) -> Optional[tuple[FailureCategory, str]]:
    """Detect the failure category from log text."""
    for category, patterns in ERROR_PATTERNS.items():
        for pattern in patterns:
            match = re.search(pattern, log_text, re.IGNORECASE)
            if match:
                return (category, match.group(0))
    return None


def extract_traceback(log_text: str) -> Optional[str]:
    """Extract Python traceback from log text."""
    traceback_pattern = r'Traceback \(most recent call last\):.*?(?=\n[^\s]|\Z)'
    match = re.search(traceback_pattern, log_text, re.DOTALL)
    return match.group(0) if match else None


def parse_log_level(line: str) -> LogLevel:
    """Parse log level from a log line."""
    line_upper = line.upper()
    if "ERROR" in line_upper or "CRITICAL" in line_upper:
        return LogLevel.ERROR
    elif "WARNING" in line_upper or "WARN" in line_upper:
        return LogLevel.WARNING
    elif "DEBUG" in line_upper:
        return LogLevel.DEBUG
    return LogLevel.INFO


# =============================================================================
# PYDANTIC MODELS FOR API
# =============================================================================

class LogsRequest(BaseModel):
    """Request for logs."""
    tail: int = 100
    since_timestamp: Optional[str] = None
    level_filter: Optional[str] = None


class HealthCheckResult(BaseModel):
    """Health check result."""
    session_id: str
    healthy: bool
    state: str
    response_time_ms: Optional[float]
    error: Optional[str]
    timestamp: str


class FailureResponse(BaseModel):
    """Response containing failure information."""
    has_failure: bool
    failure: Optional[Dict[str, Any]]
    actionable_steps: List[str]


# =============================================================================
# OBSERVABILITY SERVICE
# =============================================================================

class SandboxObservabilityService:
    """
    Comprehensive observability service for sandbox previews.
    
    Provides:
    - Log collection and streaming
    - Health metrics tracking
    - Failure detection and analysis
    - Debug context generation
    """
    
    # How many logs to keep in memory per session
    MAX_LOGS_PER_SESSION = 500
    
    # Health check history size
    HEALTH_HISTORY_SIZE = 50
    
    def __init__(
        self,
        deployment_service=None,
        orchestrator=None
    ):
        """
        Initialize observability service.
        
        Args:
            deployment_service: SandboxDeploymentService instance
            orchestrator: PreviewOrchestrator instance
        """
        self.deployment_service = deployment_service
        self.orchestrator = orchestrator
        
        # Per-session data stores
        self._logs: Dict[str, deque] = {}  # session_id -> deque of LogEntry
        self._failures: Dict[str, List[StartupFailure]] = {}
        self._health_history: Dict[str, deque] = {}  # session_id -> deque of response times
        self._timelines: Dict[str, List[Dict[str, Any]]] = {}
        self._metrics: Dict[str, Dict[str, Any]] = {}  # Cached metrics
        
        # Background task for log collection
        self._collection_task: Optional[asyncio.Task] = None
        self._running = False
    
    async def start(self):
        """Start the observability service."""
        if self._running:
            return
        
        self._running = True
        self._collection_task = asyncio.create_task(self._log_collection_loop())
        logger.info("Sandbox observability service started")
    
    async def stop(self):
        """Stop the observability service."""
        self._running = False
        if self._collection_task:
            self._collection_task.cancel()
            try:
                await self._collection_task
            except asyncio.CancelledError:
                pass
        logger.info("Sandbox observability service stopped")
    
    async def _log_collection_loop(self):
        """Background task to collect logs from active containers."""
        while self._running:
            try:
                if self.deployment_service:
                    containers = await self.deployment_service.list_sandboxes()
                    for container in containers:
                        await self._collect_container_logs(container.session_id)
                
                await asyncio.sleep(5)  # Collect every 5 seconds
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Log collection error: {e}")
                await asyncio.sleep(10)
    
    async def _collect_container_logs(self, session_id: str):
        """Collect logs from a container and process them."""
        if not self.deployment_service:
            return
        
        try:
            raw_logs = await self.deployment_service.get_logs(session_id, tail=50)
            if not raw_logs:
                return
            
            # Initialize log storage if needed
            if session_id not in self._logs:
                self._logs[session_id] = deque(maxlen=self.MAX_LOGS_PER_SESSION)
            
            # Parse and store new logs
            for line in raw_logs.split('\n'):
                if not line.strip():
                    continue
                
                entry = LogEntry(
                    timestamp=datetime.utcnow(),
                    level=parse_log_level(line),
                    message=line.strip(),
                    source="container",
                    session_id=session_id,
                    raw_line=line
                )
                self._logs[session_id].append(entry)
                
                # Check for failures in this log line
                await self._check_for_failure(session_id, line)
        
        except Exception as e:
            logger.error(f"Failed to collect logs for {session_id}: {e}")
    
    async def _check_for_failure(self, session_id: str, log_line: str):
        """Check a log line for failure patterns."""
        result = detect_failure_category(log_line)
        if not result:
            return
        
        category, matched_text = result
        
        # Initialize failures list if needed
        if session_id not in self._failures:
            self._failures[session_id] = []
        
        # Don't add duplicate failures
        for existing in self._failures[session_id]:
            if existing.category == category and matched_text in existing.details:
                return
        
        # Extract traceback if available
        logs = self._logs.get(session_id, deque())
        recent_logs = [entry.raw_line for entry in list(logs)[-20:] if entry.raw_line]
        full_log_text = '\n'.join(recent_logs)
        traceback = extract_traceback(full_log_text)
        
        failure = StartupFailure(
            category=category,
            message=f"{category.value.replace('_', ' ').title()} Detected",
            details=matched_text,
            suggestion=ERROR_SUGGESTIONS.get(category, "Check the logs for more details."),
            timestamp=datetime.utcnow(),
            relevant_logs=recent_logs[-10:],
            traceback=traceback
        )
        
        self._failures[session_id].append(failure)
        
        # Add to timeline
        await self._add_timeline_event(
            session_id,
            "failure_detected",
            {
                "category": category.value,
                "message": matched_text
            }
        )
        
        logger.warning(f"Failure detected for {session_id}: {category.value}")
    
    async def _add_timeline_event(
        self,
        session_id: str,
        event_type: str,
        data: Dict[str, Any]
    ):
        """Add an event to the session timeline."""
        if session_id not in self._timelines:
            self._timelines[session_id] = []
        
        self._timelines[session_id].append({
            "timestamp": datetime.utcnow().isoformat(),
            "event": event_type,
            "data": data
        })
    
    # =========================================================================
    # PUBLIC API METHODS
    # =========================================================================
    
    async def get_logs(
        self,
        session_id: str,
        tail: int = 100,
        level_filter: Optional[LogLevel] = None,
        since: Optional[datetime] = None
    ) -> List[LogEntry]:
        """
        Get logs for a session.
        
        Args:
            session_id: Session identifier
            tail: Number of recent logs to return
            level_filter: Filter by log level
            since: Only return logs after this timestamp
        
        Returns:
            List of LogEntry objects
        """
        # Try to collect fresh logs
        await self._collect_container_logs(session_id)
        
        logs = list(self._logs.get(session_id, []))
        
        # Apply filters
        if level_filter:
            logs = [l for l in logs if l.level == level_filter]
        
        if since:
            logs = [l for l in logs if l.timestamp > since]
        
        # Return most recent
        return logs[-tail:]
    
    async def stream_logs(
        self,
        session_id: str,
        poll_interval: float = 1.0
    ) -> AsyncGenerator[str, None]:
        """
        Stream logs in real-time using Server-Sent Events format.
        
        Args:
            session_id: Session identifier
            poll_interval: How often to check for new logs
        
        Yields:
            SSE formatted log entries
        """
        last_count = 0
        
        while True:
            try:
                logs = await self.get_logs(session_id, tail=50)
                
                # Yield new logs since last check
                if len(logs) > last_count:
                    new_logs = logs[last_count:]
                    for entry in new_logs:
                        yield f"data: {json.dumps(entry.to_dict())}\n\n"
                    last_count = len(logs)
                
                await asyncio.sleep(poll_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
                await asyncio.sleep(poll_interval * 2)
    
    async def get_health_metrics(self, session_id: str) -> HealthMetrics:
        """
        Get detailed health metrics for a session.
        
        Args:
            session_id: Session identifier
        
        Returns:
            HealthMetrics object with detailed stats
        """
        # Initialize history if needed
        if session_id not in self._health_history:
            self._health_history[session_id] = deque(maxlen=self.HEALTH_HISTORY_SIZE)
        
        # Perform health check
        health_result = await self._perform_health_check(session_id)
        
        # Get container info
        container = None
        created_at = datetime.utcnow()
        if self.deployment_service:
            container = await self.deployment_service.get_sandbox(session_id)
            if container:
                created_at = container.created_at
        
        # Calculate uptime
        uptime = (datetime.utcnow() - created_at).total_seconds()
        
        # Get resource usage
        memory_mb, cpu_percent = await self._get_resource_usage(session_id)
        
        # Get history stats
        history = list(self._health_history.get(session_id, []))
        successful = [h for h in history if h.get("healthy")]
        failed = len(history) - len(successful)
        
        response_times = [h["response_time_ms"] for h in successful if h.get("response_time_ms")]
        avg_response = sum(response_times) / len(response_times) if response_times else 0
        
        # Determine state
        if not container:
            state = HealthState.UNKNOWN
        elif health_result.get("healthy"):
            state = HealthState.HEALTHY
        elif failed > len(history) * 0.5:
            state = HealthState.UNHEALTHY
        elif failed > 0:
            state = HealthState.DEGRADED
        else:
            state = HealthState.STARTING
        
        # Get recent errors
        failures = self._failures.get(session_id, [])
        errors = [f.message for f in failures[-5:]]
        
        return HealthMetrics(
            session_id=session_id,
            state=state,
            uptime_seconds=uptime,
            health_checks_total=len(history),
            health_checks_failed=failed,
            last_check_time=datetime.utcnow(),
            last_response_time_ms=health_result.get("response_time_ms"),
            avg_response_time_ms=avg_response,
            memory_usage_mb=memory_mb,
            cpu_percent=cpu_percent,
            restart_count=0,  # TODO: Track restarts
            errors=errors
        )
    
    async def _perform_health_check(self, session_id: str) -> Dict[str, Any]:
        """Perform a health check and record the result."""
        result = {
            "timestamp": datetime.utcnow().isoformat(),
            "healthy": False,
            "response_time_ms": None,
            "error": None
        }
        
        # Get container URL
        container = None
        if self.deployment_service:
            container = await self.deployment_service.get_sandbox(session_id)
        
        if not container:
            result["error"] = "Container not found"
            return result
        
        health_url = f"{container.base_url}/health"
        
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                start = time.time()
                response = await client.get(health_url)
                response_time = (time.time() - start) * 1000
                
                result["response_time_ms"] = response_time
                
                if response.status_code == 200:
                    result["healthy"] = True
                    result["response_data"] = response.json()
                else:
                    result["error"] = f"Status code: {response.status_code}"
        
        except Exception as e:
            result["error"] = str(e)
        
        # Record in history
        if session_id not in self._health_history:
            self._health_history[session_id] = deque(maxlen=self.HEALTH_HISTORY_SIZE)
        self._health_history[session_id].append(result)
        
        return result
    
    async def _get_resource_usage(
        self,
        session_id: str
    ) -> tuple[Optional[float], Optional[float]]:
        """Get memory and CPU usage for a container."""
        if not self.deployment_service:
            return None, None
        
        container = await self.deployment_service.get_sandbox(session_id)
        if not container:
            return None, None
        
        try:
            # Get Docker stats
            result = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: subprocess.run(
                    [
                        "docker", "stats", "--no-stream",
                        "--format", "{{.MemUsage}}|{{.CPUPerc}}",
                        container.container_name
                    ],
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=5
                )
            )
            
            if result.returncode == 0 and result.stdout.strip():
                parts = result.stdout.strip().split('|')
                if len(parts) == 2:
                    # Parse memory (e.g., "150MiB / 512MiB")
                    mem_str = parts[0].split('/')[0].strip()
                    memory_mb = self._parse_memory(mem_str)
                    
                    # Parse CPU (e.g., "5.50%")
                    cpu_str = parts[1].strip().rstrip('%')
                    cpu_percent = float(cpu_str) if cpu_str else None
                    
                    return memory_mb, cpu_percent
        
        except Exception as e:
            logger.debug(f"Could not get resource usage: {e}")
        
        return None, None
    
    def _parse_memory(self, mem_str: str) -> Optional[float]:
        """Parse memory string like '150MiB' or '1.5GiB' to MB."""
        try:
            mem_str = mem_str.strip()
            if 'GiB' in mem_str:
                return float(mem_str.replace('GiB', '')) * 1024
            elif 'MiB' in mem_str:
                return float(mem_str.replace('MiB', ''))
            elif 'KiB' in mem_str:
                return float(mem_str.replace('KiB', '')) / 1024
            elif 'GB' in mem_str:
                return float(mem_str.replace('GB', '')) * 1000
            elif 'MB' in mem_str:
                return float(mem_str.replace('MB', ''))
            return float(mem_str)
        except:
            return None
    
    async def get_failures(self, session_id: str) -> List[StartupFailure]:
        """
        Get detected failures for a session.
        
        Args:
            session_id: Session identifier
        
        Returns:
            List of StartupFailure objects
        """
        # Refresh log collection to catch any new failures
        await self._collect_container_logs(session_id)
        return self._failures.get(session_id, [])
    
    async def analyze_failure(self, session_id: str) -> FailureResponse:
        """
        Analyze failures and provide actionable steps.
        
        Args:
            session_id: Session identifier
        
        Returns:
            FailureResponse with analysis and suggestions
        """
        failures = await self.get_failures(session_id)
        
        if not failures:
            return FailureResponse(
                has_failure=False,
                failure=None,
                actionable_steps=[]
            )
        
        # Get the most recent/relevant failure
        primary_failure = failures[-1]
        
        # Generate actionable steps based on failure type
        steps = self._generate_actionable_steps(primary_failure, failures)
        
        return FailureResponse(
            has_failure=True,
            failure=primary_failure.to_dict(),
            actionable_steps=steps
        )
    
    def _generate_actionable_steps(
        self,
        primary: StartupFailure,
        all_failures: List[StartupFailure]
    ) -> List[str]:
        """Generate actionable debugging steps."""
        steps = []
        
        if primary.category == FailureCategory.IMPORT_ERROR:
            # Extract module name if possible
            match = re.search(r"No module named '([^']+)'", primary.details)
            module = match.group(1) if match else "the missing module"
            steps = [
                f"Add '{module}' to your requirements.txt file",
                "Regenerate the backend code",
                "If using a custom package, ensure it's spelled correctly"
            ]
        
        elif primary.category == FailureCategory.SYNTAX_ERROR:
            steps = [
                "Review the indicated line in the generated code",
                "Check for missing colons, parentheses, or brackets",
                "Regenerate the backend with clearer instructions"
            ]
        
        elif primary.category == FailureCategory.PORT_BINDING_ERROR:
            steps = [
                "Wait a moment for the previous container to be cleaned up",
                "The system will automatically retry",
                "If the issue persists, try generating a new preview"
            ]
        
        elif primary.category == FailureCategory.TIMEOUT_ERROR:
            steps = [
                "The backend may be doing heavy initialization",
                "Check if the generated code has infinite loops",
                "Try simplifying the requirements"
            ]
        
        elif primary.category == FailureCategory.DEPENDENCY_ERROR:
            steps = [
                "Check that all required packages are in requirements.txt",
                "Ensure package versions are compatible",
                "Some packages may not be available in the sandbox"
            ]
        
        else:
            steps = [
                "Review the error message and stack trace",
                "Check the container logs for more context",
                "Try regenerating the backend with simplified requirements"
            ]
        
        # Add traceback tip if available
        if primary.traceback:
            steps.append("Stack trace is available in the debug panel")
        
        return steps
    
    async def get_full_snapshot(self, session_id: str) -> ObservabilitySnapshot:
        """
        Get a complete observability snapshot for a session.
        
        This is the primary method for getting all debugging context.
        
        Args:
            session_id: Session identifier
        
        Returns:
            ObservabilitySnapshot with all available data
        """
        # Gather all data
        logs = await self.get_logs(session_id, tail=100)
        health = await self.get_health_metrics(session_id)
        failures = await self.get_failures(session_id)
        
        # Get container info
        container_name = None
        status = "unknown"
        if self.deployment_service:
            container = await self.deployment_service.get_sandbox(session_id)
            if container:
                container_name = container.container_name
                status = container.status.value
        
        # Get orchestration status if available
        orchestration_status = None
        if self.orchestrator:
            progress = self.orchestrator.get_progress(session_id)
            if progress:
                status = progress.stage.value
                orchestration_status = progress.to_dict()
        
        # Get timeline
        timeline = self._timelines.get(session_id, [])
        
        # Build debug context
        debug_context = {
            "container_name": container_name,
            "orchestration": orchestration_status,
            "total_logs": len(self._logs.get(session_id, [])),
            "total_failures": len(failures),
            "error_categories": list(set(f.category.value for f in failures)),
            "has_traceback": any(f.traceback for f in failures)
        }
        
        return ObservabilitySnapshot(
            session_id=session_id,
            container_name=container_name,
            status=status,
            health=health,
            recent_logs=logs,
            failures=failures,
            timeline=timeline,
            debug_context=debug_context
        )
    
    async def clear_session_data(self, session_id: str):
        """Clear all observability data for a session."""
        self._logs.pop(session_id, None)
        self._failures.pop(session_id, None)
        self._health_history.pop(session_id, None)
        self._timelines.pop(session_id, None)
        self._metrics.pop(session_id, None)
        logger.info(f"Cleared observability data for session {session_id}")


# =============================================================================
# FASTAPI ROUTER
# =============================================================================

router = APIRouter(prefix="/api/observability", tags=["observability"])

# Global service instance
_observability: Optional[SandboxObservabilityService] = None


def get_observability() -> SandboxObservabilityService:
    """Dependency to get the observability service."""
    if _observability is None:
        raise HTTPException(
            status_code=503,
            detail="Observability service not initialized"
        )
    return _observability


def init_observability(
    deployment_service=None,
    orchestrator=None
) -> SandboxObservabilityService:
    """Initialize the global observability service."""
    global _observability
    _observability = SandboxObservabilityService(
        deployment_service=deployment_service,
        orchestrator=orchestrator
    )
    return _observability


@router.get("/logs/{session_id}")
async def get_session_logs(
    session_id: str,
    tail: int = Query(100, ge=1, le=1000),
    level: Optional[str] = Query(None),
    observability: SandboxObservabilityService = Depends(get_observability)
):
    """
    Get logs for a sandbox session.
    
    Args:
        session_id: Session identifier
        tail: Number of recent logs to return (default 100)
        level: Filter by log level (debug, info, warning, error)
    
    Returns:
        List of log entries
    """
    level_filter = None
    if level:
        try:
            level_filter = LogLevel(level.lower())
        except ValueError:
            pass
    
    logs = await observability.get_logs(session_id, tail=tail, level_filter=level_filter)
    return {
        "session_id": session_id,
        "count": len(logs),
        "logs": [log.to_dict() for log in logs]
    }


@router.get("/logs/{session_id}/stream")
async def stream_session_logs(
    session_id: str,
    observability: SandboxObservabilityService = Depends(get_observability)
):
    """
    Stream logs in real-time using Server-Sent Events.
    
    Connect to this endpoint to receive live log updates.
    """
    return StreamingResponse(
        observability.stream_logs(session_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@router.get("/health/{session_id}")
async def get_session_health(
    session_id: str,
    observability: SandboxObservabilityService = Depends(get_observability)
):
    """
    Get detailed health metrics for a sandbox session.
    
    Returns comprehensive health information including:
    - Health state (healthy, degraded, unhealthy)
    - Uptime and response times
    - Resource usage (memory, CPU)
    - Recent errors
    """
    metrics = await observability.get_health_metrics(session_id)
    return metrics.to_dict()


@router.get("/failures/{session_id}")
async def get_session_failures(
    session_id: str,
    observability: SandboxObservabilityService = Depends(get_observability)
):
    """
    Get detected failures for a sandbox session.
    
    Automatically analyzes logs to detect common failure patterns
    and provides categorized error information.
    """
    failures = await observability.get_failures(session_id)
    return {
        "session_id": session_id,
        "count": len(failures),
        "failures": [f.to_dict() for f in failures]
    }


@router.get("/failures/{session_id}/analyze")
async def analyze_session_failure(
    session_id: str,
    observability: SandboxObservabilityService = Depends(get_observability)
):
    """
    Analyze failures and get actionable debugging steps.
    
    Returns:
    - Whether a failure was detected
    - Details of the primary failure
    - List of suggested actions to resolve the issue
    """
    result = await observability.analyze_failure(session_id)
    return result.dict()


@router.get("/snapshot/{session_id}")
async def get_session_snapshot(
    session_id: str,
    observability: SandboxObservabilityService = Depends(get_observability)
):
    """
    Get a complete observability snapshot for debugging.
    
    This is the primary endpoint for troubleshooting preview issues.
    Returns all available context including:
    - Health metrics
    - Recent logs
    - Detected failures
    - Event timeline
    - Debug context
    """
    snapshot = await observability.get_full_snapshot(session_id)
    return snapshot.to_dict()


@router.delete("/session/{session_id}")
async def clear_session_observability(
    session_id: str,
    observability: SandboxObservabilityService = Depends(get_observability)
):
    """Clear observability data for a session."""
    await observability.clear_session_data(session_id)
    return {"success": True, "message": f"Cleared data for session {session_id}"}


@router.get("/summary")
async def get_observability_summary(
    observability: SandboxObservabilityService = Depends(get_observability)
):
    """
    Get a summary of all active sessions' observability status.
    
    Useful for admin dashboards and monitoring.
    """
    sessions = []
    
    for session_id in list(observability._logs.keys()):
        health = await observability.get_health_metrics(session_id)
        failures = observability._failures.get(session_id, [])
        
        sessions.append({
            "session_id": session_id,
            "health_state": health.state.value,
            "failure_count": len(failures),
            "uptime_seconds": health.uptime_seconds
        })
    
    return {
        "total_sessions": len(sessions),
        "sessions": sessions
    }


# =============================================================================
# STANDALONE TESTING
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    from fastapi import FastAPI
    
    app = FastAPI(title="Sandbox Observability Service")
    
    # Initialize without dependencies for testing
    init_observability()
    
    app.include_router(router)
    
    @app.get("/")
    async def root():
        return {
            "message": "Sandbox Observability Service",
            "docs": "/docs",
            "endpoints": {
                "logs": "/api/observability/logs/{session_id}",
                "health": "/api/observability/health/{session_id}",
                "failures": "/api/observability/failures/{session_id}",
                "snapshot": "/api/observability/snapshot/{session_id}"
            }
        }
    
    uvicorn.run(app, host="0.0.0.0", port=8002)
