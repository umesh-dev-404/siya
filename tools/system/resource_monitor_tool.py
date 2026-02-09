"""
Resource Monitor Tool

Provides detailed resource monitoring beyond basic system status.
Per DIP Phase 11: Core system tools.

Enforces:
- LAW 4 — TOOL-ONLY EXECUTION
- LAW 12 — FAILURE TRANSPARENCY
- LAW 13 — COMPLETE AUDITABILITY
"""

import logging
from typing import Any, Dict

from mcp.tool_schema import PermissionLevel, ToolSchema
from system.resource_monitor import ResourceMonitor

logger = logging.getLogger(__name__)


def make_resource_monitor_tool() -> ToolSchema:
    """Create the resource monitor tool schema."""
    return ToolSchema(
        name="resource_monitor",
        description="[system] Get detailed resource usage with thresholds and health status.",
        input_schema={
            "type": "object",
            "properties": {
                "include_processes": {
                    "type": "boolean",
                    "description": "Include top processes by memory usage (slower)."
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


def resource_monitor_impl(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute resource monitor tool.
    
    Args:
        args: Tool arguments
            - include_processes: If true, include top memory-consuming processes
    
    Returns:
        Detailed resource status with thresholds and violations
    """
    logger.info("Executing resource_monitor tool")
    
    try:
        monitor = ResourceMonitor()
        resources = monitor.check_resources()
        
        result = {
            "status": "ok",
            "resources": resources,
        }
        
        # Optionally include top processes
        if args.get("include_processes", False):
            try:
                import psutil
                processes = []
                for proc in sorted(psutil.process_iter(['pid', 'name', 'memory_percent']), 
                                   key=lambda x: x.info.get('memory_percent', 0) or 0, 
                                   reverse=True)[:5]:
                    info = proc.info
                    processes.append({
                        "pid": info.get('pid'),
                        "name": info.get('name'),
                        "memory_percent": round(info.get('memory_percent', 0), 2)
                    })
                result["top_processes"] = processes
            except ImportError:
                result["top_processes"] = None
                result["top_processes_error"] = "psutil not available"
        
        logger.info(f"resource_monitor completed: healthy={resources.get('healthy', False)}")
        return result
        
    except Exception as e:
        logger.error(f"Resource monitor failed: {e}", exc_info=True)
        return {
            "status": "error",
            "message": str(e),
        }
