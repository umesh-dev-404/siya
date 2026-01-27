"""
MCP STDIO Server entry point.

Run this on the Pi to expose Siya tools to an MCP client via STDIO.
"""

import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.model_config import get_model_path
from config.logging_config import setup_logging
from mcp.mcp_server import MCPServer
from mcp.stdio_server import MCPStdioContext, MCPStdioServer
from mcp.tool_schema import PermissionLevel, ToolSchema
from tools.builtins import get_system_status
from tools.mail_tools import make_fetch_mails_tool, make_summarize_mails_tool
from tools.text_tools import make_summarize_text_tool
from tools.tool_executor import ToolExecutor
from ai.ai_interface import AIInterface


def main() -> int:
    setup_logging(level=logging.INFO)

    mcp_server = MCPServer()
    tool_executor = ToolExecutor()

    tool_registry = mcp_server.get_tool_registry()
    request_validator = mcp_server.get_request_validator()

    # Register starter tool schemas (keep parity with service_main)
    tool_registry.register(
        ToolSchema(
            name="get_system_status",
            description="[system] Get current system resource status (CPU/RAM/disk).",
            input_schema={"type": "object", "properties": {}, "required": []},
            output_schema={"type": "object"},
            permission_level=PermissionLevel.READ,
            requires_confirmation=False,
        )
    )
    tool_executor.register("get_system_status", get_system_status)

    tool_registry.register(
        ToolSchema(
            name="tools_list",
            description="[system] List all available tools.",
            input_schema={"type": "object", "properties": {}, "required": []},
            output_schema={"type": "object"},
            permission_level=PermissionLevel.READ,
            requires_confirmation=False,
        )
    )
    tool_executor.register("tools_list", lambda _args: {"status": "ok", "tools": tool_registry.list_tools()})

    # AI-backed tools
    model_path = get_model_path()
    ai = AIInterface(tool_registry, request_validator, model_path=model_path)
    if model_path:
        ai.load_model()

    tool_registry.register(
        ToolSchema(
            name="summarize_text",
            description="[content] Summarize a block of text (local AI).",
            input_schema={
                "type": "object",
                "properties": {"text": {"type": "string"}, "style": {"type": "string"}, "max_bullets": {"type": "integer"}},
                "required": ["text"],
            },
            output_schema={"type": "object"},
            permission_level=PermissionLevel.READ,
            requires_confirmation=False,
        )
    )
    tool_executor.register("summarize_text", make_summarize_text_tool(ai))

    # Offline-first mail tools
    mail_store_default = str(project_root / "data" / "mails.json")
    tool_registry.register(
        ToolSchema(
            name="fetch_mails",
            description="[integration:mails] Fetch mails from local mail store (offline-first).",
            input_schema={"type": "object", "properties": {"store_path": {"type": "string"}, "limit": {"type": "integer"}}, "required": []},
            output_schema={"type": "object"},
            permission_level=PermissionLevel.READ,
            requires_confirmation=False,
        )
    )
    tool_executor.register("fetch_mails", make_fetch_mails_tool(mail_store_default))

    tool_registry.register(
        ToolSchema(
            name="summarize_mails",
            description="[integration:mails] Summarize mails from local store (uses local AI).",
            input_schema={
                "type": "object",
                "properties": {
                    "store_path": {"type": "string"},
                    "limit": {"type": "integer"},
                    "max_items": {"type": "integer"},
                    "fields": {"type": "array", "items": {"type": "string"}},
                },
                "required": [],
            },
            output_schema={"type": "object"},
            permission_level=PermissionLevel.READ,
            requires_confirmation=False,
        )
    )
    tool_executor.register("summarize_mails", make_summarize_mails_tool(ai, mail_store_default))

    server = MCPStdioServer(MCPStdioContext(mcp_server=mcp_server, tool_executor=tool_executor))
    server.run_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

