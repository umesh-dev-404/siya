"""
Step Runner

Implements transactional step execution with explicit lifecycle.
Enforces LAW 11 — TRANSACTIONAL STEPS.

Per DIP Phase 1: Step lifecycle enforced, commit only on verification,
rollback on failure.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable, Optional
from uuid import UUID, uuid4

from orchestrator.execution_state import ExecutionState

logger = logging.getLogger(__name__)


@dataclass
class StepResult:
    """Result of a step execution."""

    step_id: UUID
    """Unique step identifier."""

    execution_state: ExecutionState
    """Current execution state."""

    started_at: datetime
    """When step execution started."""

    completed_at: Optional[datetime] = None
    """When step execution completed (None if not completed)."""

    success: bool = False
    """Whether step completed successfully."""

    error_code: Optional[str] = None
    """Error code if step failed."""

    error_message: Optional[str] = None
    """Error message if step failed."""

    verification_result: Optional[dict] = None
    """Result of step verification (if applicable)."""

    rollback_required: bool = False
    """Whether rollback is required due to failure."""

    rollback_completed: bool = False
    """Whether rollback has been completed."""


class StepRunner:
    """
    Step runner for transactional step execution.

    Enforces LAW 11 — TRANSACTIONAL STEPS:
    - Step lifecycle enforced
    - Commit only on verification
    - Rollback on failure

    Per DIP Phase 1 and LAW 11 enforcement.
    """

    def __init__(self) -> None:
        """Initialize the step runner."""
        self._current_state: Optional[ExecutionState] = None
        self._step_id: Optional[UUID] = None
        self._started_at: Optional[datetime] = None

    def start_step(self, step_id: Optional[UUID] = None) -> UUID:
        """
        Start a new step execution.

        Args:
            step_id: Optional step ID (generated if not provided)

        Returns:
            Step ID

        Raises:
            RuntimeError: If a step is already in progress
        """
        if self._current_state is not None:
            raise RuntimeError(
                f"Cannot start step: step {self._step_id} is already in progress "
                f"(state: {self._current_state})."
            )

        if step_id is None:
            step_id = uuid4()

        self._step_id = step_id
        self._current_state = ExecutionState.INIT
        self._started_at = datetime.now(timezone.utc)

        logger.info(
            f"Step {self._step_id} started",
            extra={
                "step_id": str(self._step_id),
                "state": self._current_state.value,
                "started_at": self._started_at.isoformat(),
            },
        )

        return step_id

    def transition_to(self, new_state: ExecutionState) -> None:
        """
        Transition to a new execution state.

        Args:
            new_state: Target state

        Raises:
            RuntimeError: If no step is in progress or transition is invalid
        """
        if self._current_state is None:
            raise RuntimeError("Cannot transition: no step is in progress.")

        if not ExecutionState.can_transition(self._current_state.value, new_state.value):
            raise RuntimeError(
                f"Invalid transition: cannot transition from {self._current_state.value} "
                f"to {new_state.value}."
            )

        old_state = self._current_state
        self._current_state = new_state

        logger.info(
            f"Step {self._step_id} transitioned: {old_state.value} -> {new_state.value}",
            extra={
                "step_id": str(self._step_id),
                "old_state": old_state.value,
                "new_state": new_state.value,
            },
        )

    def complete_step(self, verification_result: Optional[dict] = None) -> StepResult:
        """
        Complete a step successfully.

        Args:
            verification_result: Optional verification result

        Returns:
            Step result

        Raises:
            RuntimeError: If step is not in VERIFY state
        """
        if self._current_state != ExecutionState.VERIFY:
            raise RuntimeError(
                f"Cannot complete step: step must be in VERIFY state, "
                f"but is in {self._current_state.value}."
            )

        self.transition_to(ExecutionState.COMMIT)
        completed_at = datetime.now(timezone.utc)

        result = StepResult(
            step_id=self._step_id,
            execution_state=ExecutionState.COMMIT,
            started_at=self._started_at,
            completed_at=completed_at,
            success=True,
            verification_result=verification_result,
        )

        logger.info(
            f"Step {self._step_id} completed successfully",
            extra={
                "step_id": str(self._step_id),
                "state": ExecutionState.COMMIT.value,
                "completed_at": completed_at.isoformat(),
            },
        )

        self._reset()

        return result

    def fail_step(
        self,
        error_code: str,
        error_message: str,
        rollback_required: bool = False,
    ) -> StepResult:
        """
        Fail a step.

        Args:
            error_code: Machine-readable error code
            error_message: Human-readable error message
            rollback_required: Whether rollback is required

        Returns:
            Step result

        Raises:
            RuntimeError: If step is already in a terminal state
        """
        if self._current_state is None:
            raise RuntimeError("Cannot fail step: no step is in progress.")

        if ExecutionState.is_terminal(self._current_state.value):
            raise RuntimeError(
                f"Cannot fail step: step is already in terminal state "
                f"{self._current_state.value}."
            )

        self.transition_to(ExecutionState.FAIL)
        completed_at = datetime.now(timezone.utc)

        result = StepResult(
            step_id=self._step_id,
            execution_state=ExecutionState.FAIL,
            started_at=self._started_at,
            completed_at=completed_at,
            success=False,
            error_code=error_code,
            error_message=error_message,
            rollback_required=rollback_required,
        )

        logger.error(
            f"Step {self._step_id} failed: {error_code} - {error_message}",
            extra={
                "step_id": str(self._step_id),
                "state": ExecutionState.FAIL.value,
                "error_code": error_code,
                "error_message": error_message,
                "rollback_required": rollback_required,
                "completed_at": completed_at.isoformat(),
            },
        )

        self._reset()

        return result

    def abort_step(self) -> StepResult:
        """
        Abort a step.

        Can be called from any non-terminal state.

        Returns:
            Step result

        Raises:
            RuntimeError: If no step is in progress
        """
        if self._current_state is None:
            raise RuntimeError("Cannot abort step: no step is in progress.")

        if ExecutionState.is_terminal(self._current_state.value):
            # Already terminal, return current state
            completed_at = datetime.now(timezone.utc)
            return StepResult(
                step_id=self._step_id,
                execution_state=self._current_state,
                started_at=self._started_at,
                completed_at=completed_at,
                success=self._current_state == ExecutionState.COMMIT,
            )

        old_state = self._current_state
        self.transition_to(ExecutionState.ABORT)
        completed_at = datetime.now(timezone.utc)

        result = StepResult(
            step_id=self._step_id,
            execution_state=ExecutionState.ABORT,
            started_at=self._started_at,
            completed_at=completed_at,
            success=False,
        )

        logger.warning(
            f"Step {self._step_id} aborted from state {old_state.value}",
            extra={
                "step_id": str(self._step_id),
                "old_state": old_state.value,
                "state": ExecutionState.ABORT.value,
                "completed_at": completed_at.isoformat(),
            },
        )

        self._reset()

        return result

    def get_current_state(self) -> Optional[ExecutionState]:
        """
        Get the current execution state.

        Returns:
            Current state, or None if no step is in progress
        """
        return self._current_state

    def _reset(self) -> None:
        """Reset the step runner state."""
        self._current_state = None
        self._step_id = None
        self._started_at = None
