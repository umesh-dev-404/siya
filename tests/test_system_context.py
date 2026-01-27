"""
Unit tests for SystemContext module.

Tests:
- Thread safety (LAW 10)
- Write permission enforcement (LAW 8)
- Read-only access for unauthorized callers (LAW 7)
- Execution history management
- Session lifecycle
"""

import pytest
import threading
import time
from uuid import uuid4
from core.system_context import SystemContext, get_system_context


class TestSystemContextSingleton:
    """Test singleton pattern and thread safety."""
    
    def setup_method(self):
        """Reset singleton before each test."""
        SystemContext.reset_instance()
    
    def test_singleton_returns_same_instance(self):
        """Verify singleton pattern returns same instance."""
        ctx1 = SystemContext()
        ctx2 = SystemContext()
        assert ctx1 is ctx2
    
    def test_get_system_context_returns_singleton(self):
        """Verify convenience function returns singleton."""
        ctx1 = get_system_context()
        ctx2 = get_system_context()
        assert ctx1 is ctx2
    
    def test_thread_safe_singleton_creation(self):
        """Test thread-safe singleton creation under concurrent access."""
        instances = []
        errors = []
        
        def get_instance():
            try:
                instances.append(SystemContext())
            except Exception as e:
                errors.append(e)
        
        threads = [threading.Thread(target=get_instance) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        assert len(errors) == 0
        assert len(instances) == 10
        # All instances should be the same object
        assert all(inst is instances[0] for inst in instances)


class TestWritePermissionEnforcement:
    """Test LAW 8 compliance - orchestrator-only writes."""
    
    def setup_method(self):
        SystemContext.reset_instance()
        self.ctx = get_system_context()
    
    def test_orchestrator_can_write(self):
        """Verify orchestrator can write to context."""
        # Should not raise
        self.ctx.start_session("test-session", caller="orchestrator")
        assert self.ctx.get_session() is not None
    
    def test_service_main_can_write(self):
        """Verify service_main can write to context."""
        self.ctx.start_session("test-session", caller="service_main")
        assert self.ctx.get_session() is not None
    
    def test_unauthorized_caller_cannot_write(self):
        """Verify unauthorized callers cannot write (LAW 8)."""
        with pytest.raises(PermissionError) as exc_info:
            self.ctx.start_session("test-session", caller="some_tool")
        
        assert "LAW 8 violation" in str(exc_info.value)
    
    def test_tool_cannot_record_execution(self):
        """Verify tools cannot record execution directly."""
        with pytest.raises(PermissionError):
            self.ctx.record_execution(
                tool_name="test_tool",
                arguments={},
                result_status="ok",
                caller="test_tool",
            )
    
    def test_ai_cannot_set_state(self):
        """Verify AI module cannot set state."""
        with pytest.raises(PermissionError):
            self.ctx.set_state("key", "value", caller="ai_module")


class TestSessionLifecycle:
    """Test session management."""
    
    def setup_method(self):
        SystemContext.reset_instance()
        self.ctx = get_system_context()
    
    def test_start_session(self):
        """Test session start."""
        self.ctx.start_session("session-123", caller="orchestrator")
        session = self.ctx.get_session()
        
        assert session is not None
        assert session.session_id == "session-123"
        assert session.started_at is not None
    
    def test_end_session_clears_state(self):
        """Test session end clears transient state."""
        self.ctx.start_session("session-123", caller="orchestrator")
        self.ctx.record_execution("tool", {}, "ok", caller="orchestrator")
        
        self.ctx.end_session(caller="orchestrator")
        
        assert self.ctx.get_session() is None
        assert len(self.ctx.get_execution_history()) == 0


class TestExecutionHistory:
    """Test tool execution history tracking."""
    
    def setup_method(self):
        SystemContext.reset_instance()
        self.ctx = get_system_context()
    
    def test_record_execution(self):
        """Test recording tool execution."""
        task_id = uuid4()
        self.ctx.record_execution(
            tool_name="test_tool",
            arguments={"arg1": "value1"},
            result_status="ok",
            task_id=task_id,
            execution_time_ms=150,
            caller="orchestrator",
        )
        
        history = self.ctx.get_execution_history()
        assert len(history) == 1
        assert history[0].tool_name == "test_tool"
        assert history[0].result_status == "ok"
    
    def test_history_limit_enforced(self):
        """Test MAX_EXECUTION_HISTORY limit is enforced."""
        # Record more than MAX_EXECUTION_HISTORY entries
        for i in range(150):
            self.ctx.record_execution(
                tool_name=f"tool_{i}",
                arguments={},
                result_status="ok",
                caller="orchestrator",
            )
        
        # Full history should be limited
        full_history = self.ctx._execution_history
        assert len(full_history) <= SystemContext.MAX_EXECUTION_HISTORY
    
    def test_sensitive_data_redacted(self):
        """Test sensitive arguments are redacted."""
        self.ctx.record_execution(
            tool_name="auth_tool",
            arguments={"password": "secret123", "api_key": "key123"},
            result_status="ok",
            caller="orchestrator",
        )
        
        history = self.ctx.get_execution_history()
        assert history[0].arguments["password"] == "[REDACTED]"
        assert history[0].arguments["api_key"] == "[REDACTED]"


class TestReadOnlyAccess:
    """Test LAW 7 compliance - context is non-authoritative."""
    
    def setup_method(self):
        SystemContext.reset_instance()
        self.ctx = get_system_context()
        self.ctx.start_session("test", caller="orchestrator")
    
    def test_get_session_returns_data(self):
        """Verify read access works."""
        session = self.ctx.get_session()
        assert session is not None
    
    def test_get_active_task_returns_copy(self):
        """Verify active task returns a copy (cannot modify original)."""
        self.ctx.set_active_task(
            task_id=uuid4(),
            task_type="test",
            metadata={"key": "value"},
            caller="orchestrator",
        )
        
        task = self.ctx.get_active_task()
        task["modified"] = True  # Modify the copy
        
        # Original should be unmodified
        original = self.ctx.get_active_task()
        assert "modified" not in original
    
    def test_context_snapshot(self):
        """Test context snapshot for AI injection."""
        self.ctx.set_config("model", "qwen", caller="orchestrator")
        
        snapshot = self.ctx.get_context_snapshot()
        
        assert "session" in snapshot
        assert "config_keys" in snapshot
        assert "model" in snapshot["config_keys"]


class TestConcurrentAccess:
    """Test thread safety under concurrent access."""
    
    def setup_method(self):
        SystemContext.reset_instance()
        self.ctx = get_system_context()
    
    def test_concurrent_reads_safe(self):
        """Test concurrent reads don't cause issues."""
        self.ctx.start_session("test", caller="orchestrator")
        errors = []
        
        def read_context():
            try:
                for _ in range(100):
                    self.ctx.get_session()
                    self.ctx.get_execution_history()
                    self.ctx.get_context_snapshot()
            except Exception as e:
                errors.append(e)
        
        threads = [threading.Thread(target=read_context) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        assert len(errors) == 0
    
    def test_concurrent_writes_safe(self):
        """Test concurrent writes are properly serialized."""
        errors = []
        
        def write_execution(thread_id):
            try:
                for i in range(20):
                    self.ctx.record_execution(
                        tool_name=f"tool_{thread_id}_{i}",
                        arguments={},
                        result_status="ok",
                        caller="orchestrator",
                    )
            except Exception as e:
                errors.append(e)
        
        threads = [threading.Thread(target=write_execution, args=(i,)) for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        assert len(errors) == 0
        # Should have 100 total entries (5 threads * 20 writes)
        # But limited to MAX_EXECUTION_HISTORY
        assert len(self.ctx._execution_history) == 100


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
