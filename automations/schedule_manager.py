"""
Schedule Manager

Manages automation schedules with systemd backend.
Per Phase 14: Timer Integration.

LAW Compliance:
- LAW 2: Schedules trigger via orchestrator
- LAW 10: Serial execution preserved
- LAW 13: All schedule operations logged
"""

import json
import logging
import sqlite3
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

from automations.systemd_timer import (
    SystemdTimerGenerator,
    TimerSchedule,
    TimerUnit,
    get_timer_generator,
)

logger = logging.getLogger(__name__)


@dataclass
class Schedule:
    """Automation schedule definition."""
    
    schedule_id: str
    automation_id: str
    name: str
    description: str
    
    # Schedule configuration
    on_calendar: Optional[str] = None  # Calendar expression
    interval: Optional[str] = None  # Interval (e.g., "15min", "1h")
    on_boot_delay: Optional[str] = None  # Delay after boot
    
    # Status
    enabled: bool = True
    created_at: Optional[str] = None
    last_triggered: Optional[str] = None
    
    # Metadata
    requires_network: bool = False
    
    def to_timer_schedule(self) -> TimerSchedule:
        """Convert to TimerSchedule for systemd."""
        return TimerSchedule(
            on_calendar=self.on_calendar,
            on_unit_active_sec=self.interval,
            on_boot_sec=self.on_boot_delay,
            persistent=True,
        )
    
    def to_timer_unit(self) -> TimerUnit:
        """Convert to TimerUnit for systemd."""
        return TimerUnit(
            name=self.schedule_id,
            description=self.description,
            automation_id=self.automation_id,
            schedule=self.to_timer_schedule(),
            requires_network=self.requires_network,
        )


