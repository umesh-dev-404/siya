"""
Tests for Phase 21: Explicit User Intent Modes

Tests IntentMode enum and IntentModeValidator.
Enforces LAW 21 — USER-DECLARED INTENT SUPREMACY.
"""

import pytest
from core.intent_mode import (
    IntentMode,
    IntentModeValidator,
    DEFAULT_INTENT_MODE,
    get_current_intent_mode,
    format_intent_mode_for_display,
)


class TestIntentModeEnum:
    """Tests for IntentMode enum."""

    def test_informational_mode_exists(self):
        """Test that INFORMATIONAL mode is defined."""
        assert IntentMode.INFORMATIONAL.value == "informational"

    def test_operational_mode_exists(self):
        """Test that OPERATIONAL mode is defined."""
        assert IntentMode.OPERATIONAL.value == "operational"

    def test_destructive_mode_exists(self):
        """Test that DESTRUCTIVE mode is defined."""
        assert IntentMode.DESTRUCTIVE.value == "destructive"

    def test_default_mode_is_informational(self):
        """Per LAW 21: Default mode should be INFORMATIONAL (most restrictive)."""
        assert DEFAULT_INTENT_MODE == IntentMode.INFORMATIONAL


class TestIntentModeValidator:
    """Tests for IntentModeValidator class."""

    def test_validate_valid_mode_string(self):
        """Test validation of valid mode strings."""
        assert IntentModeValidator.validate_intent_mode("informational") == IntentMode.INFORMATIONAL
        assert IntentModeValidator.validate_intent_mode("operational") == IntentMode.OPERATIONAL
        assert IntentModeValidator.validate_intent_mode("destructive") == IntentMode.DESTRUCTIVE

    def test_validate_case_insensitive(self):
        """Test that validation is case-insensitive."""
        assert IntentModeValidator.validate_intent_mode("INFORMATIONAL") == IntentMode.INFORMATIONAL
        assert IntentModeValidator.validate_intent_mode("Operational") == IntentMode.OPERATIONAL

    def test_validate_none_returns_default(self):
        """Test that None returns default mode."""
        assert IntentModeValidator.validate_intent_mode(None) == DEFAULT_INTENT_MODE

    def test_validate_invalid_mode_raises_error(self):
        """Test that invalid mode raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            IntentModeValidator.validate_intent_mode("invalid_mode")
        
        assert "Invalid intent mode" in str(exc_info.value)

    def test_informational_blocks_write_tools(self):
        """Per LAW 21: INFORMATIONAL mode should block write tools."""
        write_tool = "write_file"
        
        allowed, reason = IntentModeValidator.is_tool_allowed(
            tool_name=write_tool,
            intent_mode=IntentMode.INFORMATIONAL,
        )
        
        assert allowed is False
        assert "side effects" in reason.lower()
        assert "informational" in reason.lower()

    def test_informational_allows_read_tools(self):
        """Per LAW 21: INFORMATIONAL mode should allow read tools."""
        read_tool = "get_system_status"
        
        allowed, reason = IntentModeValidator.is_tool_allowed(
            tool_name=read_tool,
            intent_mode=IntentMode.INFORMATIONAL,
        )
        
        assert allowed is True
        assert reason is None

    def test_operational_allows_all_tools(self):
        """Test that OPERATIONAL mode allows all tools."""
        write_tool = "write_file"
        
        allowed, reason = IntentModeValidator.is_tool_allowed(
            tool_name=write_tool,
            intent_mode=IntentMode.OPERATIONAL,
        )
        
        assert allowed is True
        assert reason is None

    def test_destructive_allows_all_tools(self):
        """Test that DESTRUCTIVE mode allows all tools (with extra confirmation)."""
        delete_tool = "delete_file"
        
        allowed, reason = IntentModeValidator.is_tool_allowed(
            tool_name=delete_tool,
            intent_mode=IntentMode.DESTRUCTIVE,
        )
        
        assert allowed is True
        assert reason is None

    def test_destructive_requires_extra_confirmation(self):
        """Test that DESTRUCTIVE mode requires extra confirmation for dangerous tools."""
        delete_tool = "delete_file"
        
        requires_extra = IntentModeValidator.requires_extra_confirmation(
            tool_name=delete_tool,
            intent_mode=IntentMode.DESTRUCTIVE,
        )
        
        assert requires_extra is True

    def test_operational_no_extra_confirmation(self):
        """Test that OPERATIONAL mode doesn't require extra confirmation."""
        delete_tool = "delete_file"
        
        requires_extra = IntentModeValidator.requires_extra_confirmation(
            tool_name=delete_tool,
            intent_mode=IntentMode.OPERATIONAL,
        )
        
        assert requires_extra is False

    def test_get_mode_restrictions_informational(self):
        """Test mode restrictions for INFORMATIONAL."""
        restrictions = IntentModeValidator.get_mode_restrictions(IntentMode.INFORMATIONAL)
        
        assert restrictions["mode"] == "informational"
        assert "read-only" in restrictions["description"].lower()
        assert len(restrictions["blocked_tools"]) > 0

    def test_get_mode_restrictions_operational(self):
        """Test mode restrictions for OPERATIONAL."""
        restrictions = IntentModeValidator.get_mode_restrictions(IntentMode.OPERATIONAL)
        
        assert restrictions["mode"] == "operational"
        assert len(restrictions["blocked_tools"]) == 0

    def test_get_mode_restrictions_destructive(self):
        """Test mode restrictions for DESTRUCTIVE."""
        restrictions = IntentModeValidator.get_mode_restrictions(IntentMode.DESTRUCTIVE)
        
        assert restrictions["mode"] == "destructive"
        assert len(restrictions["extra_confirmation"]) > 0


class TestIntentModeHelpers:
    """Tests for helper functions."""

    def test_get_current_intent_mode(self):
        """Test getting current intent mode."""
        mode = get_current_intent_mode()
        assert mode == DEFAULT_INTENT_MODE

    def test_format_for_display(self):
        """Test formatting intent mode for UI display."""
        info_display = format_intent_mode_for_display(IntentMode.INFORMATIONAL)
        assert "INFORMATIONAL" in info_display
        
        op_display = format_intent_mode_for_display(IntentMode.OPERATIONAL)
        assert "OPERATIONAL" in op_display
        
        dest_display = format_intent_mode_for_display(IntentMode.DESTRUCTIVE)
        assert "DESTRUCTIVE" in dest_display


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
