"""
Notification Store

SQLite persistence for notifications.
Per Phase 15: Enhanced User Notifications.

LAW Compliance:
- LAW 13: All notifications logged
- LAW 14: Retention policy enforced
"""

import json
import logging
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from notifications.notification import (
    Notification,
    NotificationType,
    Priority,
    DeliveryStatus,
)

logger = logging.getLogger(__name__)


class NotificationStore:
    """
    SQLite-backed notification persistence.
    
    Features:
    - Store notifications with full metadata
    - Query by status, type, priority
    - Cleanup old notifications (LAW 14)
    - Thread-safe operations
    """
    
    def __init__(self, db_path: Optional[Path] = None) -> None:
        """
        Initialize the notification store.
        
        Args:
            db_path: Path to SQLite database
        """
        self._db_path = db_path or Path("./notifications.db")
        self._init_database()
        
        logger.info(
            "NotificationStore initialized",
            extra={"db_path": str(self._db_path)},
        )
    
    def _init_database(self) -> None:
        """Initialize the notifications database."""
        conn = sqlite3.connect(str(self._db_path))
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS notifications (
                notification_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                message TEXT NOT NULL,
                notification_type TEXT NOT NULL,
                priority INTEGER NOT NULL,
                source TEXT,
                created_at TEXT NOT NULL,
                delivered_at TEXT,
                read_at TEXT,
                acknowledged_at TEXT,
                status TEXT NOT NULL,
                target_channels TEXT,
                metadata TEXT,
                action TEXT
            )
        """)
        
        # Create indexes for common queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_notifications_status
            ON notifications(status)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_notifications_created
            ON notifications(created_at)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_notifications_priority
            ON notifications(priority DESC)
        """)
        
        conn.commit()
        conn.close()
    
    def save(self, notification: Notification) -> None:
        """
        Save a notification.
        
        Args:
            notification: Notification to save
        """
        conn = sqlite3.connect(str(self._db_path))
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO notifications (
                notification_id, title, message, notification_type,
                priority, source, created_at, delivered_at, read_at,
                acknowledged_at, status, target_channels, metadata, action
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            notification.notification_id,
            notification.title,
            notification.message,
            notification.notification_type.value,
            notification.priority.value,
            notification.source,
            notification.created_at,
            notification.delivered_at,
            notification.read_at,
            notification.acknowledged_at,
            notification.status.value,
            json.dumps(notification.target_channels),
            json.dumps(notification.metadata),
            notification.action,
        ))
        
        conn.commit()
        conn.close()
        
        logger.debug(f"Notification saved: {notification.notification_id}")
    
    def get(self, notification_id: str) -> Optional[Notification]:
        """
        Get a notification by ID.
        
        Args:
            notification_id: Notification ID
            
        Returns:
            Notification or None if not found
        """
        conn = sqlite3.connect(str(self._db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT * FROM notifications WHERE notification_id = ?",
            (notification_id,)
        )
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        return self._row_to_notification(row)
    
    def list_notifications(
        self,
        status: Optional[DeliveryStatus] = None,
        notification_type: Optional[NotificationType] = None,
        priority_min: Optional[Priority] = None,
        limit: int = 50,
        unread_only: bool = False,
    ) -> List[Notification]:
        """
        List notifications with filters.
        
        Args:
            status: Filter by status
            notification_type: Filter by type
            priority_min: Minimum priority
            limit: Maximum results
            unread_only: Only unread notifications
            
        Returns:
            List of notifications
        """
        conn = sqlite3.connect(str(self._db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        query = "SELECT * FROM notifications WHERE 1=1"
        params: List[Any] = []
        
        if status:
            query += " AND status = ?"
            params.append(status.value)
        
        if notification_type:
            query += " AND notification_type = ?"
            params.append(notification_type.value)
        
        if priority_min:
            query += " AND priority >= ?"
            params.append(priority_min.value)
        
        if unread_only:
            query += " AND status NOT IN ('read', 'acknowledged')"
        
        query += " ORDER BY priority DESC, created_at DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        return [self._row_to_notification(row) for row in rows]
    
    def get_unread_count(self) -> int:
        """Get count of unread notifications."""
        conn = sqlite3.connect(str(self._db_path))
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT COUNT(*) FROM notifications
            WHERE status NOT IN ('read', 'acknowledged')
        """)
        
        count = cursor.fetchone()[0]
        conn.close()
        
        return count
    
    def update_status(
        self,
        notification_id: str,
        status: DeliveryStatus,
    ) -> bool:
        """
        Update notification status.
        
        Args:
            notification_id: Notification ID
            status: New status
            
        Returns:
            True if updated
        """
        notification = self.get(notification_id)
        if not notification:
            return False
        
        notification.status = status
        now = datetime.now().isoformat()
        
        if status == DeliveryStatus.DELIVERED:
            notification.delivered_at = now
        elif status == DeliveryStatus.READ:
            notification.read_at = now
        elif status == DeliveryStatus.ACKNOWLEDGED:
            notification.acknowledged_at = now
        
        self.save(notification)
        return True
    
    def delete(self, notification_id: str) -> bool:
        """
        Delete a notification.
        
        Args:
            notification_id: Notification ID
            
        Returns:
            True if deleted
        """
        conn = sqlite3.connect(str(self._db_path))
        cursor = conn.cursor()
        
        cursor.execute(
            "DELETE FROM notifications WHERE notification_id = ?",
            (notification_id,)
        )
        
        deleted = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return deleted
    
    def cleanup_old(self, days: int = 30) -> int:
        """
        Delete old notifications (LAW 14).
        
        Args:
            days: Delete notifications older than this
            
        Returns:
            Number of deleted notifications
        """
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        
        conn = sqlite3.connect(str(self._db_path))
        cursor = conn.cursor()
        
        cursor.execute("""
            DELETE FROM notifications
            WHERE created_at < ? AND status = 'acknowledged'
        """, (cutoff,))
        
        deleted = cursor.rowcount
        conn.commit()
        conn.close()
        
        logger.info(f"Cleaned up {deleted} old notifications")
        return deleted
    
    def clear_all(self, acknowledged_only: bool = True) -> int:
        """
        Clear notifications.
        
        Args:
            acknowledged_only: Only clear acknowledged notifications
            
        Returns:
            Number of deleted notifications
        """
        conn = sqlite3.connect(str(self._db_path))
        cursor = conn.cursor()
        
        if acknowledged_only:
            cursor.execute(
                "DELETE FROM notifications WHERE status = 'acknowledged'"
            )
        else:
            cursor.execute("DELETE FROM notifications")
        
        deleted = cursor.rowcount
        conn.commit()
        conn.close()
        
        return deleted
    
    def _row_to_notification(self, row: sqlite3.Row) -> Notification:
        """Convert database row to Notification."""
        return Notification(
            notification_id=row["notification_id"],
            title=row["title"],
            message=row["message"],
            notification_type=NotificationType(row["notification_type"]),
            priority=Priority(row["priority"]),
            source=row["source"],
            created_at=row["created_at"],
            delivered_at=row["delivered_at"],
            read_at=row["read_at"],
            acknowledged_at=row["acknowledged_at"],
            status=DeliveryStatus(row["status"]),
            target_channels=json.loads(row["target_channels"] or "[]"),
            metadata=json.loads(row["metadata"] or "{}"),
            action=row["action"],
        )
    
    def close(self) -> None:
        """Clean up resources."""
        pass  # SQLite connections are per-operation


# Singleton instance
_default_store: Optional[NotificationStore] = None


def get_notification_store(db_path: Optional[Path] = None) -> NotificationStore:
    """Get or create the default notification store."""
    global _default_store
    if _default_store is None:
        _default_store = NotificationStore(db_path=db_path)
    return _default_store


def reset_notification_store() -> None:
    """Reset the notification store (for testing)."""
    global _default_store
    _default_store = None
