"""
Sync Manager - L2 ↔ L3 Synchronization Orchestration

Orchestrates synchronization between L2 (SQLite) and L3 (Supabase).
Per Phase 13: Supabase Synchronization.

LAW Compliance:
- LAW 7: Synced data is informational only
- LAW 8: Only orchestrator can trigger sync operations
- LAW 13: All sync operations logged
- LAW 16: Offline-first design

Features:
- Push (L2 → L3): Upload local changes to cloud
- Pull (L3 → L2): Download cloud changes to local
- Conflict resolution (last-write-wins with timestamp)
- Sync status tracking
"""

import logging
import sqlite3
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Final, Optional

from sync.supabase_client import SupabaseClient, get_supabase_client
from sync.sync_queue import (
    OperationType,
    QueueOperation,
    SyncQueue,
    get_sync_queue,
)

logger = logging.getLogger(__name__)


class SyncDirection(str, Enum):
    """Sync direction."""

    PUSH = "PUSH"  # L2 → L3
    PULL = "PULL"  # L3 → L2
    BIDIRECTIONAL = "BIDIRECTIONAL"


class SyncStatus(str, Enum):
    """Overall sync status."""

    IDLE = "IDLE"
    SYNCING = "SYNCING"
    ERROR = "ERROR"
    OFFLINE = "OFFLINE"


@dataclass
class SyncResult:
    """Result of a sync operation."""

    success: bool
    direction: SyncDirection
    records_pushed: int = 0
    records_pulled: int = 0
    conflicts_resolved: int = 0
    errors: list[str] = field(default_factory=list)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    @property
    def duration_ms(self) -> Optional[float]:
        """Get sync duration in milliseconds."""
        if self.started_at and self.completed_at:
            delta = self.completed_at - self.started_at
            return delta.total_seconds() * 1000
        return None


