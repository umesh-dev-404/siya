"""
Interactive Menus for Siya CLI.

Per Phase 18: Arrow-key navigable menus using InquirerPy.
"""

from typing import Any, Dict, List, Optional, Tuple

from InquirerPy import inquirer
from InquirerPy.base.control import Choice
from InquirerPy.separator import Separator
from rich.console import Console

console = Console()

# Tool categories matching web UI
TOOL_CATEGORIES = {
    "System": ["get_system_status", "resource_monitor", "log_query", "get_config", "set_config", "execute_pi_command"],
    "Files": ["directory_list", "file_read", "file_write"],
    "Mail": ["fetch_mails", "get_mail", "search_mails"],
    "Sync": ["get_sync_status", "trigger_sync"],
    "Memory": ["memory_store", "memory_retrieve", "memory_search"],
    "Intelligence": ["summarize_text", "analyze_sentiment", "extract_entities", "generate_response", "ask_question"],
    "Automation": ["list_automations", "get_automation", "trigger_automation"],
    "Voice": ["speak_text", "listen_for_input"],
    "Notifications": ["list_notifications", "acknowledge_notification"],
}


def show_main_menu(tools: List[Dict[str, Any]]) -> Optional[str]:
    """
    Show the main interactive menu with categorized tools.
    
    Args:
        tools: List of tool definitions from server
        
    Returns:
        Selected tool name or None if user exits
    """
    # Build tool lookup for quick access
    tool_lookup = {t["name"]: t for t in tools}
    
    # Build choices with categories and separators
    choices = []
    
    for category, tool_names in TOOL_CATEGORIES.items():
        # Add separator for category
        choices.append(Separator(f"───── {category} ─────"))
        
        # Add tools in this category
        for tool_name in tool_names:
            if tool_name in tool_lookup:
                tool = tool_lookup[tool_name]
                # Add warning indicator for confirmation-required tools
                label = _format_tool_label(tool)
                choices.append(Choice(value=tool_name, name=label))
    
    # Add settings section
    choices.append(Separator("───── Settings ─────"))
    choices.append(Choice(value="_server_info", name="📡 Server Info"))
    choices.append(Choice(value="_help", name="❓ Help"))
    choices.append(Choice(value="_exit", name="👋 Exit"))
    
    # Show menu
    try:
        result = inquirer.select(
            message="What would you like to do?",
            choices=choices,
            default=None,
            pointer="❯",
            qmark="?",
            amark="✓",
            instruction="(Use arrow keys, type to filter)",
        ).execute()
        
        return result
    except KeyboardInterrupt:
        return "_exit"


def show_tool_select(tools: List[Dict[str, Any]], category: Optional[str] = None) -> Optional[str]:
    """
    Show a fuzzy-searchable tool selection menu.
    
    Args:
        tools: List of tool definitions
        category: Optional category filter
        
    Returns:
        Selected tool name or None
    """
    choices = []
    
    for tool in tools:
        # Filter by category if specified
        if category:
            tool_category = _get_tool_category(tool["name"])
            if tool_category != category:
                continue
        
        label = _format_tool_label(tool)
        choices.append(Choice(value=tool["name"], name=label))
    
    if not choices:
        console.print("[dim]No tools available[/dim]")
        return None
    
    try:
        result = inquirer.fuzzy(
            message="Select a tool:",
            choices=choices,
            pointer="❯",
            qmark="🔧",
        ).execute()
        
        return result
    except KeyboardInterrupt:
        return None


def _format_tool_label(tool: Dict[str, Any]) -> str:
    """Format a tool for display in menu."""
    name = tool["name"]
    desc = tool.get("description", "")[:40]
    
    # Check if requires confirmation
    schema = tool.get("inputSchema", {})
    requires_confirm = schema.get("properties", {}).get("_confirmed") is not None
    
    # Get icon based on category
    icon = _get_tool_icon(name)
    
    # Build label
    label = f"{icon} {name}"
    if requires_confirm:
        label += " ⚠"
    if desc:
        label += f" [dim]— {desc}[/dim]"
    
    return label


def _get_tool_icon(name: str) -> str:
    """Get emoji icon for tool."""
    icons = {
        "get_system_status": "💻",
        "resource_monitor": "📊",
        "log_query": "📋",
        "directory_list": "📁",
        "file_read": "📄",
        "file_write": "✏️",
        "fetch_mails": "📧",
        "get_mail": "✉️",
        "search_mails": "🔍",
        "get_sync_status": "🔄",
        "trigger_sync": "⚡",
        "memory_store": "💾",
        "memory_retrieve": "📥",
        "memory_search": "🔎",
        "summarize_text": "📝",
        "generate_response": "🤖",
        "ask_question": "❓",
        "list_automations": "⚙️",
        "trigger_automation": "🚀",
        "speak_text": "🔊",
        "listen_for_input": "🎤",
        "list_notifications": "🔔",
    }
    return icons.get(name, "🔧")


def _get_tool_category(name: str) -> Optional[str]:
    """Get category for a tool."""
    for category, tools in TOOL_CATEGORIES.items():
        if name in tools:
            return category
    return None
