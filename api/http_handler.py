"""
HTTP Request Handler

HTTP request handler for API server.
Uses standard library http.server for Phase 6 (simple implementation).

Per DIP Phase 6: HTTP API mirrors CLI exactly.
Per DIP Phase 11: MCP HTTP transport for PC client to Pi server.
"""

import json
import logging
from http.server import BaseHTTPRequestHandler
from typing import TYPE_CHECKING, Any, Optional
from urllib.parse import urlparse, parse_qs

from api.api_server import APIServer

if TYPE_CHECKING:
    from mcp.mcp_http_handler import MCPHttpHandler

logger = logging.getLogger(__name__)


class SiyaHTTPHandler(BaseHTTPRequestHandler):
    """
    HTTP request handler for Siya API.

    Per DIP Phase 6: Simple HTTP handler using standard library.
    Per DIP Phase 11: Routes /mcp to MCP HTTP handler.
    """

    def __init__(
        self,
        *args,
        api_server: Optional[APIServer] = None,
        mcp_http_handler: Optional["MCPHttpHandler"] = None,
        **kwargs
    ) -> None:
        """
        Initialize HTTP handler.

        Args:
            api_server: API server instance
            mcp_http_handler: Optional MCP HTTP handler for /mcp endpoint
            *args, **kwargs: Passed to BaseHTTPRequestHandler
        """
        self._api_server = api_server
        self._mcp_http_handler = mcp_http_handler
        super().__init__(*args, **kwargs)

    def do_GET(self) -> None:
        """Handle GET requests."""
        try:
            parsed_path = urlparse(self.path)

            if parsed_path.path == "/health":
                # Health check
                logger.debug("Health check requested")
                response = self._api_server.handle_health_check() if self._api_server else {
                    "status": "error",
                    "message": "API server not initialized",
                }
                self._send_json_response(200, response)
            else:
                logger.warning(f"GET to unknown path: {parsed_path.path}")
                self._send_json_response(404, {"status": "error", "message": "Not found"})
        except Exception as e:
            logger.error(f"GET request failed: {e}", exc_info=True)
            try:
                self._send_json_response(500, {"status": "error", "message": "Internal server error"})
            except Exception:
                # If we can't send response, log and let it fail
                logger.error("Failed to send error response", exc_info=True)

    def do_OPTIONS(self) -> None:
        """Handle OPTIONS requests for CORS preflight."""
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-Siya-Api-Key")
        self.end_headers()

    def do_POST(self) -> None:
        """Handle POST requests."""
        try:
            parsed_path = urlparse(self.path)
            logger.info(f"POST request to {parsed_path.path} from {self.address_string()}")

            if parsed_path.path == "/mcp":
                # MCP HTTP transport endpoint (Phase 11)
                self._handle_mcp_request()
                return

            if parsed_path.path == "/command":
                # Command endpoint
                try:
                    content_length = int(self.headers.get("Content-Length", 0))
                    if content_length == 0:
                        self._send_json_response(400, {"status": "error", "message": "Empty request body"})
                        return
                    
                    body = self.rfile.read(content_length)
                    request_data = json.loads(body.decode("utf-8"))
                    
                    logger.info(f"Command received: {request_data.get('command', 'N/A')}")

                    if not self._api_server:
                        logger.error("API server not initialized")
                        self._send_json_response(500, {"status": "error", "message": "API server not initialized"})
                        return

                    response = self._api_server.handle_command(request_data)
                    logger.info(f"Command response: {response.get('status', 'unknown')}")

                    self._send_json_response(200, response)

                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON in request: {e}")
                    self._send_json_response(
                        400, {"status": "error", "message": "Invalid JSON"}
                    )
                except Exception as e:
                    logger.error(f"POST /command failed: {e}", exc_info=True)
                    try:
                        self._send_json_response(
                            500, {"status": "error", "message": str(e)}
                        )
                    except Exception:
                        logger.error("Failed to send error response", exc_info=True)
            else:
                logger.warning(f"POST to unknown path: {parsed_path.path}")
                self._send_json_response(404, {"status": "error", "message": "Not found"})
        except Exception as e:
            logger.error(f"POST request failed: {e}", exc_info=True)
            try:
                self._send_json_response(500, {"status": "error", "message": "Internal server error"})
            except Exception:
                logger.error("Failed to send error response", exc_info=True)

    def _handle_mcp_request(self) -> None:
        """
        Handle MCP HTTP transport request.

        Per DIP Phase 11: MCP-over-HTTP for PC client to Pi server.
        Per LAW 16: Origin validation for network explicitness.
        """
        try:
            if not self._mcp_http_handler:
                logger.error("MCP HTTP handler not configured")
                self._send_json_response(
                    503, {"jsonrpc": "2.0", "id": None, "error": {"code": -32603, "message": "MCP not available"}}
                )
                return

            content_length = int(self.headers.get("Content-Length", 0))
            if content_length == 0:
                self._send_json_response(
                    400, {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "Empty request body"}}
                )
                return

            body = self.rfile.read(content_length)
            origin = self.headers.get("Origin")
            api_key = self.headers.get("X-Siya-Api-Key")

            # Delegate to MCP HTTP handler
            try:
                response = self._mcp_http_handler.handle_request(
                    body=body,
                    origin=origin,
                    api_key=api_key,
                )
                self._send_json_response(200, response)
            except ValueError as e:
                # Origin or API key validation failed
                logger.warning(f"MCP request rejected: {e}")
                self._send_json_response(
                    403, {"jsonrpc": "2.0", "id": None, "error": {"code": -32600, "message": str(e)}}
                )

        except Exception as e:
            logger.error(f"MCP HTTP request failed: {e}", exc_info=True)
            try:
                self._send_json_response(
                    500, {"jsonrpc": "2.0", "id": None, "error": {"code": -32603, "message": "Server error"}}
                )
            except Exception:
                logger.error("Failed to send MCP error response", exc_info=True)

    def _send_json_response(self, status_code: int, data: dict) -> None:
        """
        Send JSON response.

        Args:
            status_code: HTTP status code
            data: Response data dictionary
        """
        try:
            response_json = json.dumps(data, indent=2)
            response_bytes = response_json.encode("utf-8")

            self.send_response(status_code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(response_bytes)))
            # Add CORS headers to allow web interface to access API
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type, X-Siya-Api-Key")
            self.send_header("Connection", "keep-alive")  # Keep connection alive for long requests
            self.end_headers()
            self.wfile.write(response_bytes)
            self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError, OSError) as e:
            # Client disconnected - log but don't crash
            logger.debug(f"Client disconnected during response: {e}")
        except Exception as e:
            logger.error(f"Failed to send JSON response: {e}", exc_info=True)
            # Try to send error response if possible
            try:
                self.send_response(500)
                self.end_headers()
            except Exception:
                pass  # Connection already broken

    def log_message(self, format: str, *args: Any) -> None:
        """
        Override log_message to use our logger.

        Args:
            format: Log format string
            *args: Log arguments
        """
        logger.debug(f"{self.address_string()} - {format % args}")

    def handle_error(self, request, client_address) -> None:
        """
        Override handle_error to log errors properly.

        Args:
            request: Request object
            client_address: Client address tuple
        """
        logger.error(
            f"Error handling request from {client_address}",
            exc_info=True
        )
        # Don't call super().handle_error() as it tries to write to stderr
        # which can cause issues in daemon threads
