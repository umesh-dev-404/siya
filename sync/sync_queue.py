"""
Sync Queue - Offline-First Operation Queue

Queues sync operations locally for processing when connection is available.
Per Phase 13: Supabase Synchronization.

LAW Compliance:
- LAW 13: All queue operations logged
- LAW 16: Offline-first design (never blocks on network)

Features:
- SQLite-backed persistence (survives restart)
- Operation deduplication
- FIFO processing with retry tracking
"""

import json
import logging
import os
import sqlite3
import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Final, Optional


def _default_sync_queue_db_path() -> Path:
    """Sync queue DB path: SIYA_DATA_DIR/sync_queue.db when set (align with onboarding), else data/sync_queue.db."""
    data_dir = os.getenv("SIYA_DATA_DIR", "data")
    return Path(data_dir).expanduser() / "sync_queue.db"

logger = logging.getLogger(__name__)


class OperationType(str, Enum):
    """Sync operation types."""

    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"


class OperationStatus(str, Enum):
    """Queue operation status."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class QueueOperation:
    """A queued sync operation."""

    id: str
    operation_type: OperationType
    table_name: str
    record_id: str
    payload: dict[str, Any]
    device_id: str
    queued_at: datetime
    status: OperationStatus = OperationStatus.PENDING
    processed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    retry_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for database storage."""
        return {
            "id": self.id,
            "operation_type": self.operation_type.value,
            "table_name": self.table_name,
            "record_id": self.record_id,
            "payload": json.dumps(self.payload),
            "device_id": self.device_id,
            "queued_at": self.queued_at.isoformat(),
            "status": self.status.value,
            "processed_at": (
                self.processed_at.isoformat() if self.processed_at else None
            ),
            "error_message": self.error_message,
            "retry_count": self.retry_count,
        }

    @classmethod
    def from_row(cls, row: tuple) -> "QueueOperation":
        """Create from database row."""
        return cls(
            id=row[0],
            operation_type=OperationType(row[1]),
            table_name=row[2],
            record_id=row[3],
            payload=json.loads(row[4]) if row[4] else {},
            device_id=row[5],
            queued_at=datetime.fromisoformat(row[6]),
            status=OperationStatus(row[7]),
            processed_at=(
                datetime.fromisoformat(row[8]) if row[8] else None
            ),
            error_message=row[9],
            retry_count=row[10],
        )


# Queue table schema
SYNC_QUEUE_SCHEMA: Final[str] = """
CREATE TABLE IF NOT EXISTS sync_queue (
    id TEXT PRIMARY KEY,
    operation_type TEXT NOT NULL CHECK(operation_type IN ('INSERT', 'UPDATE', 'DELETE')),
    table_name TEXT NOT NULL CHECK(table_name IN ('memory', 'audit_log', 'log_summary')),
    record_id TEXT NOT NULL,
    payload TEXT NOT NULL,
    device_id TEXT NOT NULL,
    queued_at TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending', 'processing', 'completed', 'failed')),
    processed_at TEXT,
    error_message TEXT,
    retry_count INTEGER NOT NULL DEFAULT 0
);
"""

SYNC_QUEUE_INDEXES: Final[list[str]] = [
    "CREATE INDEX IF NOT EXISTS idx_sync_queue_status ON sync_queue(status);",
    "CREATE INDEX IF NOT EXISTS idx_sync_queue_queued_at ON sync_queue(queued_at);",
    "CREATE INDEX IF NOT EXISTS idx_sync_queue_record_id ON sync_queue(record_id);",
]


