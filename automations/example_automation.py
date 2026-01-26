"""
Example Automation

Example automation module demonstrating the automation framework.
Per DIP Phase 7: One automation = one module, explicit entry point.
"""

from typing import Any, Dict, Optional

from automations.automation_base import AutomationBase


class ExampleAutomation(AutomationBase):
    """
    Example automation module.

    Per DIP Phase 7: Demonstrates automation structure.
    """

    def __init__(self) -> None:
        """Initialize example automation."""
        super().__init__(
            automation_id="example",
            name="Example Automation",
            description="Example automation for testing",
        )

    def execute(self, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute the automation.

        Args:
            context: Optional execution context

        Returns:
            Execution result
        """
        # Example automation logic
        result = {
            "status": "success",
            "message": "Example automation executed",
            "context": context or {},
        }

        return result
