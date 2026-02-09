"""
Memory Quality Control

Implements confidence decay and memory quality preservation.
Enforces LAW 22 — MEMORY QUALITY PRESERVATION.

Per CONTINUATION_PLAN Phase 22: Memory Quality Control.
"""

import logging
import math
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


# Default decay rate (per day) - configurable
DEFAULT_DECAY_RATE = 0.05

# Minimum confidence threshold for summarization
SUMMARIZATION_THRESHOLD = 0.3

# Maximum age before forced summarization (days)
MAX_MEMORY_AGE_DAYS = 90


@dataclass
class MemoryQuality:
    """
    Memory quality metadata.
    
    Per LAW 22 — MEMORY QUALITY PRESERVATION:
    - Confidence must decay deterministically
    - Original data must be preserved in lineage
    - Summarization must not lose attribution
    """
    
    confidence_original: float
    """Original confidence when memory was created (0.0 to 1.0)."""
    
    confidence_current: float
    """Current confidence after decay (0.0 to 1.0)."""
    
    created_at: datetime
    """When the memory was created."""
    
    last_accessed: datetime
    """When the memory was last accessed."""
    
    access_count: int
    """Number of times the memory has been accessed."""
    
    decay_rate: float
    """Decay rate per day (default: 0.05)."""
    
    lineage_id: Optional[str]
    """ID of parent memory if this is a summarized version."""
    
    is_summarized: bool
    """Whether this memory has been summarized."""
    
    summarization_level: int
    """Summarization level (0 = original, 1 = first summary, etc.)."""


class ConfidenceDecayModel:
    """
    Deterministic confidence decay model.
    
    Per LAW 22 — MEMORY QUALITY PRESERVATION:
    - Uses exponential decay based on time
    - Decay is purely based on elapsed time (deterministic)
    - Access can boost confidence slightly (reinforcement)
    """
    
    def __init__(self, decay_rate: float = DEFAULT_DECAY_RATE) -> None:
        """
        Initialize the decay model.
        
        Args:
            decay_rate: Decay rate per day (default: 0.05 = 5% per day).
        """
        self._decay_rate = decay_rate
    
    def calculate_current_confidence(
        self,
        original_confidence: float,
        created_at: datetime,
        access_count: int = 0,
        now: Optional[datetime] = None,
    ) -> float:
        """
        Calculate current confidence after time-based decay.
        
        Uses exponential decay formula:
            confidence(t) = original * e^(-decay_rate * days)
        
        Access count provides minor reinforcement:
            Each access adds 0.01 to final confidence (max 0.1 boost).
        
        Args:
            original_confidence: Original confidence (0.0 to 1.0).
            created_at: When memory was created.
            access_count: Number of times accessed.
            now: Current time (defaults to utc now).
        
        Returns:
            Current confidence after decay (0.0 to 1.0).
        """
        if now is None:
            now = datetime.now(timezone.utc)
        
        # Calculate days elapsed
        elapsed = now - created_at
        days = elapsed.total_seconds() / 86400  # Convert to days
        
        # Exponential decay
        decayed = original_confidence * math.exp(-self._decay_rate * days)
        
        # Access reinforcement (max 0.1 boost)
        access_boost = min(access_count * 0.01, 0.1)
        
        # Final confidence
        confidence = min(decayed + access_boost, 1.0)
        
        # Ensure minimum of 0
        return max(confidence, 0.0)
    
    def needs_summarization(
        self,
        confidence: float,
        created_at: datetime,
        now: Optional[datetime] = None,
    ) -> bool:
        """
        Check if memory needs summarization based on quality thresholds.
        
        Per LAW 22: Summarization triggers when:
        - Confidence drops below threshold, OR
        - Memory exceeds maximum age
        
        Args:
            confidence: Current confidence.
            created_at: When memory was created.
            now: Current time.
        
        Returns:
            True if summarization is needed.
        """
        if now is None:
            now = datetime.now(timezone.utc)
        
        # Check confidence threshold
        if confidence < SUMMARIZATION_THRESHOLD:
            return True
        
        # Check age threshold
        age = now - created_at
        if age.days > MAX_MEMORY_AGE_DAYS:
            return True
        
        return False
    
    def get_decay_projection(
        self,
        original_confidence: float,
        days_ahead: int = 30,
    ) -> list[tuple[int, float]]:
        """
        Project confidence decay over time.
        
        Useful for display/debugging.
        
        Args:
            original_confidence: Starting confidence.
            days_ahead: Number of days to project.
        
        Returns:
            List of (day, confidence) tuples.
        """
        now = datetime.now(timezone.utc)
        projections = []
        
        for day in range(0, days_ahead + 1, 7):  # Weekly intervals
            future = now + timedelta(days=day)
            confidence = self.calculate_current_confidence(
                original_confidence=original_confidence,
                created_at=now,
                access_count=0,
                now=future,
            )
            projections.append((day, round(confidence, 3)))
        
        return projections


