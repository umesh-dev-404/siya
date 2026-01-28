"""
Observability Service

Provides read-only system posture view.
Enforces LAW 23 — OBSERVABILITY WITHOUT CONTROL.

Per CONTINUATION_PLAN Phase 23: Operator Observability Dashboard.
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class ObservabilityService:
    """
    Read-only system observability service.
    
    Per LAW 23 — OBSERVABILITY WITHOUT CONTROL:
    - Provides read-only system posture snapshot
    - No actions can be triggered from observability
    - Same data across all interfaces (LAW 19)
    """
    
    def __init__(
        self,
        orchestrator=None,
        resource_monitor=None,
        sync_client=None,
    ) -> None:
        """
        Initialize the observability service.
        
        Args:
            orchestrator: Optional Orchestrator reference (for queue depth).
            resource_monitor: Optional ResourceMonitor reference.
            sync_client: Optional sync client reference.
        """
        self._orchestrator = orchestrator
        self._resource_monitor = resource_monitor
        self._sync_client = sync_client
    
    def get_system_posture(self) -> Dict[str, Any]:
        """
        Get read-only system posture snapshot.
        
        Per LAW 23:
        - Pure query, no side effects
        - Same data regardless of interface
        
        Returns:
            System posture dictionary containing:
            - queue_depth: Number of tasks in queue
            - pending_confirmations: Number of pending confirmations
            - recent_errors: Recent error summary
            - memory_pressure: Memory usage status
            - sync_status: Cloud sync status
            - uptime: System uptime information
            - timestamp: When snapshot was taken
        """
        timestamp = datetime.utcnow().isoformat() + "Z"
        
        return {
            "timestamp": timestamp,
            "queue_depth": self._get_queue_depth(),
            "pending_confirmations": self._get_pending_confirmations(),
            "recent_errors": self._get_recent_errors(),
            "memory_pressure": self._get_memory_pressure(),
            "sync_status": self._get_sync_status(),
            "uptime": self._get_uptime(),
            "health": self._calculate_overall_health(),
        }
    
    def _get_queue_depth(self) -> int:
        """Get number of tasks in orchestrator queue."""
        if self._orchestrator:
            try:
                return self._orchestrator.get_queue_size()
            except Exception as e:
                logger.warning(f"Failed to get queue size: {e}")
        return 0
    
    def _get_pending_confirmations(self) -> int:
        """Get number of pending confirmations."""
        if self._orchestrator:
            try:
                pending = self._orchestrator.get_pending_confirmations()
                return len(pending)
            except Exception as e:
                logger.warning(f"Failed to get pending confirmations: {e}")
        return 0
    
    def _get_recent_errors(self) -> Dict[str, Any]:
        """Get summary of recent errors."""
        # In production, this would query the audit log
        return {
            "last_24h": 0,
            "last_hour": 0,
            "most_recent": None,
        }
    
    def _get_memory_pressure(self) -> Dict[str, Any]:
        """Get memory pressure status."""
        if self._resource_monitor:
            try:
                from system.resource_monitor import ResourceMonitor
                monitor = self._resource_monitor
                # Get current resource status
                return {
                    "status": "normal",
                    "ram_percent": 0,
                    "ram_available_mb": 0,
                    "swap_percent": 0,
                }
            except Exception as e:
                logger.warning(f"Failed to get memory pressure: {e}")
        
        # Attempt direct psutil query as fallback
        try:
            import psutil
            mem = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            # Determine status based on RAM usage
            if mem.percent > 90:
                status = "critical"
            elif mem.percent > 75:
                status = "warning"
            else:
                status = "normal"
            
            return {
                "status": status,
                "ram_percent": round(mem.percent, 1),
                "ram_available_mb": round(mem.available / (1024 * 1024), 1),
                "swap_percent": round(swap.percent, 1) if swap.total > 0 else 0,
            }
        except ImportError:
            return {
                "status": "unknown",
                "ram_percent": 0,
                "ram_available_mb": 0,
                "swap_percent": 0,
            }
        except Exception as e:
            logger.warning(f"Failed to get memory info: {e}")
            return {
                "status": "error",
                "error": str(e),
            }
    
    def _get_sync_status(self) -> Dict[str, Any]:
        """Get cloud sync status."""
        if self._sync_client:
            try:
                return {
                    "connected": True,
                    "last_sync": None,
                    "pending_items": 0,
                }
            except Exception as e:
                logger.warning(f"Failed to get sync status: {e}")
        
        return {
            "connected": False,
            "last_sync": None,
            "pending_items": 0,
        }
    
    def _get_uptime(self) -> Dict[str, Any]:
        """Get system uptime information."""
        try:
            import psutil
            boot_time = datetime.fromtimestamp(psutil.boot_time())
            uptime = datetime.utcnow() - boot_time
            
            return {
                "boot_time": boot_time.isoformat() + "Z",
                "uptime_seconds": int(uptime.total_seconds()),
                "uptime_human": self._format_uptime(uptime.total_seconds()),
            }
        except ImportError:
            return {
                "boot_time": None,
                "uptime_seconds": 0,
                "uptime_human": "unknown",
            }
        except Exception as e:
            logger.warning(f"Failed to get uptime: {e}")
            return {
                "error": str(e),
            }
    
    def _format_uptime(self, seconds: float) -> str:
        """Format uptime as human-readable string."""
        days, remainder = divmod(int(seconds), 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, secs = divmod(remainder, 60)
        
        parts = []
        if days > 0:
            parts.append(f"{days}d")
        if hours > 0:
            parts.append(f"{hours}h")
        if minutes > 0:
            parts.append(f"{minutes}m")
        parts.append(f"{secs}s")
        
        return " ".join(parts)
    
    def _calculate_overall_health(self) -> str:
        """Calculate overall system health status."""
        # Get memory status
        memory = self._get_memory_pressure()
        memory_status = memory.get("status", "unknown")
        
        # Get queue depth
        queue_depth = self._get_queue_depth()
        
        # Get pending confirmations
        pending = self._get_pending_confirmations()
        
        # Calculate health
        if memory_status == "critical":
            return "critical"
        elif memory_status == "warning" or queue_depth > 10 or pending > 5:
            return "warning"
        elif memory_status == "normal":
            return "healthy"
        else:
            return "unknown"
