"""
Request Validator

Validates tool requests against system schema and tool registry.
Enforces LAW 3 — LLM IS NOT AN AGENT (validates AI outputs are data-only).

Per DIP Phase 2: Reject malformed or unauthorized requests.
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from mcp.tool_registry import ToolRegistry
from mcp.tool_schema import PermissionLevel

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Exception raised when request validation fails."""

    def __init__(
        self,
        error_code: str,
        error_message: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Initialize validation error.

        Args:
            error_code: Machine-readable error code
            error_message: Human-readable error message
            details: Optional additional error details
        """
        super().__init__(error_message)
        self.error_code = error_code
        self.error_message = error_message
        self.details = details or {}


class RequestValidator:
    """
    Validates tool requests.

    Enforces:
    - LAW 3: LLM outputs are data-only (validates intent parsing output)
    - LAW 4: Only registered tools callable
    - Request format matches system_schema.json

    Per DIP Phase 2 and LAW 3/4 enforcement.
    """

    def __init__(self, tool_registry: ToolRegistry) -> None:
        """
        Initialize request validator.

        Args:
            tool_registry: Tool registry to validate against
        """
        self._tool_registry = tool_registry

    def validate_tool_request(self, request: Dict[str, Any]) -> tuple[bool, Optional[ValidationError]]:
        """
        Validate a tool request against system schema.

        Args:
            request: Tool request dictionary (should match system_schema.json tool_request)

        Returns:
            Tuple of (is_valid, validation_error)
            If valid, validation_error is None.
        """
        # Check required fields per system_schema.json
        required_fields = [
            "type",
            "request_id",
            "timestamp",
            "tool_name",
            "arguments",
            "requires_confirmation",
        ]

        for field in required_fields:
            if field not in request:
                error = ValidationError(
                    error_code="MISSING_REQUIRED_FIELD",
                    error_message=f"Missing required field: {field}",
                    details={"field": field},
                )
                return False, error

        # Validate type discriminator
        if request["type"] != "tool_request":
            error = ValidationError(
                error_code="INVALID_TYPE",
                error_message=f"Invalid type: expected 'tool_request', got '{request['type']}'",
                details={"expected": "tool_request", "got": request["type"]},
            )
            return False, error

        # Validate request_id format (UUID v4)
        try:
            UUID(request["request_id"])
        except (ValueError, TypeError):
            error = ValidationError(
                error_code="INVALID_REQUEST_ID",
                error_message="request_id must be a valid UUID v4",
                details={"request_id": request["request_id"]},
            )
            return False, error

        # Validate timestamp format (ISO 8601)
        try:
            datetime.fromisoformat(request["timestamp"].replace("Z", "+00:00"))
        except (ValueError, TypeError, AttributeError):
            error = ValidationError(
                error_code="INVALID_TIMESTAMP",
                error_message="timestamp must be a valid ISO 8601 datetime",
                details={"timestamp": request.get("timestamp")},
            )
            return False, error

        # Validate tool_name exists in registry (LAW 4)
        tool_name = request["tool_name"]
        if not self._tool_registry.exists(tool_name):
            error = ValidationError(
                error_code="TOOL_NOT_FOUND",
                error_message=f"Tool '{tool_name}' is not registered",
                details={"tool_name": tool_name},
            )
            return False, error

        # Validate arguments against tool schema
        tool_schema = self._tool_registry.get(tool_name)
        if tool_schema:
            is_valid, error_msg = tool_schema.validate_input(request["arguments"])
            if not is_valid:
                error = ValidationError(
                    error_code="INVALID_ARGUMENTS",
                    error_message=error_msg or "Arguments do not match tool schema",
                    details={"tool_name": tool_name, "arguments": request["arguments"]},
                )
                return False, error

        # Validate requires_confirmation is boolean
        if not isinstance(request["requires_confirmation"], bool):
            error = ValidationError(
                error_code="INVALID_CONFIRMATION_FLAG",
                error_message="requires_confirmation must be a boolean",
                details={"requires_confirmation": request["requires_confirmation"]},
            )
            return False, error

        return True, None

    def validate_intent_parsing_output(self, output: Dict[str, Any]) -> tuple[bool, Optional[ValidationError]]:
        """
        Validate AI intent parsing output.

        Enforces LAW 3 — LLM IS NOT AN AGENT: AI outputs are data-only.

        Args:
            output: Intent parsing output dictionary (should match system_schema.json intent_parsing_output)

        Returns:
            Tuple of (is_valid, validation_error)
            If valid, validation_error is None.
        """
        # Check required fields per system_schema.json
        required_fields = ["type", "request_id", "timestamp", "intent", "confidence"]

        for field in required_fields:
            if field not in output:
                error = ValidationError(
                    error_code="MISSING_REQUIRED_FIELD",
                    error_message=f"Missing required field: {field}",
                    details={"field": field},
                )
                return False, error

        # Validate type discriminator
        if output["type"] != "intent_parsing_output":
            error = ValidationError(
                error_code="INVALID_TYPE",
                error_message=f"Invalid type: expected 'intent_parsing_output', got '{output['type']}'",
                details={"expected": "intent_parsing_output", "got": output["type"]},
            )
            return False, error

        # Validate intent structure
        intent = output.get("intent", {})
        if not isinstance(intent, dict):
            error = ValidationError(
                error_code="INVALID_INTENT",
                error_message="intent must be an object",
            )
            return False, error

        if "action" not in intent:
            error = ValidationError(
                error_code="MISSING_ACTION",
                error_message="intent.action is required",
            )
            return False, error

        # Validate confidence
        confidence = output.get("confidence")
        if not isinstance(confidence, (int, float)) or not (0.0 <= confidence <= 1.0):
            error = ValidationError(
                error_code="INVALID_CONFIDENCE",
                error_message="confidence must be a number between 0.0 and 1.0",
                details={"confidence": confidence},
            )
            return False, error

        return True, None
