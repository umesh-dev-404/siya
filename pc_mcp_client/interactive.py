"""
Interactive Mode for Siya CLI.

Per Phase 18: Main interactive loop with banner, menus, and styled output.
"""

import json
from typing import Any, Dict, Optional, Union

from rich.console import Console

from pc_mcp_client.http_client import MCPHttpClient
from pc_mcp_client.stdio_client import MCPStdioClient

from pc_mcp_client.ui.banner import show_banner, show_goodbye
from pc_mcp_client.ui.menus import show_main_menu
from pc_mcp_client.ui.output import (
    show_success,
    show_error,
    show_info,
    show_table,
    ExecutionSpinner,
)
from pc_mcp_client.ui.prompts import (
    prompt_for_arguments,
    show_confirmation_dialog,
)

console = Console()


def interactive_main(
    client: Union[MCPStdioClient, MCPHttpClient],
    server_url: Optional[str] = None,
) -> int:
    """
    Run the interactive CLI main loop.
    
    Args:
        client: MCP client (already initialized)
        server_url: Server URL for display
        
    Returns:
        Exit code
    """
    # Get tools from server
    try:
        tools_resp = client.tools_list()
        tools = tools_resp.get("tools", [])
    except Exception as e:
        show_error("Connection Failed", str(e))
        return 1
    
    # Build tool lookup
    tool_lookup = {t["name"]: t for t in tools}
    
    # Show banner
    show_banner(
        version="1.0.0",
        connected=True,
        server_url=server_url or "",
    )
    
    console.print(f"[dim]{len(tools)} tools available[/dim]\n")
    
    # Main loop
    while True:
        try:
            choice = show_main_menu(tools)
            
            if choice is None or choice == "_exit":
                show_goodbye()
                return 0
            
            if choice == "_server_info":
                _show_server_info(client, server_url)
                continue
            
            if choice == "_help":
                _show_help()
                continue
            
            # Execute selected tool
            tool = tool_lookup.get(choice)
            if tool:
                _execute_tool(client, tool)
            
        except KeyboardInterrupt:
            console.print("\n")
            continue
        except EOFError:
            show_goodbye()
            return 0


def _execute_tool(
    client: Union[MCPStdioClient, MCPHttpClient],
    tool: Dict[str, Any],
) -> None:
    """Execute a tool with interactive argument prompts."""
    tool_name = tool["name"]
    
    # Prompt for arguments
    args = prompt_for_arguments(tool)
    
    console.print()
    
    # Execute with spinner
    with ExecutionSpinner(f"Executing {tool_name}..."):
        try:
            result = client.tools_call(tool_name, args)
        except Exception as e:
            show_error("Execution Failed", str(e))
            return
    
    # Check for confirmation requirement
    if result.get("confirmationNeeded"):
        confirmed = show_confirmation_dialog(
            tool_name=result.get("tool", tool_name),
            args=result.get("arguments", args),
            message=result.get("message"),
        )
        
        if confirmed:
            with ExecutionSpinner(f"Executing {tool_name} (confirmed)..."):
                try:
                    result = client.tools_call(tool_name, args, confirmed=True)
                except Exception as e:
                    show_error("Execution Failed", str(e))
                    return
        else:
            show_info("Cancelled", "Action was cancelled by user.")
            return
    
    # Display result
    _display_result(tool_name, result)


def _display_result(tool_name: str, result: Dict[str, Any]) -> None:
    """Display tool execution result."""
    # Check for error
    if result.get("isError"):
        content = result.get("content", [{}])[0]
        show_error(tool_name, content.get("text", "Unknown error"))
        return
    
    # Extract content
    content = result.get("content", [])
    if content and isinstance(content, list):
        first = content[0]
        if first.get("type") == "text":
            try:
                data = json.loads(first.get("text", "{}"))
                show_success(tool_name, data)
            except json.JSONDecodeError:
                show_success(tool_name, first.get("text", ""))
        else:
            show_success(tool_name, first)
    else:
        # Structured content or direct result
        structured = result.get("structuredContent") or result
        show_success(tool_name, structured)


def _show_server_info(
    client: Union[MCPStdioClient, MCPHttpClient],
    server_url: Optional[str],
) -> None:
    """Show server connection info."""
    info = {
        "Status": "Connected",
        "URL": server_url or "Local (stdio)",
        "Transport": "HTTP" if server_url else "stdio",
    }
    
    try:
        tools_resp = client.tools_list()
        info["Available Tools"] = len(tools_resp.get("tools", []))
    except Exception:
        info["Available Tools"] = "Error fetching"
    
    show_info("Server Information", info)


def _show_help() -> None:
    """Show help information."""
    help_text = """
[bold]Navigation:[/bold]
  ↑/↓ Arrow keys    Navigate menu
  Enter             Select option
  Type              Filter/search
  Ctrl+C            Cancel/back
  
[bold]Tool Execution:[/bold]
  Select a tool from the menu to execute it.
  You'll be prompted for any required arguments.
  
[bold]Tools marked with ⚠:[/bold]
  These require confirmation before execution
  (LAW 1: Human Sovereignty)
  
[bold]More Info:[/bold]
  Web Interface: http://<pi-ip>:3000
  Documentation: docs/USER_ACCEPTANCE_TEST_GUIDE.md
"""
    console.print(help_text)
