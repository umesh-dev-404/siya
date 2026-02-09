"""
Tests for MCP Module

Phase 2 tests for governance and control plane.
Tests validation, authorization, permissions, and confirmation gating.
"""

from datetime import datetime, timezone
from uuid import uuid4

import pytest
from mcp.authorization_layer import AuthorizationLayer, AuthorizationResult
from mcp.mcp_server import MCPServer
from mcp.policy_engine import PermissionCheck, PermissionDecision, PolicyEngine
from mcp.request_validator import RequestValidator, ValidationError
from mcp.tool_registry import ToolRegistry
from mcp.tool_schema import PermissionLevel, ToolSchema


class TestToolSchema:
    """Tests for ToolSchema."""

    def test_tool_schema_creation(self):
        """Test creating a valid tool schema."""
        schema = ToolSchema(
            name="test_tool",
            description="Test tool",
            input_schema={"type": "object", "properties": {"arg1": {"type": "string"}}},
            output_schema={"type": "object"},
            permission_level=PermissionLevel.READ,
            requires_confirmation=False,
        )

        assert schema.name == "test_tool"
        assert schema.permission_level == PermissionLevel.READ
        assert schema.requires_confirmation is False

    def test_tool_schema_validation(self):
        """Test tool schema validation."""
        schema = ToolSchema(
            name="test_tool",
            description="Test tool",
            input_schema={
                "type": "object",
                "required": ["arg1"],
                "properties": {"arg1": {"type": "string"}},
            },
            output_schema={"type": "object"},
            permission_level=PermissionLevel.NONE,
            requires_confirmation=False,
        )

        # Valid arguments
        is_valid, error = schema.validate_input({"arg1": "value"})
        assert is_valid is True
        assert error is None

        # Missing required argument
        is_valid, error = schema.validate_input({})
        assert is_valid is False
        assert error is not None
        assert "required" in error.lower()


class TestToolRegistry:
    """Tests for ToolRegistry (LAW 4, LAW 6)."""

    def test_register_tool(self):
        """Test registering a tool."""
        registry = ToolRegistry()
        schema = ToolSchema(
            name="test_tool",
            description="Test tool",
            input_schema={"type": "object"},
            output_schema={"type": "object"},
            permission_level=PermissionLevel.NONE,
            requires_confirmation=False,
        )

        registry.register(schema)
        assert registry.exists("test_tool")
        assert registry.get("test_tool") == schema

    def test_duplicate_registration(self):
        """Test that duplicate tool registration fails."""
        registry = ToolRegistry()
        schema = ToolSchema(
            name="test_tool",
            description="Test tool",
            input_schema={"type": "object"},
            output_schema={"type": "object"},
            permission_level=PermissionLevel.NONE,
            requires_confirmation=False,
        )

        registry.register(schema)

        with pytest.raises(ValueError, match="already registered"):
            registry.register(schema)

    def test_registry_lock(self):
        """Test that locked registry prevents new registrations (LAW 6)."""
        registry = ToolRegistry()
        schema = ToolSchema(
            name="test_tool",
            description="Test tool",
            input_schema={"type": "object"},
            output_schema={"type": "object"},
            permission_level=PermissionLevel.NONE,
            requires_confirmation=False,
        )

        registry.lock()

        with pytest.raises(RuntimeError, match="locked"):
            registry.register(schema)


