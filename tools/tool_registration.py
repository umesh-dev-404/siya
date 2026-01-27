"""
Tool Registration

Registers all tool implementations with the ToolExecutor.
This is called during service initialization.

Per LAW 4: Only registered tools are callable.
Per LAW 6: Registry is static (no dynamic generation).
"""

import logging

from tools.tool_executor import ToolExecutor

logger = logging.getLogger(__name__)


def register_sync_tools(executor: ToolExecutor) -> None:
    """
    Register sync tools with the executor.
    
    Tools:
    - get_sync_status: READ permission, no confirmation
    - trigger_sync: EXECUTE permission, requires confirmation (LAW 1)
    - clear_sync_queue: WRITE permission, requires confirmation (LAW 1)
    """
    from tools.sync_tools import (
        get_sync_status,
        trigger_sync,
        clear_sync_queue,
    )
    
    executor.register("get_sync_status", lambda args: get_sync_status())
    executor.register("trigger_sync", lambda args: trigger_sync(args.get("direction", "bidirectional")))
    executor.register("clear_sync_queue", lambda args: clear_sync_queue(args.get("older_than_hours", 24)))
    
    logger.info("Sync tools registered: get_sync_status, trigger_sync, clear_sync_queue")


def register_timer_tools(executor: ToolExecutor) -> None:
    """
    Register timer tools from Phase 14.
    """
    from tools.timer_tools import (
        list_scheduled_automations,
        schedule_automation,
        unschedule_automation,
        get_schedule_status,
        enable_schedule,
        disable_schedule,
    )
    
    executor.register("list_scheduled_automations", lambda args: list_scheduled_automations())
    executor.register("schedule_automation", lambda args: schedule_automation(
        automation_id=args["automation_id"],
        name=args["name"],
        on_calendar=args.get("on_calendar"),
        on_boot_sec=args.get("on_boot_sec"),
        on_unit_active_sec=args.get("on_unit_active_sec"),
    ))
    executor.register("unschedule_automation", lambda args: unschedule_automation(args["schedule_id"]))
    executor.register("get_schedule_status", lambda args: get_schedule_status(args["schedule_id"]))
    executor.register("enable_schedule", lambda args: enable_schedule(args["schedule_id"]))
    executor.register("disable_schedule", lambda args: disable_schedule(args["schedule_id"]))
    
    logger.info("Timer tools registered")


def register_notification_tools(executor: ToolExecutor) -> None:
    """
    Register notification tools from Phase 15.
    """
    from tools.notification_tools import (
        list_notifications,
        acknowledge_notification,
        acknowledge_all_notifications,
        clear_notifications,
        send_notification,
    )
    
    executor.register("list_notifications", lambda args: list_notifications(
        unread_only=args.get("unread_only", True),
        notification_type=args.get("notification_type"),
        limit=args.get("limit", 20),
    ))
    executor.register("acknowledge_notification", lambda args: acknowledge_notification(args["notification_id"]))
    executor.register("acknowledge_all_notifications", lambda args: acknowledge_all_notifications())
    executor.register("clear_notifications", lambda args: clear_notifications(args.get("days_old", 30)))
    executor.register("send_notification", lambda args: send_notification(
        title=args["title"],
        message=args["message"],
        notification_type=args.get("notification_type", "info"),
        priority=args.get("priority", "normal"),
    ))
    
    logger.info("Notification tools registered")


def register_voice_tools(executor: ToolExecutor) -> None:
    """
    Register voice tools from Phase 16.
    """
    from tools.voice_tools import (
        speak_text,
        listen_for_input,
    )
    
    executor.register("speak_text", lambda args: speak_text(args["text"]))
    executor.register("listen_for_input", lambda args: listen_for_input(args.get("timeout", 10)))
    
    logger.info("Voice tools registered")


def register_all_tools(executor: ToolExecutor) -> None:
    """
    Register all tool implementations.
    """
    # Core system tools (existing)
    try:
        from tools.system import register_system_tools
        register_system_tools(executor)
    except ImportError:
        logger.debug("System tools not available")
    
    # File tools (existing)
    try:
        from tools.file import register_file_tools
        register_file_tools(executor)
    except ImportError:
        logger.debug("File tools not available")
    
    # Mail tools (existing)
    try:
        from tools.mail_tools import register_mail_tools
        register_mail_tools(executor)
    except ImportError:
        logger.debug("Mail tools not available")
    
    # Automation tools (existing)
    try:
        from tools.automation_tools import register_automation_tools
        register_automation_tools(executor)
    except ImportError:
        logger.debug("Automation tools not available")
    
    # Sync tools (Phase 13)
    try:
        register_sync_tools(executor)
    except ImportError:
        logger.debug("Sync tools not available")
    
    # Timer tools (Phase 14)
    try:
        register_timer_tools(executor)
    except ImportError:
        logger.debug("Timer tools not available")
        
    # Notification tools (Phase 15)
    try:
        register_notification_tools(executor)
    except ImportError:
        logger.debug("Notification tools not available")

    # Voice tools (Phase 16)
    try:
        register_voice_tools(executor)
    except ImportError:
        logger.debug("Voice tools not available")
    
    logger.info("All available tools registered")
