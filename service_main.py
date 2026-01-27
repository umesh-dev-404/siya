"""
Service Entry Point

Main entry point for Siya systemd service.
Starts both API server and web server to run as background services.
"""

import logging
import os
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
from mcp.mcp_server import MCPServer
from mcp.stdio_server import MCPStdioContext, MCPStdioServer
from orchestrator.orchestrator import Orchestrator
from tools.builtins import get_system_status
from tools.mail_tools import make_fetch_mails_tool, make_summarize_mails_tool
from tools.text_tools import make_summarize_text_tool
from tools.tool_executor import ToolExecutor
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
        print("API server thread starting...", flush=True)
        logger.info("API server thread starting")
        http_server.serve_forever()
    except Exception as e:
        error_msg = f"API server thread crashed: {e}"
        print(error_msg, file=sys.stderr, flush=True)
        logger.error(error_msg, exc_info=True)
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.stderr.flush()
        # Don't re-raise - let the thread die gracefully


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


def run_mcp_stdio_server(stdio_server: MCPStdioServer) -> None:
    """
    Run MCP STDIO server (optional) in a thread.

    Note: STDIO MCP is primarily intended to be launched by an MCP client.
    In systemd service mode, stdin may be closed; so this is opt-in via env var.
    """
    try:
        logger.info("MCP STDIO server thread starting")
        stdio_server.run_forever()
    except Exception as e:
        logger.error(f"MCP STDIO server error: {e}", exc_info=True)


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
        
        print("Creating MCPServer...", flush=True)
        mcp = MCPServer()
        
        print("Getting tool registry...", flush=True)
        tool_registry = mcp.get_tool_registry()
        request_validator = mcp.get_request_validator()

        # Register initial built-in tools (schemas + implementations)
        # Note: "summarize mails" is an initial example tool; Siya will scale to many tools later.
        from mcp.tool_schema import PermissionLevel, ToolSchema
        tool_registry.register(
            tool_schema=ToolSchema(
                name="get_system_status",
                description="[system] Get current system resource status (CPU/RAM/disk).",
                input_schema={"type": "object", "properties": {}, "required": []},
                output_schema={"type": "object"},
                permission_level=PermissionLevel.READ,
                requires_confirmation=False,
            )
        )
        tool_registry.register(
            tool_schema=ToolSchema(
                name="tools_list",
                description="[system] List all available tools.",
                input_schema={"type": "object", "properties": {}, "required": []},
                output_schema={"type": "object"},
                permission_level=PermissionLevel.READ,
                requires_confirmation=False,
            )
        )
        tool_registry.register(
            tool_schema=ToolSchema(
                name="summarize_text",
                description="[content] Summarize a block of text (local AI).",
                input_schema={
                    "type": "object",
                    "properties": {
                        "text": {"type": "string"},
                        "style": {"type": "string"},
                        "max_bullets": {"type": "integer"},
                    },
                    "required": ["text"],
                },
                output_schema={"type": "object"},
                permission_level=PermissionLevel.READ,
                requires_confirmation=False,
            )
        )
        tool_registry.register(
            tool_schema=ToolSchema(
                name="fetch_mails",
                description="[integration:mails] Fetch mails from local mail store (offline-first).",
                input_schema={
                    "type": "object",
                    "properties": {"store_path": {"type": "string"}, "limit": {"type": "integer"}},
                    "required": [],
                },
                output_schema={"type": "object"},
                permission_level=PermissionLevel.READ,
                requires_confirmation=False,
            )
        )
        tool_registry.register(
            tool_schema=ToolSchema(
                name="summarize_mails",
                description="[integration:mails] Summarize mails from local store (uses local AI).",
                input_schema={
                    "type": "object",
                    "properties": {
                        "store_path": {"type": "string"},
                        "limit": {"type": "integer"},
                        "max_items": {"type": "integer"},
                        "fields": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": [],
                },
                output_schema={"type": "object"},
                permission_level=PermissionLevel.READ,
                requires_confirmation=False,
            )
        )

        # Tool implementations
        tool_executor = ToolExecutor()
        tool_executor.register("get_system_status", get_system_status)
        tool_executor.register("tools_list", lambda _args: {"status": "ok", "tools": tool_registry.list_tools()})
        
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

        # Tools that need AI (content processing) or local integrations
        tool_executor.register("summarize_text", make_summarize_text_tool(ai_interface))
        mail_store_default = str(Path(project_root) / "data" / "mails.json")
        tool_executor.register("fetch_mails", make_fetch_mails_tool(mail_store_default))
        tool_executor.register("summarize_mails", make_summarize_mails_tool(ai_interface, mail_store_default))
        
        print("Creating orchestrator...", flush=True)
        orchestrator = Orchestrator(mcp=mcp, ai_interface=ai_interface, tool_executor=tool_executor)

        print("Creating CLI...", flush=True)
        cli = CLI(orchestrator, mcp, ai_interface)
        cli.start()  # Start CLI (which also starts the orchestrator)
        logger.info("CLI started (orchestrator started via CLI)")
        print("CLI started (orchestrator started)", flush=True)
        
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

        # Optional: Start MCP STDIO server in a thread (env-gated)
        # Set SIYA_ENABLE_MCP_STDIO=1 to enable.
        if str(os.getenv("SIYA_ENABLE_MCP_STDIO", "0")).strip() == "1":
            stdio_server = MCPStdioServer(MCPStdioContext(mcp_server=mcp, tool_executor=tool_executor))
            stdio_thread = threading.Thread(
                target=run_mcp_stdio_server,
                args=(stdio_server,),
                daemon=True,
            )
            stdio_thread.start()
            logger.info("MCP STDIO server enabled (SIYA_ENABLE_MCP_STDIO=1)")
        
        # Give API server thread a moment to start
        import time
        time.sleep(0.5)
        
        # Verify API server started
        if not api_thread.is_alive():
            error_msg = "API server thread died immediately after start"
            print(error_msg, file=sys.stderr, flush=True)
            logger.error(error_msg)
            raise RuntimeError(error_msg)

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
