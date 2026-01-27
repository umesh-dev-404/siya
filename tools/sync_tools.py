"""
Sync Tools - Supabase Synchronization Control

MCP tools for controlling L3 memory synchronization.
Per Phase 13: Supabase Synchronization.

LAW Compliance:
- LAW 1: Sync triggers require confirmation
- LAW 8: Only orchestrator can execute sync
- LAW 13: All sync operations logged
"""

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


def get_sync_status() -> Dict[str, Any]:
    """
    Get current L3 synchronization status.
    
    Returns connection status, queue statistics, and last sync time.
    
    Returns:
        Dictionary with sync status details
    """
    try:
        from sync.sync_manager import get_sync_manager
        
        manager = get_sync_manager()
        return {
            "success": True,
            "status": manager.get_sync_status(),
        }
    except ImportError:
        return {
            "success": False,
            "error": "Sync package not installed. Run: pip install supabase",
        }
    except Exception as e:
        logger.error(f"Failed to get sync status: {e}")
        return {
            "success": False,
            "error": str(e),
        }


def trigger_sync(direction: str = "bidirectional") -> Dict[str, Any]:
    """
    Trigger a manual sync operation.
    
    Args:
        direction: "push" (L2→L3), "pull" (L3→L2), or "bidirectional" (both)
        
    Returns:
        Dictionary with sync result
        
    Note: This tool requires confirmation (LAW 1) since it involves
    network operations and data modification.
    """
    try:
        from sync.sync_manager import get_sync_manager, SyncDirection
        
        manager = get_sync_manager()
        
        if direction == "push":
            result = manager.push(caller="orchestrator")
        elif direction == "pull":
            result = manager.pull(caller="orchestrator")
        else:
            result = manager.sync(caller="orchestrator")
        
        return {
            "success": result.success,
            "direction": result.direction.value,
            "records_pushed": result.records_pushed,
            "records_pulled": result.records_pulled,
            "conflicts_resolved": result.conflicts_resolved,
            "errors": result.errors,
            "duration_ms": result.duration_ms,
        }
    except ImportError:
        return {
            "success": False,
            "error": "Sync package not installed. Run: pip install supabase",
        }
    except Exception as e:
        logger.error(f"Sync failed: {e}")
        return {
            "success": False,
            "error": str(e),
        }


def clear_sync_queue(older_than_hours: int = 24) -> Dict[str, Any]:
    """
    Clear completed sync operations from the queue.
    
    Args:
        older_than_hours: Clear operations completed more than this many hours ago
        
    Returns:
        Dictionary with clear result
    """
    try:
        from sync.sync_queue import get_sync_queue
        
        queue = get_sync_queue()
        cleared = queue.clear_completed(older_than_hours=older_than_hours)
        
        return {
            "success": True,
            "cleared_count": cleared,
            "older_than_hours": older_than_hours,
        }
    except ImportError:
        return {
            "success": False,
            "error": "Sync package not available",
        }
    except Exception as e:
        logger.error(f"Failed to clear sync queue: {e}")
        return {
            "success": False,
            "error": str(e),
        }


# Tool schemas for MCP registration
SYNC_TOOL_SCHEMAS = [
    {
        "name": "get_sync_status",
        "description": "Get L3 (Supabase) synchronization status including connection state, queue statistics, and last sync time.",
        "permission_level": "READ",
        "requires_confirmation": False,
        "parameters": {},
        "handler": get_sync_status,
    },
    {
        "name": "trigger_sync",
        "description": "Trigger a manual synchronization between L2 (local SQLite) and L3 (Supabase). Supports push, pull, or bidirectional sync.",
        "permission_level": "EXECUTE",
        "requires_confirmation": True,  # LAW 1: Network + data modification
        "parameters": {
            "direction": {
                "type": "string",
                "description": "Sync direction: 'push' (local to cloud), 'pull' (cloud to local), or 'bidirectional' (both)",
                "enum": ["push", "pull", "bidirectional"],
                "default": "bidirectional",
            },
        },
        "handler": trigger_sync,
    },
    {
        "name": "clear_sync_queue",
        "description": "Clear completed sync operations from the offline queue. Helps free disk space.",
        "permission_level": "WRITE",
        "requires_confirmation": True,  # LAW 1: Data deletion
        "parameters": {
            "older_than_hours": {
                "type": "integer",
                "description": "Clear operations completed more than this many hours ago",
                "default": 24,
            },
        },
        "handler": clear_sync_queue,
    },
]
