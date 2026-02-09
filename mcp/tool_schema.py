"""
Tool Schema Framework

Defines strict tool schema format for tool registration.
Per DIP Phase 2: Tool schema framework (no tools yet).
Per DIP Phase 11: Added category field for tool organization.
Per EVOLUTION_ROADMAP Phase 24.1: Added capability_domain for capability-driven tool grouping.
Per EVOLUTION_ROADMAP Phase 24.2: Added side_effect_scope for side-effect classification.

Enforces:
- LAW 4 — TOOL-ONLY EXECUTION
- LAW 6 — NO FREE-FORM COMPUTATION
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional, TYPE_CHECKING

# Phase 24.1: Allowed capability domains (EVOLUTION_ROADMAP §12)
CAPABILITY_DOMAINS = frozenset({"file", "memory", "system", "automation", "content", "integration", "general"})

# Phase 24.2: Allowed side-effect scopes (EVOLUTION_ROADMAP §14)
SIDE_EFFECT_SCOPES = frozenset({"READ_ONLY", "WRITE", "EXECUTE", "EXTERNAL"})

if TYPE_CHECKING:
    from tools.categories import ToolCategory

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

    category: Optional[str] = None
    """Tool category (system, file, memory, automation, content, integration)."""

    capability_domain: Optional[str] = None
    """Capability domain for grouping (file, memory, system, automation, content, integration, general). Phase 24.1."""

    side_effect_scope: Optional[str] = None
    """Side-effect scope: READ_ONLY, WRITE, EXECUTE, EXTERNAL. If absent, treat as READ_ONLY. Phase 24.2."""

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
        if self.capability_domain is not None and self.capability_domain not in CAPABILITY_DOMAINS:
            raise ValueError(
                f"capability_domain must be one of {sorted(CAPABILITY_DOMAINS)}, got {self.capability_domain!r}"
            )
        if self.side_effect_scope is not None and self.side_effect_scope not in SIDE_EFFECT_SCOPES:
            raise ValueError(
                f"side_effect_scope must be one of {sorted(SIDE_EFFECT_SCOPES)}, got {self.side_effect_scope!r}"
            )

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
