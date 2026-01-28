"""
Explanation Service

Provides post-hoc explainability for system decisions.
Enforces LAW 20 — POST-HOC EXPLANATION ONLY.

Per CONTINUATION_PLAN Phase 20: Decision Explanation Layer.
"""

import json
import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from audit.audit_logger import AuditLogger
from memory.database import Database

logger = logging.getLogger(__name__)


# Decision type to relevant event type mapping
DECISION_TYPE_EVENTS = {
    "permission_denied": ["PERMISSION_DENIED", "PERMISSION_CHECKED"],
    "confirmation_required": ["CONFIRMATION_REQUESTED", "CONFIRMATION_GRANTED", "CONFIRMATION_DENIED"],
    "execution_failed": ["TOOL_FAILED", "ORCHESTRATION_FAILED", "ERROR_OCCURRED"],
    "queued": ["ORCHESTRATION_STARTED", "TOOL_REQUESTED"],
}

# Law inference rules based on event patterns
LAW_INFERENCE_RULES = {
    "PERMISSION_DENIED": ["LAW 5 — EXPLICIT PERMISSIONS"],
    "CONFIRMATION_REQUESTED": ["LAW 1 — HUMAN SOVEREIGNTY"],
    "CONFIRMATION_DENIED": ["LAW 1 — HUMAN SOVEREIGNTY"],
    "CONFIRMATION_GRANTED": ["LAW 1 — HUMAN SOVEREIGNTY"],
    "TOOL_FAILED": ["LAW 12 — FAILURE TRANSPARENCY"],
    "ORCHESTRATION_FAILED": ["LAW 12 — FAILURE TRANSPARENCY"],
    "ERROR_OCCURRED": ["LAW 12 — FAILURE TRANSPARENCY", "LAW 13 — COMPLETE AUDITABILITY"],
    "TOOL_EXECUTED": ["LAW 4 — TOOL-ONLY EXECUTION"],
    "TOOL_REQUESTED": ["LAW 4 — TOOL-ONLY EXECUTION"],
    "MEMORY_WRITTEN": ["LAW 8 — MEMORY WRITE CONTROL"],
    "MEMORY_READ": ["LAW 7 — MEMORY IS NON-AUTHORITATIVE"],
}


class ExplanationUnavailable(Exception):
    """Raised when explanation cannot be generated due to insufficient data."""
    pass


