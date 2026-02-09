"""
Log Query Tool

Query audit logs and system logs.
Per DIP Phase 11: Core system tools.

Enforces:
- LAW 4 — TOOL-ONLY EXECUTION
- LAW 13 — COMPLETE AUDITABILITY
- LAW 14 — LOG RETENTION
"""

import logging
from typing import Any, Dict, List
from datetime import datetime, timedelta

from mcp.tool_schema import PermissionLevel, ToolSchema

logger = logging.getLogger(__name__)


def make_log_query_tool() -> ToolSchema:
    """Create the log query tool schema."""
    return ToolSchema(
        name="log_query",
        description="[system] Query audit logs. Filter by level, time range, or source.",
        input_schema={
            "type": "object",
            "properties": {
                "level": {
                    "type": "string",
                    "enum": ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                    "description": "Minimum log level to include."
                },
                "source": {
                    "type": "string",
                    "description": "Filter by log source/module name."
                },
                "hours": {
                    "type": "integer",
                    "description": "Limit to logs from last N hours (default: 1)."
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of log entries to return (default: 50)."
                }
            },
            "required": []
        },
        output_schema={"type": "object"},
        permission_level=PermissionLevel.READ,
        requires_confirmation=False,
        category="system",
        capability_domain="system",
        side_effect_scope="READ_ONLY",
    )


def log_query_impl(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute log query tool.
    
    Args:
        args: Tool arguments
            - level: Minimum log level
            - source: Filter by source module
            - hours: Time range in hours
            - limit: Max entries to return
    
    Returns:
        Log entries matching criteria
    """
    logger.info(f"Executing log_query tool with args: {args}")
    
    try:
        # Import audit logger to query logs
        from audit.audit_logger import AuditLogger
        
        level = args.get("level", "INFO")
        source = args.get("source")
        hours = args.get("hours", 1)
        limit = args.get("limit", 50)
        
        # Calculate time range
        since = datetime.now() - timedelta(hours=hours)
        
        # Query audit logger
        audit = AuditLogger()
        
        # Note: AuditLogger may not have a query method yet
        # This is a placeholder that returns recent log info
        entries: List[Dict[str, Any]] = []
        
        # For now, return a summary since full log query requires DB access
        result = {
            "status": "ok",
            "query": {
                "level": level,
                "source": source,
                "hours": hours,
                "limit": limit,
                "since": since.isoformat(),
            },
            "count": len(entries),
            "entries": entries,
            "note": "Full log query requires audit database implementation."
        }
        
        logger.info(f"log_query completed: {len(entries)} entries")
        return result
        
    except ImportError as e:
        logger.warning(f"Audit logger not available: {e}")
        return {
            "status": "ok",
            "query": args,
            "count": 0,
            "entries": [],
            "note": "Audit logger module not available."
        }
    except Exception as e:
        logger.error(f"Log query failed: {e}", exc_info=True)
        return {
            "status": "error",
            "message": str(e),
        }