class MemoryQualityManager:
    """
    Manages memory quality across the system.
    
    Per LAW 22 — MEMORY QUALITY PRESERVATION.
    """
    
    def __init__(self, decay_rate: float = DEFAULT_DECAY_RATE) -> None:
        """
        Initialize the memory quality manager.
        
        Args:
            decay_rate: Decay rate per day.
        """
        self._decay_model = ConfidenceDecayModel(decay_rate)
    
    def create_quality_metadata(
        self,
        initial_confidence: float = 1.0,
    ) -> Dict[str, Any]:
        """
        Create quality metadata for a new memory.
        
        Args:
            initial_confidence: Initial confidence (default: 1.0).
        
        Returns:
            Quality metadata dictionary.
        """
        now = datetime.now(timezone.utc)
        iso = now.isoformat().replace("+00:00", "Z")
        return {
            "confidence_original": initial_confidence,
            "confidence_current": initial_confidence,
            "created_at": iso,
            "last_accessed": iso,
            "access_count": 0,
            "decay_rate": self._decay_model._decay_rate,
            "lineage_id": None,
            "is_summarized": False,
            "summarization_level": 0,
        }
    
    def update_on_access(
        self,
        quality_metadata: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Update quality metadata on memory access.
        
        Per LAW 22: Access reinforces confidence slightly.
        
        Args:
            quality_metadata: Current quality metadata.
        
        Returns:
            Updated quality metadata.
        """
        now = datetime.now(timezone.utc)
        now_iso = now.isoformat().replace("+00:00", "Z")
        # Parse created_at
        created_at_str = quality_metadata.get("created_at", now_iso)
        created_at = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
        
        # Increment access count
        access_count = quality_metadata.get("access_count", 0) + 1
        
        # Calculate new confidence
        new_confidence = self._decay_model.calculate_current_confidence(
            original_confidence=quality_metadata.get("confidence_original", 1.0),
            created_at=created_at,
            access_count=access_count,
            now=now,
        )
        
        # Update metadata
        return {
            **quality_metadata,
            "confidence_current": round(new_confidence, 3),
            "last_accessed": now.isoformat().replace("+00:00", "Z"),
            "access_count": access_count,
        }
    
    def check_summarization_needed(
        self,
        quality_metadata: Dict[str, Any],
    ) -> bool:
        """
        Check if memory needs summarization.
        
        Args:
            quality_metadata: Quality metadata.
        
        Returns:
            True if summarization is needed.
        """
        confidence = quality_metadata.get("confidence_current", 1.0)
        created_at_str = quality_metadata.get("created_at")
        
        if not created_at_str:
            return False
        
        created_at = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
        
        return self._decay_model.needs_summarization(
            confidence=confidence,
            created_at=created_at,
        )
    
    def prepare_for_summarization(
        self, 
        original_id: str,
        quality_metadata: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Prepare quality metadata for summarized memory.
        
        Per LAW 22: Preserves lineage to original.
        
        Args:
            original_id: ID of the original memory.
            quality_metadata: Quality metadata of original.
        
        Returns:
            New quality metadata for summarized memory.
        """
        now = datetime.now(timezone.utc)
        iso = now.isoformat().replace("+00:00", "Z")
        summarization_level = quality_metadata.get("summarization_level", 0) + 1
        
        return {
            "confidence_original": 0.5,  # Summarized memories start at 0.5
            "confidence_current": 0.5,
            "created_at": iso,
            "last_accessed": iso,
            "access_count": 0,
            "decay_rate": self._decay_model._decay_rate,
            "lineage_id": original_id,
            "is_summarized": True,
            "summarization_level": summarization_level,
        }
