"""
Sandbox Container Cleanup Manager
=================================
Robust cleanup system for sandbox backend containers with:

- Automatic TTL-based cleanup (background task)
- On-demand cleanup when preview ends
- Orphan container detection and cleanup
- Safe, idempotent cleanup operations
- Graceful shutdown handling

Key Safety Principles:
1. Cleanup operations are idempotent - can run multiple times safely
2. Never delete containers belonging to other sessions
3. Always release resources (ports, memory tracking) on cleanup
4. Log all cleanup operations for debugging
"""

import os
import asyncio
import subprocess
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Set, Callable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# =============================================================================
# CLEANUP CONFIGURATION
# =============================================================================

@dataclass
class CleanupConfig:
    """Configuration for the cleanup manager."""
    # TTL settings
    default_ttl_minutes: int = 45
    min_ttl_minutes: int = 30
    max_ttl_minutes: int = 60
    
    # Cleanup intervals
    ttl_check_interval_seconds: int = 60      # How often to check for expired containers
    orphan_check_interval_seconds: int = 300  # How often to check for orphans (5 min)
    
    # Grace periods
    grace_period_seconds: int = 30    # Extra time before force cleanup
    shutdown_timeout_seconds: int = 30 # Max time for graceful shutdown
    
    # Resource limits
    max_containers_per_user: int = 3  # Max concurrent containers per user
    max_total_containers: int = 50    # Max total containers
    
    # Container naming pattern (for orphan detection)
    container_prefix: str = "sandbox-"
    
    # Image cleanup
    cleanup_images: bool = True       # Also remove Docker images
    cleanup_volumes: bool = True      # Also remove Docker volumes


# =============================================================================
# CLEANUP OPERATIONS (Idempotent)
# =============================================================================

class ContainerCleanup:
    """
    Low-level container cleanup operations.
    All operations are idempotent - safe to call multiple times.
    """
    
    @staticmethod
    async def stop_container(container_name: str, timeout: int = 10) -> bool:
        """
        Stop a container gracefully.
        Idempotent: Returns True even if already stopped.
        """
        result = None
        try:
            # Check if container exists and is running
            inspect = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: subprocess.run(
                    ["docker", "inspect", "-f", "{{.State.Running}}", container_name],
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace"
                )
            )
            if inspect.returncode != 0:
                # Container doesn't exist - idempotent success
                logger.debug(f"Container {container_name} not found (already removed)")
                return True
            if inspect.stdout.strip() == "false":
                # Already stopped - idempotent success
                logger.debug(f"Container {container_name} already stopped")
                return True
            # Stop the container
            result = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: subprocess.run(
                    ["docker", "stop", "-t", str(timeout), container_name],
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=timeout + 5
                )
            )
            if result.returncode == 0:
                logger.info(f"✅ Stopped container: {container_name}")
                return True
            else:
                logger.warning(f"⚠️ Failed to stop {container_name}: {result.stderr}")
                return False
        except subprocess.TimeoutExpired:
            logger.warning(f"⏰ Timeout stopping {container_name}, will force remove")
            return False
        except Exception as e:
            logger.error(f"❌ Error stopping {container_name}: {e}")
            return False
    
    @staticmethod
    async def remove_container(container_name: str, force: bool = True) -> bool:
        """
        Remove a container.
        Idempotent: Returns True even if already removed.
        """
        try:
            result = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: subprocess.run(
                    ["docker", "rm", "-f" if force else "", container_name],
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace"
                )
            )
            
            # Success or "no such container" both count as idempotent success
            if result.returncode == 0 or "No such container" in result.stderr:
                logger.info(f"🗑️ Removed container: {container_name}")
                return True
            
            logger.warning(f"⚠️ Failed to remove {container_name}: {result.stderr}")
            return False
            
        except Exception as e:
            logger.error(f"❌ Error removing {container_name}: {e}")
            return False
    
    @staticmethod
    async def remove_image(image_name: str, force: bool = False) -> bool:
        """
        Remove a Docker image.
        Idempotent: Returns True even if already removed.
        """
        try:
            args = ["docker", "rmi"]
            if force:
                args.append("-f")
            args.append(image_name)
            
            result = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: subprocess.run(
                    args,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace"
                )
            )
            
            # Success or "no such image" both count as idempotent success
            if result.returncode == 0 or "No such image" in result.stderr:
                logger.info(f"🗑️ Removed image: {image_name}")
                return True
            
            # Image might be in use by another container
            if "image is being used" in result.stderr:
                logger.debug(f"Image {image_name} in use, skipping removal")
                return True  # Not an error, just skip
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Error removing image {image_name}: {e}")
            return False
    
    @staticmethod
    async def full_cleanup(
        container_name: str,
        image_name: Optional[str] = None,
        force: bool = True,
        cleanup_image: bool = True
    ) -> Dict[str, bool]:
        """
        Complete cleanup of container and optionally its image.
        Idempotent: Safe to call multiple times.
        """
        results = {
            "container_stopped": False,
            "container_removed": False,
            "image_removed": False
        }
        
        # Stop container
        results["container_stopped"] = await ContainerCleanup.stop_container(
            container_name, timeout=10
        )
        
        # Remove container
        results["container_removed"] = await ContainerCleanup.remove_container(
            container_name, force=force
        )
        
        # Remove image if requested
        if cleanup_image and image_name:
            results["image_removed"] = await ContainerCleanup.remove_image(
                image_name, force=force
            )
        
        return results


