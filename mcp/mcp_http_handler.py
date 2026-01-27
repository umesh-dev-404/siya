"""
MCP HTTP Handler

HTTP transport for MCP (Model Context Protocol).
Handles JSON-RPC 2.0 messages over HTTP POST to /mcp endpoint.

Per DIP Phase 11: HTTP transport to Pi MCP server.
Per LAW 16: Network access is explicit (Origin validation).
"""

import json
import logging
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from uuid import uuid4

from mcp.mcp_server import MCPServer
from mcp.tool_schema import ToolSchema
from tools.tool_executor import ToolExecutor

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class MCPHttpContext:
    """Context for MCP HTTP handler."""

    mcp_server: MCPServer
    tool_executor: ToolExecutor


def get_allowed_origins() -> List[str]:
    """
    Get allowed origins for MCP HTTP endpoint.

    Returns:
        List of allowed origins.

    Environment variable: SIYA_MCP_ALLOWED_ORIGINS
    Default: * (allow all - suitable for LAN)
    """
    origins_str = os.getenv("SIYA_MCP_ALLOWED_ORIGINS", "*")
    if origins_str == "*":
        return ["*"]
    return [o.strip() for o in origins_str.split(",") if o.strip()]


def get_api_key() -> Optional[str]:
    """
    Get optional API key for MCP HTTP endpoint.

    Returns:
        API key or None if not set.

    Environment variable: SIYA_MCP_API_KEY
    """
    key = os.getenv("SIYA_MCP_API_KEY", "").strip()
    return key if key else None


