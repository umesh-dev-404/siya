"""
Resource Monitor

Monitors system resources for exhaustion detection.
Per DIP Phase 8: Resource exhaustion handling.

Enforces:
- LAW 12 — FAILURE TRANSPARENCY
"""

import logging
from typing import Any, Dict, Optional

try:
    import psutil
except ImportError:
    psutil = None  # Optional dependency

logger = logging.getLogger(__name__)


class ResourceMonitor:
    """
    Resource monitor for system resources.

    Per DIP Phase 8:
    - Monitor RAM, CPU, disk usage
    - Detect resource exhaustion
    - Trigger failures when thresholds exceeded

    Enforces:
    - LAW 12 — FAILURE TRANSPARENCY
    """

    def __init__(
        self,
        ram_threshold: float = 0.9,  # 90% RAM usage
        cpu_threshold: float = 0.95,  # 95% CPU usage
        disk_threshold: float = 0.95,  # 95% disk usage
    ) -> None:
        """
        Initialize resource monitor.

        Args:
            ram_threshold: RAM usage threshold (0.0-1.0)
            cpu_threshold: CPU usage threshold (0.0-1.0)
            disk_threshold: Disk usage threshold (0.0-1.0)
        """
        self._ram_threshold = ram_threshold
        self._cpu_threshold = cpu_threshold
        self._disk_threshold = disk_threshold

    def check_resources(self) -> Dict[str, Any]:
        """
        Check system resources.

        Returns:
            Resource status dictionary

        Note:
            Phase 8: Basic resource monitoring.
            Full monitoring requires Pi hardware for accurate measurements.
        """
        if psutil is None:
            logger.warning("psutil not available - resource monitoring disabled")
            return {
                "ram_usage": 0.0,
                "cpu_usage": 0.0,
                "disk_usage": 0.0,
                "healthy": True,
                "psutil_available": False,
            }

        try:
            # Get RAM usage
            ram = psutil.virtual_memory()
            ram_usage = ram.percent / 100.0

            # Get CPU usage
            cpu_usage = psutil.cpu_percent(interval=0.1) / 100.0

            # Get disk usage
            disk = psutil.disk_usage("/")
            disk_usage = disk.percent / 100.0

            status = {
                "ram_usage": ram_usage,
                "cpu_usage": cpu_usage,
                "disk_usage": disk_usage,
                "ram_available_mb": ram.available / (1024 * 1024),
                "disk_available_gb": disk.free / (1024 * 1024 * 1024),
                "thresholds": {
                    "ram": self._ram_threshold,
                    "cpu": self._cpu_threshold,
                    "disk": self._disk_threshold,
                },
            }

            # Check for threshold violations
            violations = []
            if ram_usage >= self._ram_threshold:
                violations.append("RAM")
            if cpu_usage >= self._cpu_threshold:
                violations.append("CPU")
            if disk_usage >= self._disk_threshold:
                violations.append("DISK")

            status["violations"] = violations
            status["healthy"] = len(violations) == 0

            return status

        except Exception as e:
            logger.error(f"Resource check failed: {e}", exc_info=True)
            return {
                "ram_usage": 0.0,
                "cpu_usage": 0.0,
                "disk_usage": 0.0,
                "healthy": False,
                "error": str(e),
            }

    def is_healthy(self) -> bool:
        """
        Check if system resources are healthy.

        Returns:
            True if all resources below thresholds, False otherwise
        """
        status = self.check_resources()
        return status.get("healthy", False)
