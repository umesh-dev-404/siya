"""
File Tools Package

File system operation tools for reading, writing, and listing.
Per DIP Phase 11: File operations tools implementation.
"""

import logging
from tools.tool_executor import ToolExecutor

logger = logging.getLogger(__name__)


def register_file_tools(executor: ToolExecutor) -> None:
    """Register file tools."""
    from tools.file.file_read_tool import file_read_impl
    from tools.file.file_write_tool import file_write_impl
    from tools.file.file_list_tool import directory_list_impl
    
    executor.register("file_read", lambda args: file_read_impl(args))
    executor.register("file_write", lambda args: file_write_impl(args))
    executor.register("directory_list", lambda args: directory_list_impl(args))
    
    logger.info("File tools registered: file_read, file_write, directory_list")
