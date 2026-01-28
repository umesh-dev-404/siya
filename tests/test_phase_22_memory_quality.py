"""
Tests for Phase 22: Memory Quality Control

Tests ConfidenceDecayModel, MemoryQualityManager, and MemorySummarizer.
Enforces LAW 22 — MEMORY QUALITY PRESERVATION.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
from uuid import uuid4

from memory.memory_quality import (
    MemoryQuality,
    ConfidenceDecayModel,
    MemoryQualityManager,
    DEFAULT_DECAY_RATE,
    SUMMARIZATION_THRESHOLD,
    MAX_MEMORY_AGE_DAYS,
)
from memory.memory_summarizer import MemorySummarizer


class TestMemoryQualityDataclass:
    """Tests for MemoryQuality dataclass."""

    def test_memory_quality_creation(self):
        """Test creating a MemoryQuality instance."""
        now = datetime.utcnow()
        quality = MemoryQuality(
            confidence_original=1.0,
            confidence_current=0.8,
            created_at=now,
            last_accessed=now,
            access_count=5,
            decay_rate=0.05,
            lineage_id=None,
            is_summarized=False,
            summarization_level=0,
        )
        
        assert quality.confidence_original == 1.0
        assert quality.confidence_current == 0.8
        assert quality.access_count == 5
        assert quality.is_summarized is False


class TestConfidenceDecayModel:
    """Tests for ConfidenceDecayModel class."""

    def test_init_with_default_decay_rate(self):
        """Test initialization with default decay rate."""
        model = ConfidenceDecayModel()
        assert model._decay_rate == DEFAULT_DECAY_RATE

    def test_init_with_custom_decay_rate(self):
        """Test initialization with custom decay rate."""
        model = ConfidenceDecayModel(decay_rate=0.1)
        assert model._decay_rate == 0.1

    def test_no_decay_at_creation(self):
        """Test that confidence is unchanged at creation time."""
        model = ConfidenceDecayModel()
        now = datetime.utcnow()
        
        confidence = model.calculate_current_confidence(
            original_confidence=1.0,
            created_at=now,
            access_count=0,
            now=now,
        )
        
        assert confidence == 1.0

    def test_decay_after_one_day(self):
        """Test confidence decay after one day."""
        model = ConfidenceDecayModel(decay_rate=0.05)
        now = datetime.utcnow()
        yesterday = now - timedelta(days=1)
        
        confidence = model.calculate_current_confidence(
            original_confidence=1.0,
            created_at=yesterday,
            access_count=0,
            now=now,
        )
        
        # After 1 day with 5% decay rate: e^(-0.05*1) ≈ 0.951
        assert 0.94 < confidence < 0.96

    def test_decay_after_one_week(self):
        """Test confidence decay after one week."""
        model = ConfidenceDecayModel(decay_rate=0.05)
        now = datetime.utcnow()
        week_ago = now - timedelta(days=7)
        
        confidence = model.calculate_current_confidence(
            original_confidence=1.0,
            created_at=week_ago,
            access_count=0,
            now=now,
        )
        
        # After 7 days: e^(-0.05*7) ≈ 0.704
        assert 0.69 < confidence < 0.72

    def test_access_reinforcement(self):
        """Test that access count boosts confidence."""
        model = ConfidenceDecayModel(decay_rate=0.05)
        now = datetime.utcnow()
        week_ago = now - timedelta(days=7)
        
        # Without access
        conf_no_access = model.calculate_current_confidence(
            original_confidence=1.0,
            created_at=week_ago,
            access_count=0,
            now=now,
        )
        
        # With access
        conf_with_access = model.calculate_current_confidence(
            original_confidence=1.0,
            created_at=week_ago,
            access_count=5,
            now=now,
        )
        
        # Access should add 0.05 (5 * 0.01)
        assert conf_with_access > conf_no_access
        assert abs(conf_with_access - conf_no_access - 0.05) < 0.01

    def test_access_reinforcement_capped(self):
        """Test that access reinforcement is capped at 0.1."""
        model = ConfidenceDecayModel(decay_rate=0.05)
        now = datetime.utcnow()
        week_ago = now - timedelta(days=7)
        
        # With many accesses
        conf_max_access = model.calculate_current_confidence(
            original_confidence=1.0,
            created_at=week_ago,
            access_count=100,
            now=now,
        )
        
        # Boost should be capped
        base_decay = model.calculate_current_confidence(1.0, week_ago, 0, now)
        assert conf_max_access <= base_decay + 0.1 + 0.01  # Allow small float error

    def test_confidence_never_exceeds_one(self):
        """Test that confidence never exceeds 1.0."""
        model = ConfidenceDecayModel()
        now = datetime.utcnow()
        
        confidence = model.calculate_current_confidence(
            original_confidence=1.0,
            created_at=now,
            access_count=100,
            now=now,
        )
        
        assert confidence <= 1.0

    def test_confidence_never_negative(self):
        """Test that confidence never goes negative."""
        model = ConfidenceDecayModel(decay_rate=1.0)  # Very high decay
        now = datetime.utcnow()
        long_ago = now - timedelta(days=365)
        
        confidence = model.calculate_current_confidence(
            original_confidence=1.0,
            created_at=long_ago,
            access_count=0,
            now=now,
        )
        
        assert confidence >= 0.0

    def test_needs_summarization_low_confidence(self):
        """Test that low confidence triggers summarization need."""
        model = ConfidenceDecayModel()
        now = datetime.utcnow()
        
        needs_summary = model.needs_summarization(
            confidence=0.2,  # Below threshold
            created_at=now,
            now=now,
        )
        
        assert needs_summary is True

    def test_needs_summarization_old_age(self):
        """Test that old age triggers summarization need."""
        model = ConfidenceDecayModel()
        now = datetime.utcnow()
        old = now - timedelta(days=100)  # Beyond max age
        
        needs_summary = model.needs_summarization(
            confidence=0.9,  # Good confidence
            created_at=old,
            now=now,
        )
        
        assert needs_summary is True

    def test_no_summarization_needed(self):
        """Test that healthy memory doesn't need summarization."""
        model = ConfidenceDecayModel()
        now = datetime.utcnow()
        recent = now - timedelta(days=7)
        
        needs_summary = model.needs_summarization(
            confidence=0.8,
            created_at=recent,
            now=now,
        )
        
        assert needs_summary is False

    def test_decay_projection(self):
        """Test decay projection over time."""
        model = ConfidenceDecayModel()
        
        projections = model.get_decay_projection(
            original_confidence=1.0,
            days_ahead=30,
        )
        
        assert len(projections) > 0
        # First projection should be current
        assert projections[0][0] == 0
        assert projections[0][1] == 1.0
        # Later projections should decrease
        assert projections[-1][1] < projections[0][1]


