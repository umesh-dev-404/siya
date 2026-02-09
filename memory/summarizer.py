"""
Memory Summarizer

Implements memory degradation through summarization.
Enforces LAW 9 — MEMORY DEGRADATION CONTROL.

Per DIP Phase 3: Implement memory tagging, confidence, lineage.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

from memory.database import Database
from memory.write_controller import WriteController

logger = logging.getLogger(__name__)


class MemorySummarizer:
    """
    Memory summarizer for degradation control.

    Enforces LAW 9 — MEMORY DEGRADATION CONTROL:
    - Periodic summarization
    - Lineage preserved
    - No silent deletion

    Per DIP Phase 3 and LAW 9 enforcement.
    """

    def __init__(self, database: Database, write_controller: WriteController) -> None:
        """
        Initialize memory summarizer.

        Args:
            database: Database connection
            write_controller: Write controller (must be orchestrator-owned)
        """
        self._database = database
        self._write_controller = write_controller

    def summarize_old_memory(
        self,
        memory_tier: str,
        older_than_days: int = 30,
        summary_key_prefix: str = "summary",
    ) -> int:
        """
        Summarize old memory entries.

        Args:
            memory_tier: Memory tier to summarize (L1, L2, L3)
            older_than_days: Summarize entries older than this many days
            summary_key_prefix: Prefix for summary memory keys

        Returns:
            Number of entries summarized

        Note:
            Phase 3: Basic summarization (creates summary entries)
            In later phases, actual summarization logic will be implemented
        """
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=older_than_days)
        cutoff_iso = cutoff_date.isoformat() + "Z"

        conn = self._database.get_connection()
        cursor = conn.cursor()

        # Find old memory entries that haven't been summarized
        cursor.execute(
            """
            SELECT id, key, value, created_at, source_request_id, parent_memory_id
            FROM memory
            WHERE memory_tier = ?
            AND created_at < ?
            AND parent_memory_id IS NULL
            ORDER BY created_at ASC
            LIMIT 100
            """,
            (memory_tier, cutoff_iso),
        )

        entries = cursor.fetchall()
        if not entries:
            return 0

        # Phase 3: Create summary entries (simplified)
        # In later phases, actual summarization will be implemented
        summarized_count = 0

        for entry in entries:
            entry_id, key, value, created_at, source_request_id, parent_memory_id = entry

            # Create summary entry
            summary_key = f"{summary_key_prefix}_{key}_{cutoff_date.strftime('%Y%m%d')}"
            summary_value = f"Summary of {key} (original: {entry_id})"

            try:
                self._write_controller.write_memory(
                    key=summary_key,
                    value=summary_value,
                    memory_tier=memory_tier,  # Keep same tier
                    confidence=1.0,
                    source_request_id=source_request_id,
                    source_type="tool_execution",  # Default
                    parent_memory_id=entry_id,  # Link to original
                    suggested_by="ORCHESTRATOR",
                )

                # Mark original as summarized (by setting parent_memory_id)
                # Phase 3: Simplified - in later phases, proper summarization tracking
                summarized_count += 1

            except Exception as e:
                logger.error(
                    f"Failed to create summary for memory {entry_id}: {e}",
                    extra={"memory_id": entry_id, "error": str(e)},
                )

        logger.info(
            f"Summarized {summarized_count} memory entries",
            extra={
                "memory_tier": memory_tier,
                "older_than_days": older_than_days,
                "summarized_count": summarized_count,
            },
        )

        return summarized_count
