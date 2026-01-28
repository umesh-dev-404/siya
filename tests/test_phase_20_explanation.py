"""
Tests for Phase 20: Decision Explanation Layer

Tests ExplanationService and explain_decision tool.
Enforces LAW 20 — POST-HOC EXPLANATION ONLY.
"""

import json
import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch
from uuid import uuid4


class TestExplanationService:
    """Tests for ExplanationService class."""

    def test_explanation_service_init(self):
        """Test ExplanationService initialization."""
        from audit.explanation_service import ExplanationService
        from memory.database import Database
        
        with patch('audit.explanation_service.AuditLogger') as mock_audit_class:
            mock_audit = MagicMock()
            mock_audit_class.return_value = mock_audit
            
            db = MagicMock(spec=Database)
            service = ExplanationService(db)
            
            assert service._database == db
            assert service._audit_logger is not None

    def test_invalid_decision_type_raises_error(self):
        """Test that invalid decision_type raises ValueError."""
        from audit.explanation_service import ExplanationService
        from memory.database import Database
        
        db = MagicMock(spec=Database)
        service = ExplanationService(db)
        
        with pytest.raises(ValueError) as exc_info:
            service.explain_decision(
                request_id=str(uuid4()),
                decision_type="invalid_type",
            )
        
        assert "Invalid decision_type" in str(exc_info.value)

    def test_invalid_request_id_format_raises_error(self):
        """Test that invalid request_id format raises ValueError."""
        from audit.explanation_service import ExplanationService
        from memory.database import Database
        
        db = MagicMock(spec=Database)
        service = ExplanationService(db)
        
        with pytest.raises(ValueError) as exc_info:
            service.explain_decision(
                request_id="not-a-uuid",
                decision_type="confirmation_required",
            )
        
        assert "Invalid request_id format" in str(exc_info.value)

    def test_no_events_raises_explanation_unavailable(self):
        """Test that missing events raises ExplanationUnavailable."""
        from audit.explanation_service import ExplanationService, ExplanationUnavailable
        from memory.database import Database
        
        db = MagicMock(spec=Database)
        service = ExplanationService(db)
        
        # Mock audit logger to return empty list
        service._audit_logger.get_events_by_request_id = MagicMock(return_value=[])
        
        with pytest.raises(ExplanationUnavailable) as exc_info:
            service.explain_decision(
                request_id=str(uuid4()),
                decision_type="permission_denied",
            )
        
        assert "insufficient data" in str(exc_info.value).lower()

    def test_explanation_contains_required_fields(self):
        """Test that explanation contains all required fields."""
        from audit.explanation_service import ExplanationService
        from memory.database import Database
        
        db = MagicMock(spec=Database)
        service = ExplanationService(db)
        
        # Mock audit logger with sample events
        request_id = str(uuid4())
        mock_events = [
            {
                "id": str(uuid4()),
                "request_id": request_id,
                "event_type": "CONFIRMATION_REQUESTED",
                "event_data": json.dumps({"tool_name": "trigger_sync"}),
                "timestamp": datetime.utcnow().isoformat() + "Z",
            }
        ]
        service._audit_logger.get_events_by_request_id = MagicMock(return_value=mock_events)
        
        result = service.explain_decision(
            request_id=request_id,
            decision_type="confirmation_required",
        )
        
        assert "summary" in result
        assert "decision_basis" in result
        assert "laws_applied" in result
        assert "referenced_logs" in result
        assert "confidence" in result
        assert isinstance(result["confidence"], float)
        assert 0 <= result["confidence"] <= 1

    def test_law_inference_for_confirmation(self):
        """Test that LAW 1 is inferred for confirmation events."""
        from audit.explanation_service import ExplanationService
        from memory.database import Database
        
        db = MagicMock(spec=Database)
        service = ExplanationService(db)
        
        request_id = str(uuid4())
        mock_events = [
            {
                "id": str(uuid4()),
                "request_id": request_id,
                "event_type": "CONFIRMATION_REQUESTED",
                "event_data": json.dumps({"tool_name": "trigger_sync"}),
                "timestamp": datetime.utcnow().isoformat() + "Z",
            }
        ]
        service._audit_logger.get_events_by_request_id = MagicMock(return_value=mock_events)
        
        result = service.explain_decision(
            request_id=request_id,
            decision_type="confirmation_required",
        )
        
        assert any("LAW 1" in law for law in result["laws_applied"])


class TestExplainDecisionTool:
    """Tests for explain_decision tool function."""

    def test_explain_decision_returns_status_ok(self):
        """Test that explain_decision returns status ok on success."""
        from tools.explanation_tools import explain_decision
        
        with patch('tools.explanation_tools.Database') as mock_db_class:
            with patch('tools.explanation_tools.ExplanationService') as mock_service_class:
                mock_service = MagicMock()
                mock_service.explain_decision.return_value = {
                    "summary": "Test explanation",
                    "decision_basis": ["Test basis"],
                    "laws_applied": ["LAW 1"],
                    "referenced_logs": [],
                    "confidence": 0.9,
                }
                mock_service_class.return_value = mock_service
                
                result = explain_decision(
                    request_id=str(uuid4()),
                    decision_type="confirmation_required",
                )
                
                assert result["status"] == "ok"
                assert "explanation" in result

    def test_explain_decision_handles_unavailable(self):
        """Test that explain_decision handles ExplanationUnavailable gracefully."""
        from tools.explanation_tools import explain_decision
        from audit.explanation_service import ExplanationUnavailable
        
        with patch('tools.explanation_tools.Database') as mock_db_class:
            with patch('tools.explanation_tools.ExplanationService') as mock_service_class:
                mock_service = MagicMock()
                mock_service.explain_decision.side_effect = ExplanationUnavailable("No data")
                mock_service_class.return_value = mock_service
                
                result = explain_decision(
                    request_id=str(uuid4()),
                    decision_type="confirmation_required",
                )
                
                assert result["status"] == "unavailable"
                assert "message" in result

    def test_explain_decision_handles_value_error(self):
        """Test that explain_decision handles ValueError gracefully."""
        from tools.explanation_tools import explain_decision
        
        with patch('tools.explanation_tools.Database') as mock_db_class:
            with patch('tools.explanation_tools.ExplanationService') as mock_service_class:
                mock_service = MagicMock()
                mock_service.explain_decision.side_effect = ValueError("Invalid input")
                mock_service_class.return_value = mock_service
                
                result = explain_decision(
                    request_id=str(uuid4()),
                    decision_type="confirmation_required",
                )
                
                assert result["status"] == "error"
                assert "message" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
