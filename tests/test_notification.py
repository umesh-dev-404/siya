"""
Unit Tests for Phase 15 Notification System

Tests for:
- Notification Model
- Notification Store
- Channels
- Notification Manager
- Notification Tools
"""

import json
import os
import sqlite3
import tempfile
from datetime import datetime, timedelta
from io import StringIO
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


class TestNotificationModel:
    """Tests for Notification dataclass."""

    def test_create_notification(self):
        """Test creating a notification."""
        from notifications.notification import Notification, NotificationType, Priority
        
        n = Notification(
            title="Test",
            message="Test message",
            notification_type=NotificationType.INFO,
            priority=Priority.NORMAL,
        )
        
        assert n.title == "Test"
        assert n.message == "Test message"
        assert n.notification_type == NotificationType.INFO
        assert n.notification_id is not None

    def test_mark_delivered(self):
        """Test marking notification as delivered."""
        from notifications.notification import Notification, DeliveryStatus
        
        n = Notification(title="Test", message="Test")
        assert n.status == DeliveryStatus.PENDING
        
        n.mark_delivered()
        
        assert n.status == DeliveryStatus.DELIVERED
        assert n.delivered_at is not None

    def test_mark_acknowledged(self):
        """Test marking notification as acknowledged."""
        from notifications.notification import Notification, DeliveryStatus
        
        n = Notification(title="Test", message="Test")
        n.mark_acknowledged()
        
        assert n.status == DeliveryStatus.ACKNOWLEDGED
        assert n.acknowledged_at is not None

    def test_to_dict_and_from_dict(self):
        """Test serialization round-trip."""
        from notifications.notification import Notification, NotificationType, Priority
        
        n = Notification(
            title="Test",
            message="Test message",
            notification_type=NotificationType.WARNING,
            priority=Priority.HIGH,
            source="test",
        )
        
        data = n.to_dict()
        n2 = Notification.from_dict(data)
        
        assert n2.title == n.title
        assert n2.message == n.message
        assert n2.notification_type == n.notification_type
        assert n2.priority == n.priority

    def test_factory_functions(self):
        """Test notification factory functions."""
        from notifications.notification import (
            info_notification,
            warning_notification,
            error_notification,
            alert_notification,
            NotificationType,
            Priority,
        )
        
        info = info_notification("Info", "Info message")
        assert info.notification_type == NotificationType.INFO
        
        warning = warning_notification("Warning", "Warning message")
        assert warning.notification_type == NotificationType.WARNING
        assert warning.priority == Priority.HIGH
        
        error = error_notification("Error", "Error message")
        assert error.notification_type == NotificationType.ERROR
        
        alert = alert_notification("Alert", "Alert message")
        assert alert.notification_type == NotificationType.ALERT
        assert alert.priority == Priority.URGENT


