"""
Sync Package - L3 Memory Synchronization

Provides Supabase synchronization for L3 memory tier.
Per Phase 13: Supabase Synchronization.

Components:
- SupabaseClient: Authenticated connection management
- SyncQueue: Offline-first queue for pending operations
- SyncManager: L2 ↔ L3 synchronization orchestration

LAW Compliance:
- LAW 7: Synced data is informational only
- LAW 8: Only orchestrator can trigger sync writes
- LAW 13: All sync operations logged
- LAW 15: API keys never logged
- LAW 16: All network calls explicit
"""

from sync.supabase_client import SupabaseClient, get_supabase_client
from sync.sync_queue import (
    OperationType,
    OperationStatus,
    QueueOperation,
    SyncQueue,
    get_sync_queue,
)
from sync.sync_manager import (
    SyncDirection,
    SyncStatus,
    SyncResult,
    SyncManager,
    get_sync_manager,
)

__all__ = [
    # Client
    "SupabaseClient",
    "get_supabase_client",
    # Queue
    "OperationType",
    "OperationStatus",
    "QueueOperation",
    "SyncQueue",
    "get_sync_queue",
    # Manager
    "SyncDirection",
    "SyncStatus",
    "SyncResult",
    "SyncManager",
    "get_sync_manager",
]

