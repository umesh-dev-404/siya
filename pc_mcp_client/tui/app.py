"""
Siya Full-Screen TUI Application.

Per Phase 19: Full-screen terminal UI using Textual.
Provides responsive layout with sidebar, output panel, and input bar.
"""

from typing import Any, Dict, List, Optional

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.widgets import (
    Header,
    Footer,
    Static,
    Tree,
    Input,
    Label,
    Button,
    RichLog,
)
from textual.screen import ModalScreen
from textual import on
from rich.text import Text
from rich.panel import Panel

# Tool categories
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

TOOL_ICONS = {
    "get_system_status": "💻", "resource_monitor": "📊", "log_query": "📋",
    "directory_list": "📁", "file_read": "📄", "file_write": "✏️",
    "fetch_mails": "📧", "get_sync_status": "🔄", "trigger_sync": "⚡",
    "summarize_text": "📝", "list_automations": "⚙️", "trigger_automation": "🚀",
    "speak_text": "🔊", "listen_for_input": "🎤", "list_notifications": "🔔",
}


class ConfirmModal(ModalScreen):
    """LAW 1 confirmation modal."""
    
    BINDINGS = [
        Binding("y", "confirm", "Yes"),
        Binding("n", "cancel", "No"),
        Binding("escape", "cancel", "Cancel"),
    ]
    
    def __init__(self, tool_name: str, args: Dict[str, Any]):
        super().__init__()
        self.tool_name = tool_name
        self.args = args
    
    def compose(self) -> ComposeResult:
        args_text = "\n".join(f"  {k}: {v}" for k, v in self.args.items() if not k.startswith("_"))
        
        yield Container(
            Static("⚠ CONFIRMATION REQUIRED", id="confirm-title"),
            Static(f"Tool: {self.tool_name}", id="confirm-tool"),
            Static(f"Arguments:\n{args_text}" if args_text else "No arguments", id="confirm-args"),
            Static("This action requires your explicit confirmation.", id="confirm-law"),
            Static("LAW 1: Human Sovereignty", id="confirm-law-name"),
            Horizontal(
                Button("Yes, Execute", variant="success", id="btn-yes"),
                Button("Cancel", variant="error", id="btn-no"),
                id="confirm-buttons"
            ),
            id="confirm-dialog"
        )
    
    def action_confirm(self) -> None:
        self.dismiss(True)
    
    def action_cancel(self) -> None:
        self.dismiss(False)
    
    @on(Button.Pressed, "#btn-yes")
    def on_yes(self) -> None:
        self.dismiss(True)
    
    @on(Button.Pressed, "#btn-no")
    def on_no(self) -> None:
        self.dismiss(False)


class ToolSidebar(Static):
    """Sidebar with tool categories."""
    
    def __init__(self, tools: List[Dict[str, Any]], **kwargs):
        super().__init__(**kwargs)
        self.tools = tools
        self.tool_lookup = {t["name"]: t for t in tools}
    
    def compose(self) -> ComposeResult:
        tree: Tree[str] = Tree("📂 TOOLS", id="tool-tree")
        tree.root.expand()
        
        for category, tool_names in TOOL_CATEGORIES.items():
            # Add category as expandable node (no extra arrow - Textual provides one)
            category_node = tree.root.add(category, expand=False)
            for tool_name in tool_names:
                if tool_name in self.tool_lookup:
                    tool = self.tool_lookup[tool_name]
                    icon = TOOL_ICONS.get(tool_name, "🔧")
                    # Check if requires confirmation
                    schema = tool.get("inputSchema", {})
                    needs_confirm = schema.get("properties", {}).get("_confirmed") is not None
                    suffix = " (!)" if needs_confirm else ""
                    # Store tool_name in data for reliable retrieval
                    category_node.add_leaf(f"{icon} {tool_name}{suffix}", data=tool_name)
        
        yield tree


class OutputPanel(RichLog):
    """Scrollable output panel for results."""
    
    def __init__(self, **kwargs):
        super().__init__(highlight=True, markup=True, wrap=True, **kwargs)


class InputBar(Static):
    """Input bar for commands."""
    
    def compose(self) -> ComposeResult:
        yield Input(placeholder="Select a tool from sidebar or type command...", id="command-input")


