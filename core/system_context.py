"""
System Context Module

Provides centralized, thread-safe state management for the Siya system.
This is the single source of truth for runtime state accessible to the orchestrator and tools.

Law Compliance:
- LAW 7: Context is non-authoritative (read-only to AI and tools)
- LAW 8: Only orchestrator can write to context
- LAW 10: Thread-safe implementation with locking
- LAW 13: All context access is logged
"""

import threading
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class ContextAccessLevel(Enum):
    """Access levels for context operations."""
    READ = "read"
    WRITE = "write"


@dataclass
class ToolExecutionRecord:
    """Record of a tool execution for context history."""
    tool_name: str
    arguments: Dict[str, Any]
    result_status: str  # "ok", "error", "pending_confirmation"
    timestamp: datetime
    task_id: Optional[UUID] = None
    execution_time_ms: Optional[int] = None


@dataclass
class SessionState:
    """Current session state."""
    session_id: str
    started_at: datetime
    last_activity: datetime
    active_task_id: Optional[UUID] = None
    user_preferences: Dict[str, Any] = field(default_factory=dict)


class SystemContext:
    """
    Centralized system context providing thread-safe state management.
    
    This is a singleton that maintains:
    - Current session state
    - Recent tool execution history
    - Active task context
    - System-wide configuration cache
    
    Access Rules (enforced):
    - Tools and AI get READ-ONLY access
    - Only the Orchestrator can WRITE
    - All access is logged for audit
    """
    
    _instance: Optional["SystemContext"] = None
    _lock = threading.Lock()
    
    # Maximum entries in execution history (L1 memory constraint)
    MAX_EXECUTION_HISTORY = 100
    
    def __new__(cls) -> "SystemContext":
        """Thread-safe singleton pattern."""
        if cls._instance is None:
            with cls._lock:
                # Double-check locking pattern
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self) -> None:
        """Initialize context state (only once due to singleton)."""
        if self._initialized:
            return
            
        self._state_lock = threading.RLock()
        
        # Session state
        self._session: Optional[SessionState] = None
        
        # Tool execution history (L1 - active context)
        self._execution_history: List[ToolExecutionRecord] = []
        
        # Active task context
        self._active_task: Optional[Dict[str, Any]] = None
        
        # Configuration cache
        self._config_cache: Dict[str, Any] = {}
        
        # Custom state storage (key-value)
        self._state: Dict[str, Any] = {}
        
        # Authorized writers (component names that can write)
        self._authorized_writers = {"orchestrator", "service_main"}
        
        self._initialized = True
        logger.info("SystemContext initialized")
    
    @classmethod
    def reset_instance(cls) -> None:
        """Reset the singleton instance (for testing only)."""
        with cls._lock:
            cls._instance = None
    
    # =========================================================================
    # READ OPERATIONS (available to tools and AI)
    # =========================================================================
    
    def get_session(self) -> Optional[SessionState]:
        """Get current session state (read-only)."""
        with self._state_lock:
            self._log_access("session", ContextAccessLevel.READ)
            return self._session
    
    def get_execution_history(self, limit: int = 10) -> List[ToolExecutionRecord]:
        """
        Get recent tool execution history.
        
        Args:
            limit: Maximum number of records to return (default 10)
            
        Returns:
            List of recent execution records (newest first)
        """
        with self._state_lock:
            self._log_access("execution_history", ContextAccessLevel.READ)
            return list(reversed(self._execution_history[-limit:]))
    
    def get_active_task(self) -> Optional[Dict[str, Any]]:
        """Get active task context (read-only)."""
        with self._state_lock:
            self._log_access("active_task", ContextAccessLevel.READ)
            return self._active_task.copy() if self._active_task else None
    
    def get_config(self, key: str, default: Any = None) -> Any:
        """Get cached configuration value."""
        with self._state_lock:
            self._log_access(f"config:{key}", ContextAccessLevel.READ)
            return self._config_cache.get(key, default)
    
    def get_state(self, key: str, default: Any = None) -> Any:
        """Get custom state value."""
        with self._state_lock:
            self._log_access(f"state:{key}", ContextAccessLevel.READ)
            return self._state.get(key, default)
    
    def get_context_snapshot(self) -> Dict[str, Any]:
        """
        Get a complete snapshot of current context.
        Useful for AI context injection.
        
        Returns:
            Dictionary with all context state
        """
        with self._state_lock:
            self._log_access("full_snapshot", ContextAccessLevel.READ)
            return {
                "session": {
                    "id": self._session.session_id if self._session else None,
                    "started_at": self._session.started_at.isoformat() if self._session else None,
                    "last_activity": self._session.last_activity.isoformat() if self._session else None,
                } if self._session else None,
                "active_task": self._active_task.copy() if self._active_task else None,
                "recent_tools": [
                    {"tool": r.tool_name, "status": r.result_status}
                    for r in self._execution_history[-5:]
                ],
                "config_keys": list(self._config_cache.keys()),
            }
    
    # =========================================================================
    # WRITE OPERATIONS (orchestrator only - LAW 8)
    # =========================================================================
    
    def start_session(self, session_id: str, caller: str = "orchestrator") -> None:
        """
        Start a new session.
        
        Args:
            session_id: Unique session identifier
            caller: Component name (must be authorized)
        """
        self._verify_write_permission(caller)
        
        with self._state_lock:
            now = datetime.now()
            self._session = SessionState(
                session_id=session_id,
                started_at=now,
                last_activity=now,
            )
            self._log_access("session:start", ContextAccessLevel.WRITE, caller)
            logger.info(f"Session started: {session_id}")
    
    def end_session(self, caller: str = "orchestrator") -> None:
        """End current session and clear transient state."""
        self._verify_write_permission(caller)
        
        with self._state_lock:
            session_id = self._session.session_id if self._session else "unknown"
            self._session = None
            self._active_task = None
            self._execution_history.clear()
            self._log_access("session:end", ContextAccessLevel.WRITE, caller)
            logger.info(f"Session ended: {session_id}")
    
    def record_execution(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        result_status: str,
        task_id: Optional[UUID] = None,
        execution_time_ms: Optional[int] = None,
        caller: str = "orchestrator",
    ) -> None:
        """
        Record a tool execution in history.
        
        Args:
            tool_name: Name of the executed tool
            arguments: Tool arguments (will be sanitized)
            result_status: Execution result ("ok", "error", "pending_confirmation")
            task_id: Associated task ID
            execution_time_ms: Execution duration in milliseconds
            caller: Component name (must be authorized)
        """
        self._verify_write_permission(caller)
        
        with self._state_lock:
            # Sanitize arguments (remove sensitive data)
            safe_args = self._sanitize_arguments(arguments)
            
            record = ToolExecutionRecord(
                tool_name=tool_name,
                arguments=safe_args,
                result_status=result_status,
                timestamp=datetime.now(),
                task_id=task_id,
                execution_time_ms=execution_time_ms,
            )
            
            self._execution_history.append(record)
            
            # Enforce L1 memory limit
            if len(self._execution_history) > self.MAX_EXECUTION_HISTORY:
                self._execution_history = self._execution_history[-self.MAX_EXECUTION_HISTORY:]
            
            # Update session activity
            if self._session:
                self._session.last_activity = datetime.now()
            
            self._log_access("execution_history:add", ContextAccessLevel.WRITE, caller)
    
    def set_active_task(
        self,
        task_id: UUID,
        task_type: str,
        metadata: Optional[Dict[str, Any]] = None,
        caller: str = "orchestrator",
    ) -> None:
        """
        Set the active task context.
        
        Args:
            task_id: Task identifier
            task_type: Type of task
            metadata: Additional task metadata
            caller: Component name (must be authorized)
        """
        self._verify_write_permission(caller)
        
        with self._state_lock:
            self._active_task = {
                "task_id": str(task_id),
                "task_type": task_type,
                "started_at": datetime.now().isoformat(),
                "metadata": metadata or {},
            }
            
            if self._session:
                self._session.active_task_id = task_id
            
            self._log_access("active_task:set", ContextAccessLevel.WRITE, caller)
    
    def clear_active_task(self, caller: str = "orchestrator") -> None:
        """Clear the active task context."""
        self._verify_write_permission(caller)
        
        with self._state_lock:
            self._active_task = None
            if self._session:
                self._session.active_task_id = None
            self._log_access("active_task:clear", ContextAccessLevel.WRITE, caller)
    
    def set_config(self, key: str, value: Any, caller: str = "orchestrator") -> None:
        """Set a configuration value in cache."""
        self._verify_write_permission(caller)
        
        with self._state_lock:
            self._config_cache[key] = value
            self._log_access(f"config:{key}:set", ContextAccessLevel.WRITE, caller)
    
    def set_state(self, key: str, value: Any, caller: str = "orchestrator") -> None:
        """Set a custom state value."""
        self._verify_write_permission(caller)
        
        with self._state_lock:
            self._state[key] = value
            self._log_access(f"state:{key}:set", ContextAccessLevel.WRITE, caller)
    
    # =========================================================================
    # INTERNAL HELPERS
    # =========================================================================
    
    def _verify_write_permission(self, caller: str) -> None:
        """
        Verify the caller is authorized to write.
        
        Raises:
            PermissionError: If caller is not authorized (LAW 8 violation)
        """
        if caller not in self._authorized_writers:
            logger.warning(
                f"LAW 8 VIOLATION ATTEMPT: Unauthorized write attempt by '{caller}'"
            )
            raise PermissionError(
                f"LAW 8 violation: Only orchestrator can write to SystemContext. "
                f"Caller '{caller}' is not authorized."
            )
    
    def _sanitize_arguments(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitize arguments to remove sensitive data before storing.
        
        Removes:
        - API keys
        - Passwords
        - Tokens
        - File contents (truncated)
        """
        sensitive_keys = {"password", "api_key", "token", "secret", "key", "auth"}
        result = {}
        
        for k, v in arguments.items():
            k_lower = k.lower()
            if any(s in k_lower for s in sensitive_keys):
                result[k] = "[REDACTED]"
            elif isinstance(v, str) and len(v) > 500:
                result[k] = v[:200] + "...[TRUNCATED]"
            else:
                result[k] = v
        
        return result
    
    def _log_access(
        self,
        resource: str,
        access_level: ContextAccessLevel,
        caller: Optional[str] = None,
    ) -> None:
        """Log context access for audit trail (LAW 13)."""
        # Use debug level to avoid log spam
        logger.debug(
            f"Context access: {access_level.value} {resource}"
            + (f" by {caller}" if caller else "")
        )


# Convenience function for getting the singleton
def get_system_context() -> SystemContext:
    """Get the SystemContext singleton instance."""
    return SystemContext()
