"""
Automations Module

Automation framework for Siya.
Per DIP Phase 7: Automation & Scheduling.

Enforces:
- LAW 2 — NO AUTONOMOUS EXECUTION
- LAW 10 — SERIAL EXECUTION
- LAW 13 — COMPLETE AUDITABILITY
"""

from automations.automation_base import AutomationBase
from automations.automation_manager import AutomationManager

__all__ = ["AutomationBase", "AutomationManager"]
