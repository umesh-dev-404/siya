"""
Tests for Orchestrator Module

Phase 1 tests for core runtime skeleton.
Tests deterministic execution, serial execution, and failure propagation.
"""

from datetime import datetime, timezone
from uuid import uuid4

import pytest
from orchestrator.execution_state import ExecutionState
from orchestrator.orchestrator import Orchestrator
from orchestrator.step_runner import StepResult, StepRunner
from orchestrator.task_queue import Task, TaskQueue, TaskSource


class TestExecutionState:
    """Tests for ExecutionState enum."""

    def test_state_values(self):
        """Test that all required states exist."""
        assert ExecutionState.INIT == "INIT"
        assert ExecutionState.VALIDATE == "VALIDATE"
        assert ExecutionState.EXECUTE == "EXECUTE"
        assert ExecutionState.VERIFY == "VERIFY"
        assert ExecutionState.COMMIT == "COMMIT"
        assert ExecutionState.FAIL == "FAIL"
        assert ExecutionState.ABORT == "ABORT"

    def test_terminal_states(self):
        """Test terminal state detection."""
        assert ExecutionState.is_terminal(ExecutionState.COMMIT)
        assert ExecutionState.is_terminal(ExecutionState.FAIL)
        assert ExecutionState.is_terminal(ExecutionState.ABORT)
        assert not ExecutionState.is_terminal(ExecutionState.INIT)
        assert not ExecutionState.is_terminal(ExecutionState.VALIDATE)
        assert not ExecutionState.is_terminal(ExecutionState.EXECUTE)
        assert not ExecutionState.is_terminal(ExecutionState.VERIFY)

    def test_valid_transitions(self):
        """Test valid state transitions."""
        # INIT -> VALIDATE
        assert ExecutionState.can_transition(ExecutionState.INIT, ExecutionState.VALIDATE)
        # INIT -> ABORT
        assert ExecutionState.can_transition(ExecutionState.INIT, ExecutionState.ABORT)
        # VALIDATE -> EXECUTE
        assert ExecutionState.can_transition(ExecutionState.VALIDATE, ExecutionState.EXECUTE)
        # VALIDATE -> FAIL
        assert ExecutionState.can_transition(ExecutionState.VALIDATE, ExecutionState.FAIL)
        # EXECUTE -> VERIFY
        assert ExecutionState.can_transition(ExecutionState.EXECUTE, ExecutionState.VERIFY)
        # VERIFY -> COMMIT
        assert ExecutionState.can_transition(ExecutionState.VERIFY, ExecutionState.COMMIT)

    def test_invalid_transitions(self):
        """Test invalid state transitions."""
        # Cannot skip states
        assert not ExecutionState.can_transition(ExecutionState.INIT, ExecutionState.EXECUTE)
        # Cannot go backwards
        assert not ExecutionState.can_transition(ExecutionState.EXECUTE, ExecutionState.VALIDATE)
        # Terminal states have no transitions
        assert not ExecutionState.can_transition(ExecutionState.COMMIT, ExecutionState.INIT)


