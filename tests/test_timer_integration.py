"""
Unit Tests for Phase 14 Timer Integration

Tests for:
- Timer Generator
- Schedule Manager
- Timer Tools
"""

import os
import sqlite3
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


class TestTimerSchedule:
    """Tests for TimerSchedule dataclass."""

    def test_validate_with_calendar(self):
        """Test validation with calendar schedule."""
        from automations.systemd_timer import TimerSchedule
        
        schedule = TimerSchedule(on_calendar="Mon..Fri 09:00")
        assert schedule.validate() is True

    def test_validate_with_interval(self):
        """Test validation with interval schedule."""
        from automations.systemd_timer import TimerSchedule
        
        schedule = TimerSchedule(on_unit_active_sec="15min")
        assert schedule.validate() is True

    def test_validate_with_boot(self):
        """Test validation with boot delay."""
        from automations.systemd_timer import TimerSchedule
        
        schedule = TimerSchedule(on_boot_sec="5min")
        assert schedule.validate() is True

    def test_validate_empty(self):
        """Test validation fails without schedule type."""
        from automations.systemd_timer import TimerSchedule
        
        schedule = TimerSchedule()
        assert schedule.validate() is False


class TestTimerUnit:
    """Tests for TimerUnit dataclass."""

    def test_timer_name(self):
        """Test timer name generation."""
        from automations.systemd_timer import TimerUnit, TimerSchedule
        
        schedule = TimerSchedule(on_calendar="daily")
        unit = TimerUnit(
            name="test-task",
            description="Test",
            automation_id="auto-1",
            schedule=schedule,
        )
        
        assert unit.timer_name == "siya-test-task.timer"
        assert unit.service_name == "siya-test-task.service"