class TestNotificationStore:
    """Tests for NotificationStore."""

    @pytest.fixture
    def temp_db(self):
        """Create temporary database."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            yield Path(f.name)
        os.unlink(f.name)

    @pytest.fixture
    def store(self, temp_db):
        """Create store with temp db."""
        from notifications.notification_store import NotificationStore
        
        return NotificationStore(db_path=temp_db)

    def test_save_and_get(self, store):
        """Test saving and retrieving notification."""
        from notifications.notification import Notification
        
        n = Notification(title="Test", message="Test message")
        store.save(n)
        
        retrieved = store.get(n.notification_id)
        
        assert retrieved is not None
        assert retrieved.title == "Test"
        assert retrieved.message == "Test message"

    def test_list_notifications(self, store):
        """Test listing notifications."""
        from notifications.notification import Notification, NotificationType
        
        store.save(Notification(title="Info", message="M", notification_type=NotificationType.INFO))
        store.save(Notification(title="Warning", message="M", notification_type=NotificationType.WARNING))
        store.save(Notification(title="Error", message="M", notification_type=NotificationType.ERROR))
        
        all_notes = store.list_notifications()
        assert len(all_notes) == 3
        
        warnings = store.list_notifications(notification_type=NotificationType.WARNING)
        assert len(warnings) == 1

    def test_update_status(self, store):
        """Test updating notification status."""
        from notifications.notification import Notification, DeliveryStatus
        
        n = Notification(title="Test", message="Test")
        store.save(n)
        
        store.update_status(n.notification_id, DeliveryStatus.ACKNOWLEDGED)
        
        updated = store.get(n.notification_id)
        assert updated.status == DeliveryStatus.ACKNOWLEDGED

    def test_delete(self, store):
        """Test deleting notification."""
        from notifications.notification import Notification
        
        n = Notification(title="Test", message="Test")
        store.save(n)
        
        store.delete(n.notification_id)
        
        assert store.get(n.notification_id) is None

    def test_cleanup_old(self, store):
        """Test cleaning up old notifications."""
        from notifications.notification import Notification, DeliveryStatus
        
        n = Notification(title="Old", message="Old notification")
        n.status = DeliveryStatus.ACKNOWLEDGED
        # Manually set old date
        n.created_at = (datetime.now() - timedelta(days=60)).isoformat()
        store.save(n)
        
        cleaned = store.cleanup_old(days=30)
        
        assert cleaned == 1


class TestConsoleChannel:
    """Tests for ConsoleChannel."""

    def test_deliver(self):
        """Test console delivery."""
        from notifications.channels.console import ConsoleChannel
        from notifications.notification import Notification
        
        output = StringIO()
        channel = ConsoleChannel(output=output, use_colors=False)
        
        n = Notification(title="Test", message="Test message")
        result = channel.deliver(n)
        
        assert result is True
        assert "Test" in output.getvalue()
        assert "Test message" in output.getvalue()

    def test_is_available(self):
        """Test console availability."""
        from notifications.channels.console import ConsoleChannel
        
        channel = ConsoleChannel()
        assert channel.is_available() is True


class TestFileChannel:
    """Tests for FileChannel."""

    @pytest.fixture
    def temp_file(self):
        """Create temporary file."""
        with tempfile.NamedTemporaryFile(suffix=".log", delete=False) as f:
            yield Path(f.name)
        if Path(f.name).exists():
            os.unlink(f.name)

    def test_deliver_json(self, temp_file):
        """Test file delivery in JSON format."""
        from notifications.channels.file import FileChannel
        from notifications.notification import Notification
        
        channel = FileChannel(file_path=temp_file, format="json")
        n = Notification(title="Test", message="Test message")
        
        result = channel.deliver(n)
        
        assert result is True
        
        with open(temp_file) as f:
            line = f.readline()
            data = json.loads(line)
            assert data["notification"]["title"] == "Test"

    def test_deliver_text(self, temp_file):
        """Test file delivery in text format."""
        from notifications.channels.file import FileChannel
        from notifications.notification import Notification
        
        channel = FileChannel(file_path=temp_file, format="text")
        n = Notification(title="Test", message="Test message")
        
        result = channel.deliver(n)
        
        assert result is True
        
        with open(temp_file) as f:
            line = f.readline()
            assert "Test" in line
            assert "Test message" in line


class TestNotificationManager:
    """Tests for NotificationManager."""

    @pytest.fixture
    def temp_db(self):
        """Create temporary database."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            yield Path(f.name)
        os.unlink(f.name)

    @pytest.fixture
    def manager(self, temp_db):
        """Create manager with temp db."""
        from notifications.notification_store import NotificationStore
        from notifications.notification_manager import NotificationManager
        from notifications.channels.console import ConsoleChannel
        
        store = NotificationStore(db_path=temp_db)
        output = StringIO()
        channels = [ConsoleChannel(output=output, use_colors=False)]
        
        return NotificationManager(store=store, channels=channels)

    def test_notify(self, manager):
        """Test sending notification."""
        from notifications.notification import DeliveryStatus
        
        n = manager.notify(title="Test", message="Test message")
        
        assert n.title == "Test"
        assert n.status == DeliveryStatus.DELIVERED

    def test_notify_error(self, manager):
        """Test sending error notification."""
        from notifications.notification import NotificationType
        
        n = manager.notify_error("Error", "Error message")
        
        assert n.notification_type == NotificationType.ERROR

    def test_get_unread_count(self, manager):
        """Test getting unread count."""
        manager.notify(title="Test1", message="Message")
        manager.notify(title="Test2", message="Message")
        
        count = manager.get_unread_count()
        
        # Delivered but not read
        assert count == 2

    def test_acknowledge(self, manager):
        """Test acknowledging notification."""
        from notifications.notification import DeliveryStatus
        
        n = manager.notify(title="Test", message="Message")
        manager.acknowledge(n.notification_id)
        
        notifications = manager.get_notifications(unread_only=True)
        assert len(notifications) == 0


