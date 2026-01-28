"""
Tests for Phase 23: Operator Observability Dashboard

Tests ObservabilityService and get_system_posture tool.
Enforces LAW 23 — OBSERVABILITY WITHOUT CONTROL.
"""

import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch

from system.observability_service import ObservabilityService
from tools.observability_tools import get_system_posture, register_observability_tools


class TestObservabilityService:
    """Tests for ObservabilityService class."""

    def test_init_without_dependencies(self):
        """Test initialization without dependencies."""
        service = ObservabilityService()
        
        assert service._orchestrator is None
        assert service._resource_monitor is None
        assert service._sync_client is None

    def test_init_with_dependencies(self):
        """Test initialization with dependencies."""
        mock_orchestrator = MagicMock()
        mock_monitor = MagicMock()
        mock_sync = MagicMock()
        
        service = ObservabilityService(
            orchestrator=mock_orchestrator,
            resource_monitor=mock_monitor,
            sync_client=mock_sync,
        )
        
        assert service._orchestrator == mock_orchestrator
        assert service._resource_monitor == mock_monitor
        assert service._sync_client == mock_sync

    def test_get_system_posture_returns_required_fields(self):
        """Per LAW 23: Posture must include all required fields."""
        service = ObservabilityService()
        
        posture = service.get_system_posture()
        
        assert "timestamp" in posture
        assert "queue_depth" in posture
        assert "pending_confirmations" in posture
        assert "recent_errors" in posture
        assert "memory_pressure" in posture
        assert "sync_status" in posture
        assert "uptime" in posture
        assert "health" in posture

    def test_timestamp_is_valid_iso_format(self):
        """Test that timestamp is valid ISO format."""
        service = ObservabilityService()
        
        posture = service.get_system_posture()
        
        # Should not raise
        timestamp_str = posture["timestamp"]
        assert timestamp_str.endswith("Z")
        datetime.fromisoformat(timestamp_str.rstrip("Z"))

    def test_queue_depth_with_orchestrator(self):
        """Test queue depth retrieval with orchestrator."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.get_queue_size.return_value = 5
        
        service = ObservabilityService(orchestrator=mock_orchestrator)
        posture = service.get_system_posture()
        
        assert posture["queue_depth"] == 5

    def test_queue_depth_without_orchestrator(self):
        """Test queue depth returns 0 without orchestrator."""
        service = ObservabilityService()
        
        posture = service.get_system_posture()
        
        assert posture["queue_depth"] == 0

    def test_pending_confirmations_with_orchestrator(self):
        """Test pending confirmations retrieval."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.get_pending_confirmations.return_value = {"a": {}, "b": {}}
        mock_orchestrator.get_queue_size.return_value = 0  # Also mock queue size
        
        service = ObservabilityService(orchestrator=mock_orchestrator)
        posture = service.get_system_posture()
        
        assert posture["pending_confirmations"] == 2

    def test_memory_pressure_includes_status(self):
        """Test that memory pressure includes status field."""
        service = ObservabilityService()
        
        posture = service.get_system_posture()
        
        assert "status" in posture["memory_pressure"]

    def test_sync_status_includes_connected(self):
        """Test that sync status includes connected field."""
        service = ObservabilityService()
        
        posture = service.get_system_posture()
        
        assert "connected" in posture["sync_status"]

    def test_uptime_includes_boot_time(self):
        """Test that uptime includes boot time."""
        service = ObservabilityService()
        
        posture = service.get_system_posture()
        
        assert "boot_time" in posture["uptime"]
        assert "uptime_seconds" in posture["uptime"]
        assert "uptime_human" in posture["uptime"]

    def test_health_is_valid_status(self):
        """Test that health is a valid status string."""
        service = ObservabilityService()
        
        posture = service.get_system_posture()
        
        valid_statuses = ["healthy", "warning", "critical", "unknown"]
        assert posture["health"] in valid_statuses

    def test_uptime_format_days(self):
        """Test uptime formatting with days."""
        service = ObservabilityService()
        
        formatted = service._format_uptime(90061)  # 1d 1h 1m 1s
        
        assert "1d" in formatted
        assert "1h" in formatted

    def test_uptime_format_hours_only(self):
        """Test uptime formatting with only hours."""
        service = ObservabilityService()
        
        formatted = service._format_uptime(3661)  # 1h 1m 1s
        
        assert "d" not in formatted
        assert "1h" in formatted

    def test_health_critical_on_high_memory(self):
        """Test that critical memory triggers critical health."""
        service = ObservabilityService()
        
        # Mock memory pressure to return critical
        with patch.object(service, '_get_memory_pressure') as mock_mem:
            mock_mem.return_value = {"status": "critical"}
            
            health = service._calculate_overall_health()
            
            assert health == "critical"


class TestGetSystemPostureTool:
    """Tests for get_system_posture tool function."""

    def test_returns_status_ok(self):
        """Test that tool returns status ok on success."""
        result = get_system_posture()
        
        assert result["status"] == "ok"
        assert "posture" in result

    def test_posture_contains_required_fields(self):
        """Test that posture contains all required fields."""
        result = get_system_posture()
        
        posture = result["posture"]
        assert "timestamp" in posture
        assert "queue_depth" in posture
        assert "health" in posture

    def test_handles_exception_gracefully(self):
        """Test graceful exception handling."""
        with patch('tools.observability_tools.ObservabilityService') as mock_class:
            mock_service = MagicMock()
            mock_service.get_system_posture.side_effect = Exception("Test error")
            mock_class.return_value = mock_service
            
            result = get_system_posture()
            
            assert result["status"] == "error"
            assert "message" in result


class TestToolRegistration:
    """Tests for tool registration."""

    def test_register_observability_tools(self):
        """Test that observability tools can be registered."""
        mock_executor = MagicMock()
        
        register_observability_tools(mock_executor)
        
        # Verify register was called with tool name
        mock_executor.register.assert_called_once()
        call_args = mock_executor.register.call_args
        assert call_args[0][0] == "get_system_posture"


class TestLaw23Compliance:
    """Tests specifically for LAW 23 compliance."""

    def test_no_mutation_methods(self):
        """Per LAW 23: ObservabilityService should have no mutation methods."""
        service = ObservabilityService()
        
        # Get all public methods
        public_methods = [m for m in dir(service) if not m.startswith('_')]
        
        # None should start with set_, delete_, update_, create_, etc.
        mutation_prefixes = ['set_', 'delete_', 'update_', 'create_', 'modify_', 'add_', 'remove_']
        
        for method in public_methods:
            for prefix in mutation_prefixes:
                assert not method.startswith(prefix), f"Found mutation method: {method}"

    def test_read_only_tool_has_no_side_effects(self):
        """Per LAW 23: Tool should be read-only."""
        # Call multiple times
        result1 = get_system_posture()
        result2 = get_system_posture()
        
        # Both should succeed
        assert result1["status"] == "ok"
        assert result2["status"] == "ok"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
