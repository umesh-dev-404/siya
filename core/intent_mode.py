"""
Intent Mode

Explicit user intent mode system.
Enforces LAW 21 — USER-DECLARED INTENT SUPREMACY.

Per CONTINUATION_PLAN Phase 21: Explicit User Intent Modes.
"""

import logging
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)


class IntentMode(str, Enum):
    """
    User-declared intent posture.
    
    Per LAW 21 — USER-DECLARED INTENT SUPREMACY:
    - Intent posture must be explicitly declared, never inferred
    - May only constrain, never expand, permissions
    
    Modes:
    - INFORMATIONAL: Read-only queries, no side effects allowed
    - OPERATIONAL: Normal permission flow
    - DESTRUCTIVE: Extra confirmation required, highest restriction
    """
    
    INFORMATIONAL = "informational"
    """Read-only queries. No tool execution with side effects allowed."""
    
    OPERATIONAL = "operational"
    """Normal permission flow. Standard confirmation for side effects."""
    
    DESTRUCTIVE = "destructive"
    """Extra confirmation required. User explicitly signals destructive intent."""


# Default intent mode per LAW 21
DEFAULT_INTENT_MODE = IntentMode.INFORMATIONAL


class IntentModeValidator:
    """
    Validates and enforces intent mode constraints.
    
    Per LAW 21:
    - Intent mode must be explicitly declared
    - Must never be inferred by AI
    - May only constrain, never expand, permissions
    """
    
    # Tools that are incompatible with INFORMATIONAL mode
    # These tools have side effects and cannot be used in read-only mode
    WRITE_TOOLS = {
        # File tools
        "write_file", "delete_file", "create_directory",
        # Memory tools
        "write_memory", "delete_memory",
        # Sync tools
        "trigger_sync", "clear_sync_queue",
        # Timer tools
        "schedule_automation", "unschedule_automation", "enable_schedule", "disable_schedule",
        # Notification tools
        "acknowledge_notification", "acknowledge_all_notifications", 
        "clear_notifications", "send_notification",
        # Voice tools
        "speak_text",
        # Automation tools
        "create_automation", "delete_automation", "enable_automation", "disable_automation",
    }
    
    # Tools that require extra confirmation in DESTRUCTIVE mode
    DESTRUCTIVE_TOOLS = {
        "delete_file", "delete_memory", "clear_sync_queue",
        "unschedule_automation", "clear_notifications",
        "delete_automation", "trigger_sync",
    }
    
    @classmethod
    def validate_intent_mode(cls, mode_str: Optional[str]) -> IntentMode:
        """
        Validate and return intent mode.
        
        Args:
            mode_str: Intent mode string or None for default.
        
        Returns:
            Validated IntentMode enum value.
        
        Raises:
            ValueError: If mode_str is invalid.
        """
        if mode_str is None:
            logger.debug(f"Intent mode not specified, using default: {DEFAULT_INTENT_MODE.value}")
            return DEFAULT_INTENT_MODE
        
        try:
            mode = IntentMode(mode_str.lower())
            logger.debug(f"Intent mode validated: {mode.value}")
            return mode
        except ValueError:
            valid_modes = [m.value for m in IntentMode]
            raise ValueError(
                f"Invalid intent mode: '{mode_str}'. "
                f"Valid modes are: {valid_modes}"
            )
    
    @classmethod
    def is_tool_allowed(cls, tool_name: str, intent_mode: IntentMode) -> tuple[bool, Optional[str]]:
        """
        Check if tool is allowed in the given intent mode.
        
        Per LAW 21: Intent mode may only constrain, never expand, permissions.
        
        Args:
            tool_name: Name of the tool.
            intent_mode: Current intent mode.
        
        Returns:
            Tuple of (is_allowed, reason).
            If not allowed, reason explains why.
        """
        if intent_mode == IntentMode.INFORMATIONAL:
            # In INFORMATIONAL mode, block all write tools
            if tool_name in cls.WRITE_TOOLS:
                return False, (
                    f"Tool '{tool_name}' has side effects and is not allowed "
                    f"in 'informational' intent mode. Change to 'operational' or "
                    f"'destructive' mode to execute this tool."
                )
        
        # OPERATIONAL and DESTRUCTIVE modes allow all tools
        # (DESTRUCTIVE just adds extra confirmation, handled elsewhere)
        return True, None
    
    @classmethod
    def requires_extra_confirmation(cls, tool_name: str, intent_mode: IntentMode) -> bool:
        """
        Check if tool requires extra confirmation in the given intent mode.
        
        Args:
            tool_name: Name of the tool.
            intent_mode: Current intent mode.
        
        Returns:
            True if extra confirmation required, False otherwise.
        """
        if intent_mode == IntentMode.DESTRUCTIVE:
            # All destructive tools require extra confirmation
            return tool_name in cls.DESTRUCTIVE_TOOLS
        
        return False
    
    @classmethod
    def get_mode_restrictions(cls, intent_mode: IntentMode) -> dict:
        """
        Get restriction summary for an intent mode.
        
        Args:
            intent_mode: Intent mode to describe.
        
        Returns:
            Dict describing restrictions for this mode.
        """
        if intent_mode == IntentMode.INFORMATIONAL:
            return {
                "mode": intent_mode.value,
                "description": "Read-only queries only",
                "blocked_tools": list(cls.WRITE_TOOLS),
                "extra_confirmation": [],
            }
        elif intent_mode == IntentMode.OPERATIONAL:
            return {
                "mode": intent_mode.value,
                "description": "Normal permission flow",
                "blocked_tools": [],
                "extra_confirmation": [],
            }
        elif intent_mode == IntentMode.DESTRUCTIVE:
            return {
                "mode": intent_mode.value,
                "description": "Extra confirmation for destructive operations",
                "blocked_tools": [],
                "extra_confirmation": list(cls.DESTRUCTIVE_TOOLS),
            }
        
        return {"mode": "unknown", "description": "Unknown mode"}


def get_current_intent_mode() -> IntentMode:
    """
    Get the current default intent mode.
    
    In a real implementation, this would read from session state.
    For now, returns the default.
    """
    return DEFAULT_INTENT_MODE


def format_intent_mode_for_display(intent_mode: IntentMode) -> str:
    """
    Format intent mode for UI display.
    """
    mode_displays = {
        IntentMode.INFORMATIONAL: "📖 INFORMATIONAL (Read-Only)",
        IntentMode.OPERATIONAL: "⚙️ OPERATIONAL (Normal)",
        IntentMode.DESTRUCTIVE: "⚠️ DESTRUCTIVE (Extra Confirmation)",
    }
    return mode_displays.get(intent_mode, intent_mode.value)
