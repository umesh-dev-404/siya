"""
Intent Parser

AI intent parsing interface with strict JSON schema enforcement.
Enforces LAW 3 — LLM IS NOT AN AGENT.

Per DIP Phase 5: AI Integration (Controlled) - Stub implementation.
Per DIP Phase 10: Real AI Model Integration - llama.cpp integration.
AI is strictly an intent parser, not an agent.
"""

import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional
from uuid import uuid4

from mcp.request_validator import RequestValidator, ValidationError

logger = logging.getLogger(__name__)

# System prompt cache (loaded once)
_SYSTEM_PROMPT_CACHE: Optional[str] = None


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

    def __init__(
        self,
        request_validator: RequestValidator,
        model_manager: Optional[Any] = None,  # ModelManager type to avoid circular import
    ) -> None:
        """
        Initialize intent parser.

        Args:
            request_validator: Request validator for schema enforcement
            model_manager: Optional ModelManager instance for real AI inference
        """
        self._request_validator = request_validator
        self._model_manager = model_manager

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
            Phase 10: Real llama.cpp integration.
            Falls back to stub mode if model not available.
            All outputs are validated against system_schema.json.
        """
        request_id = str(uuid4())
        timestamp = datetime.utcnow().isoformat() + "Z"

        # Try real AI parsing, fall back to stub
        if self._model_manager and self._model_manager.is_loaded():
            try:
                intent = self._ai_parse(user_input, available_tools)
            except Exception as e:
                logger.warning(f"AI parsing failed, falling back to stub: {e}", exc_info=True)
                intent = self._stub_parse(user_input, available_tools)
        else:
            # Stub mode (no model or model not loaded)
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

    def _ai_parse(self, user_input: str, available_tools: list[str]) -> Dict[str, Any]:
        """
        Parse intent using real AI model.

        Args:
            user_input: User input text
            available_tools: Available tool names

        Returns:
            Intent object (action, arguments, etc.)

        Raises:
            RuntimeError: If model inference fails

        Note:
            Phase 10: Real AI model inference.
            LAW 3: AI output is untrusted and must be validated.
        """
        if not self._model_manager:
            raise RuntimeError("Model manager not available")

        # Generate prompt for intent parsing
        prompt = self._build_intent_prompt(user_input, available_tools)

        # Generate response from model
        try:
            response_text = self._model_manager.generate(
                prompt=prompt,
                max_tokens=256,  # Reduced for faster inference on Pi
                temperature=0.7,
                timeout=120.0,  # Increased timeout for slower hardware (Pi)
            )
        except Exception as e:
            logger.error(f"Model inference failed: {e}", exc_info=True)
            raise RuntimeError(f"Inference failed: {e}") from e

        # Parse JSON from response
        intent = self._parse_ai_response(response_text, available_tools)

        return intent

    def _get_system_prompt(self) -> str:
        """
        Load system prompt from docs/System Prompt.md.

        Returns:
            System prompt text

        Note:
            System prompt is cached after first load.
            Falls back to minimal prompt if file not found.
        """
        global _SYSTEM_PROMPT_CACHE

        if _SYSTEM_PROMPT_CACHE is not None:
            return _SYSTEM_PROMPT_CACHE

        # Try to load from docs/System Prompt.md
        project_root = Path(__file__).parent.parent
        system_prompt_path = project_root / "docs" / "System Prompt.md"

        if system_prompt_path.exists():
            try:
                content = system_prompt_path.read_text(encoding="utf-8")
                # Extract content between markers (if present) or use full content
                if "FILE START" in content and "FILE END" in content:
                    # Extract between markers
                    start_marker = "FILE START"
                    end_marker = "FILE END"
                    start_idx = content.find(start_marker) + len(start_marker)
                    end_idx = content.find(end_marker)
                    if end_idx > start_idx:
                        content = content[start_idx:end_idx].strip()
                
                # Remove markdown header if present
                if content.startswith("#"):
                    # Skip first line if it's a header
                    lines = content.split("\n")
                    if lines[0].startswith("#"):
                        content = "\n".join(lines[1:]).strip()
                
                _SYSTEM_PROMPT_CACHE = content
                logger.debug("System prompt loaded from file")
                return _SYSTEM_PROMPT_CACHE
            except Exception as e:
                logger.warning(f"Failed to load system prompt: {e}", exc_info=True)
        
        # Fallback to minimal system prompt
        fallback = """You are an intent parser for a personal assistant system named Siya.
