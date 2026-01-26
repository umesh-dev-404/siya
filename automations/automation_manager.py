"""
Automation Manager

Manages automation execution and state persistence.
Per DIP Phase 7: Serial execution enforced, persist execution state, abort on reboot.

Enforces:
- LAW 2 — NO AUTONOMOUS EXECUTION
- LAW 10 — SERIAL EXECUTION
- LAW 13 — COMPLETE AUDITABILITY
"""

import json
import logging
from pathlib import Path
from typing import Dict, Optional
from uuid import UUID, uuid4

from automations.automation_base import AutomationBase
from orchestrator.orchestrator import Orchestrator
from orchestrator.task_queue import TaskSource

logger = logging.getLogger(__name__)


class AutomationManager:
    """
    Automation manager.

    Per DIP Phase 7:
    - Serial execution enforced
    - Persist execution state
    - Abort on reboot + notify
    - No overlapping automations

    Enforces:
    - LAW 2 — NO AUTONOMOUS EXECUTION
    - LAW 10 — SERIAL EXECUTION
    - LAW 13 — COMPLETE AUDITABILITY
    """

    def __init__(
        self,
        orchestrator: Orchestrator,
        state_dir: Optional[Path] = None,
    ) -> None:
        """
        Initialize automation manager.

        Args:
            orchestrator: Orchestrator instance for task execution
            state_dir: Directory for state persistence (default: ./automation_state)
        """
        self._orchestrator = orchestrator
        self._state_dir = state_dir or Path("automation_state")
        self._state_dir.mkdir(exist_ok=True)
        self._automations: Dict[str, AutomationBase] = {}
        self._executing_automation: Optional[str] = None

        # Check for aborted automations on startup
        self._check_aborted_automations()

    def register_automation(self, automation: AutomationBase) -> None:
        """
        Register an automation.

        Args:
            automation: Automation instance

        Raises:
            ValueError: If automation ID already registered
        """
        if automation.automation_id in self._automations:
            raise ValueError(
                f"Automation '{automation.automation_id}' is already registered"
            )

        self._automations[automation.automation_id] = automation

        logger.info(
            f"Automation registered: {automation.name}",
            extra={
                "automation_id": automation.automation_id,
                "name": automation.name,
            },
        )

    def execute_automation(
        self,
        automation_id: str,
        context: Optional[Dict] = None,
    ) -> UUID:
        """
        Execute an automation.

        Args:
            automation_id: Automation ID
            context: Optional execution context

        Returns:
            Task ID

        Raises:
            ValueError: If automation not found or already executing
            RuntimeError: If orchestrator not running

        Note:
            Per DIP Phase 7: Serial execution enforced (LAW 10).
            No overlapping automations allowed.
        """
        if automation_id not in self._automations:
            raise ValueError(f"Automation '{automation_id}' not found")

        # Check if another automation is executing
        if self._executing_automation is not None:
            raise RuntimeError(
                f"Automation '{self._executing_automation}' is already executing. "
                f"This enforces LAW 10 — SERIAL EXECUTION. "
                f"Cannot execute '{automation_id}'."
            )

        automation = self._automations[automation_id]

        # Save execution state
        self._save_execution_state(automation_id, context)

        # Mark as executing
        self._executing_automation = automation_id

        # Submit task to orchestrator
        try:
            task_id = self._orchestrator.submit_task(
                source=TaskSource.AUTOMATION,
            )

            # Execute automation in orchestrator context
            # Phase 7: Automation execution is a task
            # The actual automation.execute() will be called during task processing

            logger.info(
                f"Automation '{automation.name}' execution started",
                extra={
                    "automation_id": automation_id,
                    "task_id": str(task_id),
                },
            )

            return task_id

        except Exception as e:
            # Clear executing flag on error
            self._executing_automation = None
            self._clear_execution_state(automation_id)
            raise

    def complete_automation(self, automation_id: str) -> None:
        """
        Mark automation as complete.

        Args:
            automation_id: Automation ID

        Note:
            Per DIP Phase 7: Clear execution state on completion.
        """
        if self._executing_automation == automation_id:
            self._executing_automation = None
            self._clear_execution_state(automation_id)

            logger.info(
                f"Automation '{automation_id}' execution completed",
                extra={"automation_id": automation_id},
            )

    def abort_automation(self, automation_id: str, reason: str) -> None:
        """
        Abort an automation.

        Args:
            automation_id: Automation ID
            reason: Abort reason

        Note:
            Per DIP Phase 7: Abort on reboot + notify.
            This method is called when an automation is aborted (e.g., on reboot).
        """
        self._executing_automation = None
        self._clear_execution_state(automation_id)

        logger.warning(
            f"Automation '{automation_id}' aborted: {reason}",
            extra={"automation_id": automation_id, "reason": reason},
        )

        # Phase 7: Notification will be implemented in later phases
        # For now, we log the abort

    def is_executing(self, automation_id: Optional[str] = None) -> bool:
        """
        Check if an automation is executing.

        Args:
            automation_id: Optional automation ID to check (if None, checks any)

        Returns:
            True if executing, False otherwise
        """
        if automation_id is None:
            return self._executing_automation is not None
        return self._executing_automation == automation_id

    def _save_execution_state(
        self, automation_id: str, context: Optional[Dict] = None
    ) -> None:
        """
        Save automation execution state.

        Args:
            automation_id: Automation ID
            context: Execution context

        Note:
            Per DIP Phase 7: Persist execution state.
        """
        state_file = self._state_dir / f"{automation_id}.json"

        automation = self._automations[automation_id]
        state = automation.get_state()
        state["context"] = context or {}
        state["status"] = "executing"

        with open(state_file, "w") as f:
            json.dump(state, f, indent=2)

    def _clear_execution_state(self, automation_id: str) -> None:
        """
        Clear automation execution state.

        Args:
            automation_id: Automation ID
        """
        state_file = self._state_dir / f"{automation_id}.json"
        if state_file.exists():
            state_file.unlink()

    def _check_aborted_automations(self) -> None:
        """
        Check for aborted automations on startup.

        Per DIP Phase 7: Abort on reboot + notify.
        This method is called on initialization to detect automations
        that were executing when the system was shut down.
        """
        if not self._state_dir.exists():
            return

        for state_file in self._state_dir.glob("*.json"):
            try:
                with open(state_file, "r") as f:
                    state = json.load(f)

                automation_id = state.get("automation_id")
                if automation_id:
                    self.abort_automation(
                        automation_id,
                        "System reboot detected - automation was executing",
                    )

            except Exception as e:
                logger.error(
                    f"Failed to check aborted automation {state_file}: {e}",
                    exc_info=True,
                )
