"""
Console Channel

Delivers notifications to console/terminal.
"""

import logging
import sys
from typing import TextIO

from notifications.channels.base import Channel
from notifications.notification import Notification, NotificationType, Priority

logger = logging.getLogger(__name__)


# ANSI color codes
COLORS = {
    "reset": "\033[0m",
    "bold": "\033[1m",
    "red": "\033[31m",
    "green": "\033[32m",
    "yellow": "\033[33m",
    "blue": "\033[34m",
    "magenta": "\033[35m",
    "cyan": "\033[36m",
}

TYPE_COLORS = {
    NotificationType.INFO: "blue",
    NotificationType.SUCCESS: "green",
    NotificationType.WARNING: "yellow",
    NotificationType.ERROR: "red",
    NotificationType.ALERT: "magenta",
    NotificationType.ACTION_REQUIRED: "cyan",
}

TYPE_ICONS = {
    NotificationType.INFO: "ℹ️",
    NotificationType.SUCCESS: "✅",
    NotificationType.WARNING: "⚠️",
    NotificationType.ERROR: "❌",
    NotificationType.ALERT: "🚨",
    NotificationType.ACTION_REQUIRED: "👉",
}


class ConsoleChannel(Channel):
    """
    Console notification channel.
    
    Outputs notifications to stdout with optional coloring.
    """
    
    def __init__(
        self,
        output: TextIO = sys.stdout,
        use_colors: bool = True,
        use_icons: bool = True,
    ) -> None:
        """
        Initialize console channel.
        
        Args:
            output: Output stream (default: stdout)
            use_colors: Use ANSI colors
            use_icons: Use emoji icons
        """
        self._output = output
        self._use_colors = use_colors and self._supports_colors()
        self._use_icons = use_icons
    
    @property
    def name(self) -> str:
        return "console"
    
    def _supports_colors(self) -> bool:
        """Check if terminal supports colors."""
        try:
            return hasattr(self._output, 'isatty') and self._output.isatty()
        except Exception:
            return False
    
    def deliver(self, notification: Notification) -> bool:
        """Deliver notification to console."""
        try:
            message = self._format_notification(notification)
            print(message, file=self._output)
            return True
        except Exception as e:
            logger.error(f"Console delivery failed: {e}")
            return False
    
    def _format_notification(self, notification: Notification) -> str:
        """Format notification for console output."""
        parts = []
        
        # Icon
        if self._use_icons:
            icon = TYPE_ICONS.get(notification.notification_type, "•")
            parts.append(icon)
        
        # Type label with color
        type_name = notification.notification_type.value.upper()
        if self._use_colors:
            color = TYPE_COLORS.get(notification.notification_type, "reset")
            parts.append(f"{COLORS[color]}{COLORS['bold']}[{type_name}]{COLORS['reset']}")
        else:
            parts.append(f"[{type_name}]")
        
        # Priority indicator for high/urgent
        if notification.priority.value >= Priority.HIGH.value:
            if self._use_colors:
                parts.append(f"{COLORS['red']}(!){COLORS['reset']}")
            else:
                parts.append("(!)")
        
        # Title and message
        parts.append(f"{notification.title}:")
        parts.append(notification.message)
        
        # Action if present
        if notification.action:
            parts.append(f"[Action: {notification.action}]")
        
        return " ".join(parts)
    
    def is_available(self) -> bool:
        """Console is always available."""
        return True