class TestTaskQueue:
    """Tests for TaskQueue (LAW 10 — SERIAL EXECUTION)."""

    def test_enqueue_dequeue(self):
        """Test basic enqueue/dequeue."""
        queue = TaskQueue()
        task = Task(
            task_id=uuid4(),
            source=TaskSource.USER_DIRECT,
            created_at=datetime.now(timezone.utc),
        )

        assert queue.enqueue(task) is True
        assert queue.queue_size() == 1
        assert queue.is_executing() is False

        dequeued = queue.dequeue()
        assert dequeued == task
        assert queue.is_executing() is True
        assert queue.get_current_task() == task

    def test_serial_execution_enforcement(self):
        """Test that LAW 10 is enforced (only one task at a time)."""
        queue = TaskQueue()
        task1 = Task(
            task_id=uuid4(), source=TaskSource.USER_DIRECT, created_at=datetime.now(timezone.utc)
        )
        task2 = Task(
            task_id=uuid4(), source=TaskSource.USER_DIRECT, created_at=datetime.now(timezone.utc)
        )

        # Enqueue first task
        assert queue.enqueue(task1) is True
        queue.dequeue()

        # Try to enqueue second task while first is executing
        assert queue.enqueue(task2) is False  # Should be rejected

        # Complete first task
        queue.mark_complete()
        assert queue.is_executing() is False

        # Now can enqueue second task
        assert queue.enqueue(task2) is True

    def test_cannot_dequeue_while_executing(self):
        """Test that dequeue fails if task is already executing."""
        queue = TaskQueue()
        task = Task(
            task_id=uuid4(), source=TaskSource.USER_DIRECT, created_at=datetime.now(timezone.utc)
        )

        queue.enqueue(task)
        queue.dequeue()

        # Try to dequeue again while executing
        with pytest.raises(RuntimeError, match="already executing"):
            queue.dequeue()


class TestStepRunner:
    """Tests for StepRunner (LAW 11 — TRANSACTIONAL STEPS)."""

    def test_step_lifecycle(self):
        """Test complete step lifecycle."""
        runner = StepRunner()
        step_id = runner.start_step()

        assert runner.get_current_state() == ExecutionState.INIT

        runner.transition_to(ExecutionState.VALIDATE)
        assert runner.get_current_state() == ExecutionState.VALIDATE

        runner.transition_to(ExecutionState.EXECUTE)
        assert runner.get_current_state() == ExecutionState.EXECUTE

        runner.transition_to(ExecutionState.VERIFY)
        assert runner.get_current_state() == ExecutionState.VERIFY

        result = runner.complete_step()
        assert result.success is True
        assert result.execution_state == ExecutionState.COMMIT
        assert runner.get_current_state() is None

    def test_step_failure(self):
        """Test step failure."""
        runner = StepRunner()
        runner.start_step()
        runner.transition_to(ExecutionState.VALIDATE)
        runner.transition_to(ExecutionState.EXECUTE)

        result = runner.fail_step(
            error_code="TEST_ERROR",
            error_message="Test error message",
            rollback_required=False,
        )

        assert result.success is False
        assert result.execution_state == ExecutionState.FAIL
        assert result.error_code == "TEST_ERROR"
        assert result.error_message == "Test error message"
        assert runner.get_current_state() is None

    def test_step_abort(self):
        """Test step abort from any state."""
        runner = StepRunner()
        runner.start_step()
        runner.transition_to(ExecutionState.VALIDATE)

        result = runner.abort_step()

        assert result.success is False
        assert result.execution_state == ExecutionState.ABORT
        assert runner.get_current_state() is None

    def test_invalid_transitions(self):
        """Test that invalid transitions are rejected."""
        runner = StepRunner()
        runner.start_step()

        # Cannot skip states
        with pytest.raises(RuntimeError, match="Invalid transition"):
            runner.transition_to(ExecutionState.EXECUTE)

        # Must go through VALIDATE first
        runner.transition_to(ExecutionState.VALIDATE)
        runner.transition_to(ExecutionState.EXECUTE)

    def test_cannot_complete_without_verify(self):
        """Test that step cannot be completed without being in VERIFY state."""
        runner = StepRunner()
        runner.start_step()
        runner.transition_to(ExecutionState.VALIDATE)
        runner.transition_to(ExecutionState.EXECUTE)

        # Cannot complete from EXECUTE state
        with pytest.raises(RuntimeError, match="must be in VERIFY state"):
            runner.complete_step()


