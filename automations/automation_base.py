"""
Automation Base

Base class for automation modules.
Per DIP Phase 7: One automation = one module, explicit entry point.

Enforces:
- LAW 2 — NO AUTONOMOUS EXECUTION
- LAW 10 — SERIAL EXECUTION
- LAW 13 — COMPLETE AUDITABILITY
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from uuid import UUID

logger = logging.getLogger(__name__)


class AutomationBase(ABC):
    """
    Base class for automation modules.

    Per DIP Phase 7:
    - One automation = one module
    - Explicit entry point
    - Serial execution enforced
    - Persist execution state
    - Abort on reboot + notify

    Enforces:
    - LAW 2 — NO AUTONOMOUS EXECUTION
    - LAW 10 — SERIAL EXECUTION
    - LAW 13 — COMPLETE AUDITABILITY
    """

    def __init__(self, automation_id: str, name: str, description: str) -> None:
        """
        Initialize automation.

        Args:
            automation_id: Unique automation identifier
            name: Automation name
            description: Automation description
        """
        self._automation_id = automation_id
        self._name = name
        self._description = description

    @property
    def automation_id(self) -> str:
        """Get automation ID."""
        return self._automation_id

    @property
    def name(self) -> str:
        """Get automation name."""
        return self._name

    @property
    def description(self) -> str:
        """Get automation description."""
        return self._description

    @abstractmethod
    def execute(self, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute the automation.

        This is the explicit entry point for the automation.

        Args:
            context: Optional execution context

        Returns:
            Execution result dictionary

        Note:
            Per DIP Phase 7: Explicit entry point.
            All automations must implement this method.
        """
        pass

    def get_state(self) -> Dict[str, Any]:
        """
        Get automation execution state.

        Returns:
            State dictionary

        Note:
            Per DIP Phase 7: Persist execution state.
            Override this method to provide custom state.
        """
        return {
            "automation_id": self._automation_id,
            "name": self._name,
            "status": "idle",
        }

    def restore_state(self, state: Dict[str, Any]) -> None:
        """
        Restore automation state.

        Args:
            state: State dictionary to restore

        Note:
            Per DIP Phase 7: Persist execution state.
            Override this method to restore custom state.
        """
        # Default implementation: no-op
        # Subclasses can override to restore state
        pass
