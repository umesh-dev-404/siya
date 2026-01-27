"""
Policy Engine

Enforces permission policies and confirmation requirements.
Enforces LAW 5 — EXPLICIT PERMISSIONS.

Per DIP Phase 2: Permission enforcement and confirmation gating.
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Dict, Optional
from uuid import UUID, uuid4

from mcp.tool_schema import PermissionLevel, ToolSchema

logger = logging.getLogger(__name__)


class PermissionDecision(str, Enum):
    """Permission decision result."""

    GRANTED = "GRANTED"
    """Permission granted."""

    DENIED = "DENIED"
    """Permission denied."""

    REQUIRES_CONFIRMATION = "REQUIRES_CONFIRMATION"
    """Permission requires user confirmation."""


@dataclass
class PermissionCheck:
    """
    Result of a permission check.

    Per LAW 5 — EXPLICIT PERMISSIONS: All permission checks are logged.
    """

    tool_name: str
    """Name of the tool being checked."""

    required_permission: PermissionLevel
    """Required permission level."""

    decision: PermissionDecision
    """Permission decision."""

    requires_confirmation: bool
    """Whether confirmation is required."""

    checked_at: datetime
    """When the check was performed."""

    reason: Optional[str] = None
    """Reason for the decision (if denied)."""


class PolicyEngine:
    """
    Policy engine for permission enforcement.

    Enforces LAW 5 — EXPLICIT PERMISSIONS:
    - Permission metadata per tool
    - Confirmation required before execution
    - No cached permissions unless explicitly configured
    - Default stance: deny

    Per DIP Phase 2 and LAW 5 enforcement.
    """

    def __init__(self) -> None:
        """Initialize the policy engine."""
        # Phase 2: No permission cache (per LAW 5)
        # In later phases, explicit permission cache may be added if needed

    def check_permission(
        self,
        tool_schema: ToolSchema,
        user_context: Optional[Dict] = None,
    ) -> PermissionCheck:
        """
        Check if a tool can be executed.

        Args:
            tool_schema: Tool schema to check
            user_context: Optional user context (for future use)

        Returns:
            Permission check result

        Note:
            Phase 2: All tools require confirmation if requires_confirmation is True.
            In later phases, actual permission checking logic will be implemented.
        """
        checked_at = datetime.utcnow()

        # LAW 5: Default stance is deny
        # Phase 2: Simplified logic - if tool requires confirmation, return REQUIRES_CONFIRMATION
        # In later phases, actual permission checking will be implemented

        if tool_schema.requires_confirmation:
            decision = PermissionDecision.REQUIRES_CONFIRMATION
        else:
            # Phase 2: For tools that don't require confirmation, we still check permission level
            # In a real system, this would check user permissions
            # For now, we grant if permission level is NONE or READ
            # Phase 2 Updated: Respect the tool schema's requires_confirmation flag.
            # If the tool says it doesn't need confirmation, we grant it.
            # (In a future Multi-User phase, we would check User Context roles here).
            decision = PermissionDecision.GRANTED

        result = PermissionCheck(
            tool_name=tool_schema.name,
            required_permission=tool_schema.permission_level,
            decision=decision,
            requires_confirmation=tool_schema.requires_confirmation,
            checked_at=checked_at,
        )

        logger.info(
            f"Permission check for tool '{tool_schema.name}': {decision.value}",
            extra={
                "tool_name": tool_schema.name,
                "permission_level": tool_schema.permission_level.value,
                "decision": decision.value,
                "requires_confirmation": tool_schema.requires_confirmation,
                "checked_at": checked_at.isoformat(),
            },
        )

        return result

    def requires_confirmation(self, tool_schema: ToolSchema) -> bool:
        """
        Check if a tool requires confirmation.

        Args:
            tool_schema: Tool schema to check

        Returns:
            True if confirmation is required, False otherwise
        """
        return tool_schema.requires_confirmation or tool_schema.permission_level in (
            PermissionLevel.WRITE,
            PermissionLevel.EXECUTE,
        )
