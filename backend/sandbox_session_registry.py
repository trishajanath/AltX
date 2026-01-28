"""
Sandbox Session Registry
========================
Maps preview sessions to sandbox backend URLs with user ownership tracking.

Features:
- Session → Backend URL mapping
- User ownership verification (prevents cross-user access)
- Automatic expiration synchronized with containers
- Thread-safe operations
"""

import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, field
from enum import Enum
import logging
import threading

logger = logging.getLogger(__name__)


@dataclass
class SandboxSession:
    """Represents a sandbox session with ownership."""
    session_id: str
    user_id: str
    backend_url: str
    container_name: str
    created_at: datetime
    expires_at: datetime
    project_name: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def is_expired(self) -> bool:
        return datetime.utcnow() >= self.expires_at
    
    @property
    def ttl_seconds(self) -> int:
        return max(0, int((self.expires_at - datetime.utcnow()).total_seconds()))
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "backend_url": self.backend_url,
            "container_name": self.container_name,
            "project_name": self.project_name,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "ttl_seconds": self.ttl_seconds,
            "is_expired": self.is_expired,
            "metadata": self.metadata
        }


class SessionAccessError(Exception):
    """Raised when a user attempts to access another user's session."""
    pass


class SessionNotFoundError(Exception):
    """Raised when a session is not found."""
    pass


class SessionExpiredError(Exception):
    """Raised when a session has expired."""
    pass


