"""
AI Interface

Main AI interface coordinating intent parsing and model management.
Enforces LAW 3 — LLM IS NOT AN AGENT.

Per DIP Phase 5: AI Integration (Controlled).
"""

import json
import logging
from typing import Any, Dict, List, Optional

from ai.intent_parser import IntentParser
from ai.model_manager import ModelManager
from mcp.request_validator import RequestValidator
from mcp.tool_registry import ToolRegistry

logger = logging.getLogger(__name__)


class AIInterface:
    """
    AI interface for intent parsing.

    Enforces LAW 3 — LLM IS NOT AN AGENT:
    - AI output is untrusted
    - AI cannot execute tools
    - AI cannot write memory
    - AI only produces intent_parsing_output

    Per DIP Phase 5 and LAW 3 enforcement.
    """

    def __init__(
        self,
        tool_registry: ToolRegistry,
        request_validator: RequestValidator,
        model_path: Optional[str] = None,
    ) -> None:
        """
        Initialize AI interface.

        Args:
            tool_registry: Tool registry for available tools
            request_validator: Request validator for schema enforcement
            model_path: Optional path to AI model (ignored in Phase 5 stub)
        """
        self._tool_registry = tool_registry
        self._request_validator = request_validator
        self._model_manager = ModelManager(model_path)
        self._intent_parser = IntentParser(request_validator)

    def parse_user_intent(self, user_input: str) -> Dict[str, Any]:
        """
        Parse user intent from input.

        Args:
            user_input: Raw user input text

        Returns:
            Intent parsing output (validated against system_schema.json)

        Raises:
            ValidationError: If AI output does not match schema
            RuntimeError: If parsing fails

        Note:
            LAW 3: AI is parser, not executor.
            All outputs are validated and untrusted until validated.
        """
        # Get available tools
        # list_tools() returns list of tool names (strings)
        available_tools = self._tool_registry.list_tools()

        # Parse intent (validates against schema)
        output = self._intent_parser.parse_intent(user_input, available_tools)

        logger.info(
            f"User intent parsed",
            extra={
                "request_id": output.get("request_id"),
                "action": output.get("intent", {}).get("action"),
                "confidence": output.get("confidence"),
            },
        )

        return output

    def is_model_loaded(self) -> bool:
        """
        Check if AI model is loaded.

        Returns:
            True if model is loaded
        """
        return self._model_manager.is_loaded()

    def load_model(self) -> bool:
        """
        Load AI model.

        Returns:
            True if model loaded successfully

        Note:
            Phase 5: Stub only. No actual model loading.
        """
        return self._model_manager.load_model()

    def unload_model(self) -> bool:
        """
        Unload AI model.

        Returns:
            True if model unloaded successfully

        Note:
            Phase 5: Stub only. No actual model unloading.
        """
        return self._model_manager.unload_model()
