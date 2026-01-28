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

    # Phase 22: Memory Quality Control (v1.0.1)
    
    def get_memories_by_confidence(
        self,
        max_confidence: float = 1.0,
        min_confidence: float = 0.0,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Get memories filtered by confidence level.
        
        Args:
            max_confidence: Maximum confidence_current (inclusive)
            min_confidence: Minimum confidence_current (inclusive)
            limit: Maximum number of results
            
        Returns:
            List of memory entries matching confidence criteria
            
        Note:
            LAW 22: Supports memory quality evaluation without mutation.
        """
        conn = self._database.get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            """
            SELECT * FROM memory 
            WHERE confidence_current >= ? AND confidence_current <= ?
            ORDER BY confidence_current ASC
            LIMIT ?
            """,
            (min_confidence, max_confidence, limit),
        )
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, row)) for row in rows]

    def get_summarization_candidates(
        self,
        confidence_threshold: float = 0.3,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        Get memories eligible for summarization.
        
        Args:
            confidence_threshold: Max confidence for summarization eligibility
            limit: Maximum number of results
            
        Returns:
            List of unsummarized memories below confidence threshold
            
        Note:
            LAW 22: Identifies candidates without performing summarization.
        """
        conn = self._database.get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            """
            SELECT * FROM memory 
            WHERE confidence_current <= ? 
              AND is_summarized = 0
            ORDER BY confidence_current ASC
            LIMIT ?
            """,
            (confidence_threshold, limit),
        )
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, row)) for row in rows]

    def get_memory_lineage(self, memory_id: str) -> List[Dict[str, Any]]:
        """
        Get lineage chain for a memory (parents and children).
        
        Args:
            memory_id: Starting memory ID
            
        Returns:
            List of related memories in lineage chain
            
        Note:
            LAW 22: Preserves lineage for attribution.
        """
        conn = self._database.get_connection()
        cursor = conn.cursor()
        
        # Get direct parents and children
        cursor.execute(
            """
            SELECT * FROM memory 
            WHERE id = ? 
               OR parent_memory_id = ? 
               OR lineage_id = ?
            ORDER BY summarization_level ASC, created_at ASC
            """,
            (memory_id, memory_id, memory_id),
        )
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, row)) for row in rows]