class TestSystemdTimerGenerator:
    """Tests for SystemdTimerGenerator."""

    @pytest.fixture
    def temp_systemd_dir(self):
        """Create temporary systemd directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def generator(self, temp_systemd_dir):
        """Create generator with temp directory."""
        from automations.systemd_timer import SystemdTimerGenerator
        
        return SystemdTimerGenerator(
            user_mode=True,
            systemd_dir=temp_systemd_dir,
            siya_cli_path="/usr/local/bin/siya-cli",
        )

    def test_generate_timer_unit_calendar(self, generator):
        """Test timer unit generation with calendar."""
        from automations.systemd_timer import TimerUnit, TimerSchedule
        
        schedule = TimerSchedule(on_calendar="Mon..Fri 09:00", persistent=True)
        unit = TimerUnit(
            name="morning-check",
            description="Morning check",
            automation_id="check-1",
            schedule=schedule,
        )
        
        content = generator.generate_timer_unit(unit)
        
        assert "[Unit]" in content
        assert "Description=Siya Timer: Morning check" in content
        assert "[Timer]" in content
        assert "OnCalendar=Mon..Fri 09:00" in content
        assert "Persistent=true" in content
        assert "[Install]" in content

    def test_generate_timer_unit_interval(self, generator):
        """Test timer unit generation with interval."""
        from automations.systemd_timer import TimerUnit, TimerSchedule
        
        schedule = TimerSchedule(on_unit_active_sec="15min")
        unit = TimerUnit(
            name="periodic",
            description="Periodic task",
            automation_id="task-1",
            schedule=schedule,
        )
        
        content = generator.generate_timer_unit(unit)
        
        assert "OnUnitActiveSec=15min" in content

    def test_generate_service_unit(self, generator):
        """Test service unit generation."""
        from automations.systemd_timer import TimerUnit, TimerSchedule
        
        schedule = TimerSchedule(on_calendar="daily")
        unit = TimerUnit(
            name="daily-task",
            description="Daily task",
            automation_id="task-123",
            schedule=schedule,
            requires_network=True,
        )
        
        content = generator.generate_service_unit(unit)
        
        assert "[Unit]" in content
        assert "Description=Siya Automation: Daily task" in content
        assert "After=network-online.target" in content
        assert "[Service]" in content
        assert "Type=oneshot" in content
        assert "ExecStart=/usr/local/bin/siya-cli call trigger_automation --automation_id task-123" in content

    def test_install_writes_files(self, generator, temp_systemd_dir):
        """Test install writes unit files."""
        from automations.systemd_timer import TimerUnit, TimerSchedule
        
        schedule = TimerSchedule(on_calendar="daily")
        unit = TimerUnit(
            name="test",
            description="Test",
            automation_id="auto-1",
            schedule=schedule,
        )
        
        # Mock systemctl
        with patch.object(generator, '_run_systemctl') as mock_ctl:
            with patch.object(generator, 'is_systemd_available', return_value=True):
                result = generator.install_timer(unit, enable=False)
        
        assert result["success"] is True
        assert (temp_systemd_dir / "siya-test.timer").exists()
        assert (temp_systemd_dir / "siya-test.service").exists()

    def test_install_fails_without_systemd(self, generator):
        """Test install fails gracefully without systemd."""
        from automations.systemd_timer import TimerUnit, TimerSchedule
        
        schedule = TimerSchedule(on_calendar="daily")
        unit = TimerUnit(
            name="test",
            description="Test",
            automation_id="auto-1",
            schedule=schedule,
        )
        
        with patch.object(generator, 'is_systemd_available', return_value=False):
            result = generator.install_timer(unit)
        
        assert result["success"] is False
        assert "systemd not available" in result["error"]

    def test_list_siya_timers(self, generator, temp_systemd_dir):
        """Test listing timers."""
        # Create some timer files
        (temp_systemd_dir / "siya-task1.timer").write_text("[Timer]\n")
        (temp_systemd_dir / "siya-task2.timer").write_text("[Timer]\n")
        (temp_systemd_dir / "other.timer").write_text("[Timer]\n")  # Not siya
        
        timers = generator.list_siya_timers()
        
        assert len(timers) == 2
        names = [t["timer_name"] for t in timers]
        assert "siya-task1.timer" in names
        assert "siya-task2.timer" in names


class TestScheduleManager:
    """Tests for ScheduleManager."""

    @pytest.fixture
    def temp_db(self):
        """Create temporary database."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            yield Path(f.name)
        os.unlink(f.name)

    @pytest.fixture
    def mock_timer_gen(self):
        """Create mock timer generator."""
        mock = MagicMock()
        mock.is_systemd_available.return_value = False
        mock.install_timer.return_value = {"success": True}
        mock.uninstall_timer.return_value = {"success": True}
        mock.get_timer_status.return_value = {"available": False}
        return mock

    @pytest.fixture
    def manager(self, temp_db, mock_timer_gen):
        """Create manager with temp db."""
        from automations.schedule_manager import ScheduleManager
        
        return ScheduleManager(
            db_path=temp_db,
            timer_generator=mock_timer_gen,
        )

    def test_create_schedule(self, manager):
        """Test creating a schedule."""
        result = manager.create_schedule(
            automation_id="auto-1",
            name="Daily Check",
            on_calendar="daily",
            install_timer=False,
        )
        
        assert result["success"] is True
        assert "schedule_id" in result

    def test_create_schedule_invalid(self, manager):
        """Test creating invalid schedule fails."""
        result = manager.create_schedule(
            automation_id="auto-1",
            name="Invalid",
            # No schedule type specified
            install_timer=False,
        )
        
        assert result["success"] is False
        assert "Invalid schedule" in result["error"]

    def test_list_schedules(self, manager):
        """Test listing schedules."""
        manager.create_schedule(
            automation_id="auto-1",
            name="Task 1",
            on_calendar="daily",
            install_timer=False,
        )
        manager.create_schedule(
            automation_id="auto-2",
            name="Task 2",
            interval="1h",
            install_timer=False,
        )
        
        schedules = manager.list_schedules()
        
        assert len(schedules) == 2

    def test_delete_schedule(self, manager):
        """Test deleting a schedule."""
        result = manager.create_schedule(
            automation_id="auto-1",
            name="To Delete",
            on_calendar="daily",
            install_timer=False,
        )
        
        schedule_id = result["schedule_id"]
        
        delete_result = manager.delete_schedule(schedule_id)
        
        assert delete_result["success"] is True
        assert manager.get_schedule(schedule_id) is None

    def test_enable_disable_schedule(self, manager):
        """Test enabling and disabling schedules."""
        result = manager.create_schedule(
            automation_id="auto-1",
            name="Test",
            on_calendar="daily",
            install_timer=False,
        )
        
        schedule_id = result["schedule_id"]
        
        # Disable
        manager.disable_schedule(schedule_id)
        schedule = manager.get_schedule(schedule_id)
        assert schedule.enabled is False
        
        # Enable
        manager.enable_schedule(schedule_id)
        schedule = manager.get_schedule(schedule_id)
        assert schedule.enabled is True


