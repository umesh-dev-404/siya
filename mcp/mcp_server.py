"""
MCP Server (Model Context Protocol) — internal server abstraction (Phase 11).

This is the core governance + exposure layer that will later be wrapped by:
- STDIO transport (local MCP protocol)
- HTTP transport (remote MCP protocol)

In MODE C (now), we implement the server core first and rewire CLI/API/Web to use it,
so interface behavior is consistent (LAW 19).

Important separation:
- MCP Server: validates/authorizes (no side effects)
- Orchestrator: executes tools (side effects)
"""

import logging
from typing import Any, Dict, Optional

from mcp.authorization_layer import AuthorizationLayer, AuthorizationResult
from mcp.policy_engine import PolicyEngine
from mcp.request_validator import RequestValidator
from mcp.tool_registry import ToolRegistry

logger = logging.getLogger(__name__)


class MCPServer:
    """
    MCP Server core (governance + tool/resource exposure surface).

    Today:
    - supports tool registry + validation + authorization
    - transport not implemented (internal calls only)

    Later:
    - add MCP protocol transport adapters (STDIO first).
    """

    def __init__(self) -> None:
        self._tool_registry = ToolRegistry()
        self._request_validator = RequestValidator(self._tool_registry)
        self._policy_engine = PolicyEngine()
        self._authorization_layer = AuthorizationLayer(
            self._tool_registry,
            self._request_validator,
            self._policy_engine,
        )

    def validate_and_authorize(
        self,
        tool_request: Dict[str, Any],
        user_context: Optional[Dict] = None,
    ) -> AuthorizationResult:
        """
        Validate + authorize a tool request.

        This is governance only: no execution here.
        """
        request_id = tool_request.get("request_id", "unknown")
        tool_name = tool_request.get("tool_name", "unknown")

        logger.info(
            "MCP server validating tool request",
            extra={"request_id": request_id, "tool_name": tool_name},
        )
        return self._authorization_layer.authorize_tool_request(tool_request, user_context)

    def get_tool_registry(self) -> ToolRegistry:
        return self._tool_registry

    def get_request_validator(self) -> RequestValidator:
        return self._request_validator

    def get_policy_engine(self) -> PolicyEngine:
        return self._policy_engine

    def list_tools(self) -> list[str]:
        return self._tool_registry.list_tools()

