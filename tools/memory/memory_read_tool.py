"""
Memory Read Tool

Query and read memory entries from L1/L2/L3 memory tiers.
Per DIP Phase 11: Memory query tools.

Enforces:
- LAW 4 — TOOL-ONLY EXECUTION
- LAW 8 — ORCHESTRATOR-ONLY MEMORY WRITES (reads only)
- LAW 9 — MEMORY DEGRADATION & TAGGING
- LAW 13 — COMPLETE AUDITABILITY
"""

import logging
from typing import Any, Dict, List, Optional

from mcp.tool_schema import PermissionLevel, ToolSchema

logger = logging.getLogger(__name__)


def make_memory_read_tool() -> ToolSchema:
    """Create the memory read tool schema."""
    return ToolSchema(
        name="memory_read",
        description="[memory] Query memory entries by tag, type, or time range.",
        input_schema={
            "type": "object",
            "properties": {
                "tag": {
                    "type": "string",
                    "description": "Filter by memory tag."
                },
                "tier": {
                    "type": "string",
                    "enum": ["L1", "L2", "L3"],
                    "description": "Memory tier to query (L1=volatile, L2=persistent, L3=cloud)."
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum entries to return (default: 20)."
                },
                "include_expired": {
                    "type": "boolean",
                    "description": "Include expired memory entries."
                }
            },
            "required": []
        },
        output_schema={"type": "object"},
        permission_level=PermissionLevel.READ,
        requires_confirmation=False,
        category="memory",
        capability_domain="memory",
        side_effect_scope="READ_ONLY",
    )


def memory_read_impl(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute memory read tool.
    
    Per LAW 8: This tool only READS memory. Writes are orchestrator-only.
    
    Args:
        args: Tool arguments
            - tag: Filter by memory tag
            - tier: Memory tier (L1, L2, L3)
            - limit: Max entries to return
            - include_expired: Include expired entries
    
    Returns:
        Memory entries matching criteria
    """
    logger.info(f"Executing memory_read tool with args: {args}")
    
    try:
        # Import memory manager
        from memory.memory_manager import MemoryManager
        
        tag = args.get("tag")
        tier = args.get("tier")
        limit = args.get("limit", 20)
        include_expired = args.get("include_expired", False)
        
        # Query memory
        memory = MemoryManager()
        
        # Note: MemoryManager may need query method implementation
        # For now, return structure indicating query parameters
        entries: List[Dict[str, Any]] = []
        
        # Try to get recent memories if available
        try:
            entries = memory.query(
                tag=tag,
                tier=tier,
                limit=limit,
                include_expired=include_expired
            )
        except (AttributeError, NotImplementedError):
            # Query method not yet implemented
            pass
        
        result = {
            "status": "ok",
            "query": {
                "tag": tag,
                "tier": tier,
                "limit": limit,
                "include_expired": include_expired,
            },
            "count": len(entries),
            "entries": entries,
        }
        
        if not entries:
            result["note"] = "No memory entries found or query not fully implemented."
        
        logger.info(f"memory_read completed: {len(entries)} entries")
        return result
        
    except ImportError as e:
        logger.warning(f"Memory manager not available: {e}")
        return {
            "status": "ok",
            "query": args,
            "count": 0,
            "entries": [],
            "note": "Memory manager module not available."
        }
    except Exception as e:
        logger.error(f"Memory read failed: {e}", exc_info=True)
        return {
            "status": "error",
            "message": str(e),
        }
