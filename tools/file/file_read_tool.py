"""
File Read Tool

Read file contents with security validation.
Per DIP Phase 11: File operations tools.

Enforces:
- LAW 4 — TOOL-ONLY EXECUTION
- LAW 13 — COMPLETE AUDITABILITY
- LAW 15 — SECRET ISOLATION (prevents reading secrets)
"""

import logging
import os
from pathlib import Path
from typing import Any, Dict

from mcp.tool_schema import PermissionLevel, ToolSchema

logger = logging.getLogger(__name__)

# Allowed base directories (security: prevent arbitrary file access)
ALLOWED_BASE_DIRS = [
    "/opt/siya/data",
    "/opt/siya/exports",
    "/home",
    "D:\\Projects\\siya\\data",  # PC development
]

# Blocked file patterns (LAW 15: secret isolation)
BLOCKED_PATTERNS = [
    ".env",
    "secrets",
    ".ssh",
    "password",
    "credential",
    ".key",
    ".pem",
]


def make_file_read_tool() -> ToolSchema:
    """Create the file read tool schema."""
    return ToolSchema(
        name="file_read",
        description="[file] Read contents of a file. Limited to allowed directories.",
        input_schema={
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Absolute path to the file to read."
                },
                "encoding": {
                    "type": "string",
                    "description": "File encoding (default: utf-8)."
                },
                "max_bytes": {
                    "type": "integer",
                    "description": "Maximum bytes to read (default: 100KB)."
                }
            },
            "required": ["path"]
        },
        output_schema={"type": "object"},
        permission_level=PermissionLevel.READ,
        requires_confirmation=False,
        category="file",
        capability_domain="file",
        side_effect_scope="READ_ONLY",
    )


def _validate_path(path: str) -> tuple[bool, str]:
    """
    Validate file path for security.
    
    Returns:
        (is_valid, error_message)
    """
    # Check for blocked patterns (LAW 15)
    lower_path = path.lower()
    for pattern in BLOCKED_PATTERNS:
        if pattern in lower_path:
            return False, f"Access denied: path contains blocked pattern '{pattern}' (LAW 15)"
    
    # Check if path is under allowed directories
    resolved = Path(path).resolve()
    
    for base_dir in ALLOWED_BASE_DIRS:
        try:
            base = Path(base_dir).resolve()
            if str(resolved).startswith(str(base)):
                return True, ""
        except Exception:
            continue
    
    return False, f"Access denied: path not in allowed directories"


def file_read_impl(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute file read tool.
    
    Args:
        args: Tool arguments
            - path: File path to read
            - encoding: File encoding
            - max_bytes: Maximum bytes to read
    
    Returns:
        File contents or error
    """
    path = args.get("path", "")
    encoding = args.get("encoding", "utf-8")
    max_bytes = args.get("max_bytes", 100 * 1024)  # 100KB default
    
    logger.info(f"Executing file_read tool: path={path}")
    
    try:
        # Validate path
        is_valid, error = _validate_path(path)
        if not is_valid:
            logger.warning(f"file_read blocked: {error}")
            return {
                "status": "error",
                "message": error,
            }
        
        # Check file exists
        if not os.path.isfile(path):
            return {
                "status": "error",
                "message": f"File not found: {path}",
            }
        
        # Get file info
        stat = os.stat(path)
        file_size = stat.st_size
        
        # Read file
        with open(path, "r", encoding=encoding) as f:
            content = f.read(max_bytes)
        
        truncated = file_size > max_bytes
        
        result = {
            "status": "ok",
            "path": path,
            "size_bytes": file_size,
            "encoding": encoding,
            "truncated": truncated,
            "content": content,
        }
        
        if truncated:
            result["note"] = f"File truncated at {max_bytes} bytes"
        
        logger.info(f"file_read completed: {len(content)} chars read")
        return result
        
    except UnicodeDecodeError as e:
        logger.warning(f"Encoding error reading file: {e}")
        return {
            "status": "error",
            "message": f"Encoding error: {e}. Try a different encoding.",
        }
    except Exception as e:
        logger.error(f"File read failed: {e}", exc_info=True)
        return {
            "status": "error",
            "message": str(e),
        }
