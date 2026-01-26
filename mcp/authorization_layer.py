"""
Authorization Layer

MCP authorization layer that enforces permissions and confirmations.
Enforces LAW 4 — TOOL-ONLY EXECUTION and LAW 5 — EXPLICIT PERMISSIONS.

Per DIP Phase 2: MCP as pure gatekeeper.
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID, uuid4

from mcp.policy_engine import PermissionCheck, PermissionDecision, PolicyEngine
from mcp.request_validator import RequestValidator, ValidationError
from mcp.tool_registry import ToolRegistry
from mcp.tool_schema import ToolSchema

logger = logging.getLogger(__name__)


@dataclass
class AuthorizationResult:
    """
    Result of authorization check.

    Per LAW 13 — COMPLETE AUDITABILITY: All authorization decisions are logged.
    """

    authorized: bool
    """Whether the request is authorized."""

    requires_confirmation: bool
    """Whether user confirmation is required."""

    confirmation_request_id: Optional[UUID] = None
    """Confirmation request ID if confirmation is required."""

    error_code: Optional[str] = None
    """Error code if authorization failed."""

    error_message: Optional[str] = None
    """Error message if authorization failed."""

    permission_check: Optional[PermissionCheck] = None
    """Permission check result."""


class AuthorizationLayer:
    """
    Authorization layer for MCP.

    Enforces:
    - LAW 4: Only registered tools callable
    - LAW 5: Explicit permissions required
    - All decisions are explainable and logged

    Per DIP Phase 2: MCP as pure gatekeeper.
    """

    def __init__(
        self,
        tool_registry: ToolRegistry,
        request_validator: RequestValidator,
        policy_engine: PolicyEngine,
    ) -> None:
        """
        Initialize authorization layer.

        Args:
            tool_registry: Tool registry
            request_validator: Request validator
            policy_engine: Policy engine
        """
        self._tool_registry = tool_registry
        self._request_validator = request_validator
        self._policy_engine = policy_engine

    def authorize_tool_request(
        self,
        request: Dict[str, Any],
        user_context: Optional[Dict] = None,
    ) -> AuthorizationResult:
        """
        Authorize a tool request.

        This is the main gatekeeping function. All tool requests must pass through this.

        Args:
            request: Tool request dictionary
            user_context: Optional user context

        Returns:
            Authorization result

        Per LAW 13: All authorization decisions are logged.
        """
        request_id = request.get("request_id", "unknown")
        tool_name = request.get("tool_name", "unknown")

        logger.info(
            f"Authorization check for tool request {request_id}",
            extra={
                "request_id": request_id,
                "tool_name": tool_name,
            },
        )

        # Step 1: Validate request format
        is_valid, validation_error = self._request_validator.validate_tool_request(request)
        if not is_valid:
            assert validation_error is not None
            logger.warning(
                f"Tool request {request_id} validation failed: {validation_error.error_code}",
                extra={
                    "request_id": request_id,
                    "error_code": validation_error.error_code,
                    "error_message": validation_error.error_message,
                },
            )

            return AuthorizationResult(
                authorized=False,
                requires_confirmation=False,
                error_code=validation_error.error_code,
                error_message=validation_error.error_message,
            )

        # Step 2: Get tool schema
        tool_schema = self._tool_registry.get(tool_name)
        if tool_schema is None:
            logger.error(
                f"Tool '{tool_name}' not found in registry",
                extra={
                    "request_id": request_id,
                    "tool_name": tool_name,
                },
            )

            return AuthorizationResult(
                authorized=False,
                requires_confirmation=False,
                error_code="TOOL_NOT_FOUND",
                error_message=f"Tool '{tool_name}' is not registered",
            )

        # Step 3: Check permissions
        permission_check = self._policy_engine.check_permission(tool_schema, user_context)

        # Step 4: Determine authorization
        if permission_check.decision == PermissionDecision.DENIED:
            logger.warning(
                f"Tool request {request_id} denied: {permission_check.reason}",
                extra={
                    "request_id": request_id,
                    "tool_name": tool_name,
                    "reason": permission_check.reason,
                },
            )

            return AuthorizationResult(
                authorized=False,
                requires_confirmation=False,
                error_code="PERMISSION_DENIED",
                error_message=permission_check.reason or "Permission denied",
                permission_check=permission_check,
            )

        if permission_check.decision == PermissionDecision.REQUIRES_CONFIRMATION:
            # Generate confirmation request ID
            confirmation_request_id = uuid4()

            logger.info(
                f"Tool request {request_id} requires confirmation",
                extra={
                    "request_id": request_id,
                    "tool_name": tool_name,
                    "confirmation_request_id": str(confirmation_request_id),
                },
            )

            return AuthorizationResult(
                authorized=False,  # Not authorized yet, needs confirmation
                requires_confirmation=True,
                confirmation_request_id=confirmation_request_id,
                permission_check=permission_check,
            )

        # Permission granted
        logger.info(
            f"Tool request {request_id} authorized",
            extra={
                "request_id": request_id,
                "tool_name": tool_name,
                "permission_level": tool_schema.permission_level.value,
            },
        )

        return AuthorizationResult(
            authorized=True,
            requires_confirmation=False,
            permission_check=permission_check,
        )
