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
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional
from uuid import uuid4

from mcp.request_validator import RequestValidator, ValidationError
from ai.context_manager import get_context_manager

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
        timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

        # Try real AI parsing, fall back to stub
        if self._model_manager and self._model_manager.is_loaded():
            try:
                intent = self._ai_parse(user_input, available_tools)
                # Validate that we got a valid intent (not empty/default due to errors)
                if intent.get("action") == "unknown" and not intent.get("clarification_needed"):
                    logger.debug("AI returned unknown action without clarification - this is valid")
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
            logger.info(f"Calling model with prompt length: {len(prompt)}")
            logger.debug(f"Prompt preview (last 300 chars): {prompt[-300:]}")
            response_text = self._model_manager.generate(
                prompt=prompt,
                max_tokens=128,  # Reduced further for faster inference on Pi (JSON responses are short)
                temperature=0.2,  # Very low temperature for deterministic JSON output
                timeout=120.0,  # Increased timeout for slower hardware (Pi)
                stop=None,  # Don't use stop sequences - let model generate full JSON (max_tokens will limit it)
            )
            logger.info(f"Model response received (length: {len(response_text)}): {response_text[:300]}")
            if not response_text or not response_text.strip():
                logger.warning("Model returned empty response!")
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
            Phase 12: Context is injected from ContextManager (LAW 7 - informational only).
            This ensures the AI follows Siya's canonical constraints (LAW 3).
        """
        # Get system prompt (cached after first load)
        system_prompt = self._get_system_prompt()
        
        tools_list = "\n".join([f"- {tool}" for tool in available_tools]) if available_tools else "No tools available"
        
        # Phase 12: Get context from ContextManager (LAW 7 - read-only, informational)
        context_manager = get_context_manager()
        context_str = ""
        try:
            # Inject recent execution history for context awareness
            context_manager.inject_from_system_context(limit=3)
            context_str = context_manager.get_context_for_ai()
            if context_str:
                context_str = f"\n\nRecent Context (informational only - do not base decisions on this):\n{context_str}\n"
        except Exception as e:
            logger.debug(f"Context injection skipped: {e}")
            context_str = ""

        # Ultra-simplified prompt with explicit JSON example
        tools_str = ', '.join(available_tools) if available_tools else 'none'
        task_prompt = f"""Parse this user input: "{user_input}"
Available tools: {tools_str}{context_str}

Respond with ONLY this JSON format (no other text):
{{"action":"unknown","arguments":{{}},"clarification_needed":false,"clarification_question":null}}"""

        # Combine system prompt with task-specific prompt
        full_prompt = f"""{system_prompt}

{task_prompt}"""

        return full_prompt

    def _repair_json(self, json_str: str) -> str:
        """
        Attempt to repair common JSON issues in AI responses.
        
        Args:
            json_str: Potentially malformed JSON string
            
        Returns:
            Repaired JSON string (or default JSON if repair fails)
        """
        if not json_str or not json_str.strip():
            logger.warning("JSON string is empty, returning default")
            return '{"action":"unknown","arguments":{},"clarification_needed":true,"clarification_question":"Could you please rephrase your request?"}'
        
        original = json_str
        json_str = json_str.strip()
        
        # Remove any text before first {
        start_idx = json_str.find('{')
        if start_idx > 0:
            json_str = json_str[start_idx:]
        
        # Remove any text after last }
        end_idx = json_str.rfind('}')
        if end_idx != -1 and end_idx < len(json_str) - 1:
            json_str = json_str[:end_idx+1]
        
        # If no { found, return default
        if '{' not in json_str:
            logger.warning(f"No JSON object found in: {original[:100]}, using default")
            return '{"action":"unknown","arguments":{},"clarification_needed":true,"clarification_question":"Could you please rephrase your request?"}'
        
        # Fix common issues:
        # 1. Single quotes to double quotes (but be careful with apostrophes in strings)
        # Only replace single quotes that are clearly JSON delimiters
        json_str = re.sub(r"'(\w+)':", r'"\1":', json_str)  # Keys
        json_str = re.sub(r":\s*'([^']*)'", r': "\1"', json_str)  # String values
        
        # 2. Trailing commas before }
        json_str = re.sub(r',\s*}', '}', json_str)
        json_str = re.sub(r',\s*]', ']', json_str)
        
        # 3. Missing quotes around keys (but not if already quoted)
        json_str = re.sub(r'([{,]\s*)(\w+)(\s*:)', r'\1"\2"\3', json_str)
        
        # 4. Fix unquoted string values (but not numbers/booleans/null)
        # This is tricky, so we'll be conservative - only fix obvious cases
        json_str = re.sub(r':\s*([a-zA-Z_][a-zA-Z0-9_]*)([,}])', r': "\1"\2', json_str)
        
        result = json_str.strip()
        logger.debug(f"JSON repair: {original[:100]} -> {result[:100]}")
        return result

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
        logger.info(f"Parsing AI response (length: {len(response_text)}): {response_text[:200]}")
        
        # Clean the response - remove any leading/trailing whitespace
        response_text = response_text.strip()
        
        # If response is empty, return default intent
        if not response_text:
            logger.warning("AI returned empty response, using default intent")
            return {
                "action": "unknown",
                "arguments": {},
                "clarification_needed": True,
                "clarification_question": "Could you please rephrase your request?",
            }
        
        # Try to extract JSON from response
        # First, try to find JSON object (handles nested objects better)
        json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
        else:
            # Try to find JSON between code blocks
            code_block_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
            if code_block_match:
                json_str = code_block_match.group(1)
            else:
                # Try to find first { to last }
                start_idx = response_text.find('{')
                end_idx = response_text.rfind('}')
                if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                    json_str = response_text[start_idx:end_idx+1]
                else:
                    # No JSON found - try to construct from response
                    logger.warning(f"No JSON found in response, attempting to construct default: {response_text[:100]}")
                    json_str = '{"action":"unknown","arguments":{},"clarification_needed":true,"clarification_question":"Could you please rephrase your request?"}'

        # Try to repair common JSON issues
        json_str = self._repair_json(json_str)
        logger.debug(f"Repaired JSON (first 200 chars): {json_str[:200]}")

        try:
            intent = json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {e}", extra={
                "response": response_text[:500],
                "extracted_json": json_str[:500],
                "response_length": len(response_text)
            })
            # Return default intent instead of raising error
            logger.warning("Using default intent due to JSON parsing failure")
            return {
                "action": "unknown",
                "arguments": {},
                "clarification_needed": True,
                "clarification_question": "I had trouble understanding your request. Could you please rephrase it?",
            }
        
        logger.debug(f"Successfully parsed intent: {intent}")

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
