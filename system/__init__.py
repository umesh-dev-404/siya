"""
System Module

System-level components for failure handling and resource monitoring.
Per DIP Phase 8: Failure Injection & Hardening.

Enforces:
- LAW 12 — FAILURE TRANSPARENCY
"""

from system.failure_handler import FailureHandler, FailureSeverity, FailureType
from system.production_lock import ProductionLock
from system.resource_monitor import ResourceMonitor
from system.state_checker import StateChecker

__all__ = [
    "FailureHandler",
    "FailureSeverity",
    "FailureType",
    "ProductionLock",
    "ResourceMonitor",
    "StateChecker",
]
