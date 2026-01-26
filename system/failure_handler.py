"""
Failure Handler

Failure detection and handling framework.
Per DIP Phase 8: Failure Injection & Hardening.

Enforces:
- LAW 12 — FAILURE TRANSPARENCY
- No silent failures
- No corrupted state
- User always notified
"""

import logging
from enum import Enum
from typing import Any, Dict, Optional
from uuid import uuid4

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from audit.audit_logger import AuditLogger

logger = logging.getLogger(__name__)


class FailureType(str, Enum):
    """Failure types. Per DIP Phase 8."""

    POWER_LOSS = "POWER_LOSS"
    """Power loss detected."""

    NETWORK_LOSS = "NETWORK_LOSS"
    """Network connectivity lost."""

    AI_CRASH = "AI_CRASH"
    """AI model crashed."""

    TOOL_FAILURE = "TOOL_FAILURE"
    """Tool execution failed."""

    RESOURCE_EXHAUSTION = "RESOURCE_EXHAUSTION"
    """System resources exhausted (RAM, CPU, disk)."""

    SYSTEM_ERROR = "SYSTEM_ERROR"
    """General system error."""


class FailureSeverity(str, Enum):
    """Failure severity levels. Per system_schema.json."""

    LOW = "LOW"
    """Low severity - non-critical."""

    MEDIUM = "MEDIUM"
    """Medium severity - requires attention."""

    HIGH = "HIGH"
    """High severity - user notification required."""

    CRITICAL = "CRITICAL"
    """Critical severity - immediate user notification required."""


class FailureHandler:
    """
    Failure handler for system failures.

    Per DIP Phase 8:
    - No silent failure
    - No corrupted state
    - User always notified

    Enforces:
    - LAW 12 — FAILURE TRANSPARENCY
    """

    def __init__(self, audit_logger: "AuditLogger") -> None:
        """
        Initialize failure handler.

        Args:
            audit_logger: Audit logger for failure events
        """
        self._audit_logger = audit_logger

    def handle_failure(
        self,
        failure_type: FailureType,
        error_code: str,
        error_message: str,
        severity: FailureSeverity = FailureSeverity.MEDIUM,
        context: Optional[Dict[str, Any]] = None,
        recoverable: bool = True,
        related_request_id: Optional[str] = None,
    ) -> str:
        """
        Handle a system failure.

        Args:
            failure_type: Type of failure
            error_code: Machine-readable error code
            error_message: Human-readable error message
            severity: Failure severity
            context: Optional failure context
            recoverable: Whether failure is recoverable
            related_request_id: Optional related request ID

        Returns:
            Failure ID

        Note:
            Per DIP Phase 8 and LAW 12:
            - All failures are logged
            - User notification required for HIGH/CRITICAL
            - No silent failures
        """
        failure_id = str(uuid4())

        # Log failure event
        event_data = {
            "failure_type": failure_type.value,
            "error_code": error_code,
            "error_message": error_message,
            "severity": severity.value,
            "recoverable": recoverable,
            "context": context or {},
        }

        self._audit_logger.log_event(
            event_type="ERROR_OCCURRED",
            event_data=event_data,
            correlation_id=failure_id,
            request_id=related_request_id,
            layer="SYSTEM",
        )

        # Log failure
        log_level = logging.ERROR if severity in [FailureSeverity.HIGH, FailureSeverity.CRITICAL] else logging.WARNING

        logger.log(
            log_level,
            f"Failure detected: {failure_type.value} - {error_code}: {error_message}",
            extra={
                "failure_id": failure_id,
                "failure_type": failure_type.value,
                "error_code": error_code,
                "error_message": error_message,
                "severity": severity.value,
                "recoverable": recoverable,
            },
        )

        # Phase 8: User notification framework
        # For HIGH/CRITICAL failures, user must be notified
        if severity in [FailureSeverity.HIGH, FailureSeverity.CRITICAL]:
            self._notify_user(failure_type, error_code, error_message, severity)

        return failure_id

    def _notify_user(
        self,
        failure_type: FailureType,
        error_code: str,
        error_message: str,
        severity: FailureSeverity,
    ) -> None:
        """
        Notify user of failure.

        Args:
            failure_type: Type of failure
            error_code: Error code
            error_message: Error message
            severity: Failure severity

        Note:
            Per DIP Phase 8: User always notified for HIGH/CRITICAL failures.
            Phase 8: Logging only. Full notification system in later phases.
        """
        logger.critical(
            f"USER NOTIFICATION REQUIRED: {failure_type.value} - {error_code}: {error_message}",
            extra={
                "failure_type": failure_type.value,
                "error_code": error_code,
                "error_message": error_message,
                "severity": severity.value,
                "user_notified": True,
            },
        )

        # Phase 8: Notification framework ready
        # In later phases, this will trigger actual user notifications
        # (e.g., via CLI, web interface, email, etc.)

    def handle_power_loss(self, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Handle power loss.

        Args:
            context: Optional context

        Returns:
            Failure ID

        Note:
            Per DIP Phase 8: Power loss handling.
            Phase 8: Framework only. Full testing requires Pi hardware.
        """
        return self.handle_failure(
            failure_type=FailureType.POWER_LOSS,
            error_code="POWER_LOSS_DETECTED",
            error_message="System power loss detected. State may be inconsistent.",
            severity=FailureSeverity.CRITICAL,
            context=context,
            recoverable=True,
        )

    def handle_network_loss(self, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Handle network loss.

        Args:
            context: Optional context

        Returns:
            Failure ID
        """
        return self.handle_failure(
            failure_type=FailureType.NETWORK_LOSS,
            error_code="NETWORK_LOSS_DETECTED",
            error_message="Network connectivity lost. Offline mode active.",
            severity=FailureSeverity.MEDIUM,
            context=context,
            recoverable=True,
        )

    def handle_ai_crash(self, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Handle AI crash.

        Args:
            context: Optional context

        Returns:
            Failure ID
        """
        return self.handle_failure(
            failure_type=FailureType.AI_CRASH,
            error_code="AI_CRASH_DETECTED",
            error_message="AI model crashed. Intent parsing unavailable.",
            severity=FailureSeverity.HIGH,
            context=context,
            recoverable=True,
        )

    def handle_tool_failure(
        self,
        tool_name: str,
        error_code: str,
        error_message: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Handle tool failure.

        Args:
            tool_name: Name of failed tool
            error_code: Error code
            error_message: Error message
            context: Optional context

        Returns:
            Failure ID
        """
        tool_context = context or {}
        tool_context["tool_name"] = tool_name

        return self.handle_failure(
            failure_type=FailureType.TOOL_FAILURE,
            error_code=error_code,
            error_message=f"Tool '{tool_name}' failed: {error_message}",
            severity=FailureSeverity.MEDIUM,
            context=tool_context,
            recoverable=True,
        )

    def handle_resource_exhaustion(
        self,
        resource_type: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Handle resource exhaustion.

        Args:
            resource_type: Type of resource (RAM, CPU, DISK)
            context: Optional context

        Returns:
            Failure ID
        """
        resource_context = context or {}
        resource_context["resource_type"] = resource_type

        return self.handle_failure(
            failure_type=FailureType.RESOURCE_EXHAUSTION,
            error_code=f"RESOURCE_EXHAUSTION_{resource_type}",
            error_message=f"System resource exhausted: {resource_type}",
            severity=FailureSeverity.HIGH,
            context=resource_context,
            recoverable=False,
        )
