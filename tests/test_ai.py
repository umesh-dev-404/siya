"""
Tests for AI Module

Phase 5 tests for AI integration.
Tests intent parsing, schema validation, and model management.
"""

import pytest
from mcp.request_validator import RequestValidator, ValidationError
from mcp.tool_registry import ToolRegistry, ToolSchema
from mcp.tool_schema import PermissionLevel

from ai.ai_interface import AIInterface
from ai.intent_parser import IntentParser
from ai.model_manager import ModelManager


class TestModelManager:
    """Tests for ModelManager (stub)."""

    def test_model_manager_initialization(self):
        """Test model manager initialization."""
        manager = ModelManager()
        assert manager.is_loaded() is False
        assert manager.get_model_size_mb() == 0

    def test_load_unload_model(self):
        """Test model load/unload (stub)."""
        manager = ModelManager()

        # Load model
        assert manager.load_model() is True
        assert manager.is_loaded() is True

        # Unload model
        assert manager.unload_model() is True
        assert manager.is_loaded() is False

    def test_generate_requires_loaded_model(self):
        """Test that generate requires loaded model."""
        manager = ModelManager()

        with pytest.raises(RuntimeError, match="Model not loaded"):
            manager.generate("test prompt")

        # Load and generate (stub)
        manager.load_model()
        result = manager.generate("test prompt")
        assert isinstance(result, str)


class TestIntentParser:
    """Tests for IntentParser (LAW 3)."""

    def test_intent_parser_initialization(self):
        """Test intent parser initialization."""
        tool_registry = ToolRegistry()
        request_validator = RequestValidator(tool_registry)
        parser = IntentParser(request_validator)

        assert parser is not None

    def test_parse_intent_basic(self):
        """Test basic intent parsing."""
        tool_registry = ToolRegistry()
        request_validator = RequestValidator(tool_registry)

        # Register a test tool
        tool_schema = ToolSchema(
            name="test_tool",
            description="Test tool",
            input_schema={"type": "object", "properties": {}},
            output_schema={"type": "object"},
            permission_level=PermissionLevel.READ,
            requires_confirmation=False,
        )
        tool_registry.register(tool_schema)

        parser = IntentParser(request_validator)
        output = parser.parse_intent("use test_tool", ["test_tool"])

        # Validate output structure
        assert output["type"] == "intent_parsing_output"
        assert "request_id" in output
        assert "timestamp" in output
        assert "intent" in output
        assert "confidence" in output
        assert output["intent"]["action"] == "test_tool"

    def test_parse_intent_validation(self):
        """Test that intent parsing output is validated."""
        tool_registry = ToolRegistry()
        request_validator = RequestValidator(tool_registry)

        parser = IntentParser(request_validator)

        # This should succeed (stub produces valid output)
        output = parser.parse_intent("test input", ["test_tool"])
        assert output["type"] == "intent_parsing_output"


class TestAIInterface:
    """Tests for AIInterface."""

    def test_ai_interface_initialization(self):
        """Test AI interface initialization."""
        tool_registry = ToolRegistry()
        request_validator = RequestValidator(tool_registry)

        ai_interface = AIInterface(tool_registry, request_validator)
        assert ai_interface is not None

    def test_parse_user_intent(self):
        """Test parsing user intent."""
        tool_registry = ToolRegistry()
        request_validator = RequestValidator(tool_registry)

        # Register a test tool
        tool_schema = ToolSchema(
            name="test_tool",
            description="Test tool",
            input_schema={"type": "object", "properties": {}},
            output_schema={"type": "object"},
            permission_level=PermissionLevel.READ,
            requires_confirmation=False,
        )
        tool_registry.register(tool_schema)

        ai_interface = AIInterface(tool_registry, request_validator)
        output = ai_interface.parse_user_intent("use test_tool")

        # Validate output
        assert output["type"] == "intent_parsing_output"
        assert "intent" in output
        assert "action" in output["intent"]

    def test_model_management(self):
        """Test model load/unload through interface."""
        tool_registry = ToolRegistry()
        request_validator = RequestValidator(tool_registry)

        ai_interface = AIInterface(tool_registry, request_validator)

        # Initially not loaded
        assert ai_interface.is_model_loaded() is False

        # Load model
        assert ai_interface.load_model() is True
        assert ai_interface.is_model_loaded() is True

        # Unload model
        assert ai_interface.unload_model() is True
        assert ai_interface.is_model_loaded() is False