class MCPHttpHandler:
    """
    HTTP handler for MCP-over-HTTP protocol.

    Handles JSON-RPC 2.0 requests at /mcp endpoint.
    Same protocol as STDIO transport, different transport.
    """

    def __init__(self, ctx: MCPHttpContext) -> None:
        self._ctx = ctx
        # Track initialized sessions by a simple session marker
        # For HTTP, we treat each request as potentially new session
        # but accept initialize + subsequent calls
        self._initialized_sessions: set[str] = set()
        self._protocol_version = "2025-06-18"

    def validate_origin(self, origin: Optional[str]) -> bool:
        """
        Validate Origin header against allowed origins.

        Args:
            origin: Origin header value

        Returns:
            True if allowed, False otherwise

        Per LAW 16: Network access is explicit.
        """
        allowed = get_allowed_origins()
        if "*" in allowed:
            return True
        if origin is None:
            # No origin header - allow for non-browser clients (curl, etc.)
            return True
        return origin in allowed

    def validate_api_key(self, provided_key: Optional[str]) -> bool:
        """
        Validate API key if configured.

        Args:
            provided_key: API key from X-Siya-Api-Key header

        Returns:
            True if valid or not required, False if invalid
        """
        expected = get_api_key()
        if expected is None:
            # No API key configured, allow all
            return True
        return provided_key == expected

    def handle_request(
        self,
        body: bytes,
        origin: Optional[str] = None,
        api_key: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Handle MCP HTTP request.

        Args:
            body: Request body (JSON-RPC message)
            origin: Origin header value (for validation)
            api_key: X-Siya-Api-Key header value
            session_id: Optional session identifier

        Returns:
            JSON-RPC response dictionary

        Raises:
            ValueError: If origin or API key validation fails
        """
        # Validate origin (LAW 16)
        if not self.validate_origin(origin):
            logger.warning(f"MCP HTTP request rejected: invalid origin '{origin}'")
            raise ValueError("Origin not allowed")

        # Validate API key
        if not self.validate_api_key(api_key):
            logger.warning("MCP HTTP request rejected: invalid API key")
            raise ValueError("Invalid API key")

        # Parse JSON-RPC message
        try:
            msg = json.loads(body.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            logger.warning(f"MCP HTTP invalid JSON: {e}")
            return self._error(None, -32700, "Parse error")

        return self._handle_message(msg, session_id or "default")

    def _handle_message(
        self, msg: Dict[str, Any], session_id: str
    ) -> Dict[str, Any]:
        """Handle a single JSON-RPC message."""
        jsonrpc = msg.get("jsonrpc")
        msg_id = msg.get("id")
        method = msg.get("method")
        params = msg.get("params", {}) or {}

        # Notifications have no id - for HTTP we still need to respond
        if msg_id is None:
            # Treat as notification, return empty success
            return {"jsonrpc": "2.0", "id": None, "result": {}}

        if jsonrpc != "2.0":
            return self._error(msg_id, -32600, "Invalid JSON-RPC version")

        try:
            if method == "initialize":
                return self._handle_initialize(msg_id, params, session_id)
            if method == "tools/list":
                return self._handle_tools_list(msg_id, params, session_id)
            if method == "tools/call":
                return self._handle_tools_call(msg_id, params, session_id)

            return self._error(msg_id, -32601, f"Method not found: {method}")
        except Exception as e:
            logger.error("MCP HTTP handler error", exc_info=True)
            return self._error(msg_id, -32603, f"Server error: {e}")

    def _handle_initialize(
        self, msg_id: Any, params: Dict[str, Any], session_id: str
    ) -> Dict[str, Any]:
        """Handle initialize request."""
        self._initialized_sessions.add(session_id)
        client_protocol = params.get("protocolVersion")
        if isinstance(client_protocol, str) and client_protocol:
            self._protocol_version = client_protocol

        logger.info(f"MCP HTTP session initialized: {session_id}")

        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {
                "protocolVersion": self._protocol_version,
                "capabilities": {
                    "tools": {"listChanged": False},
                },
                "serverInfo": {"name": "siya", "version": "1.0.0"},
            },
        }

    def _handle_tools_list(
        self, msg_id: Any, params: Dict[str, Any], session_id: str
    ) -> Dict[str, Any]:
        """Handle tools/list request."""
        # For HTTP, we're more lenient about initialization
        # since sessions may be stateless
        tools: list[Dict[str, Any]] = []
        registry = self._ctx.mcp_server.get_tool_registry()
        for name in registry.list_tools():
            schema = registry.get(name)
            if schema is None:
                continue
            tools.append(self._tool_schema_to_mcp(schema))

        return {"jsonrpc": "2.0", "id": msg_id, "result": {"tools": tools}}

    def _handle_tools_call(
        self, msg_id: Any, params: Dict[str, Any], session_id: str
    ) -> Dict[str, Any]:
        """Handle tools/call request."""
        name = params.get("name")
        arguments = params.get("arguments", {})
        if not isinstance(name, str) or not name:
            return self._error(msg_id, -32602, "Invalid params: name is required")
        if not isinstance(arguments, dict):
            return self._error(
                msg_id, -32602, "Invalid params: arguments must be an object"
            )

        tool_request = {
            "type": "tool_request",
            "request_id": str(uuid4()),
            "timestamp": "1970-01-01T00:00:00Z",
            "tool_name": name,
            "arguments": arguments,
            "requires_confirmation": False,
            "permission_level": "NONE",
            "source": "mcp_http",
        }

        auth = self._ctx.mcp_server.validate_and_authorize(tool_request)
        
        # Check for confirmation (LAW 1)
        # Check for confirmation (LAW 1)
        if auth.requires_confirmation:
            is_confirmed = params.get("_confirmed", False)
            if not is_confirmed:
                # Return confirmation request to client
                return {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {
                        "confirmationNeeded": True,
                        "tool": name,
                        "arguments": arguments,
                        "message": f"Tool '{name}' requires explicit confirmation.",
                    },
                }
            # If confirmed, we proceed.
            # Note: auth.authorized is False here because the policy engine returned REQUIRES_CONFIRMATION
            # But since we have the confirmation bit, we override this specific check to allow execution.
            pass
            
        elif not auth.authorized:
            # Only block if it wasn't a confirmation requirement that we just satisfied
            return self._error(
                msg_id, -32602, auth.error_message or "Tool request denied"
            )

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
        """Convert internal tool schema to MCP format."""
        return {
            "name": schema.name,
            "title": schema.name,
            "description": schema.description,
            "inputSchema": schema.input_schema,
            "outputSchema": schema.output_schema,
        }

    def _error(self, msg_id: Any, code: int, message: str) -> Dict[str, Any]:
        """Create JSON-RPC error response."""
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "error": {"code": code, "message": message},
        }
