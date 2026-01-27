"""
Timer Tools - Scheduled Automation Control

MCP tools for managing scheduled automations via systemd timers.
Per Phase 14: Timer Integration.

LAW Compliance:
- LAW 1: schedule/unschedule require confirmation
- LAW 2: Timers trigger via orchestrator
- LAW 13: All operations logged
"""

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


def list_scheduled_automations() -> Dict[str, Any]:
    """
    List all scheduled automations.
    
    Returns:
        Dictionary with list of schedules and their status
    """
    try:
        from automations.schedule_manager import get_schedule_manager
        from automations.systemd_timer import get_timer_generator
        
        manager = get_schedule_manager()
        timer_gen = get_timer_generator()
        
        schedules = manager.list_schedules()
        
        results = []
        for schedule in schedules:
            timer_status = timer_gen.get_timer_status(schedule.schedule_id)
            results.append({
                "schedule_id": schedule.schedule_id,
                "automation_id": schedule.automation_id,
                "name": schedule.name,
                "enabled": schedule.enabled,
                "on_calendar": schedule.on_calendar,
                "interval": schedule.interval,
                "timer_active": timer_status.get("is_active", False),
                "next_trigger": timer_status.get("next_trigger"),
                "last_triggered": schedule.last_triggered,
            })
        
        return {
            "success": True,
            "schedules": results,
            "count": len(results),
            "systemd_available": timer_gen.is_systemd_available(),
        }
        
    except ImportError as e:
        return {
            "success": False,
            "error": f"Timer module not available: {e}",
        }
    except Exception as e:
        logger.error(f"Failed to list schedules: {e}")
        return {
            "success": False,
            "error": str(e),
        }


def schedule_automation(
    automation_id: str,
    name: str,
    on_calendar: Optional[str] = None,
    interval: Optional[str] = None,
    on_boot_delay: Optional[str] = None,
    description: str = "",
) -> Dict[str, Any]:
    """
    Schedule an automation for periodic execution.
    
    Args:
        automation_id: ID of the automation to schedule
        name: Human-readable name for the schedule
        on_calendar: Calendar expression (e.g., "Mon..Fri 09:00", "daily", "*:0/15")
        interval: Interval between runs (e.g., "15min", "1h", "1d")
        on_boot_delay: Run after boot with delay (e.g., "5min")
        description: Optional description
        
    Returns:
        Result dictionary with schedule ID
        
    Note:
        At least one of on_calendar, interval, or on_boot_delay must be specified.
        This tool requires confirmation (LAW 1).
    """
    try:
        from automations.schedule_manager import get_schedule_manager
        
        manager = get_schedule_manager()
        
        result = manager.create_schedule(
            automation_id=automation_id,
            name=name,
            description=description,
            on_calendar=on_calendar,
            interval=interval,
            on_boot_delay=on_boot_delay,
            install_timer=True,
        )
        
        return result
        
    except ImportError as e:
        return {
            "success": False,
            "error": f"Timer module not available: {e}",
        }
    except Exception as e:
        logger.error(f"Failed to create schedule: {e}")
        return {
            "success": False,
            "error": str(e),
        }


def unschedule_automation(schedule_id: str) -> Dict[str, Any]:
    """
    Remove a scheduled automation.
    
    Args:
        schedule_id: ID of the schedule to remove
        
    Returns:
        Result dictionary
        
    Note:
        This tool requires confirmation (LAW 1).
    """
    try:
        from automations.schedule_manager import get_schedule_manager
        
        manager = get_schedule_manager()
        return manager.delete_schedule(schedule_id)
        
    except ImportError as e:
        return {
            "success": False,
            "error": f"Timer module not available: {e}",
        }
    except Exception as e:
        logger.error(f"Failed to delete schedule: {e}")
        return {
            "success": False,
            "error": str(e),
        }


def get_schedule_status(schedule_id: str) -> Dict[str, Any]:
    """
    Get detailed status of a scheduled automation.
    
    Args:
        schedule_id: ID of the schedule
        
    Returns:
        Status dictionary including timer status
    """
    try:
        from automations.schedule_manager import get_schedule_manager
        
        manager = get_schedule_manager()
        return manager.get_schedule_status(schedule_id)
        
    except ImportError as e:
        return {
            "success": False,
            "error": f"Timer module not available: {e}",
        }
    except Exception as e:
        logger.error(f"Failed to get schedule status: {e}")
        return {
            "success": False,
            "error": str(e),
        }


