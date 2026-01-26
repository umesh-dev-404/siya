"""
Supabase Synchronization (Stubbed)

Stub implementation for Supabase synchronization.
Per DIP Phase 3: Stub Supabase synchronization (no real network).

In Phase 3, this is a mock that simulates synchronization without actual network calls.
"""

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class SupabaseSync:
    """
    Supabase synchronization stub.

    Per DIP Phase 3: Stubbed (no real network).
    In later phases, actual Supabase synchronization will be implemented.

    Characteristics (when implemented):
    - Asynchronous
    - Non-blocking
    - Conflict-aware
    - Local execution always takes precedence
    """

    def __init__(self, supabase_url: Optional[str] = None, supabase_key: Optional[str] = None) -> None:
        """
        Initialize Supabase sync stub.

        Args:
            supabase_url: Supabase URL (ignored in Phase 3)
            supabase_key: Supabase API key (ignored in Phase 3)
        """
        self._supabase_url = supabase_url
        self._supabase_key = supabase_key
        self._sync_enabled = False  # Phase 3: Always disabled (stub)

        logger.info(
            "Supabase sync initialized (stub mode - no network access)",
            extra={"sync_enabled": self._sync_enabled},
        )

    def sync_memory(self, memory_entry: Dict[str, Any]) -> bool:
        """
        Sync memory entry to Supabase (stubbed).

        Args:
            memory_entry: Memory entry to sync

        Returns:
            True if sync would succeed (always True in stub mode)

        Note:
            Phase 3: This is a stub. No actual network calls are made.
        """
        if not self._sync_enabled:
            logger.debug(
                "Supabase sync disabled (stub mode)",
                extra={"memory_id": memory_entry.get("id")},
            )
            return True  # Stub: always succeeds

        # Phase 3: Stub implementation
        # In later phases, actual Supabase API calls will be implemented
        logger.debug(
            f"Would sync memory to Supabase: {memory_entry.get('id')}",
            extra={"memory_id": memory_entry.get("id")},
        )

        return True

    def sync_audit_log(self, audit_entry: Dict[str, Any]) -> bool:
        """
        Sync audit log entry to Supabase (stubbed).

        Args:
            audit_entry: Audit log entry to sync

        Returns:
            True if sync would succeed (always True in stub mode)

        Note:
            Phase 3: This is a stub. No actual network calls are made.
        """
        if not self._sync_enabled:
            logger.debug(
                "Supabase sync disabled (stub mode)",
                extra={"log_id": audit_entry.get("id")},
            )
            return True  # Stub: always succeeds

        # Phase 3: Stub implementation
        logger.debug(
            f"Would sync audit log to Supabase: {audit_entry.get('id')}",
            extra={"log_id": audit_entry.get("id")},
        )

        return True

    def is_enabled(self) -> bool:
        """
        Check if synchronization is enabled.

        Returns:
            True if enabled, False otherwise (always False in Phase 3)
        """
        return self._sync_enabled
