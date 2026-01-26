"""
Tool Registry

Static tool registry. No dynamic tool generation allowed.
Enforces LAW 4 — TOOL-ONLY EXECUTION and LAW 6 — NO FREE-FORM COMPUTATION.

Per DIP Phase 2: Tool schema framework (no tools yet).
"""

import logging
from typing import Dict, Optional

from mcp.tool_schema import ToolSchema

logger = logging.getLogger(__name__)


class ToolRegistry:
    """
    Static tool registry.

    Enforces:
    - LAW 4: Only registered tools callable
    - LAW 6: Tool registry is static (no dynamic generation)

    Per DIP Phase 2 and LAW 4/6 enforcement.
    """

    def __init__(self) -> None:
        """Initialize the tool registry."""
        self._tools: Dict[str, ToolSchema] = {}
        self._locked = False

    def register(self, tool_schema: ToolSchema) -> None:
        """
        Register a tool schema.

        Args:
            tool_schema: Tool schema to register

        Raises:
            RuntimeError: If registry is locked or tool already exists
            ValueError: If tool schema is invalid
        """
        if self._locked:
            raise RuntimeError(
                "Tool registry is locked. No new tools can be registered. "
                "This enforces LAW 6 — NO FREE-FORM COMPUTATION."
            )

        if tool_schema.name in self._tools:
            raise ValueError(f"Tool '{tool_schema.name}' is already registered")

        self._tools[tool_schema.name] = tool_schema

        logger.info(
            f"Tool '{tool_schema.name}' registered",
            extra={
                "tool_name": tool_schema.name,
                "permission_level": tool_schema.permission_level.value,
                "requires_confirmation": tool_schema.requires_confirmation,
            },
        )

    def get(self, tool_name: str) -> Optional[ToolSchema]:
        """
        Get a tool schema by name.

        Args:
            tool_name: Name of the tool

        Returns:
            Tool schema, or None if not found
        """
        return self._tools.get(tool_name)

    def exists(self, tool_name: str) -> bool:
        """
        Check if a tool is registered.

        Args:
            tool_name: Name of the tool

        Returns:
            True if tool exists, False otherwise
        """
        return tool_name in self._tools

    def list_tools(self) -> list[str]:
        """
        List all registered tool names.

        Returns:
            List of tool names
        """
        return list(self._tools.keys())

    def lock(self) -> None:
        """
        Lock the registry, preventing new tool registration.

        This enforces LAW 6 — NO FREE-FORM COMPUTATION.
        Once locked, no new tools can be added.
        """
        self._locked = True
        logger.info("Tool registry locked")

    def is_locked(self) -> bool:
        """
        Check if registry is locked.

        Returns:
            True if locked, False otherwise
        """
        return self._locked