class TestNotificationTools:
    """Tests for notification tools."""

    @pytest.fixture
    def temp_db(self):
        """Create temporary database."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            yield Path(f.name)
        os.unlink(f.name)

    def test_list_notifications(self, temp_db):
        """Test list_notifications tool."""
        from notifications.notification_store import NotificationStore, reset_notification_store
        from notifications.notification_manager import NotificationManager, reset_notification_manager
        from tools.notification_tools import list_notifications
        
        reset_notification_store()
        reset_notification_manager()
        
        with patch('notifications.notification_store.get_notification_store') as mock_get_store:
            with patch('notifications.notification_manager.get_notification_manager') as mock_get_mgr:
                mock_mgr = MagicMock()
                mock_mgr.get_notifications.return_value = []
                mock_mgr.get_unread_count.return_value = 0
                mock_get_mgr.return_value = mock_mgr
                
                result = list_notifications()
        
        assert result["success"] is True

    def test_send_notification(self, temp_db):
        """Test send_notification tool."""
        from tools.notification_tools import send_notification
        
        with patch('notifications.notification_manager.get_notification_manager') as mock_get_mgr:
            mock_mgr = MagicMock()
            mock_notification = MagicMock()
            mock_notification.notification_id = "test-123"
            mock_notification.status.value = "delivered"
            mock_mgr.notify.return_value = mock_notification
            mock_get_mgr.return_value = mock_mgr
            
            result = send_notification(title="Test", message="Test message")
        
        assert result["success"] is True

    def test_clear_requires_confirmation(self):
        """Test that clear_notifications requires confirmation (LAW 1)."""
        from tools.notification_tools import NOTIFICATION_TOOL_SCHEMAS
        
        clear_tool = next(
            t for t in NOTIFICATION_TOOL_SCHEMAS if t["name"] == "clear_notifications"
        )
        
        assert clear_tool["requires_confirmation"] is True


class TestLawCompliance:
    """Tests for LAW compliance in notification system."""

    def test_law_13_all_notifications_persisted(self):
        """Test LAW 13: All notifications are persisted."""
        from notifications.notification_store import NotificationStore
        from notifications.notification_manager import NotificationManager
        from notifications.channels.console import ConsoleChannel
        
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = Path(f.name)
        
        try:
            store = NotificationStore(db_path=db_path)
            output = StringIO()
            manager = NotificationManager(
                store=store,
                channels=[ConsoleChannel(output=output, use_colors=False)]
            )
            
            # Send notification
            n = manager.notify(title="Test", message="Test")
            
            # Verify persisted
            retrieved = store.get(n.notification_id)
            assert retrieved is not None
            
        finally:
            os.unlink(db_path)

    def test_law_14_retention_enforced(self):
        """Test LAW 14: Retention policy via cleanup."""
        from notifications.notification_store import NotificationStore
        from notifications.notification import Notification, DeliveryStatus
        
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = Path(f.name)
        
        try:
            store = NotificationStore(db_path=db_path)
            
            # Create old acknowledged notification
            n = Notification(title="Old", message="Old")
            n.status = DeliveryStatus.ACKNOWLEDGED
            n.created_at = (datetime.now() - timedelta(days=60)).isoformat()
            store.save(n)
            
            # Cleanup should remove it
            cleaned = store.cleanup_old(days=30)
            assert cleaned >= 1
            
        finally:
            os.unlink(db_path)
