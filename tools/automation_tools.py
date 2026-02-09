"""
Automation Tools

Tools for listing and triggering automations.
Per DIP Phase 11: Automation trigger tools.

Enforces:
- LAW 1 — HUMAN SOVEREIGNTY (trigger requires confirmation)
- LAW 2 — NO AUTONOMOUS EXECUTION
- LAW 4 — TOOL-ONLY EXECUTION
- LAW 10 — SERIAL EXECUTION
- LAW 13 — COMPLETE AUDITABILITY
"""

import logging
from typing import Any, Dict, List, Optional

from mcp.tool_schema import PermissionLevel, ToolSchema

logger = logging.getLogger(__name__)

# Global reference to automation manager (set during registration)
_automation_manager = None


def set_automation_manager(manager):
    """Set the automation manager reference for tool access."""
    global _automation_manager
    _automation_manager = manager


def make_list_automations_tool() -> ToolSchema:
    """Create the list automations tool schema."""
    return ToolSchema(
        name="list_automations",
        description="[automation] List all registered automations and their status.",
        input_schema={
            "type": "object",
            "properties": {
                "include_status": {
                    "type": "boolean",
                    "description": "Include execution status for each automation."
                }
            },
            "required": []
        },
        output_schema={"type": "object"},
        permission_level=PermissionLevel.READ,
        requires_confirmation=False,
        category="automation",
        capability_domain="automation",
        side_effect_scope="READ_ONLY",
    )


def list_automations_impl(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute list automations tool.
    
    Args:
        args: Tool arguments
            - include_status: Include execution status
    
    Returns:
        List of registered automations
    """
    logger.info("Executing list_automations tool")
    
    try:
        include_status = args.get("include_status", True)
        
        if _automation_manager is None:
            return {
                "status": "ok",
                "count": 0,
                "automations": [],
                "note": "Automation manager not available."
            }
        
        automations: List[Dict[str, Any]] = []
        
        for automation_id, automation in _automation_manager._automations.items():
            info = {
                "id": automation_id,
                "name": automation.name,
                "description": automation.description,
            }
            
            if include_status:
                info["executing"] = _automation_manager.is_executing(automation_id)
            
            automations.append(info)
        
        result = {
            "status": "ok",
            "count": len(automations),
            "automations": automations,
        }
        
        if _automation_manager.is_executing():
            result["currently_executing"] = _automation_manager._executing_automation
        
        logger.info(f"list_automations completed: {len(automations)} automations")
        return result
        
    except Exception as e:
        logger.error(f"List automations failed: {e}", exc_info=True)
        return {
            "status": "error",
            "message": str(e),
        }


def make_trigger_automation_tool() -> ToolSchema:
    """Create the trigger automation tool schema."""
    return ToolSchema(
        name="trigger_automation",
        description="[automation] Trigger an automation to execute. Requires confirmation (LAW 1).",
        input_schema={
            "type": "object",
            "properties": {
                "automation_id": {
                    "type": "string",
                    "description": "ID of the automation to trigger."
                },
                "context": {
                    "type": "object",
                    "description": "Optional context data to pass to the automation."
                }
            },
            "required": ["automation_id"]
        },
        output_schema={"type": "object"},
        permission_level=PermissionLevel.EXECUTE,
        requires_confirmation=True,  # LAW 1: Human sovereignty
        category="automation",
        capability_domain="automation",
        side_effect_scope="EXTERNAL",
    )


def trigger_automation_impl(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute trigger automation tool.
    
    NOTE: This tool requires confirmation before execution per LAW 1.
    
    Args:
        args: Tool arguments
            - automation_id: Automation to trigger
            - context: Optional execution context
    
    Returns:
        Trigger result with task ID
    """
    automation_id = args.get("automation_id", "")
    context = args.get("context")
    
    logger.info(f"Executing trigger_automation tool: automation_id={automation_id}")
    
    try:
        if _automation_manager is None:
            return {
                "status": "error",
                "message": "Automation manager not available.",
            }
        
        # Check if automation exists
        if automation_id not in _automation_manager._automations:
            return {
                "status": "error",
                "message": f"Automation '{automation_id}' not found.",
            }
        
        # Check if another automation is executing (LAW 10)
        if _automation_manager.is_executing():
            return {
                "status": "error",
                "message": f"Cannot trigger: automation '{_automation_manager._executing_automation}' is already executing (LAW 10 - Serial Execution).",
            }
        
        # Trigger the automation
        task_id = _automation_manager.execute_automation(
            automation_id=automation_id,
            context=context,
        )
        
        result = {
            "status": "ok",
            "automation_id": automation_id,
            "task_id": str(task_id),
            "message": f"Automation '{automation_id}' triggered successfully.",
        }
        
        logger.info(f"trigger_automation completed: task_id={task_id}")
        return result
        
    except Exception as e:
        logger.error(f"Trigger automation failed: {e}", exc_info=True)
        return {
            "status": "error",
            "message": str(e),
        }
