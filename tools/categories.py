"""
Tool Categories

Defines tool category taxonomy for organizing tools.
Per DIP Phase 11: Define tool categories.

Categories help organize and filter tools for different use cases.
"""

from enum import Enum


class ToolCategory(str, Enum):
    """
    Tool category taxonomy.
    
    Each tool belongs to exactly one category.
    Categories are used for:
    - Organizing tool listings
    - Filtering available tools
    - Documentation grouping
    """

    SYSTEM = "system"
    """System information and monitoring tools (get_system_status, resource monitor, logs)."""

    FILE = "file"
    """File system operations (read, write, list, metadata)."""

    MEMORY = "memory"
    """Memory system operations (read, query memory entries)."""

    AUTOMATION = "automation"
    """Automation triggers and scheduling (list, trigger, status)."""

    CONTENT = "content"
    """Content processing tools using AI (summarize, translate, format)."""

    INTEGRATION = "integration"
    """External integrations (mail, calendar, APIs)."""


# Category descriptions for documentation
CATEGORY_DESCRIPTIONS = {
    ToolCategory.SYSTEM: "System monitoring and status tools",
    ToolCategory.FILE: "File system read/write operations",
    ToolCategory.MEMORY: "Memory and knowledge base access",
    ToolCategory.AUTOMATION: "Automation and scheduling control",
    ToolCategory.CONTENT: "AI-powered content processing",
    ToolCategory.INTEGRATION: "External service integrations",
}
