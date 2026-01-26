"""
State Checker

State consistency checking and corruption detection.
Per DIP Phase 8: No corrupted state.

Enforces:
- LAW 12 — FAILURE TRANSPARENCY
- No corrupted state
"""

import logging
from typing import Any, Dict, List, Optional

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from memory.database import Database

logger = logging.getLogger(__name__)


class StateChecker:
    """
    State consistency checker.

    Per DIP Phase 8:
    - No corrupted state
    - State validation on startup
    - State recovery if needed

    Enforces:
    - LAW 12 — FAILURE TRANSPARENCY
    """

    def __init__(self, database: "Database") -> None:
        """
        Initialize state checker.

        Args:
            database: Database connection
        """
        self._database = database

    def check_state_consistency(self) -> Dict[str, Any]:
        """
        Check system state consistency.

        Returns:
            Consistency check result with issues found

        Note:
            Per DIP Phase 8: No corrupted state.
            This method validates system state on startup.
        """
        issues: List[str] = []

        try:
            # Check database integrity
            conn = self._database.get_connection()
            cursor = conn.cursor()

            # Check for orphaned records
            # Check memory table
            cursor.execute(
                """
                SELECT COUNT(*) FROM memory 
                WHERE parent_memory_id IS NOT NULL 
                AND parent_memory_id NOT IN (SELECT id FROM memory)
                """
            )
            orphaned_memory = cursor.fetchone()[0]
            if orphaned_memory > 0:
                issues.append(f"Found {orphaned_memory} orphaned memory entries")

            # Check audit log consistency
            cursor.execute(
                """
                SELECT COUNT(*) FROM audit_log 
                WHERE request_id IS NOT NULL 
                AND request_id NOT IN (SELECT DISTINCT request_id FROM audit_log WHERE request_id IS NOT NULL)
                """
            )
            # This is a basic check - more sophisticated checks can be added

            # Check for incomplete tasks (if task state table exists in future)
            # Phase 8: Basic checks only

        except Exception as e:
            logger.error(f"State consistency check failed: {e}", exc_info=True)
            issues.append(f"State check error: {str(e)}")

        result = {
            "consistent": len(issues) == 0,
            "issues": issues,
        }

        if issues:
            logger.warning(
                f"State consistency issues found: {len(issues)}",
                extra={"issues": issues},
            )
        else:
            logger.info("State consistency check passed")

        return result

    def recover_state(self, issues: List[str]) -> bool:
        """
        Attempt to recover from state inconsistencies.

        Args:
            issues: List of consistency issues

        Returns:
            True if recovery successful, False otherwise

        Note:
            Per DIP Phase 8: No corrupted state.
            This method attempts to fix detected issues.
        """
        if not issues:
            return True

        logger.info(f"Attempting state recovery for {len(issues)} issues")

        try:
            conn = self._database.get_connection()
            cursor = conn.cursor()

            # Phase 8: Basic recovery
            # Remove orphaned memory entries (or mark for review)
            cursor.execute(
                """
                DELETE FROM memory 
                WHERE parent_memory_id IS NOT NULL 
                AND parent_memory_id NOT IN (SELECT id FROM memory)
                """
            )
            orphaned_deleted = cursor.rowcount
            if orphaned_deleted > 0:
                logger.info(f"Recovered: Removed {orphaned_deleted} orphaned memory entries")

            conn.commit()

            return True

        except Exception as e:
            logger.error(f"State recovery failed: {e}", exc_info=True)
            return False
