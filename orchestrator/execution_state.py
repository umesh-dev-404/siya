"""
Execution State Definitions

Defines the execution lifecycle states for orchestration steps.
Per DIP Phase 1 and system_schema.json execution_state enum.

LAW 11 — TRANSACTIONAL STEPS: Each step must follow this lifecycle.
"""

from enum import Enum
from typing import Final


class ExecutionState(str, Enum):
    """
    Execution lifecycle states.

    States must be traversed in order:
    INIT -> VALIDATE -> EXECUTE -> VERIFY -> COMMIT
    Or: INIT -> VALIDATE -> EXECUTE -> VERIFY -> FAIL
    Or: Any state -> ABORT

    Per system_schema.json and DIP Phase 1.
    """

    INIT: Final[str] = "INIT"
    """Initial state. Task is created but not yet validated."""

    VALIDATE: Final[str] = "VALIDATE"
    """Validation state. Task is being validated before execution."""

    EXECUTE: Final[str] = "EXECUTE"
    """Execution state. Task is being executed."""

    VERIFY: Final[str] = "VERIFY"
    """Verification state. Task execution result is being verified."""

    COMMIT: Final[str] = "COMMIT"
    """Commit state. Task execution is committed (successful completion)."""

    FAIL: Final[str] = "FAIL"
    """Failure state. Task execution failed."""

    ABORT: Final[str] = "ABORT"
    """Abort state. Task execution was aborted (can occur from any state)."""

    @classmethod
    def get_valid_transitions(cls) -> dict[str, list[str]]:
        """
        Get valid state transitions.

        Returns:
            Dictionary mapping each state to list of valid next states.
        """
        return {
            cls.INIT: [cls.VALIDATE, cls.ABORT],
            cls.VALIDATE: [cls.EXECUTE, cls.FAIL, cls.ABORT],
            cls.EXECUTE: [cls.VERIFY, cls.FAIL, cls.ABORT],
            cls.VERIFY: [cls.COMMIT, cls.FAIL, cls.ABORT],
            cls.COMMIT: [],  # Terminal state
            cls.FAIL: [],  # Terminal state
            cls.ABORT: [],  # Terminal state
        }

    @classmethod
    def is_terminal(cls, state: str) -> bool:
        """
        Check if a state is terminal (no further transitions possible).

        Args:
            state: State to check

        Returns:
            True if state is terminal, False otherwise
        """
        return state in (cls.COMMIT, cls.FAIL, cls.ABORT)

    @classmethod
    def can_transition(cls, from_state: str, to_state: str) -> bool:
        """
        Check if a transition from one state to another is valid.

        Args:
            from_state: Current state
            to_state: Target state

        Returns:
            True if transition is valid, False otherwise
        """
        valid_transitions = cls.get_valid_transitions()
        return to_state in valid_transitions.get(from_state, [])
