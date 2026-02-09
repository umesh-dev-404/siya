"""
Memory Write Controller

Enforces orchestrator-only memory writes.
Enforces LAW 8 — MEMORY WRITE CONTROL.

Per DIP Phase 3: Enforce orchestrator-only memory writes.
"""

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from memory.database import Database
from memory.database_schema import MemoryTier

logger = logging.getLogger(__name__)


class WriteController:
    """
    Memory write controller.

    Enforces LAW 8 — MEMORY WRITE CONTROL:
    - Only orchestrator can write
    - Write operations require explicit call
    - Memory writes logged and tagged

    Per DIP Phase 3 and LAW 8 enforcement.
    """

    def __init__(self, database: Database, caller_identity: str) -> None:
        """
        Initialize write controller.

        Args:
            database: Database connection
            caller_identity: Identity of the caller (must be 'ORCHESTRATOR')
        """
        if caller_identity != "ORCHESTRATOR":
            raise ValueError(
                f"Only ORCHESTRATOR can create WriteController. "
                f"Got: {caller_identity}. This enforces LAW 8 — MEMORY WRITE CONTROL."
            )

        self._database = database
        self._caller_identity = caller_identity

    def write_memory(
        self,
        key: str,
        value: str,
        memory_tier: MemoryTier,
        tags: Optional[List[str]] = None,
        confidence: float = 1.0,
        source_request_id: Optional[str] = None,
        source_type: Optional[str] = None,
        parent_memory_id: Optional[str] = None,
        expires_at: Optional[datetime] = None,
        suggested_by: str = "ORCHESTRATOR",
    ) -> str:
        """
        Write a memory entry.

        Args:
            key: Memory key/identifier
            value: Memory value/content
            memory_tier: Target memory tier
            tags: Optional tags for categorization
            confidence: Confidence score (0.0-1.0)
            source_request_id: Request ID that generated this memory
            source_type: Type of source (intent_parsing, tool_execution, user_input, automation)
            parent_memory_id: ID of parent memory if this is a summary (LAW 9)
            expires_at: Optional expiration timestamp
            suggested_by: Component suggesting this (AI, ORCHESTRATOR, TOOL)

        Returns:
            Memory entry ID

        Raises:
            ValueError: If parameters are invalid
        """
        # Validate confidence
        if not (0.0 <= confidence <= 1.0):
            raise ValueError(f"Confidence must be between 0.0 and 1.0, got {confidence}")

        # Validate source_type
        valid_source_types = ["intent_parsing", "tool_execution", "user_input", "automation"]
        if source_type and source_type not in valid_source_types:
            raise ValueError(
                f"source_type must be one of {valid_source_types}, got {source_type}"
            )

        # Validate suggested_by
        valid_suggesters = ["AI", "ORCHESTRATOR", "TOOL"]
        if suggested_by not in valid_suggesters:
            raise ValueError(
                f"suggested_by must be one of {valid_suggesters}, got {suggested_by}"
            )

        memory_id = str(uuid4())
        now = datetime.now(timezone.utc)

        conn = self._database.get_connection()
        cursor = conn.cursor()

        # Serialize tags as JSON
        tags_json = json.dumps(tags) if tags else None

        cursor.execute(
            """
            INSERT INTO memory (
                id, key, value, memory_tier, tags, confidence,
                created_at, updated_at, expires_at,
                source_request_id, source_type, parent_memory_id, suggested_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                memory_id,
                key,
                value,
                memory_tier.value,
                tags_json,
                confidence,
                now.isoformat() + "Z",
                now.isoformat() + "Z",
                expires_at.isoformat() + "Z" if expires_at else None,
                source_request_id,
                source_type,
                parent_memory_id,
                suggested_by,
            ),
        )

        conn.commit()

        logger.info(
            f"Memory written: {key} (tier: {memory_tier.value})",
            extra={
                "memory_id": memory_id,
                "key": key,
                "memory_tier": memory_tier.value,
                "confidence": confidence,
                "source_request_id": source_request_id,
                "source_type": source_type,
                "suggested_by": suggested_by,
            },
        )

        return memory_id

    def write_from_suggestion(
        self,
        suggestion: Dict[str, Any],
    ) -> str:
        """
        Write memory from a memory write suggestion.

        Args:
            suggestion: Memory write suggestion (must match system_schema.json)

        Returns:
            Memory entry ID

        Raises:
            ValueError: If suggestion is invalid
        """
        # Validate suggestion structure
        required_fields = ["memory_tier", "content", "confidence", "lineage"]
        for field in required_fields:
            if field not in suggestion:
                raise ValueError(f"Missing required field in suggestion: {field}")

        content = suggestion["content"]
        if "key" not in content or "value" not in content:
            raise ValueError("suggestion.content must have 'key' and 'value'")

        memory_tier = MemoryTier(suggestion["memory_tier"])
        lineage = suggestion["lineage"]

        return self.write_memory(
            key=content["key"],
            value=content["value"],
            memory_tier=memory_tier,
            tags=content.get("tags"),
            confidence=suggestion["confidence"],
            source_request_id=lineage.get("source_request_id"),
            source_type=lineage.get("source_type"),
            parent_memory_id=lineage.get("parent_memory_id"),
            expires_at=datetime.fromisoformat(content["expires_at"].replace("Z", "+00:00"))
            if content.get("expires_at")
            else None,
            suggested_by=suggestion.get("suggested_by", "ORCHESTRATOR"),
        )
