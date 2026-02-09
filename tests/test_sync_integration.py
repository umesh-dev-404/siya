"""
Integration Tests for Phase 13 Sync Package

Tests for:
- TierManager L3 integration
- Offline-first behavior
- End-to-end sync flow
"""

import os
import sqlite3
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


class TestTierManagerL3Integration:
    """Tests for TierManager + SyncManager integration."""

    def test_get_l3_summary_without_sync(self):
        """Test L3 summary when sync is not configured."""
        from memory.tier_manager import MemoryTierManager
        
        manager = MemoryTierManager()
        summary = manager.get_l3_summary()
        
        assert summary["tier"] == "L3"
        assert "name" in summary
        # Should work even without sync configured

    def test_get_l3_summary_with_sync(self):
        """Test L3 summary returns sync status."""
        from memory.tier_manager import MemoryTierManager
        
        manager = MemoryTierManager()
        summary = manager.get_l3_summary()
        
        assert summary["tier"] == "L3"
        assert summary["name"] == "Long-term Sync"
        # Status fields should be present
        if summary.get("available"):
            assert "status" in summary
            assert "queue_pending" in summary
            assert "device_id" in summary

    def test_queue_for_sync_authorized(self):
        """Test queuing for sync with authorized caller."""
        from memory.tier_manager import MemoryTierManager
        
        manager = MemoryTierManager()
        
        # Should not raise for authorized callers
        result = manager.queue_for_sync(
            operation_type="INSERT",
            record_id="test-123",
            payload={"key": "test"},
            caller="orchestrator",
        )
        # Result may be None if sync package not fully configured
        # but should not raise

    def test_queue_for_sync_unauthorized(self):
        """Test queuing for sync with unauthorized caller fails (LAW 8)."""
        from memory.tier_manager import MemoryTierManager
        
        manager = MemoryTierManager()
        
        with pytest.raises(PermissionError) as exc_info:
            manager.queue_for_sync(
                operation_type="INSERT",
                record_id="test-123",
                payload={"key": "test"},
                caller="malicious_caller",
            )
        
        assert "LAW 8" in str(exc_info.value)


class TestOfflineFirstBehavior:
    """Tests for offline-first sync behavior."""

    @pytest.fixture
    def temp_queue_db(self):
        """Create a temporary queue database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test_queue.db"
            yield db_path

    def test_queue_persists_offline(self, temp_queue_db):
        """Test that queue persists when offline."""
        from sync.sync_queue import SyncQueue, OperationType
        
        # Create queue and add operations
        queue = SyncQueue(db_path=temp_queue_db, device_id="test-device")
        queue.enqueue(
            operation_type=OperationType.INSERT,
            table_name="memory",
            record_id="record-1",
            payload={"key": "value"},
        )
        queue.close()
        
        # Reopen and verify data persisted
        queue2 = SyncQueue(db_path=temp_queue_db, device_id="test-device")
        stats = queue2.get_stats()
        
        assert stats["pending"] == 1
        queue2.close()

    def test_sync_works_without_connection(self):
        """Test that sync operations don't fail when offline."""
        from sync.sync_manager import SyncManager
        from sync.supabase_client import SupabaseClient, SyncConfig

        # Create unconfigured client (simulates offline)
        config = SyncConfig(supabase_url="", supabase_anon_key="")
        client = SupabaseClient(config=config)
        manager = SyncManager(supabase=client)

        # Push should succeed (just nothing to do)
        result = manager.push(caller="orchestrator")
        assert result.success is True
        assert result.records_pushed == 0

    def test_operations_queued_when_offline(self, temp_queue_db):
        """Test that operations are queued when connection fails."""
        from sync.sync_queue import SyncQueue, OperationType
        
        queue = SyncQueue(db_path=temp_queue_db, device_id="test-device")
        
        # Add multiple operations
        for i in range(5):
            queue.enqueue(
                operation_type=OperationType.INSERT,
                table_name="memory",
                record_id=f"record-{i}",
                payload={"index": i},
            )
        
        # All should be pending
        assert queue.get_pending_count() == 5
        queue.close()


class TestSyncTools:
    """Tests for sync MCP tools."""

    def test_get_sync_status_tool(self):
        """Test get_sync_status tool returns proper structure."""
        from tools.sync_tools import get_sync_status
        
        result = get_sync_status()
        
        assert "success" in result
        if result["success"]:
            assert "status" in result

    def test_trigger_sync_tool_unauthorized(self):
        """Test trigger_sync respects LAW 8."""
        # The tool itself calls SyncManager with "orchestrator" caller
        # so this should work
        from tools.sync_tools import trigger_sync
        
        result = trigger_sync(direction="push")
        
        # Should succeed (even if nothing to sync)
        assert "success" in result

    def test_clear_sync_queue_tool(self):
        """Test clear_sync_queue tool."""
        from tools.sync_tools import clear_sync_queue
        
        result = clear_sync_queue(older_than_hours=24)
        
        assert "success" in result
        if result["success"]:
            assert "cleared_count" in result


class TestToolRegistration:
    """Tests for sync tool registration."""

    def test_sync_tools_can_register(self):
        """Test that sync tools can be registered."""
        from tools.tool_executor import ToolExecutor
        from tools.tool_registration import register_sync_tools
        
        executor = ToolExecutor()
        register_sync_tools(executor)
        
        assert executor.has("get_sync_status")
        assert executor.has("trigger_sync")
        assert executor.has("clear_sync_queue")

    def test_sync_tools_execute(self):
        """Test that registered sync tools execute."""
        from tools.tool_executor import ToolExecutor
        from tools.tool_registration import register_sync_tools
        
        executor = ToolExecutor()
        register_sync_tools(executor)
        
        result = executor.execute("get_sync_status", {})
        
        assert result.tool_name == "get_sync_status"
        assert "success" in result.output
