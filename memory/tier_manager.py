"""
Memory Tier Manager

Unified management of memory tiers:
- L1: Active Context (SystemContext - in-memory, ephemeral)
- L2: Short-term Memory (SQLite - persistent, 7-day retention)
- L3: Long-term Sync (Supabase - Phase 13 implementation)

Law Compliance:
- LAW 7: Memory is non-authoritative (read-only to AI/tools)
- LAW 8: Only orchestrator can write
- LAW 9: Memory degradation control (summarization, retention)
- LAW 14: Log retention discipline
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

from core.system_context import get_system_context, ToolExecutionRecord
from memory.database_schema import MemoryTier

# Lazy import for sync to avoid circular dependencies
_sync_manager = None

logger = logging.getLogger(__name__)


@dataclass
class TierConfig:
    """Configuration for a memory tier."""
    name: str
    max_entries: int
    retention_days: Optional[int]  # None = no expiration
    description: str


# Tier configurations (Phase 12)
TIER_CONFIGS: Dict[MemoryTier, TierConfig] = {
    MemoryTier.L1: TierConfig(
        name="Active Context",
        max_entries=100,  # Matches SystemContext.MAX_EXECUTION_HISTORY
        retention_days=None,  # Ephemeral, cleared on session end
        description="In-memory runtime context (tool history, session state)",
    ),
    MemoryTier.L2: TierConfig(
        name="Short-term Memory",
        max_entries=10000,
        retention_days=7,
        description="SQLite persistent storage (summarized interactions)",
    ),
    MemoryTier.L3: TierConfig(
        name="Long-term Sync",
        max_entries=None,  # Cloud limit
        retention_days=365,
        description="Supabase synchronized memory (designed for Phase 13)",
    ),
}


class TierMigrationDirection(Enum):
    """Direction for tier migration."""
    PROMOTE = "promote"  # L1 -> L2 -> L3
    DEMOTE = "demote"    # L3 -> L2 -> L1 (for caching)


class MemoryTierManager:
    """
    Manages memory across all tiers with unified access.
    
    Provides:
    - Unified read access across tiers
    - Tier-specific configuration
    - Migration between tiers (L1 -> L2)
    - Retention enforcement for L2
    
    Rules:
    - All writes go through orchestrator (LAW 8)
    - Memory is informational only (LAW 7)
    - Retention policies enforced (LAW 14)
    """
    
    def __init__(self, database: Optional[Any] = None) -> None:
        """
        Initialize the tier manager.
        
        Args:
            database: Optional Database instance for L2 (SQLite) access
        """
        self._context = get_system_context()
        self._database = database  # For L2 access
        self._tier_configs = TIER_CONFIGS
        
        logger.info("MemoryTierManager initialized")
    
    def get_tier_config(self, tier: MemoryTier) -> TierConfig:
        """Get configuration for a specific tier."""
        return self._tier_configs[tier]
    
    def get_l1_summary(self) -> Dict[str, Any]:
        """
        Get summary of L1 (Active Context) state.
        
        Returns:
            Dictionary with L1 state summary
        """
        session = self._context.get_session()
        history = self._context.get_execution_history(limit=10)
        
        return {
            "tier": "L1",
            "name": self._tier_configs[MemoryTier.L1].name,
            "session_id": session.session_id if session else None,
            "recent_executions": len(history),
            "active_task": self._context.get_active_task() is not None,
        }
    
    def get_l1_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent execution history from L1.
        
        Args:
            limit: Maximum entries to return
            
        Returns:
            List of execution records as dictionaries
        """
        history = self._context.get_execution_history(limit=limit)
        return [
            {
                "tool_name": record.tool_name,
                "result_status": record.result_status,
                "timestamp": record.timestamp.isoformat(),
                "task_id": str(record.task_id) if record.task_id else None,
            }
            for record in history
        ]
    
    def get_l2_summary(self) -> Dict[str, Any]:
        """
        Get summary of L2 (Short-term Memory) state.
        
        Returns:
            Dictionary with L2 state summary
        """
        if not self._database:
            return {
                "tier": "L2",
                "name": self._tier_configs[MemoryTier.L2].name,
                "available": False,
                "reason": "Database not connected",
            }
        
        try:
            conn = self._database.get_connection()
            cursor = conn.cursor()
            
            # Get count of L2 entries
            cursor.execute(
                "SELECT COUNT(*) FROM memory WHERE memory_tier = ?",
                (MemoryTier.L2.value,)
            )
            count = cursor.fetchone()[0]
            
            # Get oldest and newest entries
            cursor.execute(
                """
                SELECT MIN(created_at), MAX(created_at) 
                FROM memory WHERE memory_tier = ?
                """,
                (MemoryTier.L2.value,)
            )
            oldest, newest = cursor.fetchone()
            
            return {
                "tier": "L2",
                "name": self._tier_configs[MemoryTier.L2].name,
                "available": True,
                "entry_count": count,
                "oldest_entry": oldest,
                "newest_entry": newest,
                "retention_days": self._tier_configs[MemoryTier.L2].retention_days,
            }
        except Exception as e:
            logger.error(f"Error getting L2 summary: {e}")
            return {
                "tier": "L2",
                "name": self._tier_configs[MemoryTier.L2].name,
                "available": False,
                "reason": str(e),
            }
    
    def get_l3_summary(self) -> Dict[str, Any]:
        """
        Get summary of L3 (Long-term Sync) state.
        
        Returns:
            Dictionary with L3 state summary
        """
        global _sync_manager
        
        try:
            if _sync_manager is None:
                from sync.sync_manager import get_sync_manager
                _sync_manager = get_sync_manager()
            
            sync_status = _sync_manager.get_sync_status()
            
            return {
                "tier": "L3",
                "name": self._tier_configs[MemoryTier.L3].name,
                "available": sync_status["supabase"]["is_configured"],
                "connected": sync_status["supabase"]["is_connected"],
                "status": sync_status["status"],
                "last_sync": sync_status["last_sync"],
                "queue_pending": sync_status["queue"]["pending"],
                "queue_failed": sync_status["queue"]["failed"],
                "device_id": sync_status["device_id"],
            }
        except ImportError:
            return {
                "tier": "L3",
                "name": self._tier_configs[MemoryTier.L3].name,
                "available": False,
                "reason": "Sync package not available",
            }
        except Exception as e:
            logger.warning(f"Error getting L3 summary: {e}")
            return {
                "tier": "L3",
                "name": self._tier_configs[MemoryTier.L3].name,
                "available": False,
                "reason": str(e),
            }
    
    def get_all_tiers_summary(self) -> Dict[str, Any]:
        """
        Get summary of all memory tiers.
        
        Returns:
            Dictionary with all tier summaries
        """
        return {
            "L1": self.get_l1_summary(),
            "L2": self.get_l2_summary(),
            "L3": self.get_l3_summary(),
        }
    
    def enforce_l2_retention(self, caller: str = "orchestrator") -> int:
        """
        Enforce retention policy on L2 (delete expired entries).
        
        This is called by orchestrator/automation to clean up old data.
        
        Args:
            caller: Component name (must be authorized)
            
        Returns:
            Number of entries deleted
        """
        if caller not in {"orchestrator", "automation_manager"}:
            raise PermissionError(
                f"LAW 8 violation: Only orchestrator can modify memory. "
                f"Caller '{caller}' is not authorized."
            )
        
        if not self._database:
            return 0
        
        retention_days = self._tier_configs[MemoryTier.L2].retention_days
        if not retention_days:
            return 0
        
        cutoff = (datetime.now() - timedelta(days=retention_days)).isoformat()
        
        try:
            conn = self._database.get_connection()
            cursor = conn.cursor()
            
            # Delete expired L2 entries
            cursor.execute(
                """
                DELETE FROM memory 
                WHERE memory_tier = ? AND created_at < ?
                """,
                (MemoryTier.L2.value, cutoff)
            )
            
            deleted = cursor.rowcount
            conn.commit()
            
            if deleted > 0:
                logger.info(
                    f"L2 retention enforced: {deleted} entries deleted (older than {retention_days} days)",
                    extra={"deleted_count": deleted, "cutoff": cutoff},
                )
            
            return deleted
        except Exception as e:
            logger.error(f"Error enforcing L2 retention: {e}")
            return 0

    def queue_for_sync(
        self,
        operation_type: str,
        record_id: str,
        payload: Dict[str, Any],
        caller: str = "orchestrator",
    ) -> Optional[str]:
        """
        Queue a memory record for L3 synchronization.
        
        Called after L2 writes to ensure cloud backup.
        
        Args:
            operation_type: "INSERT", "UPDATE", or "DELETE"
            record_id: ID of the memory record
            payload: Record data
            caller: Component name (must be authorized)
            
        Returns:
            Queue operation ID if queued, None otherwise
            
        LAW 8: Only orchestrator can trigger sync writes.
        """
        if caller not in {"orchestrator", "memory_manager", "tier_manager"}:
            raise PermissionError(
                f"LAW 8 violation: Only orchestrator can queue for sync. "
                f"Caller '{caller}' is not authorized."
            )
        
        global _sync_manager
        
        try:
            if _sync_manager is None:
                from sync.sync_manager import get_sync_manager
                _sync_manager = get_sync_manager()
            
            from sync.sync_queue import OperationType
            
            op_type = OperationType(operation_type)
            return _sync_manager.queue_for_sync(
                operation_type=op_type,
                table_name="memory",
                record_id=record_id,
                payload=payload,
            )
        except ImportError:
            logger.debug("Sync package not available, skipping queue")
            return None
        except Exception as e:
            logger.warning(f"Failed to queue for sync: {e}")
            return None


# Convenience function
_default_manager: Optional[MemoryTierManager] = None


def get_tier_manager(database: Optional[Any] = None) -> MemoryTierManager:
    """Get or create the default MemoryTierManager."""
    global _default_manager
    if _default_manager is None or database is not None:
        _default_manager = MemoryTierManager(database=database)
    return _default_manager


def reset_tier_manager() -> None:
    """Reset the tier manager (for testing)."""
    global _default_manager
    _default_manager = None
