"""
Tool Executor

Executes registered tool implementations (callables) by name.

Important:
- This is execution (side effects), so it lives outside governance validation.
- Governance (MCP) validates/authorizes; Orchestrator executes.
"""

import logging
from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger(__name__)


ToolCallable = Callable[[Dict[str, Any]], Dict[str, Any]]


@dataclass(frozen=True)
class ToolExecutionResult:
    tool_name: str
    output: Dict[str, Any]


class ToolExecutor:
    """
    Executes tools by name.

    This is deliberately simple/explicit:
    - static registry (no dynamic loading)
    - one tool name -> one callable
    """

    def __init__(self) -> None:
        self._tools: Dict[str, ToolCallable] = {}

    def register(self, tool_name: str, tool_callable: ToolCallable) -> None:
        if tool_name in self._tools:
            raise ValueError(f"Tool implementation already registered: {tool_name}")
        self._tools[tool_name] = tool_callable
        logger.info("Tool implementation registered", extra={"tool_name": tool_name})

    def has(self, tool_name: str) -> bool:
        return tool_name in self._tools

    def execute(self, tool_name: str, arguments: Dict[str, Any]) -> ToolExecutionResult:
        if tool_name not in self._tools:
            raise RuntimeError(f"TOOL_NOT_IMPLEMENTED: Tool '{tool_name}' has no implementation")

        tool_fn = self._tools[tool_name]
        logger.info("Executing tool", extra={"tool_name": tool_name})
        output = tool_fn(arguments)
        if not isinstance(output, dict):
            raise RuntimeError(f"INVALID_TOOL_OUTPUT: Tool '{tool_name}' must return a dict")
        return ToolExecutionResult(tool_name=tool_name, output=output)