@dataclass
class SyncManager:
    """
    Manages synchronization between L2 (SQLite) and L3 (Supabase).

    LAW 7: Synced data is informational only.
    LAW 8: Only authorized callers can trigger sync.
    LAW 13: All sync operations logged.
    LAW 16: Offline-first (queue operations when offline).
    """

    supabase: SupabaseClient = field(default_factory=get_supabase_client)
    queue: SyncQueue = field(default_factory=get_sync_queue)
    l2_db_path: Path = field(default_factory=lambda: Path("data/siya.db"))
    device_id: str = ""

    _status: SyncStatus = field(default=SyncStatus.IDLE)
    _last_sync: Optional[datetime] = field(default=None)
    _last_pull: Optional[datetime] = field(default=None)
    _lock: threading.RLock = field(default_factory=threading.RLock, repr=False)

    # Authorized callers (LAW 8)
    AUTHORIZED_WRITERS: Final[frozenset] = frozenset({
        "orchestrator",
        "service_main",
        "sync_manager",
    })

    @property
    def status(self) -> SyncStatus:
        """Get current sync status."""
        return self._status

    @property
    def last_sync(self) -> Optional[datetime]:
        """Get timestamp of last successful sync."""
        return self._last_sync

    def _verify_caller(self, caller: str) -> bool:
        """
        Verify caller is authorized to trigger sync (LAW 8).

        Args:
            caller: Caller identifier

        Returns:
            True if authorized
        """
        if caller not in self.AUTHORIZED_WRITERS:
            logger.warning(
                f"Unauthorized sync attempt by: {caller}",
                extra={"law": "LAW 8", "caller": caller},
            )
            return False
        return True

    # ==========================================
    # Push Operations (L2 → L3)
    # ==========================================

    def push(self, caller: str = "sync_manager") -> SyncResult:
        """
        Push pending local changes to Supabase (L2 → L3).

        Args:
            caller: Caller identifier (LAW 8 verification)

        Returns:
            SyncResult with operation details
        """
        result = SyncResult(
            success=False,
            direction=SyncDirection.PUSH,
            started_at=datetime.now(timezone.utc),
        )

        if not self._verify_caller(caller):
            result.errors.append("Unauthorized caller")
            result.completed_at = datetime.now(timezone.utc)
            return result

        if not self.supabase.is_configured:
            logger.debug("Supabase not configured, skipping push")
            result.success = True  # Not an error, just nothing to do
            result.completed_at = datetime.now(timezone.utc)
            return result

        with self._lock:
            self._status = SyncStatus.SYNCING

        try:
            # Connect if needed
            if not self.supabase.is_connected:
                if not self.supabase.connect():
                    self._status = SyncStatus.OFFLINE
                    result.errors.append("Cannot connect to Supabase")
                    result.completed_at = datetime.now(timezone.utc)
                    return result

            # Process queue
            operations = self.queue.dequeue(batch_size=50)
            logger.info(f"Processing {len(operations)} sync operations")

            for op in operations:
                try:
                    self._process_push_operation(op)
                    self.queue.mark_completed(op.id)
                    result.records_pushed += 1
                except Exception as e:
                    error_msg = f"{type(e).__name__}: {str(e)}"
                    self.queue.mark_failed(op.id, error_msg)
                    result.errors.append(f"Failed {op.operation_type.value} {op.record_id}: {error_msg}")

            result.success = len(result.errors) == 0
            self._last_sync = datetime.now(timezone.utc)
            self._status = SyncStatus.IDLE

        except Exception as e:
            logger.error(f"Push sync failed: {type(e).__name__}: {e}")
            result.errors.append(f"Push failed: {type(e).__name__}")
            self._status = SyncStatus.ERROR

        result.completed_at = datetime.now(timezone.utc)
        logger.info(
            f"Push complete: {result.records_pushed} records, "
            f"{len(result.errors)} errors, {result.duration_ms:.0f}ms"
        )
        return result

    def _process_push_operation(self, op: QueueOperation) -> None:
        """Process a single push operation."""
        if op.operation_type == OperationType.INSERT:
            # Add sync metadata
            payload = op.payload.copy()
            payload["device_id"] = self.device_id
            payload["synced_at"] = datetime.now(timezone.utc).isoformat()
            success, _ = self.supabase.insert_memory(payload)
            if not success:
                raise RuntimeError("Insert failed")

        elif op.operation_type == OperationType.UPDATE:
            payload = op.payload.copy()
            payload["synced_at"] = datetime.now(timezone.utc).isoformat()
            success, _ = self.supabase.update_memory(op.record_id, payload)
            if not success:
                raise RuntimeError("Update failed")

        elif op.operation_type == OperationType.DELETE:
            success, _ = self.supabase.delete_memory(op.record_id)
            if not success:
                raise RuntimeError("Delete failed")

    # ==========================================
    # Pull Operations (L3 → L2)
    # ==========================================

    def pull(self, caller: str = "sync_manager") -> SyncResult:
        """
        Pull remote changes from Supabase to local (L3 → L2).

        Args:
            caller: Caller identifier (LAW 8 verification)

        Returns:
            SyncResult with operation details
        """
        result = SyncResult(
            success=False,
            direction=SyncDirection.PULL,
            started_at=datetime.now(timezone.utc),
        )

        if not self._verify_caller(caller):
            result.errors.append("Unauthorized caller")
            result.completed_at = datetime.now(timezone.utc)
            return result

        if not self.supabase.is_configured:
            logger.debug("Supabase not configured, skipping pull")
            result.success = True
            result.completed_at = datetime.now(timezone.utc)
            return result

        with self._lock:
            self._status = SyncStatus.SYNCING

        try:
            if not self.supabase.is_connected:
                if not self.supabase.connect():
                    self._status = SyncStatus.OFFLINE
                    result.errors.append("Cannot connect to Supabase")
                    result.completed_at = datetime.now(timezone.utc)
                    return result

            # Fetch records updated since last pull
            since = self._last_pull or datetime.min.replace(tzinfo=timezone.utc)
            success, records = self.supabase.fetch_memories_since(since)

            if not success:
                result.errors.append("Failed to fetch remote records")
                self._status = SyncStatus.ERROR
                result.completed_at = datetime.now(timezone.utc)
                return result

            logger.info(f"Fetched {len(records or [])} remote records")

            # Apply to local database
            for record in records or []:
                try:
                    conflict = self._apply_remote_record(record)
                    result.records_pulled += 1
                    if conflict:
                        result.conflicts_resolved += 1
                except Exception as e:
                    error_msg = f"{type(e).__name__}: {str(e)}"
                    result.errors.append(f"Failed to apply {record.get('id')}: {error_msg}")

            result.success = len(result.errors) == 0
            self._last_pull = datetime.now(timezone.utc)
            self._status = SyncStatus.IDLE

        except Exception as e:
            logger.error(f"Pull sync failed: {type(e).__name__}: {e}")
            result.errors.append(f"Pull failed: {type(e).__name__}")
            self._status = SyncStatus.ERROR

        result.completed_at = datetime.now(timezone.utc)
        logger.info(
            f"Pull complete: {result.records_pulled} records, "
            f"{result.conflicts_resolved} conflicts, "
            f"{len(result.errors)} errors"
        )
        return result

    def _apply_remote_record(self, record: dict[str, Any]) -> bool:
        """
        Apply a remote record to local database.

        Returns True if there was a conflict.
        """
        conn = sqlite3.connect(str(self.l2_db_path))
        try:
            cursor = conn.execute(
                "SELECT id, updated_at FROM memory WHERE id = ?",
                (record["id"],),
            )
            local_row = cursor.fetchone()

            if local_row:
                # Conflict resolution: last-write-wins
                local_updated = datetime.fromisoformat(local_row[1])
                remote_updated = datetime.fromisoformat(record["updated_at"])

                if remote_updated > local_updated:
                    # Remote wins
                    self._update_local_record(conn, record)
                    logger.debug(f"Conflict resolved (remote wins): {record['id']}")
                    return True
                else:
                    # Local wins, no action
                    logger.debug(f"Conflict resolved (local wins): {record['id']}")
                    return True
            else:
                # No conflict, insert
                self._insert_local_record(conn, record)
                return False

        finally:
            conn.close()

    def _insert_local_record(
        self, conn: sqlite3.Connection, record: dict[str, Any]
    ) -> None:
        """Insert a record into local database."""
        import json

        conn.execute(
            """
            INSERT INTO memory (
                id, key, value, memory_tier, tags, confidence,
                created_at, updated_at, expires_at, source_request_id,
                source_type, parent_memory_id, suggested_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record["id"],
                record["key"],
                record["value"],
                record.get("memory_tier", "L3"),
                json.dumps(record.get("tags", [])),
                record.get("confidence"),
                record.get("created_at", datetime.now(timezone.utc).isoformat()),
                record.get("updated_at", datetime.now(timezone.utc).isoformat()),
                record.get("expires_at"),
                record.get("source_request_id"),
                record.get("source_type"),
                record.get("parent_memory_id"),
                record.get("suggested_by"),
            ),
        )
        conn.commit()

    def _update_local_record(
        self, conn: sqlite3.Connection, record: dict[str, Any]
    ) -> None:
        """Update a record in local database."""
        import json

        conn.execute(
            """
            UPDATE memory SET
                key = ?, value = ?, memory_tier = ?, tags = ?, confidence = ?,
                updated_at = ?, expires_at = ?, source_request_id = ?,
                source_type = ?, parent_memory_id = ?, suggested_by = ?
            WHERE id = ?
            """,
            (
                record["key"],
                record["value"],
                record.get("memory_tier", "L3"),
                json.dumps(record.get("tags", [])),
                record.get("confidence"),
                record.get("updated_at", datetime.now(timezone.utc).isoformat()),
                record.get("expires_at"),
                record.get("source_request_id"),
                record.get("source_type"),
                record.get("parent_memory_id"),
                record.get("suggested_by"),
                record["id"],
            ),
        )
        conn.commit()

    # ==========================================
    # Bidirectional Sync
    # ==========================================

    def sync(self, caller: str = "sync_manager") -> SyncResult:
        """
        Perform bidirectional sync (push then pull).

        Args:
            caller: Caller identifier (LAW 8 verification)

        Returns:
            Combined SyncResult
        """
        result = SyncResult(
            success=False,
            direction=SyncDirection.BIDIRECTIONAL,
            started_at=datetime.now(timezone.utc),
        )

        # Push first
        push_result = self.push(caller)
        result.records_pushed = push_result.records_pushed
        result.errors.extend(push_result.errors)

        # Then pull
        pull_result = self.pull(caller)
        result.records_pulled = pull_result.records_pulled
        result.conflicts_resolved = pull_result.conflicts_resolved
        result.errors.extend(pull_result.errors)

        result.success = push_result.success and pull_result.success
        result.completed_at = datetime.now(timezone.utc)

        logger.info(
            f"Bidirectional sync complete: "
            f"pushed={result.records_pushed}, "
            f"pulled={result.records_pulled}, "
            f"conflicts={result.conflicts_resolved}"
        )

        return result

    # ==========================================
    # Queue Integration
    # ==========================================

    def queue_for_sync(
        self,
        operation_type: OperationType,
        table_name: str,
        record_id: str,
        payload: dict[str, Any],
    ) -> str:
        """
        Queue a record for sync (called by TierManager on L2 writes).

        Args:
            operation_type: Type of operation
            table_name: Target table
            record_id: Record ID
            payload: Record data

        Returns:
            Queue operation ID
        """
        return self.queue.enqueue(
            operation_type=operation_type,
            table_name=table_name,
            record_id=record_id,
            payload=payload,
        )

    # ==========================================
    # Status
    # ==========================================

    def get_sync_status(self) -> dict[str, Any]:
        """Get comprehensive sync status."""
        queue_stats = self.queue.get_stats()

        return {
            "status": self._status.value,
            "last_sync": self._last_sync.isoformat() if self._last_sync else None,
            "last_pull": self._last_pull.isoformat() if self._last_pull else None,
            "supabase": self.supabase.get_connection_info(),
            "queue": queue_stats,
            "device_id": self.device_id,
        }


# Singleton instance
_sync_manager: Optional[SyncManager] = None


def get_sync_manager(device_id: str = "") -> SyncManager:
    """
    Get the singleton SyncManager instance.

    Args:
        device_id: Device identifier

    Returns:
        SyncManager instance
    """
    global _sync_manager
    if _sync_manager is None:
        _sync_manager = SyncManager(device_id=device_id)
    return _sync_manager


def reset_sync_manager() -> None:
    """Reset the singleton (for testing)."""
    global _sync_manager
    _sync_manager = None
