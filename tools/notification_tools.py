"""
Notification Tools - User Notification Management

MCP tools for managing notifications.
Per Phase 15: Enhanced User Notifications.

LAW Compliance:
- LAW 1: User controls notifications
- LAW 13: All operations logged
"""

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


def list_notifications(
    unread_only: bool = True,
    notification_type: Optional[str] = None,
    limit: int = 20,
) -> Dict[str, Any]:
    """
    List notifications.
    
    Args:
        unread_only: Only show unread notifications
        notification_type: Filter by type (info, warning, error, alert)
        limit: Maximum notifications to return
        
    Returns:
        Dictionary with notification list
    """
    try:
        from notifications.notification_manager import get_notification_manager
        from notifications.notification import NotificationType
        
        manager = get_notification_manager()
        
        type_filter = None
        if notification_type:
            try:
                type_filter = NotificationType(notification_type.lower())
            except ValueError:
                pass
        
        notifications = manager.get_notifications(
            unread_only=unread_only,
            notification_type=type_filter,
            limit=limit,
        )
        
        return {
            "success": True,
            "notifications": [n.to_dict() for n in notifications],
            "count": len(notifications),
            "unread_total": manager.get_unread_count(),
        }
        
    except ImportError as e:
        return {
            "success": False,
            "error": f"Notification module not available: {e}",
        }
    except Exception as e:
        logger.error(f"Failed to list notifications: {e}")
        return {
            "success": False,
            "error": str(e),
        }


def acknowledge_notification(notification_id: str) -> Dict[str, Any]:
    """
    Acknowledge a notification.
    
    Args:
        notification_id: ID of the notification
        
    Returns:
        Result dictionary
    """
    try:
        from notifications.notification_manager import get_notification_manager
        
        manager = get_notification_manager()
        success = manager.acknowledge(notification_id)
        
        return {
            "success": success,
            "notification_id": notification_id,
            "message": "Acknowledged" if success else "Not found",
        }
        
    except Exception as e:
        logger.error(f"Failed to acknowledge notification: {e}")
        return {
            "success": False,
            "error": str(e),
        }


def acknowledge_all_notifications() -> Dict[str, Any]:
    """
    Acknowledge all unread notifications.
    
    Returns:
        Result dictionary with count
    """
    try:
        from notifications.notification_manager import get_notification_manager
        
        manager = get_notification_manager()
        count = manager.acknowledge_all()
        
        return {
            "success": True,
            "acknowledged_count": count,
        }
        
    except Exception as e:
        logger.error(f"Failed to acknowledge notifications: {e}")
        return {
            "success": False,
            "error": str(e),
        }


def clear_notifications(days_old: int = 30, clear_all: bool = False) -> Dict[str, Any]:
    """
    Clear notifications.
    
    Args:
        days_old: Clear notifications older than this (default 30, ignored if clear_all=True)
        clear_all: If True, clear ALL acknowledged notifications regardless of age
        
    Returns:
        Result dictionary with count
        
    Note:
        This tool requires confirmation (LAW 1).
    """
    try:
        from notifications.notification_manager import get_notification_manager
        from notifications.notification_store import get_notification_store
        
        if clear_all:
            # Clear all acknowledged notifications
            store = get_notification_store()
            count = store.clear_all(acknowledged_only=True)
            return {
                "success": True,
                "cleared_count": count,
                "mode": "all_acknowledged",
            }
        else:
            # Original behavior: clear old acknowledged notifications
            manager = get_notification_manager()
            count = manager.cleanup(days=days_old)
            return {
                "success": True,
                "cleared_count": count,
                "days_old": days_old,
                "mode": "older_than_days",
            }
        
    except Exception as e:
        logger.error(f"Failed to clear notifications: {e}")
        return {
            "success": False,
            "error": str(e),
        }


def send_notification(
    title: str,
    message: str,
    notification_type: str = "info",
    priority: str = "normal",
) -> Dict[str, Any]:
    """
    Send a notification.
    
    Args:
        title: Notification title
        message: Notification message
        notification_type: Type (info, success, warning, error, alert)
        priority: Priority (low, normal, high, urgent)
        
    Returns:
        Result dictionary
        
    Note:
        This is for programmatic/tool-generated notifications.
    """
    try:
        from notifications.notification_manager import get_notification_manager
        from notifications.notification import NotificationType, Priority
        
        manager = get_notification_manager()
        
        # Parse type
        try:
            n_type = NotificationType(notification_type.lower())
        except ValueError:
            n_type = NotificationType.INFO
        
        # Parse priority
        priority_map = {
            "low": Priority.LOW,
            "normal": Priority.NORMAL,
            "high": Priority.HIGH,
            "urgent": Priority.URGENT,
        }
        n_priority = priority_map.get(priority.lower(), Priority.NORMAL)
        
        notification = manager.notify(
            title=title,
            message=message,
            notification_type=n_type,
            priority=n_priority,
            source="tool:send_notification",
        )
        
        return {
            "success": True,
            "notification_id": notification.notification_id,
            "delivered": notification.status.value == "delivered",
        }
        
    except Exception as e:
        logger.error(f"Failed to send notification: {e}")
        return {
            "success": False,
            "error": str(e),
        }


# Tool schemas for MCP registration
NOTIFICATION_TOOL_SCHEMAS = [
    {
        "name": "list_notifications",
        "description": "List notifications, optionally filtered by type or unread status.",
        "permission_level": "READ",
        "requires_confirmation": False,
        "parameters": {
            "unread_only": {
                "type": "boolean",
                "description": "Only show unread notifications",
                "required": False,
            },
            "notification_type": {
                "type": "string",
                "description": "Filter by type: info, success, warning, error, alert",
                "required": False,
            },
            "limit": {
                "type": "integer",
                "description": "Maximum notifications to return",
                "required": False,
            },
        },
        "handler": list_notifications,
    },
    {
        "name": "acknowledge_notification",
        "description": "Acknowledge a specific notification.",
        "permission_level": "WRITE",
        "requires_confirmation": False,
        "parameters": {
            "notification_id": {
                "type": "string",
                "description": "ID of the notification to acknowledge",
                "required": True,
            },
        },
        "handler": acknowledge_notification,
    },
    {
        "name": "acknowledge_all_notifications",
        "description": "Acknowledge all unread notifications.",
        "permission_level": "WRITE",
        "requires_confirmation": False,
        "parameters": {},
        "handler": acknowledge_all_notifications,
    },
    {
        "name": "clear_notifications",
        "description": "Clear acknowledged notifications. Use clear_all=True to clear all acknowledged notifications immediately.",
        "permission_level": "WRITE",
        "requires_confirmation": True,  # LAW 1: Deletes data
        "parameters": {
            "days_old": {
                "type": "integer",
                "description": "Clear notifications older than this many days (ignored if clear_all=True)",
                "required": False,
            },
            "clear_all": {
                "type": "boolean",
                "description": "If True, clear ALL acknowledged notifications regardless of age",
                "required": False,
            },
        },
        "handler": clear_notifications,
    },
    {
        "name": "send_notification",
        "description": "Send a notification to the user.",
        "permission_level": "EXECUTE",
        "requires_confirmation": False,
        "parameters": {
            "title": {
                "type": "string",
                "description": "Notification title",
                "required": True,
            },
            "message": {
                "type": "string",
                "description": "Notification message",
                "required": True,
            },
            "notification_type": {
                "type": "string",
                "description": "Type: info, success, warning, error, alert",
                "required": False,
            },
            "priority": {
                "type": "string",
                "description": "Priority: low, normal, high, urgent",
                "required": False,
            },
        },
        "handler": send_notification,
    },
]
