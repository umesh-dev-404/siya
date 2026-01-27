"""
STDIO transport for MCP (Model Context Protocol).

Implements minimal JSON-RPC 2.0 handling for:
- initialize (basic lifecycle)
- tools/list
- tools/call

This server is designed to be launched by an MCP client (e.g., on PC) that speaks
MCP over STDIO.
"""

import json
import logging
import sys
from dataclasses import dataclass
from typing import Any, Dict, Optional
from uuid import uuid4

from mcp.mcp_server import MCPServer
from mcp.tool_schema import ToolSchema
from tools.tool_executor import ToolExecutor

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class MCPStdioContext:
    mcp_server: MCPServer
    tool_executor: ToolExecutor


class MCPStdioServer:
    def __init__(self, ctx: MCPStdioContext) -> None:
        self._ctx = ctx
        self._initialized = False
        # Default to current protocol date from docs (can be expanded to negotiation later)
        self._protocol_version = "2025-06-18"

    def run_forever(self) -> None:
        """
        Read newline-delimited JSON-RPC messages from stdin, write responses to stdout.
        """
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            try:
                msg = json.loads(line)
            except json.JSONDecodeError:
                # No id -> cannot respond reliably; ignore
                logger.warning("Invalid JSON received on STDIO")
                continue

            response = self._handle_message(msg)
            if response is not None:
                sys.stdout.write(json.dumps(response) + "\n")
                sys.stdout.flush()

    def _handle_message(self, msg: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        jsonrpc = msg.get("jsonrpc")
        msg_id = msg.get("id")
        method = msg.get("method")
        params = msg.get("params", {}) or {}

        # Notifications have no id
        if msg_id is None:
            return None

        if jsonrpc != "2.0":
            return self._error(msg_id, -32600, "Invalid JSON-RPC version")

        try:
            if method == "initialize":
                return self._handle_initialize(msg_id, params)
            if method == "tools/list":
                return self._handle_tools_list(msg_id, params)
            if method == "tools/call":
                return self._handle_tools_call(msg_id, params)

            return self._error(msg_id, -32601, f"Method not found: {method}")
        except Exception as e:
            logger.error("STDIO server error", exc_info=True)
            return self._error(msg_id, -32603, f"Server error: {e}")

    def _handle_initialize(self, msg_id: Any, params: Dict[str, Any]) -> Dict[str, Any]:
        # Minimal init; negotiate later if needed
        self._initialized = True
        client_protocol = params.get("protocolVersion")
        if isinstance(client_protocol, str) and client_protocol:
            # For now accept client's requested version as long as it's a date-like string
            self._protocol_version = client_protocol

        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {
                "protocolVersion": self._protocol_version,
                "capabilities": {
                    "tools": {"listChanged": False},
                    # resources/prompts later
                },
                "serverInfo": {"name": "siya", "version": "1.0.0"},
            },
        }

    def _handle_tools_list(self, msg_id: Any, params: Dict[str, Any]) -> Dict[str, Any]:
        if not self._initialized:
            return self._error(msg_id, -32002, "Server not initialized")

        # Pagination is optional; we don't paginate yet
        _cursor = params.get("cursor")

        tools: list[Dict[str, Any]] = []
        registry = self._ctx.mcp_server.get_tool_registry()
        for name in registry.list_tools():
            schema = registry.get(name)
            if schema is None:
                continue
            tools.append(self._tool_schema_to_mcp(schema))

        return {"jsonrpc": "2.0", "id": msg_id, "result": {"tools": tools}}

    def _handle_tools_call(self, msg_id: Any, params: Dict[str, Any]) -> Dict[str, Any]:
        if not self._initialized:
            return self._error(msg_id, -32002, "Server not initialized")

        name = params.get("name")
        arguments = params.get("arguments", {})
        if not isinstance(name, str) or not name:
            return self._error(msg_id, -32602, "Invalid params: name is required")
        if not isinstance(arguments, dict):
            return self._error(msg_id, -32602, "Invalid params: arguments must be an object")

        tool_request = {
            "type": "tool_request",
            "request_id": str(uuid4()),
            "timestamp": "1970-01-01T00:00:00Z",
            "tool_name": name,
            "arguments": arguments,
            "requires_confirmation": False,
            "permission_level": "NONE",
            "source": "mcp_stdio",
        }

        auth = self._ctx.mcp_server.validate_and_authorize(tool_request)
        if auth.requires_confirmation:
            # In stdio transport we return tool-level error (not protocol error),
            # so the client can decide how to prompt.
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "content": [{"type": "text", "text": "Confirmation required (not implemented yet)."}],
                    "isError": True,
                },
            }
        if not auth.authorized:
            return self._error(msg_id, -32602, auth.error_message or "Tool request denied")

        # Execute via executor (side effects are inside tool impls)
        result = self._ctx.tool_executor.execute(name, arguments)
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {
                "content": [{"type": "text", "text": json.dumps(result.output)}],
                "structuredContent": result.output,
                "isError": False,
            },
        }

    def _tool_schema_to_mcp(self, schema: ToolSchema) -> Dict[str, Any]:
        return {
            "name": schema.name,
            "title": schema.name,
            "description": schema.description,
            "inputSchema": schema.input_schema,
            # outputSchema is optional in MCP; we provide it
            "outputSchema": schema.output_schema,
        }

    def _error(self, msg_id: Any, code: int, message: str) -> Dict[str, Any]:
        return {"jsonrpc": "2.0", "id": msg_id, "error": {"code": code, "message": message}}

