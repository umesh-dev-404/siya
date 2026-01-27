"""
Unit Tests for Sync Package

Tests for Supabase synchronization components:
- SupabaseClient
- SyncQueue
- SyncManager

Per Phase 13: Supabase Synchronization.
"""

import json
import os
import sqlite3
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


class TestSyncConfig:
    """Tests for SyncConfig."""

    def test_from_env_with_values(self):
        """Test loading config from environment."""
        from sync.supabase_client import SyncConfig

        with patch.dict(
            os.environ,
            {
                "SUPABASE_URL": "https://test.supabase.co",
                "SUPABASE_ANON_KEY": "test-key",
                "DEVICE_ID": "test-device",
                "SYNC_INTERVAL_SECONDS": "600",
                "SYNC_ENABLED": "true",
                "SYNC_MAX_RETRIES": "5",
            },
        ):
            config = SyncConfig.from_env()

            assert config.supabase_url == "https://test.supabase.co"
            assert config.supabase_anon_key == "test-key"
            assert config.device_id == "test-device"
            assert config.sync_interval_seconds == 600
            assert config.sync_enabled is True
            assert config.max_retries == 5

    def test_from_env_defaults(self):
        """Test config with default values."""
        from sync.supabase_client import SyncConfig

        with patch.dict(os.environ, {}, clear=True):
            config = SyncConfig.from_env()

            assert config.supabase_url == ""
            assert config.supabase_anon_key == ""
            # Device ID should be auto-generated
            assert len(config.device_id) > 0
            assert config.sync_interval_seconds == 300
            assert config.sync_enabled is True
            assert config.max_retries == 3

    def test_is_configured(self):
        """Test configuration check."""
        from sync.supabase_client import SyncConfig

        # Not configured
        config = SyncConfig(supabase_url="", supabase_anon_key="")
        assert config.is_configured() is False

        # Partially configured
        config = SyncConfig(supabase_url="https://test.co", supabase_anon_key="")
        assert config.is_configured() is False

        # Fully configured
        config = SyncConfig(
            supabase_url="https://test.co", supabase_anon_key="key123"
        )
        assert config.is_configured() is True


class TestSupabaseClient:
    """Tests for SupabaseClient."""

    def test_not_configured(self):
        """Test client behavior when not configured."""
        from sync.supabase_client import (
            ConnectionStatus,
            SupabaseClient,
            SyncConfig,
        )

        config = SyncConfig(supabase_url="", supabase_anon_key="")
        client = SupabaseClient(config=config)

        assert client.is_configured is False
        assert client.is_connected is False
        assert client.status == ConnectionStatus.DISCONNECTED

    def test_connection_info_no_secrets(self):
        """Test that connection info never exposes secrets (LAW 15)."""
        from sync.supabase_client import SupabaseClient, SyncConfig

        config = SyncConfig(
            supabase_url="https://test.co",
            supabase_anon_key="super-secret-key",
            device_id="device-123",
        )
        client = SupabaseClient(config=config)

        info = client.get_connection_info()

        # Should NOT contain the key
        assert "super-secret-key" not in str(info)
        assert "anon_key" not in info
        assert "supabase_anon_key" not in info

        # Should contain non-sensitive info
        assert info["device_id"] == "device-123"
        assert info["is_configured"] is True


