"""
systemd Timer Generator

Generates systemd .timer and .service unit files for scheduled automations.
Per Phase 14: Timer Integration.

LAW Compliance:
- LAW 2: Timers trigger via orchestrator only (service calls siya-cli)
- LAW 10: Serial execution preserved (one automation at a time)
- LAW 12: Timer failures logged explicitly
- LAW 13: All timer operations logged
"""

import logging
import os
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class TimerSchedule:
    """Schedule configuration for a timer."""
    
    # Calendar schedule (e.g., "Mon..Fri 09:00", "daily", "*:0/15")
    on_calendar: Optional[str] = None
    
    # Interval schedule (e.g., "15min", "1h", "1d")
    on_unit_active_sec: Optional[str] = None
    
    # Boot delay (e.g., "5min" after boot)
    on_boot_sec: Optional[str] = None
    
    # Randomized delay to prevent thundering herd
    randomized_delay_sec: Optional[str] = None
    
    # Whether timer should persist across reboots
    persistent: bool = True
    
    def validate(self) -> bool:
        """Check if at least one schedule type is set."""
        return any([
            self.on_calendar,
            self.on_unit_active_sec,
            self.on_boot_sec,
        ])


@dataclass
class TimerUnit:
    """Represents a systemd timer unit."""
    
    name: str  # Unit name (without .timer suffix)
    description: str
    automation_id: str
    schedule: TimerSchedule
    
    # Optional metadata
    requires_network: bool = False
    extra_env: Dict[str, str] = field(default_factory=dict)
    
    @property
    def timer_name(self) -> str:
        return f"siya-{self.name}.timer"
    
    @property
    def service_name(self) -> str:
        return f"siya-{self.name}.service"


