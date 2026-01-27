"""
ASCII Art Banner for Siya CLI.

Per Phase 18: Interactive CLI with styled output.
"""

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

try:
    import pyfiglet
    HAS_PYFIGLET = True
except ImportError:
    HAS_PYFIGLET = False

console = Console()


def show_banner(version: str = "1.0.0", connected: bool = False, server_url: str = "") -> None:
    """
    Display the Siya CLI banner with ASCII art.
    
    Args:
        version: Current version string
        connected: Whether connected to server
        server_url: Server URL if connected
    """
    # Generate ASCII art
    if HAS_PYFIGLET:
        ascii_art = pyfiglet.figlet_format("SIYA", font="slant")
    else:
        ascii_art = r"""
   _____ _______     __    
  / ____|_   _\ \   / /    
 | (___   | |  \ \_/ / ___ 
  \___ \  | |   \   / / _ \
  ____) |_| |_   | | | (_) |
 |_____/|_____|  |_|  \___/
"""
    
    # Build status line - use ASCII-safe characters
    if connected:
        status = "[bold green][+] Connected[/bold green]"
        if server_url:
            status += f" [dim]to {server_url}[/dim]"
    else:
        status = "[dim][-] Not connected[/dim]"
    
    # Create header
    console.print(f"[bold cyan]{ascii_art}[/bold cyan]")
    console.print(f"[dim]Personal Assistant Platform v{version}[/dim]")
    console.print(status)
    console.print()


def show_goodbye() -> None:
    """Display goodbye message."""
    console.print("\n[bold yellow]Goodbye![/bold yellow]")
    console.print("[dim]Thanks for using Siya.[/dim]\n")