# =============================================================================
# ORPHAN DETECTOR
# =============================================================================

class OrphanDetector:
    """
    Detects and cleans up orphaned sandbox containers.
    
    Orphans can occur due to:
    - Server crashes
    - Incomplete cleanup
    - Manual interventions
    """
    
    def __init__(self, config: CleanupConfig, known_sessions: Set[str], known_container_names: Set[str] = None):
        self.config = config
        self.known_sessions = known_sessions
        self.known_container_names = known_container_names or set()
    
    async def find_orphans(self) -> List[Dict[str, Any]]:
        """
        Find Docker containers matching sandbox pattern that aren't tracked.
        Uses a grace period to avoid killing newly created containers that
        haven't been registered yet (prevents race condition).
        """
        try:
            # List all containers with sandbox prefix
            result = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: subprocess.run(
                    [
                        "docker", "ps", "-a",
                        "--filter", f"name={self.config.container_prefix}",
                        "--format", "{{.Names}}\t{{.Status}}\t{{.CreatedAt}}\t{{.Image}}"
                    ],
                    capture_output=True,
                    text=True
                )
            )
            
            if result.returncode != 0:
                logger.error(f"Failed to list containers: {result.stderr}")
                return []
            
            orphans = []
            
            # Grace period: don't consider containers created in the last 5 minutes as orphans
            # This prevents race conditions where a container is created but not yet registered
            grace_period_seconds = max(self.config.grace_period_seconds, 300)  # At least 5 minutes
            
            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue
                
                parts = line.split('\t')
                if len(parts) < 4:
                    continue
                
                container_name, status, created_at, image = parts
                
                # Check if this container is tracked by name (most reliable check — do FIRST)
                if container_name in self.known_container_names:
                    logger.debug(f"Container {container_name} is tracked (by name), skipping")
                    continue
                
                # Also check by session ID extraction as fallback
                session_id = self._extract_session_id(container_name)
                if session_id and any(session_id in s for s in self.known_sessions):
                    logger.debug(f"Container {container_name} is tracked (by session), skipping")
                    continue
                
                # Grace period: don't consider containers created recently as orphans
                # This prevents race conditions where a container is created but not yet registered
                try:
                    # Docker CreatedAt format: "2024-01-15 10:30:45 +0000 UTC"
                    # Use regex to extract just the YYYY-MM-DD HH:MM:SS part reliably
                    import re as date_re
                    from datetime import datetime as dt
                    date_match = date_re.match(r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})', created_at.strip())
                    if date_match:
                        container_created = dt.strptime(date_match.group(1), "%Y-%m-%d %H:%M:%S")
                        age_seconds = (dt.utcnow() - container_created).total_seconds()
                        if age_seconds < grace_period_seconds:
                            logger.debug(
                                f"⏳ Skipping container {container_name} - created {age_seconds:.0f}s ago "
                                f"(grace period: {grace_period_seconds}s)"
                            )
                            continue
                    else:
                        # Can't parse date — skip to be safe (don't kill unknown containers)
                        logger.debug(f"Could not parse created_at '{created_at}' for {container_name}, skipping")
                        continue
                except Exception as parse_err:
                    logger.debug(f"Could not parse created_at for {container_name}: {parse_err}")
                    # If we can't parse the date, skip this container to be safe
                    continue
                
                orphans.append({
                    "container_name": container_name,
                    "session_id": session_id or "unknown",
                    "status": status,
                    "created_at": created_at,
                    "image": image
                })
            
            if orphans:
                logger.info(f"🔍 Found {len(orphans)} orphaned containers")
            
            return orphans
            
        except Exception as e:
            logger.error(f"Error finding orphans: {e}")
            return []
    
    def _extract_session_id(self, container_name: str) -> Optional[str]:
        """Extract session ID from container name."""
        # Format: sandbox-{short_session_id}-{timestamp}
        if not container_name.startswith(self.config.container_prefix):
            return None
        
        parts = container_name[len(self.config.container_prefix):].split('-')
        if len(parts) >= 1:
            return parts[0]  # Return short session ID
        return None
    
    async def cleanup_orphans(self) -> Dict[str, Any]:
        """
        Find and clean up all orphaned containers.
        Returns summary of cleanup operations.
        """
        orphans = await self.find_orphans()
        
        results = {
            "found": len(orphans),
            "cleaned": 0,
            "failed": 0,
            "details": []
        }
        
        for orphan in orphans:
            try:
                cleanup_result = await ContainerCleanup.full_cleanup(
                    container_name=orphan["container_name"],
                    image_name=orphan.get("image"),
                    force=True,
                    cleanup_image=self.config.cleanup_images
                )
                
                if cleanup_result["container_removed"]:
                    results["cleaned"] += 1
                    results["details"].append({
                        "container": orphan["container_name"],
                        "status": "cleaned"
                    })
                else:
                    results["failed"] += 1
                    results["details"].append({
                        "container": orphan["container_name"],
                        "status": "failed"
                    })
                    
            except Exception as e:
                results["failed"] += 1
                results["details"].append({
                    "container": orphan["container_name"],
                    "status": "error",
                    "error": str(e)
                })
        
        if results["cleaned"] > 0:
            logger.info(f"🧹 Cleaned up {results['cleaned']} orphaned containers")
        
        return results