class ExplanationService:
    """
    Service for generating post-hoc explanations of system decisions.
    
    Enforces LAW 20 — POST-HOC EXPLANATION ONLY:
    - Explanations reflect actual logged decisions
    - Never influence execution
    - Never introduce new logic
    - Never mask uncertainty
    
    Per Phase 20: Decision Explanation Layer.
    """

    def __init__(self, database: Database) -> None:
        """
        Initialize explanation service.

        Args:
            database: Database connection for accessing audit logs.
        """
        self._database = database
        self._audit_logger = AuditLogger(database)

    def explain_decision(
        self,
        request_id: str,
        decision_type: str,
    ) -> Dict[str, Any]:
        """
        Generate explanation for a past decision.
        
        Args:
            request_id: UUID of the request to explain.
            decision_type: Type of decision (permission_denied, confirmation_required,
                          execution_failed, queued).
        
        Returns:
            Dict containing:
                - summary: Human-readable explanation
                - decision_basis: List of factors that led to decision
                - laws_applied: List of Canonical Laws that were applied
                - referenced_logs: List of audit log entry IDs
                - confidence: Confidence score (0.0 to 1.0)
        
        Raises:
            ExplanationUnavailable: If explanation cannot be generated.
            ValueError: If decision_type is invalid.
        """
        # Validate decision_type
        valid_types = list(DECISION_TYPE_EVENTS.keys())
        if decision_type not in valid_types:
            raise ValueError(
                f"Invalid decision_type: {decision_type}. "
                f"Must be one of: {valid_types}"
            )

        # Validate request_id format (UUID v4)
        uuid_pattern = r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$'
        if not re.match(uuid_pattern, request_id.lower()):
            raise ValueError(
                f"Invalid request_id format: {request_id}. "
                "Must be a valid UUID v4."
            )

        # Retrieve audit events for this request
        events = self._audit_logger.get_events_by_request_id(request_id)

        if not events:
            raise ExplanationUnavailable(
                f"Explanation unavailable due to insufficient data. "
                f"No audit events found for request_id: {request_id}"
            )

        # Filter events relevant to this decision type
        relevant_event_types = DECISION_TYPE_EVENTS[decision_type]
        relevant_events = [
            e for e in events 
            if e.get("event_type") in relevant_event_types
        ]

        if not relevant_events:
            # Fall back to all events if no specific type matches
            relevant_events = events
            confidence = 0.5  # Lower confidence when using fallback
        else:
            confidence = 0.9  # High confidence when exact match found

        # Generate explanation
        return self._build_explanation(
            events=relevant_events,
            all_events=events,
            decision_type=decision_type,
            request_id=request_id,
            base_confidence=confidence,
        )

    def _build_explanation(
        self,
        events: List[Dict[str, Any]],
        all_events: List[Dict[str, Any]],
        decision_type: str,
        request_id: str,
        base_confidence: float,
    ) -> Dict[str, Any]:
        """
        Build explanation object from audit events.
        
        Per LAW 20: Only derive from actual logged data, never speculate.
        """
        decision_basis = []
        laws_applied = set()
        referenced_logs = []

        for event in events:
            event_type = event.get("event_type", "")
            event_data_raw = event.get("event_data", "{}")
            
            # Parse event data
            try:
                if isinstance(event_data_raw, str):
                    event_data = json.loads(event_data_raw)
                else:
                    event_data = event_data_raw
            except json.JSONDecodeError:
                event_data = {}

            # Record log reference
            log_id = event.get("id")
            if log_id:
                referenced_logs.append(log_id)

            # Extract decision basis from event
            basis = self._extract_decision_basis(event_type, event_data)
            if basis:
                decision_basis.append(basis)

            # Infer applied laws
            if event_type in LAW_INFERENCE_RULES:
                laws_applied.update(LAW_INFERENCE_RULES[event_type])

        # Generate summary
        summary = self._generate_summary(
            decision_type=decision_type,
            decision_basis=decision_basis,
            laws_applied=list(laws_applied),
            events=events,
        )

        # Adjust confidence based on data completeness
        if len(decision_basis) == 0:
            confidence = max(0.3, base_confidence - 0.3)
            decision_basis.append("Limited event data available")
        else:
            confidence = base_confidence

        return {
            "summary": summary,
            "decision_basis": decision_basis,
            "laws_applied": sorted(list(laws_applied)),
            "referenced_logs": referenced_logs,
            "confidence": round(confidence, 2),
            "request_id": request_id,
            "decision_type": decision_type,
        }

    def _extract_decision_basis(
        self, 
        event_type: str, 
        event_data: Dict[str, Any],
    ) -> Optional[str]:
        """
        Extract decision basis from a single event.
        """
        if event_type == "PERMISSION_DENIED":
            reason = event_data.get("reason", "Permission denied")
            tool = event_data.get("tool_name", "unknown tool")
            return f"Permission denied for {tool}: {reason}"

        elif event_type == "CONFIRMATION_REQUESTED":
            tool = event_data.get("tool_name", "unknown tool")
            return f"Confirmation required for executing {tool}"

        elif event_type == "CONFIRMATION_DENIED":
            tool = event_data.get("tool_name", "unknown tool")
            return f"User denied confirmation for {tool}"

        elif event_type == "CONFIRMATION_GRANTED":
            tool = event_data.get("tool_name", "unknown tool")
            return f"User granted confirmation for {tool}"

        elif event_type == "TOOL_FAILED":
            tool = event_data.get("tool_name", "unknown tool")
            error = event_data.get("error", "Unknown error")
            return f"Tool execution failed ({tool}): {error}"

        elif event_type == "ORCHESTRATION_FAILED":
            error = event_data.get("error", "Unknown error")
            return f"Orchestration failed: {error}"

        elif event_type == "ERROR_OCCURRED":
            error = event_data.get("error", event_data.get("message", "Unknown error"))
            return f"Error occurred: {error}"

        elif event_type == "TOOL_REQUESTED":
            tool = event_data.get("tool_name", "unknown tool")
            return f"Tool {tool} was requested for execution"

        elif event_type == "ORCHESTRATION_STARTED":
            return "Request was queued for orchestration"

        return None

    def _generate_summary(
        self,
        decision_type: str,
        decision_basis: List[str],
        laws_applied: List[str],
        events: List[Dict[str, Any]],
    ) -> str:
        """
        Generate human-readable summary.
        
        Per LAW 20: Derived from actual data, no speculation.
        """
        type_descriptions = {
            "permission_denied": "The system denied permission for this request",
            "confirmation_required": "The system required user confirmation for this request",
            "execution_failed": "The request execution failed",
            "queued": "The request was queued for processing",
        }

        summary_parts = [type_descriptions.get(decision_type, "System decision recorded")]

        if laws_applied:
            law_names = ", ".join(laws_applied[:3])  # Limit to top 3
            summary_parts.append(f" in accordance with {law_names}")

        if decision_basis:
            summary_parts.append(f". {decision_basis[0]}")
            if len(decision_basis) > 1:
                summary_parts.append(f" Additional factors: {len(decision_basis) - 1} recorded")

        summary_parts.append(".")

        return "".join(summary_parts)
