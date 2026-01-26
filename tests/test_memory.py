"""
Tests for Memory Module

Phase 3 tests for memory and observability.
Tests memory access, writes, summarization, and audit logging.
"""

import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pytest
from audit.audit_logger import AuditLogger
from memory.access_layer import MemoryAccessLayer
from memory.database import Database
from memory.database_schema import MemoryTier
from memory.memory_manager import MemoryManager
from memory.write_controller import WriteController


class TestDatabase:
    """Tests for Database."""

    def test_database_connection(self):
        """Test database connection and schema initialization."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            db = Database(str(db_path))
            db.connect()

            # Verify WAL mode is enabled
            conn = db.get_connection()
            cursor = conn.cursor()
            cursor.execute("PRAGMA journal_mode;")
            journal_mode = cursor.fetchone()[0]
            assert journal_mode.upper() == "WAL"

            # Verify tables exist
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;"
            )
            tables = [row[0] for row in cursor.fetchall()]
            assert "memory" in tables
            assert "audit_log" in tables
            assert "log_summary" in tables

            db.close()

    def test_context_manager(self):
        """Test database context manager."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            with Database(str(db_path)) as db:
                conn = db.get_connection()
                assert conn is not None


class TestMemoryAccessLayer:
    """Tests for MemoryAccessLayer (LAW 7)."""

    def test_read_memory_empty(self):
        """Test reading from empty memory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            db = Database(str(db_path))
            db.connect()

            access_layer = MemoryAccessLayer(db)
            results = access_layer.read_memory()

            assert results == []
            db.close()

    def test_read_memory_by_key(self):
        """Test reading memory by key."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            db = Database(str(db_path))
            db.connect()

            # Write memory first
            write_controller = WriteController(db, "ORCHESTRATOR")
            memory_id = write_controller.write_memory(
                key="test_key",
                value="test_value",
                memory_tier=MemoryTier.L2,
            )

            # Read it back
            access_layer = MemoryAccessLayer(db)
            results = access_layer.read_memory(key="test_key")

            assert len(results) == 1
            assert results[0]["key"] == "test_key"
            assert results[0]["value"] == "test_value"

            db.close()


class TestWriteController:
    """Tests for WriteController (LAW 8)."""

    def test_only_orchestrator_can_write(self):
        """Test that only orchestrator can create WriteController."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            db = Database(str(db_path))
            db.connect()

            # Orchestrator can create
            controller = WriteController(db, "ORCHESTRATOR")
            assert controller is not None

            # Others cannot
            with pytest.raises(ValueError, match="Only ORCHESTRATOR"):
                WriteController(db, "AI")

            with pytest.raises(ValueError, match="Only ORCHESTRATOR"):
                WriteController(db, "TOOL")

            db.close()

    def test_write_memory(self):
        """Test writing memory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            db = Database(str(db_path))
            db.connect()

            controller = WriteController(db, "ORCHESTRATOR")
            memory_id = controller.write_memory(
                key="test_key",
                value="test_value",
                memory_tier=MemoryTier.L2,
                confidence=0.9,
                source_request_id="test_request_id",
                source_type="user_input",
            )

            assert memory_id is not None

            # Verify it was written
            conn = db.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM memory WHERE id = ?", (memory_id,))
            row = cursor.fetchone()
            assert row is not None

            db.close()

    def test_write_from_suggestion(self):
        """Test writing memory from suggestion."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            db = Database(str(db_path))
            db.connect()

            controller = WriteController(db, "ORCHESTRATOR")

            suggestion = {
                "memory_tier": "L2",
                "content": {"key": "test_key", "value": "test_value"},
                "confidence": 0.8,
                "lineage": {
                    "source_request_id": "test_request",
                    "source_type": "intent_parsing",
                },
                "suggested_by": "AI",
            }

            memory_id = controller.write_from_suggestion(suggestion)
            assert memory_id is not None

            db.close()


class TestAuditLogger:
    """Tests for AuditLogger (LAW 13, LAW 14)."""

    def test_log_event(self):
        """Test logging an audit event."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            db = Database(str(db_path))
            db.connect()

            logger = AuditLogger(db)
            log_id = logger.log_event(
                event_type="TOOL_REQUESTED",
                event_data={"tool_name": "test_tool"},
                correlation_id="test_correlation",
                request_id="test_request",
            )

            assert log_id is not None

            # Verify it was logged
            conn = db.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM audit_log WHERE id = ?", (log_id,))
            row = cursor.fetchone()
            assert row is not None

            db.close()

    def test_invalid_event_type(self):
        """Test that invalid event types are rejected."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            db = Database(str(db_path))
            db.connect()

            logger = AuditLogger(db)

            with pytest.raises(ValueError, match="Invalid event_type"):
                logger.log_event(
                    event_type="INVALID_EVENT",
                    event_data={},
                    correlation_id="test",
                )

            db.close()

    def test_get_events_by_correlation_id(self):
        """Test retrieving events by correlation ID."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            db = Database(str(db_path))
            db.connect()

            logger = AuditLogger(db)
            correlation_id = "test_correlation"

            # Log multiple events
            logger.log_event(
                event_type="USER_INPUT",
                event_data={},
                correlation_id=correlation_id,
            )
            logger.log_event(
                event_type="INTENT_PARSED",
                event_data={},
                correlation_id=correlation_id,
            )

            # Retrieve by correlation ID
            events = logger.get_events_by_correlation_id(correlation_id)
            assert len(events) == 2

            db.close()


class TestMemoryManager:
    """Tests for MemoryManager."""

    def test_memory_manager_initialization(self):
        """Test memory manager initialization."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            db = Database(str(db_path))
            db.connect()

            manager = MemoryManager(db)

            assert manager.get_access_layer() is not None
            assert manager.get_write_controller() is not None
            assert manager.get_audit_logger() is not None
            assert manager.get_supabase_sync() is not None

            db.close()

    def test_memory_read_write_flow(self):
        """Test complete memory read/write flow."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            db = Database(str(db_path))
            db.connect()

            manager = MemoryManager(db)

            # Write memory
            write_controller = manager.get_write_controller()
            memory_id = write_controller.write_memory(
                key="test_key",
                value="test_value",
                memory_tier=MemoryTier.L2,
            )

            # Read memory
            access_layer = manager.get_access_layer()
            results = access_layer.read_memory(key="test_key")

            assert len(results) == 1
            assert results[0]["id"] == memory_id

            db.close()


class TestSupabaseSync:
    """Tests for SupabaseSync (stub)."""

    def test_supabase_sync_stub(self):
        """Test that Supabase sync is stubbed."""
        from memory.supabase_sync import SupabaseSync

        sync = SupabaseSync()
        assert sync.is_enabled() is False

        # Stub should always succeed
        result = sync.sync_memory({"id": "test", "key": "test_key"})
        assert result is True
