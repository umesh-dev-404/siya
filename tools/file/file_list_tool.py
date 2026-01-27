"""
Directory List Tool

List directory contents with filtering options.
Per DIP Phase 11: File operations tools.

Enforces:
- LAW 4 — TOOL-ONLY EXECUTION
- LAW 13 — COMPLETE AUDITABILITY
- LAW 15 — SECRET ISOLATION
"""

import logging
import os
from pathlib import Path
from typing import Any, Dict, List
from datetime import datetime

from mcp.tool_schema import PermissionLevel, ToolSchema

logger = logging.getLogger(__name__)

# Allowed base directories
ALLOWED_BASE_DIRS = [
    "/opt/siya",
    "/home",
    "D:\\Projects\\siya",  # PC development
]

# Hidden directories to exclude
HIDDEN_DIRS = [
    ".git",
    "__pycache__",
    ".venv",
    "node_modules",
]


def make_directory_list_tool() -> ToolSchema:
    """Create the directory list tool schema."""
    return ToolSchema(
        name="directory_list",
        description="[file] List directory contents with file metadata.",
        input_schema={
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Absolute path to directory."
                },
                "pattern": {
                    "type": "string",
                    "description": "Glob pattern to filter files (e.g., '*.txt')."
                },
                "include_hidden": {
                    "type": "boolean",
                    "description": "Include hidden files/directories."
                },
                "max_depth": {
                    "type": "integer",
                    "description": "Maximum depth for recursive listing (0 = current only)."
                }
            },
            "required": ["path"]
        },
        output_schema={"type": "object"},
        permission_level=PermissionLevel.READ,
        requires_confirmation=False,
        category="file",
    )


def _validate_dir_path(path: str) -> tuple[bool, str]:
    """Validate directory path for security."""
    resolved = Path(path).resolve()
    
    for base_dir in ALLOWED_BASE_DIRS:
        try:
            base = Path(base_dir).resolve()
            if str(resolved).startswith(str(base)):
                return True, ""
        except Exception:
            continue
    
    return False, f"Access denied: path not in allowed directories"


def directory_list_impl(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute directory list tool.
    
    Args:
        args: Tool arguments
            - path: Directory path
            - pattern: Glob filter pattern
            - include_hidden: Include hidden files
            - max_depth: Recursive depth limit
    
    Returns:
        Directory listing with file metadata
    """
    path = args.get("path", "")
    pattern = args.get("pattern", "*")
    include_hidden = args.get("include_hidden", False)
    max_depth = args.get("max_depth", 0)
    
    logger.info(f"Executing directory_list tool: path={path}, pattern={pattern}")
    
    try:
        # Validate path
        is_valid, error = _validate_dir_path(path)
        if not is_valid:
            logger.warning(f"directory_list blocked: {error}")
            return {
                "status": "error",
                "message": error,
            }
        
        # Check directory exists
        if not os.path.isdir(path):
            return {
                "status": "error",
                "message": f"Directory not found: {path}",
            }
        
        entries: List[Dict[str, Any]] = []
        base_path = Path(path)
        
        def scan_dir(dir_path: Path, current_depth: int = 0):
            """Recursively scan directory."""
            if current_depth > max_depth:
                return
            
            try:
                for item in dir_path.iterdir():
                    name = item.name
                    
                    # Skip hidden files unless requested
                    if not include_hidden and name.startswith('.'):
                        continue
                    
                    # Skip common hidden directories
                    if item.is_dir() and name in HIDDEN_DIRS:
                        continue
                    
                    # Apply pattern filter
                    if pattern != "*" and not item.match(pattern):
                        if not item.is_dir():  # Still recurse into dirs
                            continue
                    
                    try:
                        stat = item.stat()
                        entry = {
                            "name": name,
                            "path": str(item),
                            "type": "directory" if item.is_dir() else "file",
                            "size": stat.st_size if item.is_file() else None,
                            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        }
                        entries.append(entry)
                        
                        # Recurse into subdirectories
                        if item.is_dir() and current_depth < max_depth:
                            scan_dir(item, current_depth + 1)
                            
                    except (OSError, PermissionError):
                        continue
                        
            except (OSError, PermissionError) as e:
                logger.warning(f"Cannot access {dir_path}: {e}")
        
        scan_dir(base_path)
        
        # Sort entries: directories first, then by name
        entries.sort(key=lambda x: (0 if x["type"] == "directory" else 1, x["name"]))
        
        result = {
            "status": "ok",
            "path": path,
            "pattern": pattern,
            "count": len(entries),
            "entries": entries[:100],  # Limit to 100 entries
        }
        
        if len(entries) > 100:
            result["truncated"] = True
            result["total_count"] = len(entries)
        
        logger.info(f"directory_list completed: {len(entries)} entries")
        return result
        
    except Exception as e:
        logger.error(f"Directory list failed: {e}", exc_info=True)
        return {
            "status": "error",
            "message": str(e),
        }
