"""
Tests for System Module

Phase 8 tests for failure handling and resource monitoring.
Tests failure detection, state checking, and resource monitoring.
"""

from pathlib import Path

import pytest
from audit import AuditLogger
from memory import Database
from system import FailureHandler, FailureSeverity, FailureType, ResourceMonitor, StateChecker


class TestFailureHandler:
    """Tests for FailureHandler."""

    def test_failure_handler_initialization(self, tmp_path):
        """Test failure handler initialization."""
        db_path = tmp_path / "test.db"
        db = Database(str(db_path))
        db.connect()

        try:
            audit_logger = AuditLogger(db)
            handler = FailureHandler(audit_logger)
            assert handler is not None
        finally:
            db.close()

    def test_handle_failure(self, tmp_path):
        """Test handling a failure."""
        db_path = tmp_path / "test.db"
        db = Database(str(db_path))
        db.connect()

        try:
            audit_logger = AuditLogger(db)
            handler = FailureHandler(audit_logger)

            failure_id = handler.handle_failure(
                failure_type=FailureType.SYSTEM_ERROR,
                error_code="TEST_ERROR",
                error_message="Test error",
                severity=FailureSeverity.MEDIUM,
            )

            assert failure_id is not None
        finally:
            db.close()

    def test_handle_power_loss(self, tmp_path):
        """Test handling power loss."""
        db_path = tmp_path / "test.db"
        db = Database(str(db_path))
        db.connect()

        try:
            audit_logger = AuditLogger(db)
            handler = FailureHandler(audit_logger)

            failure_id = handler.handle_power_loss()
            assert failure_id is not None
        finally:
            db.close()

    def test_handle_network_loss(self, tmp_path):
        """Test handling network loss."""
        db_path = tmp_path / "test.db"
        db = Database(str(db_path))
        db.connect()

        try:
            audit_logger = AuditLogger(db)
            handler = FailureHandler(audit_logger)

            failure_id = handler.handle_network_loss()
            assert failure_id is not None
        finally:
            db.close()

    def test_handle_ai_crash(self, tmp_path):
        """Test handling AI crash."""
        db_path = tmp_path / "test.db"
        db = Database(str(db_path))
        db.connect()

        try:
            audit_logger = AuditLogger(db)
            handler = FailureHandler(audit_logger)

            failure_id = handler.handle_ai_crash()
            assert failure_id is not None
        finally:
            db.close()

    def test_handle_tool_failure(self, tmp_path):
        """Test handling tool failure."""
        db_path = tmp_path / "test.db"
        db = Database(str(db_path))
        db.connect()

        try:
            audit_logger = AuditLogger(db)
            handler = FailureHandler(audit_logger)

            failure_id = handler.handle_tool_failure(
                tool_name="test_tool",
                error_code="TOOL_ERROR",
                error_message="Tool failed",
            )
            assert failure_id is not None
        finally:
            db.close()

    def test_handle_resource_exhaustion(self, tmp_path):
        """Test handling resource exhaustion."""
        db_path = tmp_path / "test.db"
        db = Database(str(db_path))
        db.connect()

        try:
            audit_logger = AuditLogger(db)
            handler = FailureHandler(audit_logger)

            failure_id = handler.handle_resource_exhaustion("RAM")
            assert failure_id is not None
        finally:
            db.close()


class TestStateChecker:
    """Tests for StateChecker."""

    def test_state_checker_initialization(self, tmp_path):
        """Test state checker initialization."""
        db_path = tmp_path / "test.db"
        db = Database(str(db_path))
        db.connect()

        try:
            checker = StateChecker(db)
            assert checker is not None
        finally:
            db.close()

    def test_check_state_consistency(self, tmp_path):
        """Test state consistency checking."""
        db_path = tmp_path / "test.db"
        db = Database(str(db_path))
        db.connect()

        try:
            checker = StateChecker(db)
            result = checker.check_state_consistency()

            assert "consistent" in result
            assert "issues" in result
            assert isinstance(result["issues"], list)
        finally:
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
