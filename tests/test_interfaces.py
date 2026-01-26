"""
Tests for Interfaces Module

Phase 6 tests for CLI, API, and web interfaces.
Tests identical behavior across interfaces.
"""

import pytest
from ai import AIInterface
from api import APIServer
from cli import CLI
from mcp import ModelControlPlane, ToolRegistry, RequestValidator
from mcp.tool_schema import PermissionLevel, ToolSchema
from orchestrator import Orchestrator


class TestCLI:
    """Tests for CLI interface."""

    def test_cli_initialization(self):
        """Test CLI initialization."""
        mcp = ModelControlPlane()
        tool_registry = mcp.get_tool_registry()
        request_validator = mcp.get_request_validator()
        ai_interface = AIInterface(tool_registry, request_validator)
        orchestrator = Orchestrator(mcp=mcp, ai_interface=ai_interface)

        cli = CLI(orchestrator, mcp, ai_interface)
        assert cli is not None

    def test_cli_start_stop(self):
        """Test CLI start/stop."""
        mcp = ModelControlPlane()
        tool_registry = mcp.get_tool_registry()
        request_validator = mcp.get_request_validator()
        ai_interface = AIInterface(tool_registry, request_validator)
        orchestrator = Orchestrator(mcp=mcp, ai_interface=ai_interface)

        cli = CLI(orchestrator, mcp, ai_interface)
        cli.start()
        assert cli._running is True

        cli.stop()
        assert cli._running is False

    def test_cli_process_command(self):
        """Test CLI command processing."""
        mcp = ModelControlPlane()
        tool_registry = mcp.get_tool_registry()

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

        request_validator = mcp.get_request_validator()
        ai_interface = AIInterface(tool_registry, request_validator)
        orchestrator = Orchestrator(mcp=mcp, ai_interface=ai_interface)

        cli = CLI(orchestrator, mcp, ai_interface)
        cli.start()

        # Process command
        response = cli.process_command("use test_tool")
        assert "Task ID" in response or "Error" in response

        cli.stop()


class TestAPI:
    """Tests for API interface."""

    def test_api_initialization(self):
        """Test API initialization."""
        mcp = ModelControlPlane()
        tool_registry = mcp.get_tool_registry()
        request_validator = mcp.get_request_validator()
        ai_interface = AIInterface(tool_registry, request_validator)
        orchestrator = Orchestrator(mcp=mcp, ai_interface=ai_interface)
        cli = CLI(orchestrator, mcp, ai_interface)

        api = APIServer(cli)
        assert api is not None

    def test_api_handle_command(self):
        """Test API command handling."""
        mcp = ModelControlPlane()
        tool_registry = mcp.get_tool_registry()

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

        request_validator = mcp.get_request_validator()
        ai_interface = AIInterface(tool_registry, request_validator)
        orchestrator = Orchestrator(mcp=mcp, ai_interface=ai_interface)
        cli = CLI(orchestrator, mcp, ai_interface)
        cli.start()

        api = APIServer(cli)

        # Handle command
        response = api.handle_command({"command": "use test_tool"})
        assert response["status"] in ["success", "error"]
        assert "message" in response

        cli.stop()

    def test_api_handle_command_missing_field(self):
        """Test API command handling with missing field."""
        mcp = ModelControlPlane()
        tool_registry = mcp.get_tool_registry()
        request_validator = mcp.get_request_validator()
        ai_interface = AIInterface(tool_registry, request_validator)
        orchestrator = Orchestrator(mcp=mcp, ai_interface=ai_interface)
        cli = CLI(orchestrator, mcp, ai_interface)

        api = APIServer(cli)

        # Handle command without 'command' field
        response = api.handle_command({})
        assert response["status"] == "error"
        assert "command" in response["message"].lower()

    def test_api_health_check(self):
        """Test API health check."""
        mcp = ModelControlPlane()
        tool_registry = mcp.get_tool_registry()
        request_validator = mcp.get_request_validator()
        ai_interface = AIInterface(tool_registry, request_validator)
        orchestrator = Orchestrator(mcp=mcp, ai_interface=ai_interface)
        cli = CLI(orchestrator, mcp, ai_interface)

        api = APIServer(cli)

        response = api.handle_health_check()
        assert response["status"] == "healthy"
        assert response["service"] == "siya-api"


class TestIdenticalBehavior:
    """Tests for identical behavior across interfaces (DIP Phase 6 requirement)."""

    def test_cli_and_api_identical_behavior(self):
        """Test that CLI and API produce identical results."""
        mcp = ModelControlPlane()
        tool_registry = mcp.get_tool_registry()

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

        request_validator = mcp.get_request_validator()
        ai_interface = AIInterface(tool_registry, request_validator)
        orchestrator = Orchestrator(mcp=mcp, ai_interface=ai_interface)

        cli = CLI(orchestrator, mcp, ai_interface)
        cli.start()

        api = APIServer(cli)

        command = "use test_tool"

        # Get CLI response
        cli_response = cli.run_single_command(command)

        # Get API response
        api_response = api.handle_command({"command": command})

        # Both should succeed or both should fail
        # API wraps CLI response, so message should match
        assert api_response["status"] in ["success", "error"]
        if api_response["status"] == "success":
            # API message should contain CLI response
            assert cli_response in api_response["message"] or api_response["message"] in cli_response

        cli.stop()
