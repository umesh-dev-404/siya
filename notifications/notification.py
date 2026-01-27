"""
Notification Model

Defines notification data structures.
Per Phase 15: Enhanced User Notifications.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional
from uuid import uuid4

logger = logging.getLogger(__name__)


class NotificationType(Enum):
    """Type of notification."""
    
    INFO = "info"           # Informational message
    SUCCESS = "success"     # Success confirmation
    WARNING = "warning"     # Warning requiring attention
    ERROR = "error"         # Error occurred
    ALERT = "alert"         # Urgent alert
    ACTION_REQUIRED = "action_required"  # User action needed


class Priority(Enum):
    """Notification priority level."""
    
    LOW = 1       # Can be reviewed later
    NORMAL = 2    # Standard priority
    HIGH = 3      # Should be seen soon
    URGENT = 4    # Immediate attention


class DeliveryStatus(Enum):
    """Delivery status of notification."""
    
    PENDING = "pending"       # Not yet delivered
    DELIVERED = "delivered"   # Delivered to channel
    READ = "read"             # Viewed by user
    ACKNOWLEDGED = "acknowledged"  # Explicitly acknowledged
    FAILED = "failed"         # Delivery failed


@dataclass
class Notification:
    """
    Represents a user notification.
    
    Notifications are:
    - Persisted to SQLite
    - Delivered via channels
    - Tracked for acknowledgment
    """
    
    # Core content
    title: str
    message: str
    notification_type: NotificationType = NotificationType.INFO
    priority: Priority = Priority.NORMAL
    
    # Identifiers
    notification_id: str = field(default_factory=lambda: str(uuid4())[:8])
    
    # Source tracking
    source: Optional[str] = None  # e.g., "automation:daily-check", "tool:trigger_sync"
    
    # Timestamps
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    delivered_at: Optional[str] = None
    read_at: Optional[str] = None
    acknowledged_at: Optional[str] = None
    
    # Status
    status: DeliveryStatus = DeliveryStatus.PENDING
    
    # Channel targeting (empty = all channels)
    target_channels: list = field(default_factory=list)
    
    # Additional data
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Action (optional action URL or tool call)
    action: Optional[str] = None
    
    def mark_delivered(self) -> None:
        """Mark notification as delivered."""
        self.status = DeliveryStatus.DELIVERED
        self.delivered_at = datetime.now().isoformat()
    
    def mark_read(self) -> None:
        """Mark notification as read."""
        if self.status not in (DeliveryStatus.READ, DeliveryStatus.ACKNOWLEDGED):
            self.status = DeliveryStatus.READ
            self.read_at = datetime.now().isoformat()
    
    def mark_acknowledged(self) -> None:
        """Mark notification as acknowledged."""
        self.status = DeliveryStatus.ACKNOWLEDGED
        self.acknowledged_at = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "notification_id": self.notification_id,
            "title": self.title,
            "message": self.message,
            "notification_type": self.notification_type.value,
            "priority": self.priority.value,
            "source": self.source,
            "created_at": self.created_at,
            "delivered_at": self.delivered_at,
            "read_at": self.read_at,
            "acknowledged_at": self.acknowledged_at,
            "status": self.status.value,
            "target_channels": self.target_channels,
            "metadata": self.metadata,
            "action": self.action,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Notification":
        """Create from dictionary."""
        return cls(
            notification_id=data.get("notification_id", str(uuid4())[:8]),
            title=data["title"],
            message=data["message"],
            notification_type=NotificationType(data.get("notification_type", "info")),
            priority=Priority(data.get("priority", 2)),
            source=data.get("source"),
            created_at=data.get("created_at", datetime.now().isoformat()),
            delivered_at=data.get("delivered_at"),
            read_at=data.get("read_at"),
            acknowledged_at=data.get("acknowledged_at"),
            status=DeliveryStatus(data.get("status", "pending")),
            target_channels=data.get("target_channels", []),
            metadata=data.get("metadata", {}),
            action=data.get("action"),
        )


# Factory functions for common notification types
def info_notification(title: str, message: str, source: Optional[str] = None) -> Notification:
    """Create an INFO notification."""
    return Notification(
        title=title,
        message=message,
        notification_type=NotificationType.INFO,
        priority=Priority.NORMAL,
        source=source,
    )


def success_notification(title: str, message: str, source: Optional[str] = None) -> Notification:
    """Create a SUCCESS notification."""
    return Notification(
        title=title,
        message=message,
        notification_type=NotificationType.SUCCESS,
        priority=Priority.NORMAL,
        source=source,
    )


def warning_notification(title: str, message: str, source: Optional[str] = None) -> Notification:
    """Create a WARNING notification."""
    return Notification(
        title=title,
        message=message,
        notification_type=NotificationType.WARNING,
        priority=Priority.HIGH,
        source=source,
    )


def error_notification(title: str, message: str, source: Optional[str] = None) -> Notification:
    """Create an ERROR notification."""
    return Notification(
        title=title,
        message=message,
        notification_type=NotificationType.ERROR,
        priority=Priority.HIGH,
        source=source,
    )


def alert_notification(title: str, message: str, source: Optional[str] = None) -> Notification:
    """Create an ALERT notification (urgent)."""
    return Notification(
        title=title,
        message=message,
        notification_type=NotificationType.ALERT,
        priority=Priority.URGENT,
        source=source,
    )


def action_required_notification(
    title: str,
    message: str,
    action: str,
    source: Optional[str] = None,
) -> Notification:
    """Create an ACTION_REQUIRED notification."""
    return Notification(
        title=title,
        message=message,
        notification_type=NotificationType.ACTION_REQUIRED,
        priority=Priority.URGENT,
        source=source,
        action=action,
    )
