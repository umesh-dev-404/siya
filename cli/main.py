"""
CLI Entry Point

Main entry point for Siya CLI.
"""

import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from ai.ai_interface import AIInterface
from cli.cli import CLI
from config.logging_config import setup_logging
from config.model_config import get_model_path
from mcp.mcp import ModelControlPlane
from orchestrator.orchestrator import Orchestrator

# Setup logging
setup_logging(level=logging.INFO)


def main() -> int:
    """
    Main CLI entry point.

    Returns:
        Exit code (0 for success, non-zero for error)
    """
    try:
        # Initialize components
        mcp = ModelControlPlane()
        tool_registry = mcp.get_tool_registry()
        request_validator = mcp.get_request_validator()
        model_path = get_model_path()
        ai_interface = AIInterface(tool_registry, request_validator, model_path=model_path)
        orchestrator = Orchestrator(mcp=mcp, ai_interface=ai_interface)

        # Create CLI
        cli = CLI(orchestrator, mcp, ai_interface)

        # Run interactive CLI
        cli.run_interactive()

        return 0

    except Exception as e:
        logging.error(f"CLI failed: {e}", exc_info=True)
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
