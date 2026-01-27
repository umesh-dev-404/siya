"""
File Write Tool

Write file contents with confirmation requirement.
Per DIP Phase 11: File operations tools.

Enforces:
- LAW 1 — HUMAN SOVEREIGNTY (requires confirmation)
- LAW 4 — TOOL-ONLY EXECUTION
- LAW 5 — EXPLICIT PERMISSIONS
- LAW 13 — COMPLETE AUDITABILITY
- LAW 15 — SECRET ISOLATION
"""

import logging
import os
from pathlib import Path
from typing import Any, Dict
from datetime import datetime

from mcp.tool_schema import PermissionLevel, ToolSchema

logger = logging.getLogger(__name__)

# Allowed base directories for writing
ALLOWED_WRITE_DIRS = [
    "/opt/siya/data",
    "/opt/siya/exports",
    "D:\\Projects\\siya\\data",  # PC development
]

# Blocked file patterns (LAW 15)
BLOCKED_PATTERNS = [
    ".env",
    "secrets",
    ".ssh",
    "password",
    "credential",
    ".key",
    ".pem",
    ".service",  # Prevent overwriting systemd files
]


def make_file_write_tool() -> ToolSchema:
    """Create the file write tool schema."""
    return ToolSchema(
        name="file_write",
        description="[file] Write content to a file. Requires confirmation (LAW 1).",
        input_schema={
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Absolute path to write to."
                },
                "content": {
                    "type": "string",
                    "description": "Content to write."
                },
                "mode": {
                    "type": "string",
                    "enum": ["overwrite", "append"],
                    "description": "Write mode (default: overwrite)."
                },
                "encoding": {
                    "type": "string",
                    "description": "File encoding (default: utf-8)."
                }
            },
            "required": ["path", "content"]
        },
        output_schema={"type": "object"},
        permission_level=PermissionLevel.WRITE,
        requires_confirmation=True,  # LAW 1: Human sovereignty
        category="file",
    )


def _validate_write_path(path: str) -> tuple[bool, str]:
    """
    Validate file path for write security.
    
    Returns:
        (is_valid, error_message)
    """
    # Check for blocked patterns (LAW 15)
    lower_path = path.lower()
    for pattern in BLOCKED_PATTERNS:
        if pattern in lower_path:
            return False, f"Write denied: path contains blocked pattern '{pattern}' (LAW 15)"
    
    # Check if path is under allowed directories
    resolved = Path(path).resolve()
    
    for base_dir in ALLOWED_WRITE_DIRS:
        try:
            base = Path(base_dir).resolve()
            if str(resolved).startswith(str(base)):
                return True, ""
        except Exception:
            continue
    
    return False, f"Write denied: path not in allowed directories"


def file_write_impl(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute file write tool.
    
    NOTE: This tool requires confirmation before execution.
    The orchestrator should verify user consent before calling this.
    
    Args:
        args: Tool arguments
            - path: File path to write
            - content: Content to write
            - mode: 'overwrite' or 'append'
            - encoding: File encoding
    
    Returns:
        Write result or error
    """
    path = args.get("path", "")
    content = args.get("content", "")
    mode = args.get("mode", "overwrite")
    encoding = args.get("encoding", "utf-8")
    
    logger.info(f"Executing file_write tool: path={path}, mode={mode}, content_len={len(content)}")
    
    try:
        # Validate path
        is_valid, error = _validate_write_path(path)
        if not is_valid:
            logger.warning(f"file_write blocked: {error}")
            return {
                "status": "error",
                "message": error,
            }
        
        # Ensure parent directory exists
        parent = Path(path).parent
        if not parent.exists():
            os.makedirs(parent, exist_ok=True)
            logger.info(f"Created directory: {parent}")
        
        # Write file
        file_mode = "a" if mode == "append" else "w"
        existed = os.path.exists(path)
        
        with open(path, file_mode, encoding=encoding) as f:
            f.write(content)
        
        stat = os.stat(path)
        
        result = {
            "status": "ok",
            "path": path,
            "mode": mode,
            "bytes_written": len(content.encode(encoding)),
            "file_size": stat.st_size,
            "created": not existed,
            "timestamp": datetime.now().isoformat(),
        }
        
        logger.info(f"file_write completed: {result['bytes_written']} bytes to {path}")
        return result
        
    except Exception as e:
        logger.error(f"File write failed: {e}", exc_info=True)
        return {
            "status": "error",
            "message": str(e),
        }
