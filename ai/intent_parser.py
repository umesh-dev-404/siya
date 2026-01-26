"""
Intent Parser

AI intent parsing interface with strict JSON schema enforcement.
Enforces LAW 3 — LLM IS NOT AN AGENT.

Per DIP Phase 5: AI Integration (Controlled).
AI is strictly an intent parser, not an agent.
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import uuid4

from mcp.request_validator import RequestValidator, ValidationError

logger = logging.getLogger(__name__)


class IntentParser:
    """
    Intent parser interface.

    Enforces LAW 3 — LLM IS NOT AN AGENT:
    - AI output is untrusted
    - AI cannot execute tools
    - AI cannot write memory
    - AI only produces intent_parsing_output

    Per DIP Phase 5 and LAW 3 enforcement.
    """

    def __init__(self, request_validator: RequestValidator) -> None:
        """
        Initialize intent parser.

        Args:
            request_validator: Request validator for schema enforcement
        """
        self._request_validator = request_validator

    def parse_intent(
        self, user_input: str, available_tools: list[str]
    ) -> Dict[str, Any]:
        """
        Parse user intent from input.

        Args:
            user_input: Raw user input text
            available_tools: List of available tool names

        Returns:
            Intent parsing output (must match system_schema.json intent_parsing_output)

        Raises:
            ValidationError: If AI output does not match schema
            RuntimeError: If parsing fails

        Note:
            Phase 5: This is a stub. In later phases, this will call llama.cpp.
            All outputs are validated against system_schema.json.
        """
        # Phase 5: Stub implementation
        # In later phases, this will:
        # 1. Load model (if not loaded)
        # 2. Generate prompt with available tools
        # 3. Call llama.cpp
        # 4. Parse JSON response
        # 5. Validate against schema

        # For now, return a stub response that matches schema
        request_id = str(uuid4())
        timestamp = datetime.utcnow().isoformat() + "Z"

        # Stub: Simple intent parsing (will be replaced with actual AI)
        intent = self._stub_parse(user_input, available_tools)

        output = {
            "type": "intent_parsing_output",
            "request_id": request_id,
            "timestamp": timestamp,
            "intent": intent,
            "confidence": 0.8,  # Stub confidence
            "raw_input": user_input,
            "explanation": f"Parsed intent: {intent.get('action', 'unknown')}",
        }

        # Validate against schema (LAW 3 enforcement)
        is_valid, validation_error = self._request_validator.validate_intent_parsing_output(
            output
        )

        if not is_valid:
            logger.error(
                f"Intent parsing output validation failed: {validation_error}",
                extra={
                    "request_id": request_id,
                    "error_code": validation_error.error_code if validation_error else None,
                    "error_message": validation_error.error_message if validation_error else None,
                },
            )
            raise ValidationError(
                error_code="INTENT_PARSING_VALIDATION_FAILED",
                error_message=f"AI output does not match schema: {validation_error.error_message if validation_error else 'Unknown error'}",
                details={"output": output, "validation_error": str(validation_error)},
            )

        logger.info(
            f"Intent parsed: {intent.get('action', 'unknown')}",
            extra={
                "request_id": request_id,
                "action": intent.get("action"),
                "confidence": output["confidence"],
            },
        )

        return output

    def _stub_parse(self, user_input: str, available_tools: list[str]) -> Dict[str, Any]:
        """
        Stub intent parsing logic.

        Args:
            user_input: User input text
            available_tools: Available tool names

        Returns:
            Intent object (action, arguments, etc.)

        Note:
            Phase 5: This is a placeholder. Will be replaced with actual AI model.
        """
        # Very simple stub: try to match tool name in input
        user_lower = user_input.lower()

        # Find matching tool
        matched_tool = None
        for tool in available_tools:
            if tool.lower() in user_lower:
                matched_tool = tool
                break

        if not matched_tool and available_tools:
            # Default to first tool if no match
            matched_tool = available_tools[0]

        return {
            "action": matched_tool or "unknown",
            "arguments": {},
            "clarification_needed": matched_tool is None,
            "clarification_question": "Which tool would you like to use?" if matched_tool is None else None,
        }