class TestTimerTools:
    """Tests for timer tools."""

    @pytest.fixture
    def temp_db(self):
        """Create temporary database."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            yield Path(f.name)
        os.unlink(f.name)

    def test_list_scheduled_automations(self, temp_db):
        """Test list_scheduled_automations tool."""
        from tools.timer_tools import list_scheduled_automations
        
        # Mock at the source module
        with patch('automations.schedule_manager.get_schedule_manager') as mock_get_mgr:
            with patch('automations.systemd_timer.get_timer_generator') as mock_get_gen:
                mock_mgr = MagicMock()
                mock_mgr.list_schedules.return_value = []
                mock_get_mgr.return_value = mock_mgr
                
                mock_gen = MagicMock()
                mock_gen.is_systemd_available.return_value = False
                mock_get_gen.return_value = mock_gen
                
                result = list_scheduled_automations()
        
        assert result["success"] is True
        assert "schedules" in result

    def test_schedule_automation(self, temp_db):
        """Test schedule_automation tool."""
        from tools.timer_tools import schedule_automation
        
        with patch('automations.schedule_manager.get_schedule_manager') as mock_get_mgr:
            mock_mgr = MagicMock()
            mock_mgr.create_schedule.return_value = {
                "success": True,
                "schedule_id": "test-123",
            }
            mock_get_mgr.return_value = mock_mgr
            
            result = schedule_automation(
                automation_id="auto-1",
                name="Test",
                on_calendar="daily",
            )
        
        assert result["success"] is True

    def test_unschedule_automation(self):
        """Test unschedule_automation tool."""
        from tools.timer_tools import unschedule_automation
        
        with patch('automations.schedule_manager.get_schedule_manager') as mock_get_mgr:
            mock_mgr = MagicMock()
            mock_mgr.delete_schedule.return_value = {
                "success": True,
            }
            mock_get_mgr.return_value = mock_mgr
            
            result = unschedule_automation("test-123")
        
        assert result["success"] is True


class TestLawCompliance:
    """Tests for LAW compliance in timer integration."""

    def test_law_2_timer_uses_orchestrator(self):
        """Test LAW 2: Timers go through orchestrator (via siya-cli)."""
        from automations.systemd_timer import (
            SystemdTimerGenerator,
            TimerUnit,
            TimerSchedule,
        )
        
        gen = SystemdTimerGenerator(siya_cli_path="/usr/local/bin/siya-cli")
        schedule = TimerSchedule(on_calendar="daily")
        unit = TimerUnit(
            name="test",
            description="Test",
            automation_id="auto-1",
            schedule=schedule,
        )
        
        service_content = gen.generate_service_unit(unit)
        
        # Service must call siya-cli which goes through orchestrator
        assert "siya-cli call trigger_automation" in service_content

    def test_timer_tools_require_confirmation(self):
        """Test LAW 1: schedule/unschedule require confirmation."""
        from tools.timer_tools import TIMER_TOOL_SCHEMAS
        
        schedule_tool = next(
            t for t in TIMER_TOOL_SCHEMAS if t["name"] == "schedule_automation"
        )
        unschedule_tool = next(
            t for t in TIMER_TOOL_SCHEMAS if t["name"] == "unschedule_automation"
        )
        
        assert schedule_tool["requires_confirmation"] is True
        assert unschedule_tool["requires_confirmation"] is True
        
        # Read-only tools don't require confirmation
        list_tool = next(
            t for t in TIMER_TOOL_SCHEMAS if t["name"] == "list_scheduled_automations"
        )
        assert list_tool["requires_confirmation"] is False