class SystemdTimerGenerator:
    """
    Generates and manages systemd timer units for Siya automations.
    
    Generates:
    - .timer unit (schedule definition)
    - .service unit (automation execution via siya-cli)
    
    Supports:
    - User-level systemd (--user)
    - Install/uninstall/enable/disable
    - Status checking
    
    LAW Compliance:
    - LAW 2: Service calls siya-cli which goes through orchestrator
    - LAW 12: All failures are logged and returned
    """
    
    # Default paths
    USER_SYSTEMD_DIR = Path.home() / ".config" / "systemd" / "user"
    SYSTEM_SYSTEMD_DIR = Path("/etc/systemd/system")
    
    def __init__(
        self,
        user_mode: bool = True,
        systemd_dir: Optional[Path] = None,
        siya_cli_path: Optional[str] = None,
    ) -> None:
        """
        Initialize the timer generator.
        
        Args:
            user_mode: Use user-level systemd (default True)
            systemd_dir: Override systemd unit directory
            siya_cli_path: Path to siya-cli command
        """
        self._user_mode = user_mode
        
        if systemd_dir:
            self._systemd_dir = systemd_dir
        else:
            self._systemd_dir = (
                self.USER_SYSTEMD_DIR if user_mode else self.SYSTEM_SYSTEMD_DIR
            )
        
        # Find siya-cli path
        self._siya_cli = siya_cli_path or self._find_siya_cli()
        
        logger.info(
            "SystemdTimerGenerator initialized",
            extra={
                "user_mode": user_mode,
                "systemd_dir": str(self._systemd_dir),
                "siya_cli": self._siya_cli,
            },
        )
    
    def _find_siya_cli(self) -> str:
        """Find siya-cli in PATH or common locations."""
        # Check if in PATH
        try:
            result = subprocess.run(
                ["which", "siya-cli"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        # Common locations
        common_paths = [
            "/usr/local/bin/siya-cli",
            Path.home() / ".local" / "bin" / "siya-cli",
            Path.home() / "siya" / "venv" / "bin" / "siya-cli",
        ]
        
        for path in common_paths:
            if Path(path).exists():
                return str(path)
        
        # Fallback to module execution
        return "python -m pc_mcp_client.main"
    
    def is_systemd_available(self) -> bool:
        """Check if systemd is available on this system."""
        try:
            result = subprocess.run(
                ["systemctl", "--version"],
                capture_output=True,
                timeout=5,
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def generate_timer_unit(self, timer: TimerUnit) -> str:
        """
        Generate .timer unit file content.
        
        Args:
            timer: Timer unit configuration
            
        Returns:
            Unit file content as string
        """
        lines = [
            "[Unit]",
            f"Description=Siya Timer: {timer.description}",
            "",
            "[Timer]",
        ]
        
        schedule = timer.schedule
        
        if schedule.on_calendar:
            lines.append(f"OnCalendar={schedule.on_calendar}")
        
        if schedule.on_unit_active_sec:
            lines.append(f"OnUnitActiveSec={schedule.on_unit_active_sec}")
        
        if schedule.on_boot_sec:
            lines.append(f"OnBootSec={schedule.on_boot_sec}")
        
        if schedule.randomized_delay_sec:
            lines.append(f"RandomizedDelaySec={schedule.randomized_delay_sec}")
        
        if schedule.persistent:
            lines.append("Persistent=true")
        
        lines.extend([
            "",
            "[Install]",
            "WantedBy=timers.target",
        ])
        
        return "\n".join(lines) + "\n"
    
    def generate_service_unit(self, timer: TimerUnit) -> str:
        """
        Generate .service unit file content.
        
        Args:
            timer: Timer unit configuration
            
        Returns:
            Unit file content as string
        """
        lines = [
            "[Unit]",
            f"Description=Siya Automation: {timer.description}",
        ]
        
        if timer.requires_network:
            lines.append("After=network-online.target")
            lines.append("Wants=network-online.target")
        
        lines.extend([
            "",
            "[Service]",
            "Type=oneshot",
        ])
        
        # Add environment variables
        for key, value in timer.extra_env.items():
            lines.append(f"Environment={key}={value}")
        
        # ExecStart calls siya-cli to trigger the automation
        exec_cmd = f"{self._siya_cli} call trigger_automation --automation_id {timer.automation_id}"
        lines.append(f"ExecStart={exec_cmd}")
        
        # Logging
        lines.append("StandardOutput=journal")
        lines.append("StandardError=journal")
        
        return "\n".join(lines) + "\n"
    
    def install_timer(self, timer: TimerUnit, enable: bool = True) -> Dict[str, Any]:
        """
        Install a timer unit to systemd.
        
        Args:
            timer: Timer unit to install
            enable: Enable timer after installation
            
        Returns:
            Result dictionary with success status
            
        LAW 12: All failures logged explicitly.
        """
        if not self.is_systemd_available():
            return {
                "success": False,
                "error": "systemd not available on this system",
                "timer_name": timer.timer_name,
            }
        
        if not timer.schedule.validate():
            return {
                "success": False,
                "error": "Timer schedule is invalid (no schedule type set)",
                "timer_name": timer.timer_name,
            }
        
        try:
            # Ensure systemd directory exists
            self._systemd_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate unit files
            timer_content = self.generate_timer_unit(timer)
            service_content = self.generate_service_unit(timer)
            
            timer_path = self._systemd_dir / timer.timer_name
            service_path = self._systemd_dir / timer.service_name
            
            # Write unit files
            timer_path.write_text(timer_content)
            service_path.write_text(service_content)
            
            logger.info(
                f"Timer unit files written: {timer.timer_name}",
                extra={
                    "timer_path": str(timer_path),
                    "service_path": str(service_path),
                },
            )
            
            # Reload systemd
            self._run_systemctl("daemon-reload")
            
            # Enable if requested
            if enable:
                self._run_systemctl("enable", timer.timer_name)
                self._run_systemctl("start", timer.timer_name)
            
            return {
                "success": True,
                "timer_name": timer.timer_name,
                "service_name": timer.service_name,
                "timer_path": str(timer_path),
                "service_path": str(service_path),
                "enabled": enable,
            }
            
        except Exception as e:
            logger.error(f"Failed to install timer: {e}")
            return {
                "success": False,
                "error": str(e),
                "timer_name": timer.timer_name,
            }
    
    def uninstall_timer(self, timer_name: str) -> Dict[str, Any]:
        """
        Uninstall a timer unit from systemd.
        
        Args:
            timer_name: Timer name (with or without .timer suffix)
            
        Returns:
            Result dictionary
        """
        if not timer_name.endswith(".timer"):
            timer_name = f"siya-{timer_name}.timer"
        
        service_name = timer_name.replace(".timer", ".service")
        
        try:
            # Stop and disable
            self._run_systemctl("stop", timer_name)
            self._run_systemctl("disable", timer_name)
            
            # Remove files
            timer_path = self._systemd_dir / timer_name
            service_path = self._systemd_dir / service_name
            
            if timer_path.exists():
                timer_path.unlink()
            if service_path.exists():
                service_path.unlink()
            
            # Reload
            self._run_systemctl("daemon-reload")
            
            logger.info(f"Timer uninstalled: {timer_name}")
            
            return {
                "success": True,
                "timer_name": timer_name,
                "service_name": service_name,
            }
            
        except Exception as e:
            logger.error(f"Failed to uninstall timer: {e}")
            return {
                "success": False,
                "error": str(e),
                "timer_name": timer_name,
            }
    
    def get_timer_status(self, timer_name: str) -> Dict[str, Any]:
        """
        Get status of a timer.
        
        Args:
            timer_name: Timer name
            
        Returns:
            Status dictionary
        """
        if not timer_name.endswith(".timer"):
            timer_name = f"siya-{timer_name}.timer"
        
        if not self.is_systemd_available():
            return {
                "timer_name": timer_name,
                "available": False,
                "reason": "systemd not available",
            }
        
        try:
            result = self._run_systemctl("is-active", timer_name, check=False)
            is_active = result.stdout.strip() == "active"
            
            result = self._run_systemctl("is-enabled", timer_name, check=False)
            is_enabled = result.stdout.strip() == "enabled"
            
            # Get next trigger time
            next_trigger = None
            try:
                result = subprocess.run(
                    ["systemctl", "list-timers", timer_name, "--no-legend"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if result.returncode == 0 and result.stdout.strip():
                    # Parse first column (NEXT)
                    parts = result.stdout.strip().split()
                    if len(parts) >= 2:
                        next_trigger = " ".join(parts[:2])
            except Exception:
                pass
            
            return {
                "timer_name": timer_name,
                "available": True,
                "is_active": is_active,
                "is_enabled": is_enabled,
                "next_trigger": next_trigger,
            }
            
        except Exception as e:
            return {
                "timer_name": timer_name,
                "available": False,
                "error": str(e),
            }
    
    def list_siya_timers(self) -> List[Dict[str, Any]]:
        """
        List all Siya timers.
        
        Returns:
            List of timer status dictionaries
        """
        timers = []
        
        if not self._systemd_dir.exists():
            return timers
        
        for path in self._systemd_dir.glob("siya-*.timer"):
            timer_name = path.name
            status = self.get_timer_status(timer_name)
            timers.append(status)
        
        return timers
    
    def _run_systemctl(
        self,
        command: str,
        unit: Optional[str] = None,
        check: bool = True,
    ) -> subprocess.CompletedProcess:
        """Run a systemctl command."""
        cmd = ["systemctl"]
        
        if self._user_mode:
            cmd.append("--user")
        
        cmd.append(command)
        
        if unit:
            cmd.append(unit)
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
        )
        
        if check and result.returncode != 0:
            logger.warning(
                f"systemctl {command} failed",
                extra={"stderr": result.stderr},
            )
        
        return result


# Convenience function
_default_generator: Optional[SystemdTimerGenerator] = None


def get_timer_generator(user_mode: bool = True) -> SystemdTimerGenerator:
    """Get or create the default timer generator."""
    global _default_generator
    if _default_generator is None:
        _default_generator = SystemdTimerGenerator(user_mode=user_mode)
    return _default_generator


def reset_timer_generator() -> None:
    """Reset the timer generator (for testing)."""
    global _default_generator
    _default_generator = None
