"""
Tests for Automations Module

Phase 7 tests for automation framework.
Tests serial execution, state persistence, and abort handling.
"""

import json
import tempfile
from pathlib import Path

import pytest
from automations.automation_base import AutomationBase
from automations.automation_manager import AutomationManager
from automations.example_automation import ExampleAutomation
from orchestrator import Orchestrator
from orchestrator.task_queue import TaskSource


class TestAutomationBase:
    """Tests for AutomationBase."""

    def test_automation_base_initialization(self):
        """Test automation base initialization."""
        automation = ExampleAutomation()

        assert automation.automation_id == "example"
        assert automation.name == "Example Automation"
        assert automation.description == "Example automation for testing"

    def test_automation_base_execute(self):
        """Test automation execute method."""
        automation = ExampleAutomation()
        result = automation.execute()

        assert result["status"] == "success"
        assert "message" in result

    def test_automation_base_state(self):
        """Test automation state management."""
        automation = ExampleAutomation()
        state = automation.get_state()

        assert state["automation_id"] == "example"
        assert state["name"] == "Example Automation"
        assert state["status"] == "idle"


class TestAutomationManager:
    """Tests for AutomationManager."""

    def test_automation_manager_initialization(self):
        """Test automation manager initialization."""
        orchestrator = Orchestrator()
        manager = AutomationManager(orchestrator)

        assert manager is not None

    def test_register_automation(self):
        """Test registering an automation."""
        orchestrator = Orchestrator()
        manager = AutomationManager(orchestrator)
        automation = ExampleAutomation()

        manager.register_automation(automation)

        # Try to register again (should fail)
        with pytest.raises(ValueError, match="already registered"):
            manager.register_automation(automation)

    def test_execute_automation_serial_enforcement(self):
        """Test that serial execution is enforced (LAW 10)."""
        orchestrator = Orchestrator()
        orchestrator.start()

        manager = AutomationManager(orchestrator)
        automation = ExampleAutomation()
        manager.register_automation(automation)

        # Execute first automation
        task_id1 = manager.execute_automation("example")

        # Try to execute second automation (should fail)
        automation2 = ExampleAutomation()
        automation2._automation_id = "example2"
        manager.register_automation(automation2)

        with pytest.raises(RuntimeError, match="already executing"):
            manager.execute_automation("example2")

        # Complete first automation
        manager.complete_automation("example")

        # Now can execute second
        task_id2 = manager.execute_automation("example2")
        assert task_id2 is not None

        orchestrator.stop()

    def test_execute_automation_not_found(self):
        """Test executing non-existent automation."""
        orchestrator = Orchestrator()
        manager = AutomationManager(orchestrator)

        with pytest.raises(ValueError, match="not found"):
            manager.execute_automation("nonexistent")

    def test_state_persistence(self):
        """Test execution state persistence."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_dir = Path(tmpdir) / "automation_state"
            orchestrator = Orchestrator()
            orchestrator.start()

            manager = AutomationManager(orchestrator, state_dir=state_dir)
            automation = ExampleAutomation()
            manager.register_automation(automation)

            # Execute automation
            manager.execute_automation("example")

            # Check state file exists
            state_file = state_dir / "example.json"
            assert state_file.exists()

            # Check state content
            with open(state_file, "r") as f:
                state = json.load(f)

            assert state["automation_id"] == "example"
            assert state["status"] == "executing"

            # Complete automation
            manager.complete_automation("example")

            # State file should be cleared
            assert not state_file.exists()

            orchestrator.stop()

    def test_abort_on_reboot(self):
        """Test abort on reboot detection."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_dir = Path(tmpdir) / "automation_state"
            state_dir.mkdir()

            # Create a state file (simulating aborted automation)
            state_file = state_dir / "example.json"
            with open(state_file, "w") as f:
                json.dump(
                    {
                        "automation_id": "example",
                        "name": "Example Automation",
                        "status": "executing",
                    },
                    f,
                )

            orchestrator = Orchestrator()
            manager = AutomationManager(orchestrator, state_dir=state_dir)

            # State file should be cleared (automation aborted)
            assert not state_file.exists()

    def test_is_executing(self):
        """Test is_executing check."""
        orchestrator = Orchestrator()
        orchestrator.start()

        manager = AutomationManager(orchestrator)
        automation = ExampleAutomation()
        manager.register_automation(automation)

        assert manager.is_executing() is False
        assert manager.is_executing("example") is False

        # Execute automation
        manager.execute_automation("example")
        assert manager.is_executing() is True
        assert manager.is_executing("example") is True

        # Complete automation
        manager.complete_automation("example")
        assert manager.is_executing() is False

        orchestrator.stop()
