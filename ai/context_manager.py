"""
Context Window Manager

Manages AI context window for tool selection and content processing.
Implements token counting, context pruning, and relevance scoring.

Law Compliance:
- LAW 7: Context is informational only (non-authoritative)
- LAW 3: AI cannot execute based on context alone
- LAW 13: All context usage is logged
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from enum import Enum

from core.system_context import get_system_context, ToolExecutionRecord

logger = logging.getLogger(__name__)


class PruningStrategy(Enum):
    """Strategies for pruning context when limits are exceeded."""
    FIFO = "fifo"  # First In, First Out (oldest removed first)
    RELEVANCE = "relevance"  # Remove least relevant items
    SUMMARY = "summary"  # Summarize old context instead of removing


@dataclass
class ContextEntry:
    """A single entry in the context window."""
    content: str
    entry_type: str  # "system", "tool_result", "user_input", "summary"
    timestamp: datetime
    token_count: int
    relevance_score: float = 1.0  # 0.0 to 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ContextWindow:
    """Represents the current AI context window state."""
    entries: List[ContextEntry]
    total_tokens: int
    max_tokens: int
    pruned_count: int = 0


class ContextManager:
    """
    Manages AI context window for tool selection and content processing.
    
    Features:
    - Token counting (estimate: ~4 chars per token)
    - Context pruning strategies
    - Relevance scoring
    - History summarization (placeholder for future)
    - SystemContext integration
    
    Rules (enforced):
    - Context is READ-ONLY for AI (LAW 7)
    - AI cannot execute based on context (LAW 3)
    - All context operations are logged (LAW 13)
    """
    
    # Token estimation ratio (chars per token, conservative estimate)
    CHARS_PER_TOKEN = 4
    
    # Default context limits
    DEFAULT_MAX_TOKENS = 4096
    DEFAULT_RESERVED_TOKENS = 512  # For system prompt and response
    
    def __init__(
        self,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        reserved_tokens: int = DEFAULT_RESERVED_TOKENS,
        pruning_strategy: PruningStrategy = PruningStrategy.FIFO,
    ) -> None:
        """
        Initialize the context manager.
        
        Args:
            max_tokens: Maximum tokens allowed in context window
            reserved_tokens: Tokens reserved for system prompt and response
            pruning_strategy: Strategy for removing context when limit exceeded
        """
        self._max_tokens = max_tokens
        self._reserved_tokens = reserved_tokens
        self._available_tokens = max_tokens - reserved_tokens
        self._pruning_strategy = pruning_strategy
        
        # Context entries (managed as a list)
        self._entries: List[ContextEntry] = []
        self._current_tokens = 0
        self._pruned_count = 0
        
        # System prompt (set once, rarely changes)
        self._system_prompt: Optional[str] = None
        self._system_prompt_tokens = 0
        
        logger.info(
            f"ContextManager initialized: max_tokens={max_tokens}, "
            f"available={self._available_tokens}, strategy={pruning_strategy.value}"
        )
    
    def estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for a piece of text.
        
        Uses a conservative character-to-token ratio.
        
        Args:
            text: Text to estimate
            
        Returns:
            Estimated token count
        """
        if not text:
            return 0
        return max(1, len(text) // self.CHARS_PER_TOKEN)
    
    def set_system_prompt(self, prompt: str) -> None:
        """
        Set the system prompt (deducted from available tokens).
        
        Args:
            prompt: System prompt text
        """
        self._system_prompt = prompt
        self._system_prompt_tokens = self.estimate_tokens(prompt)
        self._available_tokens = (
            self._max_tokens - self._reserved_tokens - self._system_prompt_tokens
        )
        logger.debug(
            f"System prompt set: {self._system_prompt_tokens} tokens, "
            f"available now: {self._available_tokens}"
        )
    
    def add_entry(
        self,
        content: str,
        entry_type: str,
        relevance_score: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Add an entry to the context window.
        
        If adding the entry would exceed the limit, pruning is applied.
        
        Args:
            content: Entry content
            entry_type: Type of entry ("tool_result", "user_input", etc.)
            relevance_score: How relevant this entry is (0.0-1.0)
            metadata: Optional metadata
            
        Returns:
            True if entry was added, False if it was too large
        """
        token_count = self.estimate_tokens(content)
        
        # Check if single entry exceeds available space
        if token_count > self._available_tokens:
            logger.warning(
                f"Entry too large ({token_count} tokens) for context window "
                f"({self._available_tokens} available)"
            )
            return False
        
        # Prune if needed to make space
        while self._current_tokens + token_count > self._available_tokens:
            self._prune_one()
        
        # Add the entry
        entry = ContextEntry(
            content=content,
            entry_type=entry_type,
            timestamp=datetime.now(),
            token_count=token_count,
            relevance_score=relevance_score,
            metadata=metadata or {},
        )
        
        self._entries.append(entry)
        self._current_tokens += token_count
        
        logger.debug(
            f"Context entry added: type={entry_type}, tokens={token_count}, "
            f"total={self._current_tokens}/{self._available_tokens}"
        )
        
        return True
    
    def add_tool_result(
        self,
        tool_name: str,
        result: Any,
        relevance_score: float = 0.8,
    ) -> bool:
        """
        Add a tool execution result to context.
        
        Args:
            tool_name: Name of the tool
            result: Tool result (will be stringified)
            relevance_score: Relevance score
            
        Returns:
            True if added successfully
        """
        content = f"[Tool: {tool_name}] Result: {str(result)[:1000]}"  # Truncate
        return self.add_entry(
            content=content,
            entry_type="tool_result",
            relevance_score=relevance_score,
            metadata={"tool_name": tool_name},
        )
    
    def add_user_input(self, user_input: str) -> bool:
        """
        Add user input to context.
        
        Args:
            user_input: User's input text
            
        Returns:
            True if added successfully
        """
        return self.add_entry(
            content=f"[User] {user_input}",
            entry_type="user_input",
            relevance_score=1.0,  # User input is always relevant
        )
    
    def inject_from_system_context(self, limit: int = 5) -> None:
        """
        Inject recent execution history from SystemContext.
        
        This provides AI with awareness of recent tool executions
        without giving it authority over them (LAW 7).
        
        Args:
            limit: Maximum number of recent executions to inject
        """
        ctx = get_system_context()
        history = ctx.get_execution_history(limit=limit)
        
        for record in history:
            summary = f"[Recent] {record.tool_name}: {record.result_status}"
            self.add_entry(
                content=summary,
                entry_type="history",
                relevance_score=0.5,  # Lower relevance for history
                metadata={"tool_name": record.tool_name},
            )
        
        logger.debug(f"Injected {len(history)} entries from SystemContext")
    
    def get_context_for_ai(self) -> str:
        """
        Build the context string for AI consumption.
        
        Returns:
            Formatted context string ready for AI prompt
        """
        if not self._entries:
            return ""
        
        lines = ["--- Context ---"]
        for entry in self._entries:
            lines.append(entry.content)
        lines.append("--- End Context ---")
        
        return "\n".join(lines)
    
    def get_window_state(self) -> ContextWindow:
        """
        Get current context window state.
        
        Returns:
            ContextWindow with current state
        """
        return ContextWindow(
            entries=list(self._entries),
            total_tokens=self._current_tokens,
            max_tokens=self._available_tokens,
            pruned_count=self._pruned_count,
        )
    
    def clear(self) -> None:
        """Clear all context entries."""
        self._entries.clear()
        self._current_tokens = 0
        self._pruned_count = 0
        logger.debug("Context window cleared")
    
    def _prune_one(self) -> None:
        """Remove one entry based on pruning strategy."""
        if not self._entries:
            return
        
        if self._pruning_strategy == PruningStrategy.FIFO:
            # Remove oldest entry
            removed = self._entries.pop(0)
        elif self._pruning_strategy == PruningStrategy.RELEVANCE:
            # Remove least relevant entry
            min_idx = min(
                range(len(self._entries)),
                key=lambda i: self._entries[i].relevance_score
            )
            removed = self._entries.pop(min_idx)
        else:
            # Default to FIFO
            removed = self._entries.pop(0)
        
        self._current_tokens -= removed.token_count
        self._pruned_count += 1
        
        logger.debug(
            f"Pruned entry: type={removed.entry_type}, tokens={removed.token_count}"
        )


# Convenience function for getting a shared context manager
_default_manager: Optional[ContextManager] = None


def get_context_manager() -> ContextManager:
    """Get or create the default ContextManager instance."""
    global _default_manager
    if _default_manager is None:
        _default_manager = ContextManager()
    return _default_manager


def reset_context_manager() -> None:
    """Reset the default context manager (for testing)."""
    global _default_manager
    _default_manager = None