class ScheduleManager:
    """
    Manages automation schedules.
    
    Provides:
    - Schedule CRUD operations
    - Persistence to SQLite
    - Integration with systemd timer generator
    
    LAW Compliance:
    - LAW 2: All scheduled executions go through orchestrator
    - LAW 13: All operations logged
    """
    
    def __init__(
        self,
        db_path: Optional[Path] = None,
        timer_generator: Optional[SystemdTimerGenerator] = None,
    ) -> None:
        """
        Initialize the schedule manager.
        
        Args:
            db_path: Path to SQLite database
            timer_generator: Timer generator instance
        """
        self._db_path = db_path or Path("./schedules.db")
        self._timer_gen = timer_generator or get_timer_generator()
        
        self._init_database()
        
        logger.info(
            "ScheduleManager initialized",
            extra={"db_path": str(self._db_path)},
        )
    
    def _init_database(self) -> None:
        """Initialize the schedules database."""
        conn = sqlite3.connect(str(self._db_path))
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS schedules (
                schedule_id TEXT PRIMARY KEY,
                automation_id TEXT NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                on_calendar TEXT,
                interval TEXT,
                on_boot_delay TEXT,
                enabled INTEGER DEFAULT 1,
                requires_network INTEGER DEFAULT 0,
                created_at TEXT,
                last_triggered TEXT
            )
        """)
        
        conn.commit()
        conn.close()
    
    def create_schedule(
        self,
        automation_id: str,
        name: str,
        description: str = "",
        on_calendar: Optional[str] = None,
        interval: Optional[str] = None,
        on_boot_delay: Optional[str] = None,
        requires_network: bool = False,
        install_timer: bool = True,
    ) -> Dict[str, Any]:
        """
        Create a new schedule.
        
        Args:
            automation_id: ID of automation to schedule
            name: Schedule name
            description: Schedule description
            on_calendar: Calendar expression (e.g., "Mon..Fri 09:00")
            interval: Interval (e.g., "15min", "1h")
            on_boot_delay: Boot delay (e.g., "5min")
            requires_network: Whether automation requires network
            install_timer: Install systemd timer
            
        Returns:
            Result dictionary with schedule info
        """
        schedule_id = str(uuid4())[:8]
        created_at = datetime.now().isoformat()
        
        schedule = Schedule(
            schedule_id=schedule_id,
            automation_id=automation_id,
            name=name,
            description=description,
            on_calendar=on_calendar,
            interval=interval,
            on_boot_delay=on_boot_delay,
            enabled=True,
            requires_network=requires_network,
            created_at=created_at,
        )
        
        # Validate schedule
        timer_schedule = schedule.to_timer_schedule()
        if not timer_schedule.validate():
            return {
                "success": False,
                "error": "Invalid schedule: must specify on_calendar, interval, or on_boot_delay",
            }
        
        # Save to database
        conn = sqlite3.connect(str(self._db_path))
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO schedules (
                schedule_id, automation_id, name, description,
                on_calendar, interval, on_boot_delay,
                enabled, requires_network, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            schedule.schedule_id,
            schedule.automation_id,
            schedule.name,
            schedule.description,
            schedule.on_calendar,
            schedule.interval,
            schedule.on_boot_delay,
            1 if schedule.enabled else 0,
            1 if schedule.requires_network else 0,
            schedule.created_at,
        ))
        
        conn.commit()
        conn.close()
        
        logger.info(
            f"Schedule created: {schedule_id}",
            extra={
                "schedule_id": schedule_id,
                "automation_id": automation_id,
            },
        )
        
        result = {
            "success": True,
            "schedule_id": schedule_id,
            "automation_id": automation_id,
            "name": name,
        }
        
        # Install timer if requested
        if install_timer:
            timer_result = self._timer_gen.install_timer(
                schedule.to_timer_unit(),
                enable=True,
            )
            result["timer_installed"] = timer_result["success"]
            if not timer_result["success"]:
                result["timer_error"] = timer_result.get("error")
        
        return result
    
    def delete_schedule(self, schedule_id: str) -> Dict[str, Any]:
        """
        Delete a schedule.
        
        Args:
            schedule_id: Schedule ID
            
        Returns:
            Result dictionary
        """
        # Uninstall timer first
        timer_result = self._timer_gen.uninstall_timer(schedule_id)
        
        # Delete from database
        conn = sqlite3.connect(str(self._db_path))
        cursor = conn.cursor()
        
        cursor.execute(
            "DELETE FROM schedules WHERE schedule_id = ?",
            (schedule_id,)
        )
        
        deleted = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        logger.info(f"Schedule deleted: {schedule_id}")
        
        return {
            "success": deleted,
            "schedule_id": schedule_id,
            "timer_uninstalled": timer_result["success"],
        }
    
    def enable_schedule(self, schedule_id: str) -> Dict[str, Any]:
        """Enable a schedule."""
        return self._set_enabled(schedule_id, True)
    
    def disable_schedule(self, schedule_id: str) -> Dict[str, Any]:
        """Disable a schedule."""
        return self._set_enabled(schedule_id, False)
    
    def _set_enabled(self, schedule_id: str, enabled: bool) -> Dict[str, Any]:
        """Set schedule enabled state."""
        conn = sqlite3.connect(str(self._db_path))
        cursor = conn.cursor()
        
        cursor.execute(
            "UPDATE schedules SET enabled = ? WHERE schedule_id = ?",
            (1 if enabled else 0, schedule_id)
        )
        
        updated = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        # Start/stop timer
        if self._timer_gen.is_systemd_available():
            timer_name = f"siya-{schedule_id}.timer"
            if enabled:
                self._timer_gen._run_systemctl("start", timer_name)
            else:
                self._timer_gen._run_systemctl("stop", timer_name)
        
        logger.info(f"Schedule {'enabled' if enabled else 'disabled'}: {schedule_id}")
        
        return {
            "success": updated,
            "schedule_id": schedule_id,
            "enabled": enabled,
        }
    
    def get_schedule(self, schedule_id: str) -> Optional[Schedule]:
        """Get a schedule by ID."""
        conn = sqlite3.connect(str(self._db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT * FROM schedules WHERE schedule_id = ?",
            (schedule_id,)
        )
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        return self._row_to_schedule(row)
    
    def list_schedules(self, automation_id: Optional[str] = None) -> List[Schedule]:
        """List all schedules."""
        conn = sqlite3.connect(str(self._db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        if automation_id:
            cursor.execute(
                "SELECT * FROM schedules WHERE automation_id = ?",
                (automation_id,)
            )
        else:
            cursor.execute("SELECT * FROM schedules")
        
        rows = cursor.fetchall()
        conn.close()
        
        return [self._row_to_schedule(row) for row in rows]
    
    def get_schedule_status(self, schedule_id: str) -> Dict[str, Any]:
        """Get schedule status including timer status."""
        schedule = self.get_schedule(schedule_id)
        
        if not schedule:
            return {
                "success": False,
                "error": f"Schedule not found: {schedule_id}",
            }
        
        timer_status = self._timer_gen.get_timer_status(schedule_id)
        
        return {
            "success": True,
            "schedule_id": schedule_id,
            "automation_id": schedule.automation_id,
            "name": schedule.name,
            "enabled": schedule.enabled,
            "timer_status": timer_status,
            "last_triggered": schedule.last_triggered,
        }
    
    def record_trigger(self, schedule_id: str) -> None:
        """Record that a schedule was triggered."""
        conn = sqlite3.connect(str(self._db_path))
        cursor = conn.cursor()
        
        cursor.execute(
            "UPDATE schedules SET last_triggered = ? WHERE schedule_id = ?",
            (datetime.now().isoformat(), schedule_id)
        )
        
        conn.commit()
        conn.close()
    
    def _row_to_schedule(self, row: sqlite3.Row) -> Schedule:
        """Convert database row to Schedule."""
        return Schedule(
            schedule_id=row["schedule_id"],
            automation_id=row["automation_id"],
            name=row["name"],
            description=row["description"] or "",
            on_calendar=row["on_calendar"],
            interval=row["interval"],
            on_boot_delay=row["on_boot_delay"],
            enabled=bool(row["enabled"]),
            requires_network=bool(row["requires_network"]),
            created_at=row["created_at"],
            last_triggered=row["last_triggered"],
        )
    
    def close(self) -> None:
        """Clean up resources."""
        pass  # SQLite connections are per-operation


# Convenience function
_default_manager: Optional[ScheduleManager] = None


def get_schedule_manager(db_path: Optional[Path] = None) -> ScheduleManager:
    """Get or create the default schedule manager."""
    global _default_manager
    if _default_manager is None:
        _default_manager = ScheduleManager(db_path=db_path)
    return _default_manager


def reset_schedule_manager() -> None:
    """Reset the schedule manager (for testing)."""
    global _default_manager
    _default_manager = None
