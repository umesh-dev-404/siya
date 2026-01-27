"""
Simple Siya Wake Command.

Per Phase 18: Simple `siya` command for quick interactive access.
Saves connection config for auto-connect on subsequent runs.
"""

import json
import os
import sys
from pathlib import Path
from typing import Optional

from rich.console import Console

console = Console()

# Config file location
CONFIG_DIR = Path.home() / ".siya"
CONFIG_FILE = CONFIG_DIR / "config.json"


def get_config() -> dict:
    """Load saved configuration."""
    if CONFIG_FILE.exists():
        try:
            return json.loads(CONFIG_FILE.read_text())
        except Exception:
            return {}
    return {}


def save_config(config: dict) -> None:
    """Save configuration to file."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(config, indent=2))


def first_run_setup() -> Optional[str]:
    """Run first-time setup to get server URL."""
    from InquirerPy import inquirer
    
    console.print("\n[bold cyan]Welcome to Siya![/bold cyan]")
    console.print("[dim]First-time setup - let's configure your connection.[/dim]\n")
    
    try:
        url = inquirer.text(
            message="Enter your Pi server URL:",
            default="http://192.168.1.39:8080",
            validate=lambda x: x.startswith("http"),
            invalid_message="URL must start with http:// or https://",
        ).execute()
        
        if url:
            save_config({"url": url, "transport": "http"})
            console.print(f"\n[green]Config saved to {CONFIG_FILE}[/green]")
            return url
    except KeyboardInterrupt:
        console.print("\n[dim]Setup cancelled.[/dim]")
        return None
    
    return None


def main() -> int:
    """
    Main entry point for the simple `siya` command.
    
    Auto-connects to saved server or runs first-time setup.
    """
    # Check for saved config
    config = get_config()
    url = config.get("url")
    
    # First-run setup if no config
    if not url:
        url = first_run_setup()
        if not url:
            return 1
    
    # Create client and launch interactive mode
    from pc_mcp_client.http_client import MCPHttpClient
    from pc_mcp_client.interactive import interactive_main
    
    try:
        client = MCPHttpClient(base_url=url)
        with client:
            client.initialize()
            return interactive_main(client, server_url=url)
    except Exception as e:
        console.print(f"[red]Connection failed: {e}[/red]")
        console.print(f"[dim]Server URL: {url}[/dim]")
        console.print("[dim]Run 'siya --reset' to reconfigure.[/dim]")
        return 1


def reset_config() -> None:
    """Reset saved configuration."""
    if CONFIG_FILE.exists():
        CONFIG_FILE.unlink()
        console.print("[green]Config reset. Run 'siya' to set up again.[/green]")
    else:
        console.print("[dim]No config to reset.[/dim]")


if __name__ == "__main__":
    # Handle --reset flag
    if "--reset" in sys.argv:
        reset_config()
        sys.exit(0)
    
    sys.exit(main())
