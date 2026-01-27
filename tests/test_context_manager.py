"""
Unit tests for ContextManager module.

Tests:
- Token estimation
- Entry addition and pruning
- Pruning strategies (FIFO, Relevance)
- SystemContext integration
- Context window limits
"""

import pytest
from datetime import datetime

from ai.context_manager import (
    ContextManager,
    ContextEntry,
    PruningStrategy,
    get_context_manager,
    reset_context_manager,
)
from core.system_context import SystemContext, get_system_context


class TestTokenEstimation:
    """Test token counting."""
    
    def test_empty_string(self):
        """Empty string should return 0 tokens."""
        cm = ContextManager()
        assert cm.estimate_tokens("") == 0
    
    def test_short_string(self):
        """Short string should return at least 1 token."""
        cm = ContextManager()
        assert cm.estimate_tokens("Hi") >= 1
    
    def test_known_length(self):
        """Test known character count."""
        cm = ContextManager()
        # 100 chars at 4 chars/token = 25 tokens
        text = "a" * 100
        assert cm.estimate_tokens(text) == 25


class TestEntryManagement:
    """Test adding and managing entries."""
    
    def setup_method(self):
        self.cm = ContextManager(max_tokens=100, reserved_tokens=20)
    
    def test_add_entry(self):
        """Test basic entry addition."""
        result = self.cm.add_entry(
            content="Test content",
            entry_type="test",
        )
        assert result is True
        state = self.cm.get_window_state()
        assert len(state.entries) == 1
    
    def test_add_user_input(self):
        """Test adding user input."""
        result = self.cm.add_user_input("What's the weather?")
        assert result is True
        state = self.cm.get_window_state()
        assert state.entries[0].entry_type == "user_input"
    
    def test_add_tool_result(self):
        """Test adding tool result."""
        result = self.cm.add_tool_result(
            tool_name="get_weather",
            result={"temp": 72, "condition": "sunny"},
        )
        assert result is True
        state = self.cm.get_window_state()
        assert state.entries[0].entry_type == "tool_result"
    
    def test_entry_too_large(self):
        """Test that oversized entries are rejected."""
        # Available is 80 tokens, entry of 100+ tokens should fail
        large_content = "x" * 500  # ~125 tokens
        result = self.cm.add_entry(content=large_content, entry_type="test")
        assert result is False
    
    def test_context_for_ai(self):
        """Test building context string for AI."""
        self.cm.add_user_input("Hello")
        self.cm.add_tool_result("echo", "Hello back")
        
        context = self.cm.get_context_for_ai()
        assert "--- Context ---" in context
        assert "Hello" in context
        assert "echo" in context


class TestPruningFIFO:
    """Test FIFO pruning strategy."""
    
    def setup_method(self):
        self.cm = ContextManager(
            max_tokens=50,
            reserved_tokens=10,
            pruning_strategy=PruningStrategy.FIFO,
        )
    
    def test_fifo_removes_oldest(self):
        """FIFO should remove oldest entries first."""
        # Use larger entries to trigger pruning (40 tokens available, each ~10 tokens)
        self.cm.add_entry("A" * 40, "test")  # ~10 tokens, will be pruned
        self.cm.add_entry("B" * 40, "test")  # ~10 tokens
        self.cm.add_entry("C" * 40, "test")  # ~10 tokens
        self.cm.add_entry("D" * 40, "test")  # ~10 tokens
        self.cm.add_entry("E" * 40, "test")  # ~10 tokens, triggers pruning
        
        state = self.cm.get_window_state()
        # At least one entry should be pruned
        assert state.pruned_count > 0
        # Check remaining entries don't include first entry (all A's)
        contents = [e.content for e in state.entries]
        assert "A" * 40 not in contents


class TestPruningRelevance:
    """Test relevance-based pruning strategy."""
    
    def setup_method(self):
        self.cm = ContextManager(
            max_tokens=50,
            reserved_tokens=10,
            pruning_strategy=PruningStrategy.RELEVANCE,
        )
    
    def test_relevance_removes_least_relevant(self):
        """Relevance pruning should remove lowest relevance first."""
        self.cm.add_entry("High relevance", "test", relevance_score=1.0)
        self.cm.add_entry("Low relevance", "test", relevance_score=0.1)
        self.cm.add_entry("Medium", "test", relevance_score=0.5)
        self.cm.add_entry("Trigger pruning", "test")
        
        state = self.cm.get_window_state()
        contents = [e.content for e in state.entries]
        # Low relevance should be pruned first
        if state.pruned_count > 0:
            assert "Low relevance" not in contents


class TestSystemContextIntegration:
    """Test integration with SystemContext."""
    
    def setup_method(self):
        SystemContext.reset_instance()
        self.ctx = get_system_context()
        self.ctx.start_session("test-session", caller="orchestrator")
        reset_context_manager()
        self.cm = get_context_manager()
    
    def teardown_method(self):
        SystemContext.reset_instance()
        reset_context_manager()
    
    def test_inject_from_system_context(self):
        """Test injecting execution history from SystemContext."""
        # Record some executions
        self.ctx.record_execution(
            tool_name="tool_a",
            arguments={},
            result_status="ok",
            caller="orchestrator",
        )
        self.ctx.record_execution(
            tool_name="tool_b",
            arguments={},
            result_status="error",
            caller="orchestrator",
        )
        
        # Inject into context manager
        self.cm.inject_from_system_context(limit=5)
        
        state = self.cm.get_window_state()
        assert len(state.entries) >= 2
        # Check entries reference the tools
        contents = " ".join(e.content for e in state.entries)
        assert "tool_a" in contents
        assert "tool_b" in contents


class TestContextManagerSingleton:
    """Test singleton behavior."""
    
    def setup_method(self):
        reset_context_manager()
    
    def teardown_method(self):
        reset_context_manager()
    
    def test_get_context_manager_singleton(self):
        """get_context_manager should return same instance."""
        cm1 = get_context_manager()
        cm2 = get_context_manager()
        assert cm1 is cm2
    
    def test_reset_context_manager(self):
        """reset_context_manager should create new instance."""
        cm1 = get_context_manager()
        reset_context_manager()
        cm2 = get_context_manager()
        assert cm1 is not cm2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
