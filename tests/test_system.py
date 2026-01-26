"""
Tests for System Module

Phase 8 tests for failure handling and resource monitoring.
Tests failure detection, state checking, and resource monitoring.
"""

import tempfile
from pathlib import Path

import pytest
from audit import AuditLogger
from memory import Database
from system import FailureHandler, FailureSeverity, FailureType, ResourceMonitor, StateChecker


class TestFailureHandler:
    """Tests for FailureHandler."""

    def test_failure_handler_initialization(self):
        """Test failure handler initialization."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            db = Database(str(db_path))
            db.connect()

            audit_logger = AuditLogger(db)
            handler = FailureHandler(audit_logger)

            assert handler is not None

            db.close()

    def test_handle_failure(self):
        """Test handling a failure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            db = Database(str(db_path))
            db.connect()

            audit_logger = AuditLogger(db)
            handler = FailureHandler(audit_logger)

            failure_id = handler.handle_failure(
                failure_type=FailureType.SYSTEM_ERROR,
                error_code="TEST_ERROR",
                error_message="Test error",
                severity=FailureSeverity.MEDIUM,
            )

            assert failure_id is not None

            db.close()

    def test_handle_power_loss(self):
        """Test handling power loss."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            db = Database(str(db_path))
            db.connect()

            audit_logger = AuditLogger(db)
            handler = FailureHandler(audit_logger)

            failure_id = handler.handle_power_loss()
            assert failure_id is not None

            db.close()

    def test_handle_network_loss(self):
        """Test handling network loss."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            db = Database(str(db_path))
            db.connect()

            audit_logger = AuditLogger(db)
            handler = FailureHandler(audit_logger)

            failure_id = handler.handle_network_loss()
            assert failure_id is not None

            db.close()

    def test_handle_ai_crash(self):
        """Test handling AI crash."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            db = Database(str(db_path))
            db.connect()

            audit_logger = AuditLogger(db)
            handler = FailureHandler(audit_logger)

            failure_id = handler.handle_ai_crash()
            assert failure_id is not None

            db.close()

    def test_handle_tool_failure(self):
        """Test handling tool failure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            db = Database(str(db_path))
            db.connect()

            audit_logger = AuditLogger(db)
            handler = FailureHandler(audit_logger)

            failure_id = handler.handle_tool_failure(
                tool_name="test_tool",
                error_code="TOOL_ERROR",
                error_message="Tool failed",
            )
            assert failure_id is not None

            db.close()

    def test_handle_resource_exhaustion(self):
        """Test handling resource exhaustion."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            db = Database(str(db_path))
            db.connect()

            audit_logger = AuditLogger(db)
            handler = FailureHandler(audit_logger)

            failure_id = handler.handle_resource_exhaustion("RAM")
            assert failure_id is not None

            db.close()


class TestStateChecker:
    """Tests for StateChecker."""

    def test_state_checker_initialization(self):
        """Test state checker initialization."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            db = Database(str(db_path))
            db.connect()

            checker = StateChecker(db)
            assert checker is not None

            db.close()

    def test_check_state_consistency(self):
        """Test state consistency checking."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            db = Database(str(db_path))
            db.connect()

            checker = StateChecker(db)
            result = checker.check_state_consistency()

            assert "consistent" in result
            assert "issues" in result
            assert isinstance(result["issues"], list)

            db.close()


class TestResourceMonitor:
    """Tests for ResourceMonitor."""

    def test_resource_monitor_initialization(self):
        """Test resource monitor initialization."""
        monitor = ResourceMonitor()
        assert monitor is not None

    def test_check_resources(self):
        """Test resource checking."""
        monitor = ResourceMonitor()
        status = monitor.check_resources()

        assert "ram_usage" in status
        assert "cpu_usage" in status
        assert "disk_usage" in status
        assert "healthy" in status

    def test_is_healthy(self):
        """Test health check."""
        monitor = ResourceMonitor()
        healthy = monitor.is_healthy()

        assert isinstance(healthy, bool)
