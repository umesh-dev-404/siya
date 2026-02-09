"""
Memory Summarizer

Summarizes memories while preserving lineage.
Enforces LAW 22 — MEMORY QUALITY PRESERVATION.

Per CONTINUATION_PLAN Phase 22: Memory Quality Control.
"""

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from memory.memory_quality import MemoryQualityManager

logger = logging.getLogger(__name__)


class MemorySummarizer:
    """
    Memory summarization with lineage preservation.
    
    Per LAW 22 — MEMORY QUALITY PRESERVATION:
    - Summarization must preserve attribution
    - Original data retained in lineage chain
    - No information loss (only compression)
    """
    
    def __init__(
        self,
        quality_manager: Optional[MemoryQualityManager] = None,
    ) -> None:
        """
        Initialize the memory summarizer.
        
        Args:
            quality_manager: Memory quality manager for metadata handling.
        """
        self._quality_manager = quality_manager or MemoryQualityManager()
    
    def summarize_memory(
        self,
        memory_id: str,
        memory_content: str,
        memory_metadata: Dict[str, Any],
        quality_metadata: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Summarize a memory while preserving lineage.
        
        Per LAW 22:
        - Original memory ID preserved in lineage
        - Key facts extracted and preserved
        - Attribution maintained
        
        Args:
            memory_id: ID of the original memory.
            memory_content: Content of the memory.
            memory_metadata: Metadata of the memory.
            quality_metadata: Quality metadata.
        
        Returns:
            New summarized memory record with lineage.
        """
        # Generate summary content
        summary_content = self._generate_summary(memory_content, memory_metadata)
        
        # Create new quality metadata with lineage
        new_quality = self._quality_manager.prepare_for_summarization(
            original_id=memory_id,
            quality_metadata=quality_metadata,
        )
        
        # Build summarized memory record
        new_id = str(uuid4())
        now = datetime.now(timezone.utc)
        iso = now.isoformat().replace("+00:00", "Z")
        summarized_record = {
            "id": new_id,
            "content": summary_content,
            "created_at": iso,
            "type": memory_metadata.get("type", "general"),
            "source": "summarization",
            "metadata": {
                "original_id": memory_id,
                "original_created_at": memory_metadata.get("created_at"),
                "original_type": memory_metadata.get("type"),
                "summarization_timestamp": iso,
                "summarization_reason": self._get_summarization_reason(quality_metadata),
            },
            "quality": new_quality,
        }
        
        logger.info(
            f"Memory summarized: {memory_id} -> {new_id}",
            extra={
                "original_id": memory_id,
                "new_id": new_id,
                "summarization_level": new_quality.get("summarization_level"),
            },
        )
        
        return summarized_record
    
    def _generate_summary(
        self,
        content: str,
        metadata: Dict[str, Any],
    ) -> str:
        """
        Generate summary of memory content.
        
        Per LAW 22: Summarization is deterministic compression.
        This is a rule-based summarization, not AI-generated.
        
        Args:
            content: Original memory content.
            metadata: Memory metadata.
        
        Returns:
            Summarized content.
        """
        # Rule-based summarization (deterministic, per LAW 22)
        # For production, this could be enhanced with AI assistance
        # but output must be verified/confirmed by system
        
        # Strategy: Truncate to key information
        max_length = 200  # Characters
        
        content_str = str(content)
        
        if len(content_str) <= max_length:
            return content_str
        
        # Extract first sentence or truncate
        sentences = content_str.split('. ')
        if sentences:
            first_sentence = sentences[0]
            if len(first_sentence) <= max_length:
                # Include as many complete sentences as fit
                summary_parts = []
                current_length = 0
                for sentence in sentences:
                    if current_length + len(sentence) + 2 <= max_length:
                        summary_parts.append(sentence)
                        current_length += len(sentence) + 2
                    else:
                        break
                return '. '.join(summary_parts) + '.'
        
        # Fallback: Truncate with ellipsis
        return content_str[:max_length - 3] + "..."
    
    def _get_summarization_reason(
        self,
        quality_metadata: Dict[str, Any],
    ) -> str:
        """
        Determine the reason for summarization.
        
        Args:
            quality_metadata: Quality metadata.
        
        Returns:
            Reason string for auditing.
        """
        confidence = quality_metadata.get("confidence_current", 1.0)
        created_at_str = quality_metadata.get("created_at", "")
        
        if confidence < 0.3:
            return f"confidence_below_threshold (current: {confidence})"
        
        if created_at_str:
            try:
                created_at = datetime.fromisoformat(created_at_str.rstrip("Z"))
                now_utc = datetime.now(timezone.utc).replace(tzinfo=None)
                age_days = (now_utc - created_at).days
                if age_days > 90:
                    return f"age_exceeded (days: {age_days})"
            except ValueError:
                pass
        
        return "manual_summarization"
    
    def batch_summarize(
        self,
        memories: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Batch summarize multiple memories.
        
        Args:
            memories: List of memory records to summarize.
        
        Returns:
            List of summarized memory records.
        """
        summarized = []
        
        for memory in memories:
            try:
                summarized_record = self.summarize_memory(
                    memory_id=memory.get("id", str(uuid4())),
                    memory_content=memory.get("content", ""),
                    memory_metadata=memory.get("metadata", {}),
                    quality_metadata=memory.get("quality", {}),
                )
                summarized.append(summarized_record)
            except Exception as e:
                logger.error(f"Failed to summarize memory {memory.get('id')}: {e}")
        
        logger.info(f"Batch summarization complete: {len(summarized)}/{len(memories)} succeeded")
        return summarized
    
    def get_lineage_chain(
        self,
        memory_record: Dict[str, Any],
        all_memories: Dict[str, Dict[str, Any]],
    ) -> List[str]:
        """
        Get full lineage chain for a memory.
        
        Per LAW 22: Lineage must be traceable.
        
        Args:
            memory_record: The memory to trace.
            all_memories: Dictionary of all memories (id -> record).
        
        Returns:
            List of memory IDs in lineage order (oldest first).
        """
        chain = []
        current = memory_record
        
        # Prevent infinite loops
        max_depth = 10
        depth = 0
        
        while current and depth < max_depth:
            current_id = current.get("id")
            if current_id:
                chain.insert(0, current_id)
            
            # Get parent from lineage
            quality = current.get("quality", {})
            lineage_id = quality.get("lineage_id")
            
            if not lineage_id:
                break
            
            current = all_memories.get(lineage_id)
            depth += 1
        
        return chain