class TestMemoryQualityManager:
    """Tests for MemoryQualityManager class."""

    def test_create_quality_metadata(self):
        """Test creating quality metadata for new memory."""
        manager = MemoryQualityManager()
        metadata = manager.create_quality_metadata(initial_confidence=1.0)
        
        assert metadata["confidence_original"] == 1.0
        assert metadata["confidence_current"] == 1.0
        assert metadata["access_count"] == 0
        assert metadata["lineage_id"] is None
        assert metadata["is_summarized"] is False
        assert metadata["summarization_level"] == 0

    def test_update_on_access(self):
        """Test updating metadata on memory access."""
        manager = MemoryQualityManager()
        
        # Create initial metadata
        metadata = manager.create_quality_metadata()
        
        # Simulate access
        updated = manager.update_on_access(metadata)
        
        assert updated["access_count"] == 1
        assert updated["last_accessed"] != metadata["last_accessed"]

    def test_prepare_for_summarization(self):
        """Test preparing metadata for summarized memory."""
        manager = MemoryQualityManager()
        
        original_id = str(uuid4())
        original_metadata = manager.create_quality_metadata()
        
        new_metadata = manager.prepare_for_summarization(
            original_id=original_id,
            quality_metadata=original_metadata,
        )
        
        assert new_metadata["lineage_id"] == original_id
        assert new_metadata["is_summarized"] is True
        assert new_metadata["summarization_level"] == 1
        assert new_metadata["confidence_original"] == 0.5  # Summarized starts at 0.5


class TestMemorySummarizer:
    """Tests for MemorySummarizer class."""

    def test_summarize_preserves_lineage(self):
        """Per LAW 22: Summarization must preserve lineage."""
        summarizer = MemorySummarizer()
        
        original_id = str(uuid4())
        result = summarizer.summarize_memory(
            memory_id=original_id,
            memory_content="This is a long memory content that needs to be summarized.",
            memory_metadata={"type": "general"},
            quality_metadata={"confidence_current": 0.2},
        )
        
        assert result["quality"]["lineage_id"] == original_id
        assert result["metadata"]["original_id"] == original_id

    def test_summarize_creates_new_id(self):
        """Test that summarization creates a new memory ID."""
        summarizer = MemorySummarizer()
        
        original_id = str(uuid4())
        result = summarizer.summarize_memory(
            memory_id=original_id,
            memory_content="Test content",
            memory_metadata={},
            quality_metadata={},
        )
        
        assert result["id"] != original_id

    def test_summarize_truncates_long_content(self):
        """Test that summarization truncates long content."""
        summarizer = MemorySummarizer()
        
        long_content = "x" * 500
        result = summarizer.summarize_memory(
            memory_id=str(uuid4()),
            memory_content=long_content,
            memory_metadata={},
            quality_metadata={},
        )
        
        assert len(result["content"]) <= 200

    def test_batch_summarize(self):
        """Test batch summarization of multiple memories."""
        summarizer = MemorySummarizer()
        
        memories = [
            {
                "id": str(uuid4()),
                "content": f"Memory content {i}",
                "metadata": {},
                "quality": {},
            }
            for i in range(3)
        ]
        
        results = summarizer.batch_summarize(memories)
        
        assert len(results) == 3

    def test_lineage_chain(self):
        """Test getting lineage chain for a memory."""
        summarizer = MemorySummarizer()
        
        # Create a chain of memories
        id1 = str(uuid4())
        id2 = str(uuid4())
        id3 = str(uuid4())
        
        all_memories = {
            id1: {"id": id1, "quality": {"lineage_id": None}},
            id2: {"id": id2, "quality": {"lineage_id": id1}},
            id3: {"id": id3, "quality": {"lineage_id": id2}},
        }
        
        chain = summarizer.get_lineage_chain(
            memory_record=all_memories[id3],
            all_memories=all_memories,
        )
        
        assert chain == [id1, id2, id3]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