def enable_schedule(schedule_id: str) -> Dict[str, Any]:
    """
    Enable a disabled schedule.
    
    Args:
        schedule_id: ID of the schedule
        
    Returns:
        Result dictionary
    """
    try:
        from automations.schedule_manager import get_schedule_manager
        
        manager = get_schedule_manager()
        return manager.enable_schedule(schedule_id)
        
    except Exception as e:
        logger.error(f"Failed to enable schedule: {e}")
        return {"success": False, "error": str(e)}


def disable_schedule(schedule_id: str) -> Dict[str, Any]:
    """
    Disable a schedule without deleting it.
    
    Args:
        schedule_id: ID of the schedule
        
    Returns:
        Result dictionary
    """
    try:
        from automations.schedule_manager import get_schedule_manager
        
        manager = get_schedule_manager()
        return manager.disable_schedule(schedule_id)
        
    except Exception as e:
        logger.error(f"Failed to disable schedule: {e}")
        return {"success": False, "error": str(e)}


# Tool schemas for MCP registration
TIMER_TOOL_SCHEMAS = [
    {
        "name": "list_scheduled_automations",
        "description": "List all scheduled automations with their status and next trigger time.",
        "permission_level": "READ",
        "requires_confirmation": False,
        "parameters": {},
        "handler": list_scheduled_automations,
    },
    {
        "name": "schedule_automation",
        "description": "Schedule an automation for periodic execution. Specify on_calendar (e.g., 'daily', 'Mon..Fri 09:00'), interval (e.g., '15min', '1h'), or on_boot_delay.",
        "permission_level": "EXECUTE",
        "requires_confirmation": True,  # LAW 1: Creates persistent state
        "parameters": {
            "automation_id": {
                "type": "string",
                "description": "ID of the automation to schedule",
                "required": True,
            },
            "name": {
                "type": "string",
                "description": "Human-readable name for the schedule",
                "required": True,
            },
            "on_calendar": {
                "type": "string",
                "description": "Calendar expression (e.g., 'daily', 'Mon..Fri 09:00')",
                "required": False,
            },
            "interval": {
                "type": "string",
                "description": "Interval between runs (e.g., '15min', '1h')",
                "required": False,
            },
            "on_boot_delay": {
                "type": "string",
                "description": "Run after boot with delay (e.g., '5min')",
                "required": False,
            },
            "description": {
                "type": "string",
                "description": "Optional description",
                "required": False,
            },
        },
        "handler": schedule_automation,
    },
    {
        "name": "unschedule_automation",
        "description": "Remove a scheduled automation.",
        "permission_level": "WRITE",
        "requires_confirmation": True,  # LAW 1: Removes persistent state
        "parameters": {
            "schedule_id": {
                "type": "string",
                "description": "ID of the schedule to remove",
                "required": True,
            },
        },
        "handler": unschedule_automation,
    },
    {
        "name": "get_schedule_status",
        "description": "Get detailed status of a scheduled automation including timer status.",
        "permission_level": "READ",
        "requires_confirmation": False,
        "parameters": {
            "schedule_id": {
                "type": "string",
                "description": "ID of the schedule",
                "required": True,
            },
        },
        "handler": get_schedule_status,
    },
    {
        "name": "enable_schedule",
        "description": "Enable a disabled schedule.",
        "permission_level": "WRITE",
        "requires_confirmation": False,
        "parameters": {
            "schedule_id": {
                "type": "string",
                "description": "ID of the schedule to enable",
                "required": True,
            },
        },
        "handler": enable_schedule,
    },
    {
        "name": "disable_schedule",
        "description": "Disable a schedule without deleting it.",
        "permission_level": "WRITE",
        "requires_confirmation": False,
        "parameters": {
            "schedule_id": {
                "type": "string",
                "description": "ID of the schedule to disable",
                "required": True,
            },
        },
        "handler": disable_schedule,
    },
]
