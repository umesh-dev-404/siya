"""
Notification Manager

Orchestrates notification creation, storage, and delivery.
Per Phase 15: Enhanced User Notifications.

LAW Compliance:
- LAW 12: Failures become notifications
- LAW 13: All notifications logged
"""

import logging
from typing import Any, Dict, List, Optional

from notifications.notification import (
    Notification,
    NotificationType,
    Priority,
    DeliveryStatus,
    info_notification,
    warning_notification,
    error_notification,
    alert_notification,
)
from notifications.notification_store import NotificationStore, get_notification_store
from notifications.channels.base import Channel
from notifications.channels.console import ConsoleChannel
from notifications.channels.file import FileChannel

logger = logging.getLogger(__name__)


class NotificationManager:
    """
    Manages notification lifecycle.
    
    Responsibilities:
    - Create and store notifications
    - Route to appropriate channels
    - Track delivery and acknowledgment
    - Provide notification API
    
    LAW Compliance:
    - LAW 12: System failures generate notifications
    - LAW 13: All notifications persisted
    """
    
    def __init__(
        self,
        store: Optional[NotificationStore] = None,
        channels: Optional[List[Channel]] = None,
    ) -> None:
        """
        Initialize notification manager.
        
        Args:
            store: Notification store (default: singleton)
            channels: Delivery channels (default: console + file)
        """
        self._store = store or get_notification_store()
        
        if channels is None:
            self._channels = [
                ConsoleChannel(),
                FileChannel(),
            ]
        else:
            self._channels = channels
        
        logger.info(
            "NotificationManager initialized",
            extra={"channels": [c.name for c in self._channels]},
        )
    
    def notify(
        self,
        title: str,
        message: str,
        notification_type: NotificationType = NotificationType.INFO,
        priority: Priority = Priority.NORMAL,
        source: Optional[str] = None,
        action: Optional[str] = None,
        target_channels: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Notification:
        """
        Create and deliver a notification.
        
        Args:
            title: Notification title
            message: Notification message
            notification_type: Type of notification
            priority: Priority level
            source: Source identifier
            action: Optional action URL or tool call
            target_channels: Specific channels (None = all)
            metadata: Additional metadata
            
        Returns:
            Created notification
        """
        notification = Notification(
            title=title,
            message=message,
            notification_type=notification_type,
            priority=priority,
            source=source,
            action=action,
            target_channels=target_channels or [],
            metadata=metadata or {},
        )
        
        # Persist first (LAW 13)
        self._store.save(notification)
        
        # Deliver to channels
        self._deliver(notification)
        
        return notification
    
    def notify_info(self, title: str, message: str, source: Optional[str] = None) -> Notification:
        """Send an INFO notification."""
        return self.notify(
            title=title,
            message=message,
            notification_type=NotificationType.INFO,
            priority=Priority.NORMAL,
            source=source,
        )
    
    def notify_success(self, title: str, message: str, source: Optional[str] = None) -> Notification:
        """Send a SUCCESS notification."""
        return self.notify(
            title=title,
            message=message,
            notification_type=NotificationType.SUCCESS,
            priority=Priority.NORMAL,
            source=source,
        )
    
    def notify_warning(self, title: str, message: str, source: Optional[str] = None) -> Notification:
        """Send a WARNING notification."""
        return self.notify(
            title=title,
            message=message,
            notification_type=NotificationType.WARNING,
            priority=Priority.HIGH,
            source=source,
        )
    
    def notify_error(self, title: str, message: str, source: Optional[str] = None) -> Notification:
        """Send an ERROR notification (LAW 12)."""
        return self.notify(
            title=title,
            message=message,
            notification_type=NotificationType.ERROR,
            priority=Priority.HIGH,
            source=source,
        )
    
    def notify_alert(self, title: str, message: str, source: Optional[str] = None) -> Notification:
        """Send an ALERT notification (urgent)."""
        return self.notify(
            title=title,
            message=message,
            notification_type=NotificationType.ALERT,
            priority=Priority.URGENT,
            source=source,
        )
    
    def notify_action_required(
        self,
        title: str,
        message: str,
        action: str,
        source: Optional[str] = None,
    ) -> Notification:
        """Send an ACTION_REQUIRED notification."""
        return self.notify(
            title=title,
            message=message,
            notification_type=NotificationType.ACTION_REQUIRED,
            priority=Priority.URGENT,
            source=source,
            action=action,
        )
    
    def _deliver(self, notification: Notification) -> None:
        """Deliver notification to channels."""
        target_channels = notification.target_channels
        delivered = False
        
        for channel in self._channels:
            # Skip if targeting specific channels
            if target_channels and channel.name not in target_channels:
                continue
            
            if not channel.is_available():
                logger.debug(f"Channel {channel.name} not available")
                continue
            
            try:
                if channel.deliver(notification):
                    delivered = True
            except Exception as e:
                logger.error(f"Delivery failed on {channel.name}: {e}")
        
        if delivered:
            notification.mark_delivered()
            self._store.save(notification)
    
    def get_notifications(
        self,
        status: Optional[DeliveryStatus] = None,
        notification_type: Optional[NotificationType] = None,
        unread_only: bool = False,
        limit: int = 50,
    ) -> List[Notification]:
        """Get notifications with filters."""
        return self._store.list_notifications(
            status=status,
            notification_type=notification_type,
            unread_only=unread_only,
            limit=limit,
        )
    
    def get_unread_count(self) -> int:
        """Get count of unread notifications."""
        return self._store.get_unread_count()
    
    def mark_read(self, notification_id: str) -> bool:
        """Mark notification as read."""
        return self._store.update_status(notification_id, DeliveryStatus.READ)
    
    def acknowledge(self, notification_id: str) -> bool:
        """Acknowledge a notification."""
        return self._store.update_status(notification_id, DeliveryStatus.ACKNOWLEDGED)
    
    def acknowledge_all(self) -> int:
        """Acknowledge all unread notifications."""
        notifications = self._store.list_notifications(unread_only=True)
        count = 0
        for n in notifications:
            if self._store.update_status(n.notification_id, DeliveryStatus.ACKNOWLEDGED):
                count += 1
        return count
    
    def delete_notification(self, notification_id: str) -> bool:
        """Delete a notification."""
        return self._store.delete(notification_id)
    
    def cleanup(self, days: int = 30) -> int:
        """Cleanup old notifications (LAW 14)."""
        return self._store.cleanup_old(days=days)
    
    def add_channel(self, channel: Channel) -> None:
        """Add a delivery channel."""
        self._channels.append(channel)
        logger.info(f"Added notification channel: {channel.name}")
    
    def remove_channel(self, channel_name: str) -> bool:
        """Remove a delivery channel by name."""
        for i, channel in enumerate(self._channels):
            if channel.name == channel_name:
                del self._channels[i]
                return True
        return False


# Singleton instance
_default_manager: Optional[NotificationManager] = None


def get_notification_manager() -> NotificationManager:
    """Get or create the default notification manager."""
    global _default_manager
    if _default_manager is None:
        _default_manager = NotificationManager()
    return _default_manager


def reset_notification_manager() -> None:
    """Reset the notification manager (for testing)."""
    global _default_manager
    _default_manager = None
