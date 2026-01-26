"""
Memory Access Layer

Read-only memory access for non-orchestrator components.
Enforces LAW 7 — MEMORY IS NON-AUTHORITATIVE.

Per DIP Phase 3: Memory must not influence execution.
"""

import logging
from typing import Any, Dict, List, Optional

from memory.database import Database
from memory.database_schema import MemoryTier

logger = logging.getLogger(__name__)


class MemoryAccessLayer:
    """
    Read-only memory access layer.

    Enforces LAW 7 — MEMORY IS NON-AUTHORITATIVE:
    - Memory is read-only to AI
    - Memory cannot influence tool selection
    - No branching logic reads memory state

    Per DIP Phase 3 and LAW 7 enforcement.
    """

    def __init__(self, database: Database) -> None:
        """
        Initialize memory access layer.

        Args:
            database: Database connection
        """
        self._database = database

    def read_memory(
        self,
        key: Optional[str] = None,
        memory_tier: Optional[MemoryTier] = None,
        tags: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Read memory entries.

        Args:
            key: Optional memory key to filter by
            memory_tier: Optional memory tier to filter by
            tags: Optional tags to filter by

        Returns:
            List of memory entries

        Note:
            LAW 7: Memory is read-only and non-authoritative.
            This method only reads, never influences execution.
        """
        conn = self._database.get_connection()
        cursor = conn.cursor()

        query = "SELECT * FROM memory WHERE 1=1"
        params: List[Any] = []

        if key:
            query += " AND key = ?"
            params.append(key)

        if memory_tier:
            query += " AND memory_tier = ?"
            params.append(memory_tier.value)

        if tags:
            # Filter by tags (tags stored as JSON array)
            # Phase 3: Simple tag matching
            # In later phases, proper JSON querying will be implemented
            for tag in tags:
                query += " AND tags LIKE ?"
                params.append(f'%"{tag}"%')

        query += " ORDER BY created_at DESC"

        cursor.execute(query, params)
        rows = cursor.fetchall()

        # Convert rows to dictionaries
        columns = [desc[0] for desc in cursor.description]
        results = [dict(zip(columns, row)) for row in rows]

        logger.debug(
            f"Memory read: {len(results)} entries",
            extra={
                "key": key,
                "memory_tier": memory_tier.value if memory_tier else None,
                "tags": tags,
                "result_count": len(results),
            },
        )

        return results

    def get_memory_by_id(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific memory entry by ID.

        Args:
            memory_id: Memory entry ID

        Returns:
            Memory entry, or None if not found
        """
        conn = self._database.get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM memory WHERE id = ?", (memory_id,))
        row = cursor.fetchone()

        if row is None:
            return None

        columns = [desc[0] for desc in cursor.description]
        return dict(zip(columns, row))
