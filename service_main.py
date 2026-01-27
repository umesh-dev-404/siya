"""
Service Entry Point

Main entry point for Siya systemd service.
Starts both API server and web server to run as background services.
"""

import logging
import sys
import threading
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from ai.ai_interface import AIInterface
from api.api_server import APIServer
from api.server import SiyaAPIServer
from cli.cli import CLI
from config.logging_config import setup_logging
from config.model_config import get_model_path
from mcp.mcp import ModelControlPlane
from orchestrator.orchestrator import Orchestrator
from web.web_server import WebServer

# Setup logging first (before any other imports that might log)
try:
    setup_logging(level=logging.INFO)
except Exception as e:
    print(f"Failed to setup logging: {e}", file=sys.stderr, flush=True)
    # Fallback to basic logging
    logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")

logger = logging.getLogger(__name__)


def run_api_server(http_server: SiyaAPIServer) -> None:
    """
    Run API server in a separate thread.

    Args:
        http_server: API server instance
    """
    try:
        http_server.serve_forever()
    except Exception as e:
        logger.error(f"API server error: {e}", exc_info=True)
        raise


def run_web_server(web_server: WebServer) -> None:
    """
    Run web server in a separate thread.

    Args:
        web_server: Web server instance
    """
    try:
        web_server.serve_forever()
    except Exception as e:
        logger.error(f"Web server error: {e}", exc_info=True)
        raise


def main() -> int:
    """
    Main service entry point.

    Starts both API server and web server to run as a systemd service.

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
        
        print("Getting model path...", flush=True)
        model_path = get_model_path()
        if model_path:
            print(f"Model path: {model_path}", flush=True)
        else:
            print("No model path configured - will use stub mode", flush=True)
        
        print("Creating AI interface...", flush=True)
        ai_interface = AIInterface(tool_registry, request_validator, model_path=model_path)
        
        # Load model if path is configured (Phase 10)
        if model_path:
            print(f"Loading AI model from {model_path}...", flush=True)
            try:
                if ai_interface.load_model():
                    print("✅ AI model loaded successfully", flush=True)
                    logger.info("AI model loaded successfully")
                else:
                    print("⚠️  Model loading failed - will use stub mode", flush=True)
                    logger.warning("Model loading failed - will use stub mode")
            except Exception as e:
                print(f"⚠️  Model loading error: {e} - will use stub mode", flush=True)
                logger.warning(f"Model loading error: {e} - will use stub mode", exc_info=True)
        else:
            print("No model path configured - using stub mode", flush=True)
            logger.info("No model path configured - using stub mode")
        
        print("Creating orchestrator...", flush=True)
        orchestrator = Orchestrator(mcp=mcp, ai_interface=ai_interface)
        orchestrator.start()  # Start orchestrator to enable task processing
        logger.info("Orchestrator started")
        print("Orchestrator started", flush=True)

        print("Creating CLI...", flush=True)
        cli = CLI(orchestrator, mcp, ai_interface)
        cli.start()  # Start CLI (which also ensures orchestrator is started)
        logger.info("CLI started")
        print("CLI started", flush=True)
        
        print("Creating API server...", flush=True)
        api_server = APIServer(cli)

        print("Starting API HTTP server...", flush=True)
        http_server = SiyaAPIServer(api_server)
        http_server.start()

        print(f"Siya API server started on http://{http_server._host}:{http_server._port}", flush=True)
        logger.info("Siya API server started successfully")
        logger.info(f"API server running on http://{http_server._host}:{http_server._port}")

        print("Starting web server...", flush=True)
        web_server = WebServer()
        web_server.start()

        print(f"Siya web server started on http://{web_server._host}:{web_server._port}", flush=True)
        logger.info("Web server started successfully")
        logger.info(f"Web server running on http://{web_server._host}:{web_server._port}")

        # Start API server in a thread
        api_thread = threading.Thread(target=run_api_server, args=(http_server,), daemon=True)
        api_thread.start()

        # Start web server in main thread (blocking)
        # This keeps the main process alive
        web_server.serve_forever()

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