class SiyaApp(App):
    """Main Siya TUI Application."""
    
    CSS_PATH = "styles.tcss"
    
    TITLE = "SIYA"
    SUB_TITLE = "Personal Assistant Platform"
    
    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit", show=True),
        Binding("ctrl+h", "help", "Help", show=True),
        Binding("ctrl+r", "refresh", "Refresh"),
        Binding("escape", "close_or_unfocus", "Close/Back"),
        Binding("ctrl+l", "clear", "Clear"),
    ]
    
    def __init__(self, client=None, server_url: str = ""):
        super().__init__()
        self.client = client
        self.server_url = server_url
        self.tools: List[Dict[str, Any]] = []
        self.selected_tool: Optional[str] = None
    
    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        
        with Horizontal(id="main-content"):
            with Vertical(id="sidebar"):
                yield Static(f"[bold cyan]Connected:[/] {self.server_url}", id="status")
                if self.tools:
                    yield ToolSidebar(self.tools, id="tool-sidebar")
                else:
                    yield Static("[dim]Loading tools...[/dim]", id="loading")
            
            with Vertical(id="output-area"):
                yield Static("[bold]OUTPUT[/bold]", id="output-header")
                yield OutputPanel(id="output")
        
        yield InputBar(id="input-bar")
        yield Footer()
    
    async def on_mount(self) -> None:
        """Called when app is mounted."""
        # Focus on the tool tree when app starts
        self.call_after_refresh(self._focus_tree)
        
        if self.client:
            try:
                result = self.client.tools_list()
                self.tools = result.get("tools", [])
                # Rebuild sidebar with tools
                sidebar = self.query_one("#sidebar", Vertical)
                loading = sidebar.query_one("#loading", Static)
                await loading.remove()
                await sidebar.mount(ToolSidebar(self.tools, id="tool-sidebar"))
                
                self.log_output("[green]Connected successfully![/green]")
                self.log_output(f"[dim]Available tools: {len(self.tools)}[/dim]")
            except Exception as e:
                self.log_output(f"[red]Error loading tools: {e}[/red]")
    
    def log_output(self, message: str) -> None:
        """Add message to output panel."""
        try:
            output = self.query_one("#output", OutputPanel)
            output.write(message)
        except Exception:
            pass
    
    @on(Tree.NodeSelected)
    async def on_tree_select(self, event: Tree.NodeSelected) -> None:
        """Handle tool selection from tree."""
        node = event.node
        
        # If node allows expand (is a branch/category), toggle it
        if node.allow_expand:
            node.toggle()
            return
        
        # Leaf node (tool) - get tool name from data attribute
        tool_name = node.data
        if tool_name:
            await self.execute_tool(tool_name)
    
    async def execute_tool(self, tool_name: str, args: Optional[Dict[str, Any]] = None) -> None:
        """Execute a tool."""
        if not self.client:
            self.log_output("[red]Not connected to server[/red]")
            return
        
        tool = None
        for t in self.tools:
            if t["name"] == tool_name:
                tool = t
                break
        
        if not tool:
            self.log_output(f"[red]Tool not found: {tool_name}[/red]")
            return
        
        # Build arguments
        if args is None:
            args = {}
        
        # Check if requires confirmation
        schema = tool.get("inputSchema", {})
        needs_confirm = schema.get("properties", {}).get("_confirmed") is not None
        
        if needs_confirm and not args.get("_confirmed"):
            # Show confirmation modal
            confirmed = await self.push_screen_wait(ConfirmModal(tool_name, args))
            if not confirmed:
                self.log_output(f"[yellow]Cancelled: {tool_name}[/yellow]")
                return
            args["_confirmed"] = True
        
        # Execute
        self.log_output(f"\n[bold cyan]Executing: {tool_name}[/bold cyan]")
        
        try:
            result = self.client.tools_call(tool_name, args)
            self._display_result(tool_name, result)
        except Exception as e:
            self.log_output(f"[red]Error: {e}[/red]")
    
    def _display_result(self, tool_name: str, result: Any) -> None:
        """Display tool result."""
        self.log_output(f"[green]--- {tool_name} ---[/green]")
        
        if isinstance(result, dict):
            for key, value in result.items():
                if isinstance(value, dict):
                    self.log_output(f"[cyan]{key}:[/cyan]")
                    for k, v in value.items():
                        self.log_output(f"  {k}: {v}")
                elif isinstance(value, list):
                    self.log_output(f"[cyan]{key}:[/cyan] {len(value)} items")
                else:
                    self.log_output(f"[cyan]{key}:[/cyan] {value}")
        else:
            self.log_output(str(result))
        
        self.log_output("[green]--- end ---[/green]\n")
    
    def action_help(self) -> None:
        """Show help."""
        self.log_output("\n[bold yellow]KEYBOARD SHORTCUTS[/bold yellow]")
        self.log_output("  [cyan]Ctrl+Q[/cyan]  - Quit")
        self.log_output("  [cyan]Ctrl+H[/cyan]  - Help")
        self.log_output("  [cyan]Ctrl+R[/cyan]  - Refresh")
        self.log_output("  [cyan]Ctrl+L[/cyan]  - Clear output")
        self.log_output("  [cyan]↑↓[/cyan]      - Navigate tree")
        self.log_output("  [cyan]Space[/cyan]   - Expand/Collapse category")
        self.log_output("  [cyan]Enter[/cyan]   - Execute tool")
        self.log_output("  [cyan]Escape[/cyan]  - Back/Close\n")
    
    def action_clear(self) -> None:
        """Clear output."""
        try:
            output = self.query_one("#output", OutputPanel)
            output.clear()
        except Exception:
            pass
    
    def _focus_tree(self) -> None:
        """Focus on the tool tree."""
        try:
            tree = self.query_one("#tool-tree", Tree)
            self.set_focus(tree)
        except Exception:
            pass
    
    def action_close_or_unfocus(self) -> None:
        """Close modal or unfocus current widget."""
        self.set_focus(None)
    
    async def action_refresh(self) -> None:
        """Refresh tools list."""
        if self.client:
            result = self.client.tools_list()
            self.tools = result.get("tools", [])
            self.log_output(f"[green]Refreshed: {len(self.tools)} tools[/green]")


def run_tui(client, server_url: str) -> int:
    """Run the TUI application."""
    app = SiyaApp(client=client, server_url=server_url)
    app.run()
    return 0
