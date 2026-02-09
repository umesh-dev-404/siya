"""
Explanation Tools

Tools for explaining system decisions.
Enforces LAW 20 — POST-HOC EXPLANATION ONLY.

Per CONTINUATION_PLAN Phase 20: Decision Explanation Layer.
"""

import logging
from typing import Any, Dict

from audit.explanation_service import ExplanationService, ExplanationUnavailable
from memory.database import Database

logger = logging.getLogger(__name__)


def explain_decision(
    request_id: str,
    decision_type: str,
) -> Dict[str, Any]:
    """
    Explain why a previous decision was made.
    
    This tool provides post-hoc explainability for system decisions
    without influencing execution. It reads from audit logs only.
    
    Per LAW 20 — POST-HOC EXPLANATION ONLY:
    - Explanations reflect actual logged decisions
    - Never influence execution
    - Never introduce new logic
    - Never mask uncertainty
    
    Args:
        request_id: UUID of the request to explain.
        decision_type: Type of decision to explain.
            Valid values:
            - "permission_denied": Why permission was denied
            - "confirmation_required": Why confirmation was needed
            - "execution_failed": Why execution failed
            - "queued": Why request was queued
    
    Returns:
        Dict containing:
            - status: "ok" or "error"
            - explanation: Explanation object with:
                - summary: Human-readable explanation
                - decision_basis: Factors that led to decision
                - laws_applied: Canonical Laws that were applied
                - referenced_logs: Audit log entry IDs
                - confidence: Confidence score (0.0 to 1.0)
            - message: (if error) Error message
    
    Example:
        explain_decision(
            request_id="a1b2c3d4-e5f6-7890-abcd-ef1234567890",
            decision_type="confirmation_required"
        )
    """
    try:
        with Database() as database:
            service = ExplanationService(database)
            explanation = service.explain_decision(
                request_id=request_id,
                decision_type=decision_type,
            )

        logger.info(
            f"Generated explanation for request {request_id}",
            extra={
                "request_id": request_id,
                "decision_type": decision_type,
                "confidence": explanation.get("confidence"),
            },
        )

        return {
            "status": "ok",
            "explanation": explanation,
        }

    except ExplanationUnavailable as e:
        logger.warning(f"Explanation unavailable: {e}")
        return {
            "status": "unavailable",
            "message": str(e),
            "explanation": {
                "summary": "Explanation unavailable due to insufficient data.",
                "decision_basis": [],
                "laws_applied": ["LAW 20 — POST-HOC EXPLANATION ONLY"],
                "referenced_logs": [],
                "confidence": 0.0,
            },
        }
        
    except ValueError as e:
        logger.warning(f"Invalid input: {e}")
        return {
            "status": "error",
            "message": str(e),
        }
        
    except Exception as e:
        logger.exception(f"Error generating explanation: {e}")
        return {
            "status": "error",
            "message": f"Failed to generate explanation: {str(e)}",
        }


def register_explanation_tools(executor) -> None:
    """
    Register explanation tools with the ToolExecutor.
    
    Per Phase 20: Decision Explanation Layer.
    """
    executor.register(
        "explain_decision",
        lambda args: explain_decision(
            request_id=args["request_id"],
            decision_type=args["decision_type"],
        ),
    )
    
    logger.info("Explanation tools registered: explain_decision")
