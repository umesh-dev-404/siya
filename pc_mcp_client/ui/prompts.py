"""
Interactive Prompts for Siya CLI.

Per Phase 18: Argument prompts and LAW 1 confirmation dialogs.
"""

from typing import Any, Dict, List, Optional

from InquirerPy import inquirer
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

console = Console()


def prompt_for_arguments(tool: Dict[str, Any]) -> Dict[str, Any]:
    """
    Interactively prompt user for tool arguments.
    
    Args:
        tool: Tool definition with inputSchema
        
    Returns:
        Dict of argument values
    """
    schema = tool.get("inputSchema", {})
    properties = schema.get("properties", {})
    required = schema.get("required", [])
    
    # Filter out internal properties
    user_properties = {
        k: v for k, v in properties.items() 
        if not k.startswith("_")
    }
    
    if not user_properties:
        return {}
    
    console.print(f"\n[bold cyan]Arguments for {tool['name']}:[/bold cyan]\n")
    
    args = {}
    for name, prop in user_properties.items():
        value = _prompt_for_property(name, prop, name in required)
        if value is not None:
            args[name] = value
    
    return args


def _prompt_for_property(name: str, prop: Dict[str, Any], required: bool) -> Any:
    """Prompt for a single property value."""
    prop_type = prop.get("type", "string")
    description = prop.get("description", "")
    default = prop.get("default")
    enum = prop.get("enum")
    
    # Format label - no Rich markup since InquirerPy shows it literally
    label = _format_label(name)
    if required:
        label += " *"  # Simple asterisk for required
    if description:
        console.print(f"[dim]{description}[/dim]")
    
    try:
        # Handle enum types (select from list)
        if enum:
            result = inquirer.select(
                message=f"{label}:",
                choices=enum,
                default=default or enum[0],
            ).execute()
            return result
        
        # Handle boolean
        if prop_type == "boolean":
            result = inquirer.confirm(
                message=f"{label}:",
                default=default if default is not None else False,
            ).execute()
            return result
        
        # Handle integer
        if prop_type == "integer":
            result = inquirer.number(
                message=f"{label}:",
                default=default,
                float_allowed=False,
            ).execute()
            return int(result) if result else None
        
        # Handle number
        if prop_type == "number":
            result = inquirer.number(
                message=f"{label}:",
                default=default,
                float_allowed=True,
            ).execute()
            return float(result) if result else None
        
        # Handle array
        if prop_type == "array":
            result = inquirer.text(
                message=f"{label} (comma-separated):",
                default=",".join(default) if default else "",
            ).execute()
            return [v.strip() for v in result.split(",")] if result else []
        
        # Default: string input
        result = inquirer.text(
            message=f"{label}:",
            default=default or "",
        ).execute()
        
        # Return None for empty optional fields
        if not result and not required:
            return None
        
        return result
        
    except KeyboardInterrupt:
        return default


def show_confirmation_dialog(tool_name: str, args: Dict[str, Any], message: Optional[str] = None) -> bool:
    """
    Show LAW 1 confirmation dialog.
    
    Args:
        tool_name: Name of the tool
        args: Tool arguments
        message: Optional server message
        
    Returns:
        True if user confirms, False otherwise
    """
    # Build confirmation content
    content = Text()
    content.append("Tool: ", style="bold")
    content.append(f"{tool_name}\n", style="cyan")
    
    if args:
        content.append("\nArguments:\n", style="bold")
        for key, value in args.items():
            if not key.startswith("_"):
                content.append(f"  {_format_label(key)}: ", style="dim")
                content.append(f"{value}\n")
    
    content.append("\n")
    if message:
        content.append(f"{message}\n\n", style="yellow")
    
    content.append("This action requires your explicit confirmation.\n", style="yellow")
    content.append("LAW 1: Human Sovereignty", style="bold red")
    
    # Show panel
    panel = Panel(
        content,
        title="[bold yellow]⚠ CONFIRMATION REQUIRED[/bold yellow]",
        border_style="yellow",
        padding=(1, 2),
    )
    console.print(panel)
    
    # Prompt for confirmation
    try:
        result = inquirer.confirm(
            message="Proceed with execution?",
            default=False,
        ).execute()
        return result
    except KeyboardInterrupt:
        console.print("[dim]Cancelled[/dim]")
        return False


def prompt_text(message: str, default: str = "") -> str:
    """Simple text prompt."""
    try:
        return inquirer.text(message=message, default=default).execute()
    except KeyboardInterrupt:
        return ""


def prompt_confirm(message: str, default: bool = False) -> bool:
    """Simple confirmation prompt."""
    try:
        return inquirer.confirm(message=message, default=default).execute()
    except KeyboardInterrupt:
        return False


def _format_label(name: str) -> str:
    """Convert snake_case to Title Case."""
    return name.replace("_", " ").title()
