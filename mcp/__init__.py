"""
MCP (Model Control Plane) Module

Pure gatekeeper for tool request validation and authorization.
Per DIP Phase 2: Governance & Control Plane.

Enforces:
- LAW 3 — LLM IS NOT AN AGENT
- LAW 4 — TOOL-ONLY EXECUTION
- LAW 5 — EXPLICIT PERMISSIONS
- LAW 13 — COMPLETE AUDITABILITY
"""

from mcp.authorization_layer import AuthorizationLayer, AuthorizationResult
from mcp.mcp_server import MCPServer
from mcp.policy_engine import PermissionCheck, PermissionDecision, PolicyEngine
from mcp.request_validator import RequestValidator, ValidationError
from mcp.tool_registry import ToolRegistry
from mcp.tool_schema import PermissionLevel, ToolSchema

__all__ = [
    "AuthorizationLayer",
    "AuthorizationResult",
    "MCPServer",
    "PermissionCheck",
    "PermissionDecision",
    "PermissionLevel",
    "PolicyEngine",
    "RequestValidator",
    "ToolRegistry",
    "ToolSchema",
    "ValidationError",
]
