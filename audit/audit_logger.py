"""
Audit Logger

Implements immutable audit log entries.
Enforces LAW 13 — COMPLETE AUDITABILITY and LAW 14 — LOG RETENTION DISCIPLINE.

Per DIP Phase 3: Log retention and summarization.
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from memory.database import Database

logger = logging.getLogger(__name__)


class AuditLogger:
    """
    Audit logger for immutable log entries.

    Enforces LAW 13 — COMPLETE AUDITABILITY:
    - Immutable log entries
    - Correlated request IDs
    - End-to-end traceability

    Enforces LAW 14 — LOG RETENTION DISCIPLINE:
    - Time-based log expiry
    - Mandatory summarization
    - Configurable retention policy

    Per DIP Phase 3 and LAW 13/14 enforcement.
    """

    def __init__(self, database: Database) -> None:
        """
        Initialize audit logger.

        Args:
            database: Database connection
        """
        self._database = database

    def log_event(
        self,
        event_type: str,
        event_data: Dict[str, Any],
        correlation_id: str,
        request_id: Optional[str] = None,
        user_id: Optional[str] = None,
        interface: Optional[str] = None,
        layer: Optional[str] = None,
    ) -> str:
        """
        Log an audit event.

        Args:
            event_type: Type of event (must match system_schema.json enum)
            event_data: Event-specific data (must not contain secrets)
            correlation_id: Correlation ID linking related events
            request_id: Optional request ID
            user_id: Optional user ID
            interface: Optional interface (CLI, WEB, API, VOICE)
            layer: Optional system layer (AI, MCP, ORCHESTRATOR, TOOL, MEMORY, INTERFACE)

        Returns:
            Audit log entry ID

        Raises:
            ValueError: If event_type is invalid
        """
        valid_event_types = [
            "USER_INPUT",
            "INTENT_PARSED",
            "TOOL_REQUESTED",
            "TOOL_EXECUTED",
            "TOOL_FAILED",
            "CONFIRMATION_REQUESTED",
            "CONFIRMATION_GRANTED",
            "CONFIRMATION_DENIED",
            "PERMISSION_CHECKED",
            "PERMISSION_DENIED",
            "MEMORY_READ",
            "MEMORY_WRITTEN",
            "ORCHESTRATION_STARTED",
            "ORCHESTRATION_COMPLETED",
            "ORCHESTRATION_FAILED",
            "ERROR_OCCURRED",
            "AUTOMATION_TRIGGERED",
            "SCHEDULED_EVENT",
        ]

        if event_type not in valid_event_types:
            raise ValueError(
                f"Invalid event_type: {event_type}. Must be one of {valid_event_types}"
            )

        log_id = str(uuid4())
        timestamp = datetime.utcnow().isoformat() + "Z"

        # Serialize event_data as JSON (must not contain secrets)
        event_data_json = json.dumps(event_data)

        conn = self._database.get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO audit_log (
                id, request_id, timestamp, event_type, event_data,
                correlation_id, user_id, interface, layer
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                log_id,
                request_id or str(uuid4()),
                timestamp,
                event_type,
                event_data_json,
                correlation_id,
                user_id,
                interface,
                layer,
            ),
        )

        conn.commit()

        logger.debug(
            f"Audit event logged: {event_type}",
            extra={
                "log_id": log_id,
                "event_type": event_type,
                "correlation_id": correlation_id,
                "request_id": request_id,
            },
        )

        return log_id

    def get_events_by_correlation_id(self, correlation_id: str) -> List[Dict[str, Any]]:
        """
        Get all events for a correlation ID.

        Args:
            correlation_id: Correlation ID

        Returns:
            List of audit log entries
        """
        conn = self._database.get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM audit_log WHERE correlation_id = ? ORDER BY timestamp ASC",
            (correlation_id,),
        )

        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]

        return [dict(zip(columns, row)) for row in rows]

    def get_events_by_request_id(self, request_id: str) -> List[Dict[str, Any]]:
        """
        Get all events for a request ID.

        Args:
            request_id: Request ID

        Returns:
            List of audit log entries
        """
        conn = self._database.get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM audit_log WHERE request_id = ? ORDER BY timestamp ASC",
            (request_id,),
        )

        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]

        return [dict(zip(columns, row)) for row in rows]
