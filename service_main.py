"""
Service Entry Point

Main entry point for Siya systemd service.
Starts the API server to run as a background service.
"""

import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from ai.ai_interface import AIInterface
from api.api_server import APIServer
from api.server import SiyaAPIServer
from cli.cli import CLI
from config.logging_config import setup_logging
from mcp.mcp import ModelControlPlane
from orchestrator.orchestrator import Orchestrator

# Setup logging
setup_logging(level=logging.INFO)

logger = logging.getLogger(__name__)


def main() -> int:
    """
    Main service entry point.

    Starts the API server to run as a systemd service.

    Returns:
        Exit code (0 for success, non-zero for error)
    """
    try:
        # Initialize components
        logger.info("Initializing Siya components...")
        mcp = ModelControlPlane()
        tool_registry = mcp.get_tool_registry()
        request_validator = mcp.get_request_validator()
        ai_interface = AIInterface(tool_registry, request_validator)
        orchestrator = Orchestrator(mcp=mcp, ai_interface=ai_interface)

        # Create CLI (API mirrors CLI)
        cli = CLI(orchestrator, mcp, ai_interface)
        api_server = APIServer(cli)

        # Create and start HTTP server
        http_server = SiyaAPIServer(api_server)
        http_server.start()

        logger.info("Siya API server started successfully")
        logger.info(f"API server running on http://{http_server._host}:{http_server._port}")

        # Serve forever (blocking)
        http_server.serve_forever()

        return 0

    except KeyboardInterrupt:
        logger.info("Service stopped by user")
        return 0
    except Exception as e:
        logger.error(f"Service failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
