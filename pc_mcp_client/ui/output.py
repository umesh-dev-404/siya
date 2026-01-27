"""
Styled Output Panels for Siya CLI.

Per Phase 18: Rich panels, tables, and spinners for formatted output.
"""

import json
from typing import Any, Dict, List, Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.spinner import Spinner
from rich.live import Live
from rich.syntax import Syntax

console = Console()


def show_success(title: str, content: Any) -> None:
    """
    Display a success panel with formatted content.
    
    Args:
        title: Panel title
        content: Content to display (dict, list, or string)
    """
    formatted = _format_content(content)
    panel = Panel(
        formatted,
        title=f"[bold green]✓ {title}[/bold green]",
        border_style="green",
        padding=(1, 2),
    )
    console.print(panel)


def show_error(title: str, message: str) -> None:
    """
    Display an error panel.
    
    Args:
        title: Error title
        message: Error message
    """
    panel = Panel(
        Text(message, style="red"),
        title=f"[bold red]✗ {title}[/bold red]",
        border_style="red",
        padding=(1, 2),
    )
    console.print(panel)


def show_warning(title: str, message: str) -> None:
    """
    Display a warning panel.
    
    Args:
        title: Warning title
        message: Warning message
    """
    panel = Panel(
        Text(message, style="yellow"),
        title=f"[bold yellow]⚠ {title}[/bold yellow]",
        border_style="yellow",
        padding=(1, 2),
    )
    console.print(panel)


def show_info(title: str, content: Any) -> None:
    """
    Display an info panel.
    
    Args:
        title: Panel title
        content: Content to display
    """
    formatted = _format_content(content)
    panel = Panel(
        formatted,
        title=f"[bold cyan]ℹ {title}[/bold cyan]",
        border_style="cyan",
        padding=(1, 2),
    )
    console.print(panel)


def show_table(title: str, data: List[Dict[str, Any]], columns: Optional[List[str]] = None) -> None:
    """
    Display data as a table.
    
    Args:
        title: Table title
        data: List of dicts to display
        columns: Optional column names (auto-detected if not provided)
    """
    if not data:
        console.print(f"[dim]No data for {title}[/dim]")
        return
    
    # Auto-detect columns from first row
    if columns is None:
        columns = list(data[0].keys())
    
    table = Table(title=title, border_style="cyan")
    
    for col in columns:
        table.add_column(_format_label(col), style="cyan", no_wrap=True)
    
    for row in data:
        table.add_row(*[str(row.get(col, "")) for col in columns])
    
    console.print(table)


def show_json(data: Any, title: Optional[str] = None) -> None:
    """
    Display formatted JSON output.
    
    Args:
        data: Data to format as JSON
        title: Optional title
    """
    json_str = json.dumps(data, indent=2, ensure_ascii=False)
    syntax = Syntax(json_str, "json", theme="monokai", line_numbers=False)
    
    if title:
        console.print(f"\n[bold]{title}[/bold]")
    console.print(syntax)


class ExecutionSpinner:
    """Context manager for showing a spinner during execution."""
    
    def __init__(self, message: str = "Executing..."):
        self.message = message
        self.live = None
    
    def __enter__(self):
        spinner = Spinner("dots", text=f" {self.message}", style="cyan")
        self.live = Live(spinner, console=console, refresh_per_second=10, transient=True)
        self.live.__enter__()
        return self
    
    def __exit__(self, *args):
        if self.live:
            self.live.__exit__(*args)


def _format_content(content: Any) -> Text:
    """Format content for display in panels."""
    if isinstance(content, str):
        return Text(content)
    
    if isinstance(content, dict):
        return _format_dict(content)
    
    if isinstance(content, list):
        return _format_list(content)
    
    return Text(str(content))


def _format_dict(data: Dict[str, Any], indent: int = 0) -> Text:
    """Format a dictionary for display."""
    text = Text()
    prefix = "  " * indent
    
    for key, value in data.items():
        label = _format_label(key)
        text.append(f"{prefix}{label}: ", style="bold cyan")
        
        if isinstance(value, dict):
            text.append("\n")
            text.append(_format_dict(value, indent + 1))
        elif isinstance(value, list):
            if len(value) == 0:
                text.append("(empty)", style="dim")
            elif all(isinstance(v, (str, int, float, bool)) for v in value):
                text.append(", ".join(str(v) for v in value))
            else:
                text.append("\n")
                text.append(_format_list(value, indent + 1))
        elif isinstance(value, bool):
            text.append("✓ Yes" if value else "✗ No", style="green" if value else "red")
        elif value is None:
            text.append("—", style="dim")
        else:
            # Check for status-like values
            str_val = str(value)
            style = _get_status_style(str_val)
            text.append(str_val, style=style)
        
        text.append("\n")
    
    return text


def _format_list(data: List[Any], indent: int = 0) -> Text:
    """Format a list for display."""
    text = Text()
    prefix = "  " * indent
    
    for i, item in enumerate(data):
        if isinstance(item, dict):
            text.append(f"{prefix}[{i + 1}]\n")
            text.append(_format_dict(item, indent + 1))
        else:
            text.append(f"{prefix}• {item}\n")
    
    return text


def _format_label(key: str) -> str:
    """Convert snake_case to Title Case."""
    return key.replace("_", " ").title()


def _get_status_style(value: str) -> str:
    """Get style based on status-like values."""
    lower = value.lower()
    if lower in ("success", "ok", "online", "connected", "true", "active", "enabled"):
        return "green"
    if lower in ("error", "fail", "failed", "offline", "disconnected", "false", "disabled"):
        return "red"
    if lower in ("warning", "pending", "waiting", "partial"):
        return "yellow"
    return ""
