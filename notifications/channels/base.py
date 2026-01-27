"""
Base Channel Interface

Abstract base class for notification delivery channels.
"""

import logging
from abc import ABC, abstractmethod
from typing import List

from notifications.notification import Notification

logger = logging.getLogger(__name__)


class Channel(ABC):
    """
    Abstract base class for notification channels.
    
    A channel is responsible for delivering notifications to users
    via a specific medium (console, file, desktop, etc.).
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Get channel name."""
        pass
    
    @abstractmethod
    def deliver(self, notification: Notification) -> bool:
        """
        Deliver a notification.
        
        Args:
            notification: Notification to deliver
            
        Returns:
            True if delivered successfully
        """
        pass
    
    def deliver_batch(self, notifications: List[Notification]) -> int:
        """
        Deliver multiple notifications.
        
        Args:
            notifications: List of notifications
            
        Returns:
            Count of successfully delivered notifications
        """
        delivered = 0
        for notification in notifications:
            if self.deliver(notification):
                delivered += 1
        return delivered
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if channel is available for delivery."""
        pass
