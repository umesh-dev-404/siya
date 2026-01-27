"""
System Tools Package

Core system tools for monitoring and status.
Per DIP Phase 11: Core system tools implementation.
"""

import logging
from tools.tool_executor import ToolExecutor

logger = logging.getLogger(__name__)


def register_system_tools(executor: ToolExecutor) -> None:
    """Register system tools."""
    from tools.system.resource_monitor_tool import resource_monitor_impl
    from tools.system.log_query_tool import log_query_impl
    
    executor.register("resource_monitor", lambda args: resource_monitor_impl(args))
    executor.register("log_query", lambda args: log_query_impl(args))
    
    logger.info("System tools registered: resource_monitor, log_query")
