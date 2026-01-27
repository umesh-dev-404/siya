"""
Tool Executor

Executes registered tool implementations (callables) by name.

Important:
- This is execution (side effects), so it lives outside governance validation.
- Governance (MCP) validates/authorizes; Orchestrator executes.
- Phase 12: Tools can access read-only context via get_execution_context()
"""

import logging
from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger(__name__)


# Phase 12: Context-aware tool callable signature
# Tools can optionally receive context as second argument
ToolCallable = Callable[[Dict[str, Any]], Dict[str, Any]]
ContextAwareToolCallable = Callable[[Dict[str, Any], Dict[str, Any]], Dict[str, Any]]


@dataclass(frozen=True)
class ToolExecutionResult:
    tool_name: str
    output: Dict[str, Any]
    execution_time_ms: Optional[int] = None  # Phase 12: Execution timing


class ToolExecutor:
    """
    Executes tools by name.

    This is deliberately simple/explicit:
    - static registry (no dynamic loading)
    - one tool name -> one callable
    
    Phase 12 additions:
    - Tools can access read-only context (LAW 7 compliant)
    - Execution timing is tracked
    """

    def __init__(self) -> None:
        self._tools: Dict[str, ToolCallable] = {}
        self._context_aware_tools: Dict[str, bool] = {}  # Track which tools want context

    def register(
        self, 
        tool_name: str, 
        tool_callable: ToolCallable,
        context_aware: bool = False,
    ) -> None:
        """
        Register a tool implementation.
        
        Args:
            tool_name: Name of the tool
            tool_callable: Function to execute
            context_aware: If True, tool will receive context as second arg (LAW 7 - read-only)
        """
        if tool_name in self._tools:
            raise ValueError(f"Tool implementation already registered: {tool_name}")
        self._tools[tool_name] = tool_callable
        self._context_aware_tools[tool_name] = context_aware
        logger.info("Tool implementation registered", extra={
            "tool_name": tool_name,
            "context_aware": context_aware,
        })

    def has(self, tool_name: str) -> bool:
        return tool_name in self._tools

    def get_execution_context(self) -> Dict[str, Any]:
        """
        Get read-only execution context for tools (LAW 7 compliant).
        
        Returns:
            Dictionary with read-only context information:
            - session_id: Current session identifier
            - recent_tools: List of recently executed tool names
            - active_task: Boolean indicating if a task is active
            
        Note:
            LAW 7: This context is informational only.
            Tools MUST NOT use this to make decisions that bypass governance.
        """
        try:
            from core.system_context import get_system_context
            ctx = get_system_context()
            
            session = ctx.get_session()
            history = ctx.get_execution_history(limit=5)
            
            return {
                "session_id": session.session_id if session else None,
                "recent_tools": [r.tool_name for r in history],
                "active_task": ctx.get_active_task() is not None,
                "_law7_notice": "This context is informational only. Do not use for authorization.",
            }
        except Exception as e:
            logger.debug(f"Context access failed (expected in tests): {e}")
            return {
                "session_id": None,
                "recent_tools": [],
                "active_task": False,
                "_law7_notice": "Context unavailable.",
            }

    def execute(self, tool_name: str, arguments: Dict[str, Any]) -> ToolExecutionResult:
        if tool_name not in self._tools:
            raise RuntimeError(f"TOOL_NOT_IMPLEMENTED: Tool '{tool_name}' has no implementation")

        tool_fn = self._tools[tool_name]
        is_context_aware = self._context_aware_tools.get(tool_name, False)
        
        logger.info("Executing tool", extra={
            "tool_name": tool_name,
            "context_aware": is_context_aware,
        })
        
        # Phase 12: Provide context to context-aware tools
        if is_context_aware:
            context = self.get_execution_context()
            output = tool_fn(arguments, context)  # type: ignore
        else:
            output = tool_fn(arguments)
            
        if not isinstance(output, dict):
            raise RuntimeError(f"INVALID_TOOL_OUTPUT: Tool '{tool_name}' must return a dict")
        return ToolExecutionResult(tool_name=tool_name, output=output)

