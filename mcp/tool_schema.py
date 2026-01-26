"""
Tool Schema Framework

Defines strict tool schema format for tool registration.
Per DIP Phase 2: Tool schema framework (no tools yet).

Enforces:
- LAW 4 — TOOL-ONLY EXECUTION
- LAW 6 — NO FREE-FORM COMPUTATION
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional

# Import JSON schema validation when available
try:
    import jsonschema
except ImportError:
    jsonschema = None  # Will be added in later phases if needed


class PermissionLevel(str, Enum):
    """
    Permission levels for tools.

    Per system_schema.json permission_level enum.
    """

    NONE = "NONE"
    """No permissions required."""

    READ = "READ"
    """Read-only permission."""

    WRITE = "WRITE"
    """Write permission."""

    EXECUTE = "EXECUTE"
    """Execute permission."""


@dataclass
class ToolSchema:
    """
    Tool schema definition.

    Each tool must be explicitly declared with this schema.
    Per LAW 4 and LAW 6: All tools must be pre-declared.
    """

    name: str
    """Tool name (must be unique, exact match required)."""

    description: str
    """Human-readable tool description."""

    input_schema: Dict[str, Any]
    """JSON schema for tool input arguments."""

    output_schema: Dict[str, Any]
    """JSON schema for tool output."""

    permission_level: PermissionLevel
    """Required permission level for this tool."""

    requires_confirmation: bool
    """Whether this tool requires explicit user confirmation before execution."""

    version: str = "1.0.0"
    """Tool schema version."""

    def __post_init__(self) -> None:
        """Validate tool schema."""
        if not self.name:
            raise ValueError("Tool name cannot be empty")
        if not self.description:
            raise ValueError("Tool description cannot be empty")
        if not isinstance(self.input_schema, dict):
            raise ValueError("input_schema must be a dictionary")
        if not isinstance(self.output_schema, dict):
            raise ValueError("output_schema must be a dictionary")

    def validate_input(self, arguments: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        Validate tool input arguments against schema.

        Args:
            arguments: Tool arguments to validate

        Returns:
            Tuple of (is_valid, error_message)
            If valid, error_message is None.
        """
        # Phase 2: Basic validation (structure only)
        # In later phases, full JSON schema validation will be implemented
        if not isinstance(arguments, dict):
            return False, "Arguments must be a dictionary"

        # Check required fields from input_schema
        required = self.input_schema.get("required", [])
        for field in required:
            if field not in arguments:
                return False, f"Missing required argument: {field}"

        return True, None
