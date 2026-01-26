"""
Production Lock

Production lock mechanism for schema versions and tool registry.
Per DIP Phase 9: Production Lock & Baseline.

Enforces:
- LAW 6 — NO FREE-FORM COMPUTATION (tool registry lock)
- System reproducibility
- System stability
"""

import json
import logging
from pathlib import Path
from typing import Dict, Optional

from mcp.tool_registry import ToolRegistry

logger = logging.getLogger(__name__)


class ProductionLock:
    """
    Production lock manager.

    Per DIP Phase 9:
    - Lock schema versions
    - Lock tool registry
    - Ensure reproducibility
    - Ensure stability

    Enforces:
    - LAW 6 — NO FREE-FORM COMPUTATION
    """

    def __init__(self, lock_file: Optional[Path] = None) -> None:
        """
        Initialize production lock.

        Args:
            lock_file: Path to lock file (default: ./production_lock.json)
        """
        self._lock_file = lock_file or Path("production_lock.json")
        self._locked = False
        self._schema_version: Optional[str] = None
        self._tool_registry_locked = False

    def lock_schema_version(self, schema_version: str) -> None:
        """
        Lock schema version.

        Args:
            schema_version: Schema version to lock (e.g., "1.0.0")

        Raises:
            RuntimeError: If already locked with different version
        """
        if self._locked and self._schema_version != schema_version:
            raise RuntimeError(
                f"Schema version already locked to {self._schema_version}. "
                f"Cannot lock to {schema_version}."
            )

        self._schema_version = schema_version
        self._save_lock()

        logger.info(
            f"Schema version locked to {schema_version}",
            extra={"schema_version": schema_version},
        )

    def lock_tool_registry(self, tool_registry: ToolRegistry) -> None:
        """
        Lock tool registry.

        Args:
            tool_registry: Tool registry to lock

        Note:
            Per DIP Phase 9: Lock tool registry for production baseline.
            This enforces LAW 6 — NO FREE-FORM COMPUTATION.
        """
        if not tool_registry.is_locked():
            tool_registry.lock()

        self._tool_registry_locked = True
        self._save_lock()

        logger.info("Tool registry locked for production")

    def finalize_lock(self) -> None:
        """
        Finalize production lock.

        This makes the lock permanent and prevents further changes.

        Note:
            Per DIP Phase 9: Finalize baseline for production.
        """
        if not self._schema_version:
            raise RuntimeError("Cannot finalize lock: schema version not locked")

        if not self._tool_registry_locked:
            raise RuntimeError("Cannot finalize lock: tool registry not locked")

        self._locked = True
        self._save_lock()

        logger.info("Production lock finalized", extra={"schema_version": self._schema_version})

    def is_locked(self) -> bool:
        """
        Check if production is locked.

        Returns:
            True if locked, False otherwise
        """
        return self._locked

    def get_schema_version(self) -> Optional[str]:
        """
        Get locked schema version.

        Returns:
            Schema version, or None if not locked
        """
        return self._schema_version

    def _save_lock(self) -> None:
        """Save lock state to file."""
        lock_data = {
            "locked": self._locked,
            "schema_version": self._schema_version,
            "tool_registry_locked": self._tool_registry_locked,
        }

        with open(self._lock_file, "w") as f:
            json.dump(lock_data, f, indent=2)

    def load_lock(self) -> None:
        """
        Load lock state from file.

        Note:
            Called on system startup to restore lock state.
        """
        if not self._lock_file.exists():
            return

        try:
            with open(self._lock_file, "r") as f:
                lock_data = json.load(f)

            self._locked = lock_data.get("locked", False)
            self._schema_version = lock_data.get("schema_version")
            self._tool_registry_locked = lock_data.get("tool_registry_locked", False)

            if self._locked:
                logger.info(
                    "Production lock loaded",
                    extra={"schema_version": self._schema_version},
                )

        except Exception as e:
            logger.error(f"Failed to load production lock: {e}", exc_info=True)
