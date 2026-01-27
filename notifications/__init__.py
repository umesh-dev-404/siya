"""
Notifications Package

User notification system with multi-channel delivery, persistence, and acknowledgment.
Per Phase 15: Enhanced User Notifications.

LAW Compliance:
- LAW 1: User controls notification settings
- LAW 12: Failures become notifications
- LAW 13: All notifications logged
- LAW 14: Retention policy enforced
"""

from notifications.notification import (
    Notification,
    NotificationType,
    Priority,
    DeliveryStatus,
)
from notifications.notification_store import NotificationStore, get_notification_store
from notifications.notification_manager import NotificationManager, get_notification_manager

__all__ = [
    "Notification",
    "NotificationType",
    "Priority",
    "DeliveryStatus",
    "NotificationStore",
    "get_notification_store",
    "NotificationManager",
    "get_notification_manager",
]
