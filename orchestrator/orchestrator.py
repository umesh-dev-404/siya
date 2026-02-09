"""
Orchestration Engine Skeleton

Main orchestrator that coordinates task execution.
Per DIP Phase 1: Deterministic execution backbone without intelligence.
Per DIP Phase 5: Integrated with AI intent parsing.

Enforces:
- LAW 10 — SERIAL EXECUTION
- LAW 11 — TRANSACTIONAL STEPS
- LAW 12 — FAILURE TRANSPARENCY
- LAW 3 — LLM IS NOT AN AGENT (via AI integration)
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import UUID, uuid4

from ai.ai_interface import AIInterface
from core.system_context import get_system_context
from mcp.mcp_server import MCPServer
from orchestrator.execution_state import ExecutionState
from orchestrator.step_runner import StepRunner
from orchestrator.task_queue import Task, TaskQueue, TaskSource
from tools.tool_executor import ToolExecutor, ToolExecutionResult

logger = logging.getLogger(__name__)


class Orchestrator:
    """
    Orchestration engine skeleton.

    Per DIP Phase 1:
    - Deterministic task execution
    - Explicit failure propagation
    - Complete execution logs

    Per DIP Phase 5:
    - Integrated with AI intent parsing
    - Converts intent parsing output to tool requests
    - Coordinates with MCP for tool authorization

    Explicit Exclusions (Phase 1):
    - No tools (Phase 1)
    - No memory (Phase 3)
    - No scheduling (Phase 7)
    """

    def __init__(
        self,
        mcp: Optional[MCPServer] = None,
        ai_interface: Optional[AIInterface] = None,
        tool_executor: Optional[ToolExecutor] = None,
    ) -> None:
        """
        Initialize the orchestrator.

        Args:
            mcp: Optional MCP Server (for tool authorization)
            ai_interface: Optional AI Interface (for intent parsing)
        """
        self._task_queue = TaskQueue()
        self._step_runner = StepRunner()
        self._running = False
        self._mcp = mcp
        self._ai_interface = ai_interface
        self._tool_executor = tool_executor or ToolExecutor()
        self._task_results: Dict[UUID, Dict[str, Any]] = {}
        
        # Phase 11: Confirmation flow support (LAW 1 - Human Sovereignty)
        self._pending_confirmations: Dict[UUID, Dict[str, Any]] = {}
        self._pending_tool_requests: Dict[UUID, Dict[str, Any]] = {}
        
        # Phase 12: SystemContext for state management (LAW 8)
        self._context = get_system_context()

    def start(self) -> None:
        """
        Start the orchestrator.

        Raises:
            RuntimeError: If orchestrator is already running
        """
        if self._running:
            raise RuntimeError("Orchestrator is already running.")

        self._running = True
        logger.info("Orchestrator started")

    def stop(self) -> None:
        """
        Stop the orchestrator.

        Waits for current task to complete, then stops.
        """
        if not self._running:
            return

        logger.info("Orchestrator stopping...")

        # Wait for current task to complete
        if self._task_queue.is_executing():
            logger.warning(
                "Orchestrator stop requested while task is executing. "
                "Waiting for task completion..."
            )
            # In Phase 1, we just mark as not running
            # In later phases, we'd implement proper graceful shutdown

        self._running = False
        logger.info("Orchestrator stopped")

    def submit_task(
        self,
        source: TaskSource,
        task_id: Optional[UUID] = None,
    ) -> UUID:
        """
        Submit a task for execution.

        Args:
            source: Source of the task request
            task_id: Optional task ID (generated if not provided)

        Returns:
            Task ID

        Raises:
            RuntimeError: If orchestrator is not running or task rejected
        """
        if not self._running:
            raise RuntimeError("Cannot submit task: orchestrator is not running.")

        if task_id is None:
            from uuid import uuid4

            task_id = uuid4()

        task = Task(
            task_id=task_id,
            source=source,
            created_at=datetime.now(timezone.utc),
        )

        if not self._task_queue.enqueue(task):
            raise RuntimeError(
                "Task rejected: another task is currently executing. "
                "This enforces LAW 10 — SERIAL EXECUTION."
            )

        logger.info(
            f"Task {task_id} submitted",
            extra={
                "task_id": str(task_id),
                "source": source.value,
                "created_at": task.created_at.isoformat(),
            },
        )

        return task_id

    def submit_user_input(self, user_input: str) -> UUID:
        """
        Submit user input for processing through AI intent parsing.

        Per DIP Phase 5: User input -> AI intent parsing -> tool request -> execution.

        Args:
            user_input: Raw user input text

        Returns:
            Task ID

        Raises:
            RuntimeError: If orchestrator is not running or AI interface not available
            ValueError: If intent parsing fails or requires clarification

        Note:
            LAW 3: AI is parser, not executor. This method converts AI output to tool request.
        """
        if not self._running:
            raise RuntimeError("Cannot submit user input: orchestrator is not running.")

        if self._ai_interface is None:
            raise RuntimeError(
                "Cannot submit user input: AI interface not available. "
                "Initialize orchestrator with ai_interface parameter."
            )

        # Parse user intent using AI
        try:
            intent_output = self._ai_interface.parse_user_intent(user_input)
        except Exception as e:
            logger.error(
                f"Intent parsing failed: {e}",
                extra={"user_input": user_input},
                exc_info=True,
            )
            raise ValueError(f"Intent parsing failed: {e}") from e

        # Check if action is "unknown" - this means no tool matched
        intent = intent_output.get("intent", {})
        action = intent.get("action", "unknown")
        
        if action == "unknown":
            # No tool matched - check if clarification is needed
            clarification_needed = intent.get("clarification_needed", True)
            clarification_question = intent.get("clarification_question")
            
            if clarification_needed:
                if clarification_question and clarification_question.strip() and clarification_question != "null":
                    raise ValueError(f"Clarification needed: {clarification_question}")
                else:
                    raise ValueError("Clarification needed: I couldn't understand your request. Could you please rephrase it or be more specific?")
            else:
                # No clarification needed but no tool matched - return helpful message
                raise ValueError("I couldn't understand your request. Could you please rephrase it or be more specific?")

        # Check if clarification is needed for known actions
        if intent.get("clarification_needed", False):
            clarification_question = intent.get("clarification_question")
            if clarification_question and clarification_question.strip() and clarification_question != "null":
                raise ValueError(f"Clarification needed: {clarification_question}")
            else:
                raise ValueError("Clarification needed: Could you please provide more details?")

        # Convert intent parsing output to tool request
        tool_request = self._intent_to_tool_request(intent_output)

        # Submit tool request as task
        task_id = uuid4()
        task = Task(
            task_id=task_id,
            source=TaskSource.USER_PARSED,
            created_at=datetime.now(timezone.utc),
        )

        # Store tool request with task (Phase 5: extend Task if needed)
        # For now, we'll store it separately and use it in process_next_task
        if not hasattr(self, "_pending_tool_requests"):
            self._pending_tool_requests: Dict[UUID, Dict[str, Any]] = {}
        self._pending_tool_requests[task_id] = tool_request

        if not self._task_queue.enqueue(task):
            del self._pending_tool_requests[task_id]
            raise RuntimeError(
                "Task rejected: another task is currently executing. "
                "This enforces LAW 10 — SERIAL EXECUTION."
            )

        logger.info(
            f"User input submitted and parsed as task {task_id}",
            extra={
                "task_id": str(task_id),
                "user_input": user_input,
                "intent_action": intent_output.get("intent", {}).get("action"),
                "confidence": intent_output.get("confidence"),
            },
        )

        return task_id

    def _intent_to_tool_request(self, intent_output: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert intent parsing output to tool request.

        Per DIP Phase 5: Orchestrator converts AI output to tool request format.

        Args:
            intent_output: Intent parsing output (validated against system_schema.json)

        Returns:
            Tool request dictionary (matches system_schema.json tool_request)

        Raises:
            ValueError: If intent output is invalid
        """
        intent = intent_output.get("intent", {})
        action = intent.get("action")
        arguments = intent.get("arguments", {})

        if not action:
            raise ValueError("Intent output missing action field")

        # Get tool schema to determine permission level, confirmation, capability_domain (24.1), side_effect_scope (24.2b)
        requires_confirmation = False
        permission_level = "NONE"
        capability_domain = None
        side_effect_scope = None

        if self._mcp:
            tool_registry = self._mcp.get_tool_registry()
            if tool_registry.exists(action):
                tool_schema = tool_registry.get(action)
                if tool_schema:
                    requires_confirmation = tool_schema.requires_confirmation
                    permission_level = tool_schema.permission_level.value
                    capability_domain = tool_schema.capability_domain
                    side_effect_scope = tool_schema.side_effect_scope

        # Create tool request (matches system_schema.json tool_request; capability_domain optional 24.1, side_effect_scope optional 24.2b)
        tool_request = {
            "type": "tool_request",
            "request_id": str(uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "tool_name": action,
            "arguments": arguments,
            "requires_confirmation": requires_confirmation,
            "permission_level": permission_level,
            "source": "user_parsed",
            "intent_parsing_output_id": intent_output.get("request_id"),
        }
        if capability_domain is not None:
            tool_request["capability_domain"] = capability_domain
        if side_effect_scope is not None:
            tool_request["side_effect_scope"] = side_effect_scope

        return tool_request

    def process_next_task(self) -> bool:
        """
        Process the next task in the queue.

        Per DIP Phase 1: This is a skeleton implementation.
        In Phase 1, we only validate the execution flow, not actual tool execution.

        Returns:
            True if a task was processed, False if queue is empty

        Raises:
            RuntimeError: If orchestrator is not running
        """
        if not self._running:
            raise RuntimeError("Cannot process task: orchestrator is not running.")

        task = self._task_queue.dequeue()
        if task is None:
            return False

        logger.info(
            f"Processing task {task.task_id}",
            extra={
                "task_id": str(task.task_id),
                "source": task.source.value,
            },
        )

        try:
            # Phase 5: Integrated execution flow with MCP and AI
            # Get tool request if available (from user input parsing)
            tool_request = None
            if hasattr(self, "_pending_tool_requests"):
                tool_request = self._pending_tool_requests.pop(task.task_id, None)

            # Start step
            step_id = self._step_runner.start_step()

            # Transition through lifecycle
            self._step_runner.transition_to(ExecutionState.VALIDATE)

            # Phase 5: Validate tool request through MCP
            if tool_request and self._mcp:
                authorization_result = self._mcp.validate_and_authorize(tool_request)

                if not authorization_result.authorized:
                    error_code = authorization_result.error_code or "AUTHORIZATION_DENIED"
                    error_message = authorization_result.error_message or "Tool request denied by MCP"
                    raise RuntimeError(f"{error_code}: {error_message}")

                if authorization_result.requires_confirmation:
                    # Phase 11: Store pending confirmation (LAW 1 - Human Sovereignty)
                    tool_name = tool_request.get('tool_name')
                    self._pending_confirmations[task.task_id] = {
                        "tool_request": tool_request,
                        "task": task,
                        "step_id": step_id,
                        "tool_name": tool_name,
                        "arguments": tool_request.get("arguments", {}),
                        "message": f"Tool '{tool_name}' requires confirmation before execution.",
                    }
                    
                    # Store task result as pending
                    self._task_results[task.task_id] = {
                        "status": "pending_confirmation",
                        "tool_name": tool_name,
                        "message": f"Tool '{tool_name}' requires your confirmation to execute. Use confirm_execution() or reject_execution().",
                    }
                    
                    logger.info(
                        f"Confirmation required for tool {tool_name} (task {task.task_id})",
                        extra={"task_id": str(task.task_id), "tool_name": tool_name},
                    )
                    
                    # Mark task as waiting for confirmation (not failed, not complete)
                    self._task_queue.mark_complete()  # Remove from queue but track in pending
                    return True

                logger.debug(
                    f"Step {step_id} validated and authorized",
                    extra={"tool_name": tool_request.get("tool_name")},
                )
            else:
                # Phase 1: Validation always passes (no MCP or tool request)
                logger.debug(f"Step {step_id} validated (no tool request)")

            self._step_runner.transition_to(ExecutionState.EXECUTE)
            # Execute tool (Phase 11+): orchestration executes, MCP only validates/authorizes
            execution_result: Optional[ToolExecutionResult] = None
            if tool_request:
                tool_name = tool_request.get("tool_name")
                arguments = tool_request.get("arguments", {})
                if not isinstance(arguments, dict):
                    raise RuntimeError("INVALID_ARGUMENTS: tool_request.arguments must be an object")

                # Phase 12: Track execution time
                import time
                start_time = time.monotonic()
                execution_result = self._tool_executor.execute(tool_name, arguments)
                execution_time_ms = int((time.monotonic() - start_time) * 1000)
                
                # Phase 12: Record execution in SystemContext (LAW 8 - orchestrator writes)
                self._context.record_execution(
                    tool_name=tool_name,
                    arguments=arguments,
                    result_status="ok",
                    task_id=task.task_id,
                    execution_time_ms=execution_time_ms,
                    caller="orchestrator",
                )
                
                self._task_results[task.task_id] = {
                    "tool_name": execution_result.tool_name,
                    "output": execution_result.output,
                }

                logger.info(
                    f"Step {step_id} executed tool",
                    extra={"tool_name": tool_name, "task_id": str(task.task_id)},
                )
            else:
                logger.debug(f"Step {step_id} executed (no tool)")

            self._step_runner.transition_to(ExecutionState.VERIFY)
            # Phase 5: Verification always passes (no actual verification yet)
            logger.debug(f"Step {step_id} verified")

            # Complete step
            result = self._step_runner.complete_step()

            logger.info(
                f"Task {task.task_id} completed successfully",
                extra={
                    "task_id": str(task.task_id),
                    "step_id": str(step_id),
                    "result_state": result.execution_state.value,
                },
            )

            self._task_queue.mark_complete()
            return True

        except Exception as e:
            # LAW 12 — FAILURE TRANSPARENCY: All failures must be logged
            error_code = "ORCHESTRATOR_ERROR"
            error_message = str(e)

            logger.error(
                f"Task {task.task_id} failed: {error_message}",
                extra={
                    "task_id": str(task.task_id),
                    "error_code": error_code,
                    "error_message": error_message,
                },
                exc_info=True,
            )
            
            # Phase 12: Record failed execution in SystemContext
            if tool_request:
                self._context.record_execution(
                    tool_name=tool_request.get("tool_name", "unknown"),
                    arguments=tool_request.get("arguments", {}),
                    result_status="error",
                    task_id=task.task_id,
                    caller="orchestrator",
                )

            # Fail the step
            try:
                self._step_runner.fail_step(
                    error_code=error_code,
                    error_message=error_message,
                    rollback_required=False,  # Phase 1: No rollback yet
                )
            except Exception:
                # If step runner is in invalid state, abort it
                self._step_runner.abort_step()

            self._task_queue.mark_failed()
            return True

    def get_task_result(self, task_id: UUID) -> Optional[Dict[str, Any]]:
        """
        Get the latest execution result for a task (if available).

        Used by interfaces to show tool outputs.
        """
        return self._task_results.get(task_id)

    def is_running(self) -> bool:
        """
        Check if orchestrator is running.

        Returns:
            True if running, False otherwise
        """
        return self._running

    def get_queue_size(self) -> int:
        """
        Get the number of tasks waiting in the queue.

        Returns:
            Number of queued tasks
        """
        return self._task_queue.queue_size()

    def is_executing(self) -> bool:
        """
        Check if a task is currently executing.

        Returns:
            True if executing, False otherwise
        """
        return self._task_queue.is_executing()

    # Phase 11: Confirmation Flow (LAW 1 - Human Sovereignty)
    
    def get_pending_confirmations(self) -> Dict[UUID, Dict[str, Any]]:
        """
        Get all pending confirmations.
        
        Per LAW 1: Human Sovereignty - tools requiring confirmation are held
        until user explicitly approves or rejects.
        
        Returns:
            Dictionary of task_id -> confirmation details
        """
        return dict(self._pending_confirmations)

    def confirm_execution(self, task_id: UUID) -> Dict[str, Any]:
        """
        Confirm and execute a pending tool request.
        
        Per LAW 1: Human Sovereignty - user explicitly approves execution.
        
        Args:
            task_id: Task ID of the pending confirmation
            
        Returns:
            Execution result
            
        Raises:
            ValueError: If task_id not in pending confirmations
        """
        if task_id not in self._pending_confirmations:
            raise ValueError(f"No pending confirmation for task {task_id}")
        
        confirmation = self._pending_confirmations.pop(task_id)
        tool_request = confirmation["tool_request"]
        tool_name = confirmation["tool_name"]
        arguments = confirmation["arguments"]
        
        logger.info(
            f"Confirmation received for tool {tool_name} (task {task_id})",
            extra={"task_id": str(task_id), "tool_name": tool_name},
        )
        
        try:
            # Execute the tool
            execution_result = self._tool_executor.execute(tool_name, arguments)
            
            # Update task result
            self._task_results[task_id] = {
                "status": "ok",
                "tool_name": execution_result.tool_name,
                "output": execution_result.output,
                "confirmed": True,
            }
            
            logger.info(
                f"Tool {tool_name} executed after confirmation",
                extra={"task_id": str(task_id), "tool_name": tool_name},
            )
            
            return self._task_results[task_id]
            
        except Exception as e:
            logger.error(
                f"Tool {tool_name} failed after confirmation: {e}",
                extra={"task_id": str(task_id), "tool_name": tool_name},
                exc_info=True,
            )
            
            self._task_results[task_id] = {
                "status": "error",
                "tool_name": tool_name,
                "message": str(e),
                "confirmed": True,
            }
            
            return self._task_results[task_id]

    def reject_execution(self, task_id: UUID, reason: Optional[str] = None) -> Dict[str, Any]:
        """
        Reject a pending tool request.
        
        Per LAW 1: Human Sovereignty - user explicitly rejects execution.
        
        Args:
            task_id: Task ID of the pending confirmation
            reason: Optional rejection reason
            
        Returns:
            Rejection result
            
        Raises:
            ValueError: If task_id not in pending confirmations
        """
        if task_id not in self._pending_confirmations:
            raise ValueError(f"No pending confirmation for task {task_id}")
        
        confirmation = self._pending_confirmations.pop(task_id)
        tool_name = confirmation["tool_name"]
        
        logger.info(
            f"Execution rejected for tool {tool_name} (task {task_id})",
            extra={"task_id": str(task_id), "tool_name": tool_name, "reason": reason},
        )
        
        self._task_results[task_id] = {
            "status": "rejected",
            "tool_name": tool_name,
            "message": reason or "Execution rejected by user",
            "confirmed": False,
        }
        
        return self._task_results[task_id]