class TestOrchestrator:
    """Tests for Orchestrator."""

    def test_start_stop(self):
        """Test orchestrator start/stop."""
        orchestrator = Orchestrator()

        assert orchestrator.is_running() is False

        orchestrator.start()
        assert orchestrator.is_running() is True

        orchestrator.stop()
        assert orchestrator.is_running() is False

    def test_cannot_submit_when_stopped(self):
        """Test that tasks cannot be submitted when orchestrator is stopped."""
        orchestrator = Orchestrator()

        with pytest.raises(RuntimeError, match="not running"):
            orchestrator.submit_task(TaskSource.USER_DIRECT)

    def test_serial_execution(self):
        """Test that orchestrator enforces serial execution."""
        orchestrator = Orchestrator()
        orchestrator.start()

        task_id1 = orchestrator.submit_task(TaskSource.USER_DIRECT)
        assert orchestrator.get_queue_size() == 1

        # Process first task
        orchestrator.process_next_task()
        assert orchestrator.is_executing() is False

        # Submit second task
        task_id2 = orchestrator.submit_task(TaskSource.USER_DIRECT)
        assert orchestrator.get_queue_size() == 1

        # Process second task
        orchestrator.process_next_task()
        assert orchestrator.is_executing() is False
        assert orchestrator.get_queue_size() == 0

        orchestrator.stop()


class TestOrchestratorAIIntegration:
    """Tests for Orchestrator AI integration (Phase 5)."""

    def test_submit_user_input_requires_ai_interface(self):
        """Test that submit_user_input requires AI interface."""
        from mcp import MCPServer

        orchestrator = Orchestrator(mcp=MCPServer())
        orchestrator.start()

        with pytest.raises(RuntimeError, match="AI interface not available"):
            orchestrator.submit_user_input("test input")

        orchestrator.stop()

    def test_submit_user_input_basic(self):
        """Test submitting user input through AI intent parsing."""
        from ai import AIInterface
        from mcp import MCPServer, ToolRegistry, RequestValidator
        from mcp.tool_schema import PermissionLevel, ToolSchema

        # Setup MCP and AI
        tool_registry = ToolRegistry()
        request_validator = RequestValidator(tool_registry)
        mcp = MCPServer()
        ai_interface = AIInterface(tool_registry, request_validator)

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

        orchestrator = Orchestrator(mcp=mcp, ai_interface=ai_interface)
        orchestrator.start()

        # Submit user input
        task_id = orchestrator.submit_user_input("use test_tool")

        assert task_id is not None
        assert orchestrator.get_queue_size() == 1

        orchestrator.stop()

    def test_submit_user_input_clarification_needed(self):
        """Test that clarification needed raises ValueError."""
        from ai import AIInterface
        from mcp import MCPServer, ToolRegistry, RequestValidator

        tool_registry = ToolRegistry()
        request_validator = RequestValidator(tool_registry)
        mcp = MCPServer()
        ai_interface = AIInterface(tool_registry, request_validator)

        orchestrator = Orchestrator(mcp=mcp, ai_interface=ai_interface)
        orchestrator.start()

        # Submit input that requires clarification (no tools registered)
        with pytest.raises(ValueError, match="Clarification needed"):
            orchestrator.submit_user_input("do something")

        orchestrator.stop()

    def test_process_task_with_tool_request(self):
        """Test processing task with tool request from AI."""
        from ai import AIInterface
        from mcp import MCPServer, ToolRegistry, RequestValidator
        from mcp.tool_schema import PermissionLevel, ToolSchema

        # Setup MCP and AI
        tool_registry = ToolRegistry()
        request_validator = RequestValidator(tool_registry)
        mcp = MCPServer()
        ai_interface = AIInterface(tool_registry, request_validator)

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

        orchestrator = Orchestrator(mcp=mcp, ai_interface=ai_interface)
        orchestrator.start()

        # Submit user input
        task_id = orchestrator.submit_user_input("use test_tool")

        # Process task
        processed = orchestrator.process_next_task()

        assert processed is True
        assert orchestrator.get_queue_size() == 0
        assert orchestrator.is_executing() is False

        orchestrator.stop()