class TestSyncQueue:
    """Tests for SyncQueue."""

    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test_sync_queue.db"
            yield db_path

    def test_enqueue_insert(self, temp_db):
        """Test enqueuing an insert operation."""
        from sync.sync_queue import OperationType, SyncQueue

        queue = SyncQueue(db_path=temp_db, device_id="test-device")

        op_id = queue.enqueue(
            operation_type=OperationType.INSERT,
            table_name="memory",
            record_id="rec-123",
            payload={"key": "test", "value": "data"},
        )

        assert op_id is not None
        assert len(op_id) > 0

        stats = queue.get_stats()
        assert stats["pending"] == 1
        assert stats["total"] == 1

        queue.close()

    def test_dequeue_and_complete(self, temp_db):
        """Test dequeuing and completing operations."""
        from sync.sync_queue import OperationType, SyncQueue

        queue = SyncQueue(db_path=temp_db, device_id="test-device")

        # Enqueue
        op_id = queue.enqueue(
            operation_type=OperationType.INSERT,
            table_name="memory",
            record_id="rec-123",
            payload={"key": "test"},
        )

        # Dequeue
        operations = queue.dequeue(batch_size=10)
        assert len(operations) == 1
        assert operations[0].id == op_id
        assert operations[0].record_id == "rec-123"

        # Mark completed
        queue.mark_completed(op_id)

        stats = queue.get_stats()
        assert stats["pending"] == 0
        assert stats["completed"] == 1

        queue.close()

    def test_deduplication_update(self, temp_db):
        """Test that updates deduplicate with pending operations."""
        from sync.sync_queue import OperationType, SyncQueue

        queue = SyncQueue(db_path=temp_db, device_id="test-device")

        # Enqueue insert
        queue.enqueue(
            operation_type=OperationType.INSERT,
            table_name="memory",
            record_id="rec-123",
            payload={"key": "test", "value": "v1"},
        )

        # Enqueue update for same record
        queue.enqueue(
            operation_type=OperationType.UPDATE,
            table_name="memory",
            record_id="rec-123",
            payload={"key": "test", "value": "v2"},
        )

        # Should only have 1 operation (deduplicated)
        stats = queue.get_stats()
        assert stats["pending"] == 1

        queue.close()

    def test_retry_count(self, temp_db):
        """Test retry count tracking."""
        from sync.sync_queue import OperationType, SyncQueue

        queue = SyncQueue(db_path=temp_db, device_id="test-device", max_retries=2)

        op_id = queue.enqueue(
            operation_type=OperationType.INSERT,
            table_name="memory",
            record_id="rec-123",
            payload={},
        )

        # Fail once
        queue.dequeue()
        queue.mark_failed(op_id, "Error 1")

        # Should still be pending (retry 1)
        ops = queue.dequeue()
        assert len(ops) == 1

        # Fail again
        queue.mark_failed(op_id, "Error 2")

        # Should now be failed (max retries reached)
        ops = queue.dequeue()
        assert len(ops) == 0

        stats = queue.get_stats()
        assert stats["failed"] == 1

        queue.close()


class TestSyncManager:
    """Tests for SyncManager."""

    def test_unauthorized_caller_rejected(self):
        """Test that unauthorized callers are rejected (LAW 8)."""
        from sync.sync_manager import SyncManager

        manager = SyncManager()

        # Unauthorized caller
        result = manager.push(caller="malicious_caller")
        assert result.success is False
        assert "Unauthorized" in result.errors[0]

    def test_authorized_callers_accepted(self):
        """Test that authorized callers are accepted (LAW 8)."""
        from sync.supabase_client import SyncConfig
        from sync.sync_manager import SyncManager

        # Create manager with unconfigured Supabase (will skip sync)
        from sync.supabase_client import SupabaseClient

        client = SupabaseClient(config=SyncConfig(supabase_url="", supabase_anon_key=""))
        manager = SyncManager(supabase=client)

        # These should be accepted (even though Supabase is not configured)
        result = manager.push(caller="orchestrator")
        assert result.success is True

        result = manager.push(caller="service_main")
        assert result.success is True

        result = manager.push(caller="sync_manager")
        assert result.success is True

    def test_sync_status(self):
        """Test sync status reporting."""
        from sync.sync_manager import SyncManager, SyncStatus

        manager = SyncManager()

        status = manager.get_sync_status()
        assert status["status"] == SyncStatus.IDLE.value
        assert "queue" in status
        assert "supabase" in status


class TestLawCompliance:
    """Tests for law compliance."""

    def test_law_15_no_secrets_in_logs(self):
        """Test LAW 15 - API keys never logged."""
        import logging
        from io import StringIO

        from sync.supabase_client import SupabaseClient, SyncConfig

        # Set up log capture
        log_stream = StringIO()
        handler = logging.StreamHandler(log_stream)
        handler.setLevel(logging.DEBUG)

        logger = logging.getLogger("sync.supabase_client")
        original_handlers = logger.handlers.copy()
        logger.handlers = [handler]
        logger.setLevel(logging.DEBUG)

        try:
            # Create client with secret key
            secret_key = "super-secret-api-key-12345"
            config = SyncConfig(
                supabase_url="https://test.co",
                supabase_anon_key=secret_key,
            )
            client = SupabaseClient(config=config)

            # Trigger some logging
            client.connect()  # Will fail but should log
            _ = client.get_connection_info()

            # Check logs don't contain secret
            log_contents = log_stream.getvalue()
            assert secret_key not in log_contents

        finally:
            logger.handlers = original_handlers

    def test_law_8_write_control(self):
        """Test LAW 8 - Only orchestrator can trigger sync."""
        from sync.sync_manager import SyncManager

        manager = SyncManager()

        # Unauthorized callers should fail
        unauthorized = ["ai", "tool", "user", "cli", "random"]
        for caller in unauthorized:
            result = manager.push(caller=caller)
            assert result.success is False
            assert "Unauthorized" in str(result.errors)