class TestRequestValidator:
    """Tests for RequestValidator (LAW 3, LAW 4)."""

    def test_validate_valid_tool_request(self):
        """Test validating a valid tool request."""
        registry = ToolRegistry()
        schema = ToolSchema(
            name="test_tool",
            description="Test tool",
            input_schema={"type": "object", "properties": {}},
            output_schema={"type": "object"},
            permission_level=PermissionLevel.NONE,
            requires_confirmation=False,
        )
        registry.register(schema)

        validator = RequestValidator(registry)

        request = {
            "type": "tool_request",
            "request_id": str(uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "tool_name": "test_tool",
            "arguments": {},
            "requires_confirmation": False,
        }

        is_valid, error = validator.validate_tool_request(request)
        assert is_valid is True
        assert error is None

    def test_validate_missing_fields(self):
        """Test that missing required fields are rejected."""
        registry = ToolRegistry()
        validator = RequestValidator(registry)

        request = {
            "type": "tool_request",
            # Missing request_id, timestamp, etc.
        }

        is_valid, error = validator.validate_tool_request(request)
        assert is_valid is False
        assert error is not None
        assert error.error_code == "MISSING_REQUIRED_FIELD"

    def test_validate_tool_not_found(self):
        """Test that unregistered tools are rejected (LAW 4)."""
        registry = ToolRegistry()
        validator = RequestValidator(registry)

        request = {
            "type": "tool_request",
            "request_id": str(uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "tool_name": "nonexistent_tool",
            "arguments": {},
            "requires_confirmation": False,
        }

        is_valid, error = validator.validate_tool_request(request)
        assert is_valid is False
        assert error is not None
        assert error.error_code == "TOOL_NOT_FOUND"

    def test_validate_intent_parsing_output(self):
        """Test validating intent parsing output (LAW 3)."""
        registry = ToolRegistry()
        validator = RequestValidator(registry)

        output = {
            "type": "intent_parsing_output",
            "request_id": str(uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "intent": {"action": "test_tool", "arguments": {}},
            "confidence": 0.9,
        }

        is_valid, error = validator.validate_intent_parsing_output(output)
        assert is_valid is True
        assert error is None


class TestPolicyEngine:
    """Tests for PolicyEngine (LAW 5)."""

    def test_permission_check_none(self):
        """Test permission check for NONE permission level."""
        engine = PolicyEngine()
        schema = ToolSchema(
            name="test_tool",
            description="Test tool",
            input_schema={"type": "object"},
            output_schema={"type": "object"},
            permission_level=PermissionLevel.NONE,
            requires_confirmation=False,
        )

        result = engine.check_permission(schema)
        assert result.decision == PermissionDecision.GRANTED

    def test_permission_check_requires_confirmation(self):
        """Test that tools requiring confirmation return REQUIRES_CONFIRMATION."""
        engine = PolicyEngine()
        schema = ToolSchema(
            name="test_tool",
            description="Test tool",
            input_schema={"type": "object"},
            output_schema={"type": "object"},
            permission_level=PermissionLevel.EXECUTE,
            requires_confirmation=True,
        )

        result = engine.check_permission(schema)
        assert result.decision == PermissionDecision.REQUIRES_CONFIRMATION
        assert result.requires_confirmation is True


class TestAuthorizationLayer:
    """Tests for AuthorizationLayer."""

    def test_authorize_valid_request(self):
        """Test authorizing a valid tool request."""
        registry = ToolRegistry()
        schema = ToolSchema(
            name="test_tool",
            description="Test tool",
            input_schema={"type": "object", "properties": {}},
            output_schema={"type": "object"},
            permission_level=PermissionLevel.NONE,
            requires_confirmation=False,
        )
        registry.register(schema)

        validator = RequestValidator(registry)
        policy_engine = PolicyEngine()
        auth_layer = AuthorizationLayer(registry, validator, policy_engine)

        request = {
            "type": "tool_request",
            "request_id": str(uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "tool_name": "test_tool",
            "arguments": {},
            "requires_confirmation": False,
        }

        result = auth_layer.authorize_tool_request(request)
        assert result.authorized is True
        assert result.requires_confirmation is False

    def test_authorize_requires_confirmation(self):
        """Test that tools requiring confirmation are flagged."""
        registry = ToolRegistry()
        schema = ToolSchema(
            name="test_tool",
            description="Test tool",
            input_schema={"type": "object", "properties": {}},
            output_schema={"type": "object"},
            permission_level=PermissionLevel.EXECUTE,
            requires_confirmation=True,
        )
        registry.register(schema)

        validator = RequestValidator(registry)
        policy_engine = PolicyEngine()
        auth_layer = AuthorizationLayer(registry, validator, policy_engine)

        request = {
            "type": "tool_request",
            "request_id": str(uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "tool_name": "test_tool",
            "arguments": {},
            "requires_confirmation": True,
        }

        result = auth_layer.authorize_tool_request(request)
        assert result.authorized is False
        assert result.requires_confirmation is True
        assert result.confirmation_request_id is not None


class TestMCPServer:
    """Tests for MCPServer (MCP)."""

    def test_mcp_initialization(self):
        """Test MCP initialization."""
        mcp = MCPServer()
        assert mcp.get_tool_registry() is not None
        assert mcp.get_request_validator() is not None
        assert mcp.get_policy_engine() is not None

    def test_mcp_authorizes_request(self):
        """Test that MCP authorizes valid requests."""
        mcp = MCPServer()

        # Register a tool
        schema = ToolSchema(
            name="test_tool",
            description="Test tool",
            input_schema={"type": "object", "properties": {}},
            output_schema={"type": "object"},
            permission_level=PermissionLevel.NONE,
            requires_confirmation=False,
        )
        mcp.get_tool_registry().register(schema)

        request = {
            "type": "tool_request",
            "request_id": str(uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "tool_name": "test_tool",
            "arguments": {},
            "requires_confirmation": False,
        }

        result = mcp.validate_and_authorize(request)
        assert result.authorized is True

    def test_mcp_rejects_invalid_request(self):
        """Test that MCP rejects invalid requests."""
        mcp = MCPServer()

        request = {
            "type": "tool_request",
            "request_id": str(uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "tool_name": "nonexistent_tool",
            "arguments": {},
            "requires_confirmation": False,
        }

        result = mcp.validate_and_authorize(request)
        assert result.authorized is False
        assert result.error_code == "TOOL_NOT_FOUND"
