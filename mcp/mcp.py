"""
Model Control Plane (MCP)

Pure gatekeeper that validates and authorizes all tool requests.
Enforces all Canonical System Laws related to execution control.

Per DIP Phase 2: MCP as pure gatekeeper.
"""

import logging
from typing import Any, Dict, Optional

from mcp.authorization_layer import AuthorizationLayer, AuthorizationResult
from mcp.policy_engine import PolicyEngine
from mcp.request_validator import RequestValidator
from mcp.tool_registry import ToolRegistry

logger = logging.getLogger(__name__)


class ModelControlPlane:
    """
    Model Control Plane (MCP).

    Pure gatekeeper that:
    - Validates tool requests
    - Enforces permissions
    - Enforces confirmation policies
    - Rejects malformed or unauthorized requests
    - Logs every decision

    Enforces:
    - LAW 3 — LLM IS NOT AN AGENT
    - LAW 4 — TOOL-ONLY EXECUTION
    - LAW 5 — EXPLICIT PERMISSIONS
    - LAW 13 — COMPLETE AUDITABILITY

    Per DIP Phase 2 and TRD Section 8.
    """

    def __init__(self) -> None:
        """Initialize the Model Control Plane."""
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
        Validate and authorize a tool request.

        This is the main entry point for all tool requests.
        No execution bypasses MCP (per DIP Phase 2 exit criteria).

        Args:
            tool_request: Tool request dictionary (must match system_schema.json)
            user_context: Optional user context

        Returns:
            Authorization result

        Per LAW 13: All decisions are logged.
        """
        request_id = tool_request.get("request_id", "unknown")

        logger.info(
            f"MCP processing tool request {request_id}",
            extra={
                "request_id": request_id,
                "tool_name": tool_request.get("tool_name"),
            },
        )

        # Authorize through authorization layer
        result = self._authorization_layer.authorize_tool_request(tool_request, user_context)

        # Log decision
        if result.authorized:
            logger.info(
                f"Tool request {request_id} authorized by MCP",
                extra={
                    "request_id": request_id,
                    "tool_name": tool_request.get("tool_name"),
                },
            )
        elif result.requires_confirmation:
            logger.info(
                f"Tool request {request_id} requires confirmation",
                extra={
                    "request_id": request_id,
                    "confirmation_request_id": str(result.confirmation_request_id),
                },
            )
        else:
            logger.warning(
                f"Tool request {request_id} denied by MCP: {result.error_code}",
                extra={
                    "request_id": request_id,
                    "error_code": result.error_code,
                    "error_message": result.error_message,
                },
            )

        return result

    def get_tool_registry(self) -> ToolRegistry:
        """
        Get the tool registry.

        Returns:
            Tool registry
        """
        return self._tool_registry

    def get_request_validator(self) -> RequestValidator:
        """
        Get the request validator.

        Returns:
            Request validator
        """
        return self._request_validator

    def get_policy_engine(self) -> PolicyEngine:
        """
        Get the policy engine.

        Returns:
            Policy engine
        """
        return self._policy_engine