class SandboxSessionRegistry:
    """
    Thread-safe registry for sandbox session → backend URL mappings.
    
    Provides:
    - User-scoped session management
    - Automatic expiration cleanup
    - Cross-user access prevention
    """
    
    # Cleanup interval in seconds
    CLEANUP_INTERVAL = 30
    
    def __init__(self):
        # Main registry: session_id -> SandboxSession
        self._sessions: Dict[str, SandboxSession] = {}
        
        # User index: user_id -> set of session_ids
        self._user_sessions: Dict[str, set] = {}
        
        # Thread lock for safe concurrent access
        self._lock = threading.RLock()
        
        # Background cleanup task
        self._cleanup_task: Optional[asyncio.Task] = None
        self._running = False
    
    async def start(self):
        """Start the registry with background cleanup."""
        if self._running:
            return
        
        self._running = True
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.info("Sandbox session registry started")
    
    async def stop(self):
        """Stop the registry and cleanup."""
        self._running = False
        
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        
        with self._lock:
            self._sessions.clear()
            self._user_sessions.clear()
        
        logger.info("Sandbox session registry stopped")
    
    async def _cleanup_loop(self):
        """Background task to remove expired sessions."""
        while self._running:
            try:
                await asyncio.sleep(self.CLEANUP_INTERVAL)
                self._cleanup_expired()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Registry cleanup error: {e}")
    
    def _cleanup_expired(self):
        """Remove all expired sessions."""
        with self._lock:
            expired_ids = [
                sid for sid, session in self._sessions.items()
                if session.is_expired
            ]
            
            for session_id in expired_ids:
                self._remove_session_unsafe(session_id)
            
            if expired_ids:
                logger.info(f"Cleaned up {len(expired_ids)} expired sessions")
    
    def _remove_session_unsafe(self, session_id: str):
        """Remove a session without acquiring lock (caller must hold lock)."""
        session = self._sessions.pop(session_id, None)
        if session:
            user_sessions = self._user_sessions.get(session.user_id)
            if user_sessions:
                user_sessions.discard(session_id)
                if not user_sessions:
                    del self._user_sessions[session.user_id]
    
    def register(
        self,
        session_id: str,
        user_id: str,
        backend_url: str,
        container_name: str,
        expires_at: datetime,
        project_name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> SandboxSession:
        """
        Register a new sandbox session.
        
        Args:
            session_id: Unique session identifier
            user_id: Owner's user ID
            backend_url: Backend API base URL
            container_name: Docker container name
            expires_at: Expiration timestamp
            project_name: Optional project name
            metadata: Optional additional data
        
        Returns:
            SandboxSession object
        """
        session = SandboxSession(
            session_id=session_id,
            user_id=user_id,
            backend_url=backend_url,
            container_name=container_name,
            created_at=datetime.utcnow(),
            expires_at=expires_at,
            project_name=project_name,
            metadata=metadata or {}
        )
        
        with self._lock:
            # Remove existing session if present
            if session_id in self._sessions:
                self._remove_session_unsafe(session_id)
            
            # Add to main registry
            self._sessions[session_id] = session
            
            # Add to user index
            if user_id not in self._user_sessions:
                self._user_sessions[user_id] = set()
            self._user_sessions[user_id].add(session_id)
        
        logger.info(f"Registered session {session_id} for user {user_id}")
        return session
    
    def get_backend_url(
        self,
        session_id: str,
        user_id: str,
        check_expiry: bool = True
    ) -> str:
        """
        Get the backend URL for a session with user verification.
        
        Args:
            session_id: Session identifier
            user_id: Requesting user's ID
            check_expiry: Whether to check if session is expired
        
        Returns:
            Backend base URL
        
        Raises:
            SessionNotFoundError: Session doesn't exist
            SessionAccessError: User doesn't own this session
            SessionExpiredError: Session has expired
        """
        with self._lock:
            session = self._sessions.get(session_id)
            
            if not session:
                raise SessionNotFoundError(f"Session {session_id} not found")
            
            # Verify ownership - CRITICAL for security
            if session.user_id != user_id:
                logger.warning(
                    f"Cross-user access attempt: user {user_id} "
                    f"tried to access session {session_id} owned by {session.user_id}"
                )
                raise SessionAccessError("Access denied: session belongs to another user")
            
            if check_expiry and session.is_expired:
                # Auto-cleanup expired session
                self._remove_session_unsafe(session_id)
                raise SessionExpiredError(f"Session {session_id} has expired")
            
            return session.backend_url
    
    def get_session(
        self,
        session_id: str,
        user_id: str,
        check_expiry: bool = True
    ) -> SandboxSession:
        """
        Get full session details with user verification.
        
        Args:
            session_id: Session identifier
            user_id: Requesting user's ID
            check_expiry: Whether to check if session is expired
        
        Returns:
            SandboxSession object
        
        Raises:
            SessionNotFoundError: Session doesn't exist
            SessionAccessError: User doesn't own this session
            SessionExpiredError: Session has expired
        """
        with self._lock:
            session = self._sessions.get(session_id)
            
            if not session:
                raise SessionNotFoundError(f"Session {session_id} not found")
            
            if session.user_id != user_id:
                logger.warning(
                    f"Cross-user access attempt: user {user_id} "
                    f"tried to access session {session_id}"
                )
                raise SessionAccessError("Access denied: session belongs to another user")
            
            if check_expiry and session.is_expired:
                self._remove_session_unsafe(session_id)
                raise SessionExpiredError(f"Session {session_id} has expired")
            
            return session
    
    def get_user_sessions(self, user_id: str) -> List[SandboxSession]:
        """
        Get all active sessions for a user.
        
        Args:
            user_id: User identifier
        
        Returns:
            List of SandboxSession objects (non-expired only)
        """
        with self._lock:
            session_ids = self._user_sessions.get(user_id, set()).copy()
            sessions = []
            
            for sid in session_ids:
                session = self._sessions.get(sid)
                if session and not session.is_expired:
                    sessions.append(session)
                elif session and session.is_expired:
                    self._remove_session_unsafe(sid)
            
            return sessions
    
    def unregister(self, session_id: str, user_id: str) -> bool:
        """
        Remove a session with user verification.
        
        Args:
            session_id: Session identifier
            user_id: Requesting user's ID
        
        Returns:
            True if removed, False if not found
        
        Raises:
            SessionAccessError: User doesn't own this session
        """
        with self._lock:
            session = self._sessions.get(session_id)
            
            if not session:
                return False
            
            if session.user_id != user_id:
                raise SessionAccessError("Access denied: session belongs to another user")
            
            self._remove_session_unsafe(session_id)
            logger.info(f"Unregistered session {session_id}")
            return True
    
    def extend_expiry(
        self,
        session_id: str,
        user_id: str,
        new_expires_at: datetime
    ) -> SandboxSession:
        """
        Extend session expiry time.
        
        Args:
            session_id: Session identifier
            user_id: Requesting user's ID
            new_expires_at: New expiration timestamp
        
        Returns:
            Updated SandboxSession
        
        Raises:
            SessionNotFoundError: Session doesn't exist
            SessionAccessError: User doesn't own this session
        """
        with self._lock:
            session = self._sessions.get(session_id)
            
            if not session:
                raise SessionNotFoundError(f"Session {session_id} not found")
            
            if session.user_id != user_id:
                raise SessionAccessError("Access denied: session belongs to another user")
            
            session.expires_at = new_expires_at
            logger.info(f"Extended session {session_id} to {new_expires_at}")
            return session
    
    def force_unregister(self, session_id: str) -> bool:
        """
        Remove a session without user verification (admin use only).
        
        Args:
            session_id: Session identifier
        
        Returns:
            True if removed, False if not found
        """
        with self._lock:
            if session_id not in self._sessions:
                return False
            
            self._remove_session_unsafe(session_id)
            logger.info(f"Force unregistered session {session_id}")
            return True
    
    def get_stats(self) -> Dict[str, Any]:
        """Get registry statistics."""
        with self._lock:
            total_sessions = len(self._sessions)
            total_users = len(self._user_sessions)
            
            expired_count = sum(
                1 for s in self._sessions.values() if s.is_expired
            )
            
            return {
                "total_sessions": total_sessions,
                "active_sessions": total_sessions - expired_count,
                "expired_sessions": expired_count,
                "total_users": total_users
            }


# =============================================================================
# Global Registry Instance
# =============================================================================

# Singleton registry instance
_registry: Optional[SandboxSessionRegistry] = None


def get_registry() -> SandboxSessionRegistry:
    """Get the global registry instance."""
    global _registry
    if _registry is None:
        _registry = SandboxSessionRegistry()
    return _registry


async def init_registry() -> SandboxSessionRegistry:
    """Initialize and start the global registry."""
    registry = get_registry()
    await registry.start()
    return registry


async def shutdown_registry():
    """Shutdown the global registry."""
    global _registry
    if _registry:
        await _registry.stop()
        _registry = None


# =============================================================================
# FastAPI Integration
# =============================================================================

from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/sessions", tags=["Session Registry"])
security = HTTPBearer()


class RegisterSessionRequest(BaseModel):
    session_id: str = Field(..., description="Unique session identifier")
    backend_url: str = Field(..., description="Backend API base URL")
    container_name: str = Field(..., description="Docker container name")
    ttl_minutes: int = Field(default=45, ge=30, le=60)
    project_name: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class SessionResponse(BaseModel):
    success: bool
    session: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class BackendUrlResponse(BaseModel):
    session_id: str
    backend_url: str
    ttl_seconds: int


# Helper to extract user_id from token (integrate with your auth system)
async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> str:
    """
    Extract user ID from JWT token.
    Replace with your actual token verification logic.
    """
    # Import your auth verification function
    try:
        from auth import verify_token
        payload = verify_token(credentials.credentials)
        if not payload:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # Extract user ID from token payload
        user_id = payload.get("sub") or payload.get("user_id") or payload.get("email")
        if not user_id:
            raise HTTPException(status_code=401, detail="No user ID in token")
        
        return str(user_id)
    except ImportError:
        # Fallback for testing - extract from token directly
        import base64
        import json
        try:
            parts = credentials.credentials.split(".")
            if len(parts) >= 2:
                payload_b64 = parts[1] + "=" * (4 - len(parts[1]) % 4)
                payload = json.loads(base64.urlsafe_b64decode(payload_b64))
                return payload.get("sub", "unknown")
        except:
            pass
        raise HTTPException(status_code=401, detail="Invalid token")


@router.post("/register", response_model=SessionResponse)
async def register_session(
    request: RegisterSessionRequest,
    user_id: str = Depends(get_current_user_id)
):
    """
    Register a new sandbox session for the authenticated user.
    """
    registry = get_registry()
    
    try:
        session = registry.register(
            session_id=request.session_id,
            user_id=user_id,
            backend_url=request.backend_url,
            container_name=request.container_name,
            expires_at=datetime.utcnow() + timedelta(minutes=request.ttl_minutes),
            project_name=request.project_name,
            metadata=request.metadata
        )
        return SessionResponse(success=True, session=session.to_dict())
    
    except Exception as e:
        logger.error(f"Failed to register session: {e}")
        return SessionResponse(success=False, error=str(e))


@router.get("/{session_id}/backend-url", response_model=BackendUrlResponse)
async def get_backend_url(
    session_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """
    Get the backend URL for a session (user must own the session).
    
    This is the primary function for the frontend preview launcher.
    """
    registry = get_registry()
    
    try:
        session = registry.get_session(session_id, user_id)
        return BackendUrlResponse(
            session_id=session_id,
            backend_url=session.backend_url,
            ttl_seconds=session.ttl_seconds
        )
    
    except SessionNotFoundError:
        raise HTTPException(status_code=404, detail="Session not found")
    except SessionAccessError:
        raise HTTPException(status_code=403, detail="Access denied")
    except SessionExpiredError:
        raise HTTPException(status_code=410, detail="Session expired")


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """Get full session details."""
    registry = get_registry()
    
    try:
        session = registry.get_session(session_id, user_id)
        return SessionResponse(success=True, session=session.to_dict())
    
    except SessionNotFoundError:
        raise HTTPException(status_code=404, detail="Session not found")
    except SessionAccessError:
        raise HTTPException(status_code=403, detail="Access denied")
    except SessionExpiredError:
        raise HTTPException(status_code=410, detail="Session expired")


@router.delete("/{session_id}", response_model=SessionResponse)
async def unregister_session(
    session_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """Unregister a session (user must own the session)."""
    registry = get_registry()
    
    try:
        removed = registry.unregister(session_id, user_id)
        if not removed:
            raise HTTPException(status_code=404, detail="Session not found")
        return SessionResponse(success=True)
    
    except SessionAccessError:
        raise HTTPException(status_code=403, detail="Access denied")


@router.get("/", response_model=Dict[str, Any])
async def list_user_sessions(
    user_id: str = Depends(get_current_user_id)
):
    """List all active sessions for the authenticated user."""
    registry = get_registry()
    sessions = registry.get_user_sessions(user_id)
    
    return {
        "user_id": user_id,
        "count": len(sessions),
        "sessions": [s.to_dict() for s in sessions]
    }


@router.post("/{session_id}/extend", response_model=SessionResponse)
async def extend_session(
    session_id: str,
    minutes: int = 15,
    user_id: str = Depends(get_current_user_id)
):
    """Extend session expiry time."""
    registry = get_registry()
    
    try:
        # Get current session to calculate new expiry
        session = registry.get_session(session_id, user_id, check_expiry=False)
        
        # Cap at 60 minutes from now
        max_expires = datetime.utcnow() + timedelta(minutes=60)
        new_expires = session.expires_at + timedelta(minutes=minutes)
        new_expires = min(new_expires, max_expires)
        
        session = registry.extend_expiry(session_id, user_id, new_expires)
        return SessionResponse(success=True, session=session.to_dict())
    
    except SessionNotFoundError:
        raise HTTPException(status_code=404, detail="Session not found")
    except SessionAccessError:
        raise HTTPException(status_code=403, detail="Access denied")


@router.get("/admin/stats")
async def get_registry_stats():
    """Get registry statistics (admin endpoint)."""
    registry = get_registry()
    return registry.get_stats()


# =============================================================================
# Convenience Functions for Integration
# =============================================================================

def register_sandbox_session(
    session_id: str,
    user_id: str,
    backend_url: str,
    container_name: str,
    ttl_minutes: int = 45,
    project_name: Optional[str] = None
) -> SandboxSession:
    """
    Convenience function to register a session.
    Call this after successfully creating a sandbox container.
    """
    registry = get_registry()
    return registry.register(
        session_id=session_id,
        user_id=user_id,
        backend_url=backend_url,
        container_name=container_name,
        expires_at=datetime.utcnow() + timedelta(minutes=ttl_minutes),
        project_name=project_name
    )


def get_sandbox_backend_url(session_id: str, user_id: str) -> str:
    """
    Convenience function to get backend URL with user verification.
    Use this in your frontend preview launcher.
    
    Raises:
        SessionNotFoundError: Session doesn't exist
        SessionAccessError: User doesn't own this session  
        SessionExpiredError: Session has expired
    """
    registry = get_registry()
    return registry.get_backend_url(session_id, user_id)


def unregister_sandbox_session(session_id: str, user_id: str) -> bool:
    """
    Convenience function to unregister a session.
    Call this when destroying a sandbox container.
    """
    registry = get_registry()
    try:
        return registry.unregister(session_id, user_id)
    except SessionAccessError:
        return False