@dataclass
class SyncQueue:
    """
    Offline-first sync queue backed by SQLite.

    Features:
    - Persists operations across restarts
    - Deduplicates redundant operations
    - FIFO processing order
    - Retry tracking

    LAW 13: All operations logged.
    LAW 16: Offline-first (queue locally, sync when available).
    """

    db_path: Path = field(default_factory=_default_sync_queue_db_path)
    device_id: str = ""
    max_retries: int = 3
    _conn: Optional[sqlite3.Connection] = field(default=None, repr=False)
    _lock: threading.RLock = field(default_factory=threading.RLock, repr=False)

    def __post_init__(self) -> None:
        """Initialize database after dataclass creation."""
        self._ensure_database()

    def _ensure_database(self) -> None:
        """Ensure database and tables exist."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        with self._lock:
            conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute(SYNC_QUEUE_SCHEMA)
            for index_sql in SYNC_QUEUE_INDEXES:
                conn.execute(index_sql)
            conn.commit()
            self._conn = conn

        logger.info(f"Sync queue initialized: {self.db_path}")

    def close(self) -> None:
        """Close database connection."""
        with self._lock:
            if self._conn:
                self._conn.close()
                self._conn = None

    # ==========================================
    # Enqueue Operations
    # ==========================================

    def enqueue(
        self,
        operation_type: OperationType,
        table_name: str,
        record_id: str,
        payload: dict[str, Any],
    ) -> str:
        """
        Enqueue a sync operation.

        Args:
            operation_type: Type of operation (INSERT, UPDATE, DELETE)
            table_name: Target table (memory, audit_log, log_summary)
            record_id: ID of the record
            payload: Operation payload

        Returns:
            Queue operation ID

        LAW 13: Operation logged.
        """
        operation = QueueOperation(
            id=str(uuid.uuid4()),
            operation_type=operation_type,
            table_name=table_name,
            record_id=record_id,
            payload=payload,
            device_id=self.device_id,
            queued_at=datetime.now(timezone.utc),
        )

        with self._lock:
            # Check for existing pending operation on same record
            # (deduplication)
            cursor = self._conn.execute(
                """
                SELECT id FROM sync_queue
                WHERE record_id = ? AND status = 'pending'
                ORDER BY queued_at DESC LIMIT 1
                """,
                (record_id,),
            )
            existing = cursor.fetchone()

            if existing and operation_type in (
                OperationType.UPDATE,
                OperationType.DELETE,
            ):
                # Update existing pending operation
                self._conn.execute(
                    """
                    UPDATE sync_queue
                    SET operation_type = ?, payload = ?, queued_at = ?
                    WHERE id = ?
                    """,
                    (
                        operation_type.value,
                        json.dumps(payload),
                        operation.queued_at.isoformat(),
                        existing[0],
                    ),
                )
                self._conn.commit()
                logger.debug(
                    f"Updated existing queue operation: {existing[0]} -> {operation_type.value}"
                )
                return existing[0]

            # Insert new operation
            data = operation.to_dict()
            self._conn.execute(
                """
                INSERT INTO sync_queue (
                    id, operation_type, table_name, record_id, payload,
                    device_id, queued_at, status, retry_count
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    data["id"],
                    data["operation_type"],
                    data["table_name"],
                    data["record_id"],
                    data["payload"],
                    data["device_id"],
                    data["queued_at"],
                    data["status"],
                    data["retry_count"],
                ),
            )
            self._conn.commit()

        logger.debug(
            f"Queued sync operation: {operation.id} ({operation_type.value} {table_name})"
        )
        return operation.id

    # ==========================================
    # Dequeue Operations
    # ==========================================

    def dequeue(self, batch_size: int = 10) -> list[QueueOperation]:
        """
        Dequeue pending operations for processing.

        Args:
            batch_size: Maximum operations to dequeue

        Returns:
            List of operations to process
        """
        operations: list[QueueOperation] = []

        with self._lock:
            cursor = self._conn.execute(
                """
                SELECT id, operation_type, table_name, record_id, payload,
                       device_id, queued_at, status, processed_at, error_message, retry_count
                FROM sync_queue
                WHERE status = 'pending' AND retry_count < ?
                ORDER BY queued_at ASC
                LIMIT ?
                """,
                (self.max_retries, batch_size),
            )

            rows = cursor.fetchall()
            for row in rows:
                operations.append(QueueOperation.from_row(row))

            # Mark as processing
            if operations:
                ids = [op.id for op in operations]
                placeholders = ",".join("?" * len(ids))
                self._conn.execute(
                    f"""
                    UPDATE sync_queue
                    SET status = 'processing'
                    WHERE id IN ({placeholders})
                    """,
                    ids,
                )
                self._conn.commit()

        return operations

    def mark_completed(self, operation_id: str) -> None:
        """Mark an operation as completed."""
        with self._lock:
            self._conn.execute(
                """
                UPDATE sync_queue
                SET status = 'completed', processed_at = ?
                WHERE id = ?
                """,
                (datetime.now(timezone.utc).isoformat(), operation_id),
            )
            self._conn.commit()

        logger.debug(f"Queue operation completed: {operation_id}")

    def mark_failed(
        self, operation_id: str, error_message: str
    ) -> None:
        """Mark an operation as failed with error."""
        with self._lock:
            # Increment retry count
            self._conn.execute(
                """
                UPDATE sync_queue
                SET status = CASE
                    WHEN retry_count + 1 >= ? THEN 'failed'
                    ELSE 'pending'
                END,
                retry_count = retry_count + 1,
                error_message = ?,
                processed_at = ?
                WHERE id = ?
                """,
                (
                    self.max_retries,
                    error_message,
                    datetime.now(timezone.utc).isoformat(),
                    operation_id,
                ),
            )
            self._conn.commit()

        logger.warning(f"Queue operation failed: {operation_id} - {error_message}")

    def requeue_processing(self) -> int:
        """
        Requeue any operations stuck in 'processing' state.
        Called on startup to handle interrupted operations.

        Returns:
            Number of requeued operations
        """
        with self._lock:
            cursor = self._conn.execute(
                """
                UPDATE sync_queue
                SET status = 'pending'
                WHERE status = 'processing'
                """
            )
            self._conn.commit()
            count = cursor.rowcount

        if count > 0:
            logger.info(f"Requeued {count} interrupted sync operations")

        return count

    # ==========================================
    # Queue Status
    # ==========================================

    def get_stats(self) -> dict[str, int]:
        """Get queue statistics."""
        stats = {
            "pending": 0,
            "processing": 0,
            "completed": 0,
            "failed": 0,
            "total": 0,
        }

        with self._lock:
            cursor = self._conn.execute(
                """
                SELECT status, COUNT(*) FROM sync_queue GROUP BY status
                """
            )
            for row in cursor.fetchall():
                stats[row[0]] = row[1]

            stats["total"] = sum(stats.values())

        return stats

    def get_pending_count(self) -> int:
        """Get count of pending operations."""
        with self._lock:
            cursor = self._conn.execute(
                "SELECT COUNT(*) FROM sync_queue WHERE status = 'pending'"
            )
            return cursor.fetchone()[0]

    def clear_completed(self, older_than_hours: int = 24) -> int:
        """
        Clear completed operations older than specified hours.

        Args:
            older_than_hours: Clear operations older than this

        Returns:
            Number of cleared operations
        """
        cutoff = datetime.now(timezone.utc)
        # Subtract hours (simple calculation)
        from datetime import timedelta

        cutoff = cutoff - timedelta(hours=older_than_hours)

        with self._lock:
            cursor = self._conn.execute(
                """
                DELETE FROM sync_queue
                WHERE status = 'completed' AND processed_at < ?
                """,
                (cutoff.isoformat(),),
            )
            self._conn.commit()
            count = cursor.rowcount

        if count > 0:
            logger.info(f"Cleared {count} completed sync operations")

        return count


# Singleton instance
_sync_queue: Optional[SyncQueue] = None


def get_sync_queue(device_id: str = "") -> SyncQueue:
    """
    Get the singleton SyncQueue instance.

    Args:
        device_id: Device identifier for sync tracking

    Returns:
        SyncQueue instance
    """
    global _sync_queue
    if _sync_queue is None:
        _sync_queue = SyncQueue(device_id=device_id)
        # Requeue any interrupted operations from previous run
        _sync_queue.requeue_processing()
    return _sync_queue


def reset_sync_queue() -> None:
    """Reset the singleton (for testing)."""
    global _sync_queue
    if _sync_queue:
        _sync_queue.close()
    _sync_queue = None
