"""
Memory Manager

Main memory management interface.
Coordinates memory access, writes, and synchronization.

Per DIP Phase 3: Memory governance layer.
"""

import logging
from typing import Optional

from audit.audit_logger import AuditLogger
from memory.access_layer import MemoryAccessLayer
from memory.database import Database
from memory.database_schema import MemoryTier
from memory.supabase_sync import SupabaseSync
from memory.write_controller import WriteController

logger = logging.getLogger(__name__)


class MemoryManager:
    """
    Memory manager coordinating all memory operations.

    Per DIP Phase 3:
    - SQLite runtime memory (L2)
    - Memory governance layer
    - Supabase sync (mocked)

    Enforces:
    - LAW 7 — MEMORY IS NON-AUTHORITATIVE
    - LAW 8 — MEMORY WRITE CONTROL
    - LAW 9 — MEMORY DEGRADATION CONTROL
    """

    def __init__(self, database: Database) -> None:
        """
        Initialize memory manager.

        Args:
            database: Database connection
        """
        self._database = database
        self._access_layer = MemoryAccessLayer(database)
        self._write_controller = WriteController(database, "ORCHESTRATOR")
        self._audit_logger = AuditLogger(database)
        self._supabase_sync = SupabaseSync()  # Stub in Phase 3

    def get_access_layer(self) -> MemoryAccessLayer:
        """
        Get read-only memory access layer.

        Returns:
            Memory access layer (read-only)

        Note:
            LAW 7: Memory is non-authoritative. This provides read-only access.
        """
        return self._access_layer

    def get_write_controller(self) -> WriteController:
        """
        Get memory write controller.

        Returns:
            Write controller (orchestrator-only)

        Note:
            LAW 8: Only orchestrator can write. This controller enforces that.
        """
        return self._write_controller

    def get_audit_logger(self) -> AuditLogger:
        """
        Get audit logger.

        Returns:
            Audit logger
        """
        return self._audit_logger

    def get_supabase_sync(self) -> SupabaseSync:
        """
        Get Supabase synchronization.

        Returns:
            Supabase sync (stub in Phase 3)
        """
        return self._supabase_sync
