"""
Observability Tools

Tools for read-only system observability.
Enforces LAW 23 — OBSERVABILITY WITHOUT CONTROL.

Per CONTINUATION_PLAN Phase 23: Operator Observability Dashboard.
"""

import logging
from typing import Any, Dict

from system.observability_service import ObservabilityService

logger = logging.getLogger(__name__)


def get_system_posture() -> Dict[str, Any]:
    """
    Get read-only system posture snapshot.
    
    Per LAW 23 — OBSERVABILITY WITHOUT CONTROL:
    - Pure read-only operation
    - No actions can be triggered
    - Same data across all interfaces (LAW 19)
    
    Returns:
        Dict containing:
            - status: "ok" or "error"
            - posture: System posture snapshot with:
                - queue_depth: Tasks in queue
                - pending_confirmations: Awaiting user approval
                - recent_errors: Error summary
                - memory_pressure: Memory usage status
                - sync_status: Cloud sync status
                - uptime: System uptime info
                - health: Overall health status
                - timestamp: When snapshot was taken
    
    Example:
        get_system_posture()
        # Returns: {"status": "ok", "posture": {...}}
    """
    try:
        # Create observability service
        service = ObservabilityService()
        
        # Get posture snapshot
        posture = service.get_system_posture()
        
        logger.info(
            "System posture retrieved",
            extra={
                "health": posture.get("health"),
                "queue_depth": posture.get("queue_depth"),
            },
        )
        
        return {
            "status": "ok",
            "posture": posture,
        }
        
    except Exception as e:
        logger.exception(f"Error getting system posture: {e}")
        return {
            "status": "error",
            "message": f"Failed to get system posture: {str(e)}",
        }


def register_observability_tools(executor) -> None:
    """
    Register observability tools with the ToolExecutor.
    
    Per Phase 23: Operator Observability Dashboard.
    
    Note: All tools are read-only (LAW 23).
    """
    executor.register(
        "get_system_posture",
        lambda args: get_system_posture(),
    )
    
    logger.info("Observability tools registered: get_system_posture")
