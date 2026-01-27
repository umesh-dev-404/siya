"""
File Channel

Delivers notifications to a file.
Useful for cron jobs, scripts, and persistent logging.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from notifications.channels.base import Channel
from notifications.notification import Notification

logger = logging.getLogger(__name__)


class FileChannel(Channel):
    """
    File notification channel.
    
    Writes notifications to a file in JSON or text format.
    Useful for:
    - Cron job monitoring
    - Script integration
    - Persistent notification log
    """
    
    def __init__(
        self,
        file_path: Optional[Path] = None,
        format: str = "json",
        max_size_mb: float = 10.0,
    ) -> None:
        """
        Initialize file channel.
        
        Args:
            file_path: Output file path
            format: Output format ("json" or "text")
            max_size_mb: Maximum file size before rotation
        """
        self._file_path = file_path or Path("./notifications.log")
        self._format = format
        self._max_size_bytes = int(max_size_mb * 1024 * 1024)
    
    @property
    def name(self) -> str:
        return "file"
    
    def deliver(self, notification: Notification) -> bool:
        """Deliver notification to file."""
        try:
            self._ensure_directory()
            self._check_rotation()
            
            with open(self._file_path, "a", encoding="utf-8") as f:
                if self._format == "json":
                    entry = {
                        "timestamp": datetime.now().isoformat(),
                        "notification": notification.to_dict(),
                    }
                    f.write(json.dumps(entry) + "\n")
                else:
                    line = self._format_text(notification)
                    f.write(line + "\n")
            
            return True
            
        except Exception as e:
            logger.error(f"File delivery failed: {e}")
            return False
    
    def _format_text(self, notification: Notification) -> str:
        """Format notification as text line."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        type_name = notification.notification_type.value.upper()
        priority = "!" * notification.priority.value
        
        return f"[{timestamp}] [{type_name}] {priority} {notification.title}: {notification.message}"
    
    def _ensure_directory(self) -> None:
        """Ensure output directory exists."""
        self._file_path.parent.mkdir(parents=True, exist_ok=True)
    
    def _check_rotation(self) -> None:
        """Rotate file if too large."""
        if not self._file_path.exists():
            return
        
        if self._file_path.stat().st_size > self._max_size_bytes:
            # Rotate: rename current to .old and start fresh
            old_path = self._file_path.with_suffix(".old")
            if old_path.exists():
                old_path.unlink()
            self._file_path.rename(old_path)
            logger.info(f"Rotated notification file: {self._file_path}")
    
    def is_available(self) -> bool:
        """Check if file channel is available."""
        try:
            self._ensure_directory()
            return True
        except Exception:
            return False
    
    def read_recent(self, count: int = 10) -> list:
        """
        Read recent notifications from file.
        
        Args:
            count: Number of recent notifications
            
        Returns:
            List of notification dictionaries
        """
        if not self._file_path.exists():
            return []
        
        try:
            with open(self._file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
            
            recent = lines[-count:] if len(lines) > count else lines
            
            if self._format == "json":
                return [json.loads(line) for line in recent if line.strip()]
            else:
                return [{"text": line.strip()} for line in recent if line.strip()]
                
        except Exception as e:
            logger.error(f"Failed to read notifications: {e}")
            return []