# =============================================================================
# TTL MANAGER
# =============================================================================

@dataclass
class TrackedContainer:
    """Container tracking data for TTL management."""
    session_id: str
    container_name: str
    image_name: str
    port: int
    created_at: datetime
    expires_at: datetime
    user_id: Optional[str] = None
    cleanup_callback: Optional[Callable] = None
    
    @property
    def is_expired(self) -> bool:
        return datetime.utcnow() >= self.expires_at
    
    @property
    def ttl_seconds(self) -> int:
        return max(0, int((self.expires_at - datetime.utcnow()).total_seconds()))


class TTLManager:
    """
    Manages container TTLs and automatic expiration cleanup.
    """
    
    def __init__(self, config: CleanupConfig):
        self.config = config
        self._containers: Dict[str, TrackedContainer] = {}
        self._lock = asyncio.Lock()
    
    async def register(
        self,
        session_id: str,
        container_name: str,
        image_name: str,
        port: int,
        ttl_minutes: int,
        user_id: Optional[str] = None,
        cleanup_callback: Optional[Callable] = None
    ) -> TrackedContainer:
        """Register a container for TTL tracking."""
        async with self._lock:
            # Validate TTL
            ttl = max(
                self.config.min_ttl_minutes,
                min(self.config.max_ttl_minutes, ttl_minutes)
            )
            
            container = TrackedContainer(
                session_id=session_id,
                container_name=container_name,
                image_name=image_name,
                port=port,
                created_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(minutes=ttl),
                user_id=user_id,
                cleanup_callback=cleanup_callback
            )
            
            self._containers[session_id] = container
            
            logger.info(
                f"📝 Registered container {container_name} with TTL {ttl}min "
                f"(expires: {container.expires_at.isoformat()})"
            )
            
            return container
    
    async def unregister(self, session_id: str) -> Optional[TrackedContainer]:
        """Remove a container from TTL tracking."""
        async with self._lock:
            return self._containers.pop(session_id, None)
    
    async def extend_ttl(self, session_id: str, additional_minutes: int = 15) -> bool:
        """Extend container TTL."""
        async with self._lock:
            container = self._containers.get(session_id)
            if not container:
                return False
            
            max_expires = datetime.utcnow() + timedelta(minutes=self.config.max_ttl_minutes)
            new_expires = container.expires_at + timedelta(minutes=additional_minutes)
            container.expires_at = min(new_expires, max_expires)
            
            logger.info(
                f"⏰ Extended TTL for {container.container_name} to "
                f"{container.expires_at.isoformat()}"
            )
            
            return True
    
    async def get_expired(self) -> List[TrackedContainer]:
        """Get all expired containers."""
        async with self._lock:
            now = datetime.utcnow()
            return [c for c in self._containers.values() if c.expires_at <= now]
    
    async def get_all_session_ids(self) -> Set[str]:
        """Get all tracked session IDs."""
        async with self._lock:
            return set(self._containers.keys())
    
    async def get_all_container_names(self) -> Set[str]:
        """Get all tracked container names (for orphan detection)."""
        async with self._lock:
            return {c.container_name for c in self._containers.values()}
    
    async def get_status(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get TTL status for a container."""
        async with self._lock:
            container = self._containers.get(session_id)
            if not container:
                return None
            
            return {
                "session_id": session_id,
                "container_name": container.container_name,
                "created_at": container.created_at.isoformat(),
                "expires_at": container.expires_at.isoformat(),
                "ttl_seconds": container.ttl_seconds,
                "is_expired": container.is_expired
            }


# =============================================================================
# CLEANUP MANAGER (Main Entry Point)
# =============================================================================

class SandboxCleanupManager:
    """
    Central cleanup manager for sandbox containers.
    
    Features:
    - Automatic TTL-based cleanup
    - On-demand cleanup
    - Orphan detection and cleanup
    - Graceful shutdown handling
    """
    
    def __init__(self, config: CleanupConfig = None):
        self.config = config or CleanupConfig()
        self.ttl_manager = TTLManager(self.config)
        
        # Background tasks
        self._running = False
        self._ttl_task: Optional[asyncio.Task] = None
        self._orphan_task: Optional[asyncio.Task] = None
        
        # Cleanup callbacks
        self._port_release_callback: Optional[Callable[[int], None]] = None
        self._registry_callback: Optional[Callable[[str], None]] = None
        
        # Statistics
        self._stats = {
            "ttl_cleanups": 0,
            "manual_cleanups": 0,
            "orphan_cleanups": 0,
            "failed_cleanups": 0
        }
    
    def set_port_release_callback(self, callback: Callable[[int], None]):
        """Set callback to release ports on cleanup."""
        self._port_release_callback = callback
    
    def set_registry_callback(self, callback: Callable[[str], None]):
        """Set callback to update registry on cleanup."""
        self._registry_callback = callback
    
    async def start(self):
        """Start the cleanup manager background tasks."""
        if self._running:
            return
        
        self._running = True
        
        # Start TTL check loop
        self._ttl_task = asyncio.create_task(self._ttl_cleanup_loop())
        
        # Start orphan check loop
        self._orphan_task = asyncio.create_task(self._orphan_cleanup_loop())
        
        # Register shutdown handlers
        self._register_shutdown_handlers()
        
        logger.info("🚀 Sandbox cleanup manager started")
    
    async def stop(self):
        """Stop the cleanup manager and clean up all containers."""
        if not self._running:
            return
        
        self._running = False
        logger.info("🛑 Stopping sandbox cleanup manager...")
        
        # Cancel background tasks
        for task in [self._ttl_task, self._orphan_task]:
            if task:
                task.cancel()
                try:
                    await asyncio.wait_for(task, timeout=5)
                except (asyncio.CancelledError, asyncio.TimeoutError):
                    pass
        
        # Clean up all remaining containers
        await self.cleanup_all()
        
        logger.info("✅ Sandbox cleanup manager stopped")
    
    async def register_container(
        self,
        session_id: str,
        container_name: str,
        image_name: str,
        port: int,
        ttl_minutes: int,
        user_id: Optional[str] = None
    ) -> TrackedContainer:
        """Register a container for cleanup management."""
        return await self.ttl_manager.register(
            session_id=session_id,
            container_name=container_name,
            image_name=image_name,
            port=port,
            ttl_minutes=ttl_minutes,
            user_id=user_id
        )
    
    async def cleanup_container(
        self,
        session_id: str,
        reason: str = "manual"
    ) -> Dict[str, Any]:
        """
        Clean up a specific container (on-demand).
        Idempotent: Safe to call multiple times.
        """
        result = {
            "session_id": session_id,
            "success": False,
            "reason": reason,
            "details": {}
        }
        
        # Get container info
        container = await self.ttl_manager.unregister(session_id)
        
        if not container:
            # Check if container exists in Docker anyway
            container_name = f"sandbox-{session_id[:8]}"
            exists = await self._container_exists(container_name)
            
            if exists:
                # Cleanup orphaned container
                cleanup_result = await ContainerCleanup.full_cleanup(
                    container_name=container_name,
                    cleanup_image=self.config.cleanup_images
                )
                result["details"] = cleanup_result
                result["success"] = cleanup_result["container_removed"]
            else:
                # Already cleaned - idempotent success
                result["success"] = True
                result["details"]["message"] = "Container already cleaned or not found"
            
            return result
        
        # Perform cleanup
        cleanup_result = await ContainerCleanup.full_cleanup(
            container_name=container.container_name,
            image_name=container.image_name,
            cleanup_image=self.config.cleanup_images
        )
        
        result["details"] = cleanup_result
        result["success"] = cleanup_result["container_removed"]
        
        # Release port
        if self._port_release_callback and container.port:
            try:
                self._port_release_callback(container.port)
            except Exception as e:
                logger.warning(f"Failed to release port {container.port}: {e}")
        
        # Update registry
        if self._registry_callback:
            try:
                self._registry_callback(session_id)
            except Exception as e:
                logger.warning(f"Failed to update registry for {session_id}: {e}")
        
        # Update stats
        if result["success"]:
            self._stats["manual_cleanups"] += 1
        else:
            self._stats["failed_cleanups"] += 1
        
        logger.info(f"🧹 Cleaned up container for session {session_id} ({reason})")
        
        return result
    
    async def cleanup_all(self) -> Dict[str, Any]:
        """Clean up all tracked containers in parallel for speed."""
        import time
        results = {
            "total": 0,
            "success": 0,
            "failed": 0,
            "details": []
        }
        # Get all tracked session IDs
        session_ids = await self.ttl_manager.get_all_session_ids()
        results["total"] = len(session_ids)
        start = time.perf_counter()
        # Run all cleanups in parallel
        cleanup_tasks = [self.cleanup_container(session_id, reason="shutdown") for session_id in session_ids]
        cleanup_results = await asyncio.gather(*cleanup_tasks, return_exceptions=True)
        for result in cleanup_results:
            if isinstance(result, Exception):
                results["failed"] += 1
                results["details"].append({"success": False, "error": str(result)})
            elif result.get("success"):
                results["success"] += 1
                results["details"].append(result)
            else:
                results["failed"] += 1
                results["details"].append(result)
        elapsed = time.perf_counter() - start
        logger.info(f"🧹 Parallel cleanup complete in {elapsed:.2f}s: {results['success']}/{results['total']} containers cleaned")
        
        # Also cleanup any orphans
        orphan_detector = OrphanDetector(self.config, set())
        orphan_results = await orphan_detector.cleanup_orphans()
        
        results["orphans_cleaned"] = orphan_results["cleaned"]
        
        logger.info(
            f"🧹 Cleanup all complete: {results['success']}/{results['total']} "
            f"containers + {results['orphans_cleaned']} orphans"
        )
        
        return results
    
    async def extend_ttl(self, session_id: str, additional_minutes: int = 15) -> bool:
        """Extend container TTL."""
        return await self.ttl_manager.extend_ttl(session_id, additional_minutes)
    
    async def get_status(self, session_id: str = None) -> Dict[str, Any]:
        """Get cleanup status for a container or all containers."""
        if session_id:
            status = await self.ttl_manager.get_status(session_id)
            return status or {"error": "Session not found"}
        
        # Return overall status
        session_ids = await self.ttl_manager.get_all_session_ids()
        expired = await self.ttl_manager.get_expired()
        
        return {
            "active_containers": len(session_ids),
            "expired_pending_cleanup": len(expired),
            "stats": self._stats.copy(),
            "config": {
                "default_ttl_minutes": self.config.default_ttl_minutes,
                "ttl_check_interval": self.config.ttl_check_interval_seconds,
                "orphan_check_interval": self.config.orphan_check_interval_seconds
            }
        }
    
    # =========================================================================
    # BACKGROUND TASKS
    # =========================================================================
    
    async def _ttl_cleanup_loop(self):
        """Background loop to clean up expired containers."""
        while self._running:
            try:
                await asyncio.sleep(self.config.ttl_check_interval_seconds)
                
                if not self._running:
                    break
                
                expired = await self.ttl_manager.get_expired()
                
                for container in expired:
                    try:
                        result = await self.cleanup_container(
                            container.session_id,
                            reason="ttl_expired"
                        )
                        
                        if result["success"]:
                            self._stats["ttl_cleanups"] += 1
                            logger.info(
                                f"⏰ TTL expired cleanup: {container.container_name}"
                            )
                    except Exception as e:
                        logger.error(f"TTL cleanup error for {container.session_id}: {e}")
                        self._stats["failed_cleanups"] += 1
                        
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"TTL cleanup loop error: {e}")
    
    async def _orphan_cleanup_loop(self):
        """Background loop to clean up orphaned containers."""
        while self._running:
            try:
                await asyncio.sleep(self.config.orphan_check_interval_seconds)
                
                if not self._running:
                    break
                
                # Get known session IDs and container names
                known_sessions = await self.ttl_manager.get_all_session_ids()
                known_container_names = await self.ttl_manager.get_all_container_names()
                
                # Find and cleanup orphans
                detector = OrphanDetector(self.config, known_sessions, known_container_names)
                results = await detector.cleanup_orphans()
                
                self._stats["orphan_cleanups"] += results["cleaned"]
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Orphan cleanup loop error: {e}")
    
    # =========================================================================
    # HELPERS
    # =========================================================================
    
    async def _container_exists(self, container_name: str) -> bool:
        """Check if a container exists."""
        try:
            result = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: subprocess.run(
                    ["docker", "inspect", container_name],
                    capture_output=True
                )
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def _register_shutdown_handlers(self):
        """
        Register handlers for graceful shutdown.
        
        NOTE: With FastAPI/uvicorn, shutdown is handled by the @app.on_event("shutdown")
        handler in main.py which calls shutdown_cleanup_manager(). We don't register
        signal handlers here to avoid conflicts with uvicorn's signal handling.
        """
        # FastAPI's shutdown event handles cleanup - no need for signal handlers
        # This prevents conflicts with uvicorn's signal handling and reloader
        pass


# =============================================================================
# FASTAPI INTEGRATION
# =============================================================================

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

cleanup_router = APIRouter(prefix="/api/cleanup", tags=["Cleanup"])

# Global cleanup manager instance
_cleanup_manager: Optional[SandboxCleanupManager] = None


def get_cleanup_manager() -> SandboxCleanupManager:
    """Get the global cleanup manager instance."""
    if _cleanup_manager is None:
        raise HTTPException(status_code=503, detail="Cleanup manager not initialized")
    return _cleanup_manager


async def init_cleanup_manager(config: CleanupConfig = None) -> SandboxCleanupManager:
    """Initialize the global cleanup manager."""
    global _cleanup_manager
    _cleanup_manager = SandboxCleanupManager(config)
    await _cleanup_manager.start()
    return _cleanup_manager


async def shutdown_cleanup_manager():
    """Shutdown the global cleanup manager."""
    global _cleanup_manager
    if _cleanup_manager:
        await _cleanup_manager.stop()
        _cleanup_manager = None


class CleanupRequest(BaseModel):
    session_id: str = Field(..., description="Session ID to clean up")
    reason: str = Field(default="api_request", description="Reason for cleanup")


class CleanupResponse(BaseModel):
    success: bool
    session_id: str
    reason: str
    details: Dict[str, Any] = Field(default_factory=dict)


class StatusResponse(BaseModel):
    active_containers: int
    expired_pending_cleanup: int
    stats: Dict[str, int]
    config: Dict[str, Any]


@cleanup_router.post("/container", response_model=CleanupResponse)
async def cleanup_single_container(request: CleanupRequest):
    """Clean up a specific container."""
    manager = get_cleanup_manager()
    result = await manager.cleanup_container(request.session_id, request.reason)
    return CleanupResponse(
        success=result["success"],
        session_id=request.session_id,
        reason=request.reason,
        details=result.get("details", {})
    )


@cleanup_router.post("/all")
async def cleanup_all_containers():
    """Clean up all containers (admin operation)."""
    manager = get_cleanup_manager()
    return await manager.cleanup_all()


@cleanup_router.post("/orphans")
async def cleanup_orphan_containers():
    """Clean up orphaned containers."""
    manager = get_cleanup_manager()
    known_sessions = await manager.ttl_manager.get_all_session_ids()
    known_container_names = await manager.ttl_manager.get_all_container_names()
    detector = OrphanDetector(manager.config, known_sessions, known_container_names)
    return await detector.cleanup_orphans()


@cleanup_router.post("/extend/{session_id}")
async def extend_container_ttl(session_id: str, minutes: int = 15):
    """Extend container TTL."""
    manager = get_cleanup_manager()
    success = await manager.extend_ttl(session_id, minutes)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"success": True, "session_id": session_id, "extended_minutes": minutes}


@cleanup_router.get("/status", response_model=StatusResponse)
async def get_cleanup_status():
    """Get overall cleanup status."""
    manager = get_cleanup_manager()
    return await manager.get_status()


@cleanup_router.get("/status/{session_id}")
async def get_container_status(session_id: str):
    """Get cleanup status for a specific container."""
    manager = get_cleanup_manager()
    status = await manager.get_status(session_id)
    if "error" in status:
        raise HTTPException(status_code=404, detail=status["error"])
    return status


# =============================================================================
# CONVENIENCE INTEGRATION FUNCTION
# =============================================================================

async def integrate_with_deployment_service(
    deployment_service,
    cleanup_manager: SandboxCleanupManager
):
    """
    Integrate cleanup manager with SandboxDeploymentService.
    
    This hooks the cleanup manager into the deployment service
    for automatic TTL tracking and port release.
    """
    # Set port release callback
    cleanup_manager.set_port_release_callback(
        deployment_service._release_port
    )
    
    # Monkey-patch create_sandbox to register containers
    original_create = deployment_service.create_sandbox
    
    async def create_with_tracking(session_id: str, project_files: dict, ttl_minutes: int = None):
        # Pre-register the container name BEFORE build starts
        # This prevents the orphan detector from killing it during build
        expected_name = deployment_service._generate_container_name(session_id)
        pre_registered = await cleanup_manager.register_container(
            session_id=session_id,
            container_name=expected_name,
            image_name=f"pending-{session_id[:16]}",
            port=0,
            ttl_minutes=ttl_minutes or cleanup_manager.config.default_ttl_minutes
        )
        
        try:
            container = await original_create(session_id, project_files, ttl_minutes)
            
            # Update registration with actual container details
            await cleanup_manager.register_container(
                session_id=session_id,
                container_name=container.container_name,
                image_name=container.image_name,
                port=container.port,
                ttl_minutes=ttl_minutes or cleanup_manager.config.default_ttl_minutes
            )
            
            return container
        except Exception as e:
            # If build fails, unregister the pre-registration
            await cleanup_manager.ttl_manager.unregister(session_id)
            raise
    
    deployment_service.create_sandbox = create_with_tracking
    
    # Monkey-patch destroy_sandbox to use cleanup manager
    original_destroy = deployment_service.destroy_sandbox
    
    async def destroy_with_cleanup(session_id: str):
        await cleanup_manager.cleanup_container(session_id, reason="destroy_request")
        return True
    
    deployment_service.destroy_sandbox = destroy_with_cleanup
    
    logger.info("✅ Cleanup manager integrated with deployment service")


# =============================================================================
# STANDALONE TESTING
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    from fastapi import FastAPI
    
    app = FastAPI(title="Sandbox Cleanup Service")
    app.include_router(cleanup_router)
    
    @app.on_event("startup")
    async def startup():
        await init_cleanup_manager()
    
    @app.on_event("shutdown")
    async def shutdown():
        await shutdown_cleanup_manager()
    
    @app.get("/health")
    async def health():
        return {"status": "ok", "service": "sandbox-cleanup"}
    
    uvicorn.run(app, host="0.0.0.0", port=8081)
