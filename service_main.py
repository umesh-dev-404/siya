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

# Setup logging first (before any other imports that might log)
try:
    setup_logging(level=logging.INFO)
except Exception as e:
    print(f"Failed to setup logging: {e}", file=sys.stderr, flush=True)
    # Fallback to basic logging
    logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")

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
        print("Initializing Siya components...", flush=True)
        logger.info("Initializing Siya components...")
        
        print("Creating ModelControlPlane...", flush=True)
        mcp = ModelControlPlane()
        
        print("Getting tool registry...", flush=True)
        tool_registry = mcp.get_tool_registry()
        request_validator = mcp.get_request_validator()
        
        print("Creating AI interface...", flush=True)
        ai_interface = AIInterface(tool_registry, request_validator)
        
        print("Creating orchestrator...", flush=True)
        orchestrator = Orchestrator(mcp=mcp, ai_interface=ai_interface)

        print("Creating CLI...", flush=True)
        cli = CLI(orchestrator, mcp, ai_interface)
        
        print("Creating API server...", flush=True)
        api_server = APIServer(cli)

        print("Starting HTTP server...", flush=True)
        http_server = SiyaAPIServer(api_server)
        http_server.start()

        print(f"Siya API server started successfully on http://{http_server._host}:{http_server._port}", flush=True)
        logger.info("Siya API server started successfully")
        logger.info(f"API server running on http://{http_server._host}:{http_server._port}")

        # Serve forever (blocking)
        http_server.serve_forever()

        return 0

    except KeyboardInterrupt:
        print("Service stopped by user", flush=True)
        logger.info("Service stopped by user")
        return 0
    except Exception as e:
        error_msg = f"Service failed: {e}"
        print(error_msg, file=sys.stderr, flush=True)
        logger.error(error_msg, exc_info=True)
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.stderr.flush()
        return 1


if __name__ == "__main__":
    sys.exit(main())