You are NOT an autonomous agent, decision-maker, or executor.
You are an intent interpreter that extracts structured information from user input.
Your output is data only - execution is handled by deterministic system components."""
        
        _SYSTEM_PROMPT_CACHE = fallback
        logger.warning("Using fallback system prompt (System Prompt.md not found)")
        return _SYSTEM_PROMPT_CACHE

    def _build_intent_prompt(self, user_input: str, available_tools: list[str]) -> str:
        """
        Build prompt for intent parsing.

        Args:
            user_input: User input text
            available_tools: Available tool names

        Returns:
            Formatted prompt string with system prompt prepended

        Note:
            System prompt is loaded from docs/System Prompt.md and prepended.
            This ensures the AI follows Siya's canonical constraints (LAW 3).
        """
        # Get system prompt (cached after first load)
        system_prompt = self._get_system_prompt()
        
        tools_list = "\n".join([f"- {tool}" for tool in available_tools]) if available_tools else "No tools available"

        task_prompt = f"""
## CURRENT TASK: Intent Parsing

Available tools:
{tools_list}

User input: "{user_input}"

Parse the user's intent and respond with a JSON object in this exact format:
{{
  "action": "tool_name",
  "arguments": {{}},
  "clarification_needed": false,
  "clarification_question": null
}}

Rules:
- "action" must be one of the available tools or "unknown" if no tool matches
- "arguments" should contain any parameters needed for the tool (empty object if none)
- "clarification_needed" should be true if the intent is unclear
- "clarification_question" should be a helpful question if clarification is needed, null otherwise

Respond with ONLY the JSON object, no other text."""

        # Combine system prompt with task-specific prompt
        full_prompt = f"""{system_prompt}

{task_prompt}"""

        return full_prompt

    def _parse_ai_response(self, response_text: str, available_tools: list[str]) -> Dict[str, Any]:
        """
        Parse AI response into intent object.

        Args:
            response_text: Raw AI response text
            available_tools: Available tool names for validation

        Returns:
            Intent object

        Raises:
            RuntimeError: If response cannot be parsed
        """
        # Try to extract JSON from response
        # AI might return JSON wrapped in markdown or other text
        # Look for JSON object (handles nested objects)
        json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
        else:
            # Try to find JSON between code blocks
            code_block_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
            if code_block_match:
                json_str = code_block_match.group(1)
            else:
                json_str = response_text.strip()

        try:
            intent = json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {e}", extra={"response": response_text})
            raise RuntimeError(f"Invalid JSON response from AI: {e}") from e

        # Validate and normalize intent structure
        action = intent.get("action", "unknown")
        if action not in available_tools and action != "unknown":
            logger.warning(
                f"AI returned unknown tool: {action}",
                extra={"action": action, "available_tools": available_tools},
            )
            action = "unknown"
            intent["clarification_needed"] = True
            intent["clarification_question"] = f"Tool '{action}' is not available. Which tool would you like to use?"

        return {
            "action": action,
            "arguments": intent.get("arguments", {}),
            "clarification_needed": intent.get("clarification_needed", False),
            "clarification_question": intent.get("clarification_question"),
        }

    def _stub_parse(self, user_input: str, available_tools: list[str]) -> Dict[str, Any]:
        """
        Stub intent parsing logic (fallback).

        Args:
            user_input: User input text
            available_tools: Available tool names

        Returns:
            Intent object (action, arguments, etc.)

        Note:
            Phase 5: Stub implementation (fallback when model not available).
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
