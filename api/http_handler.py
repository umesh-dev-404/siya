"""
HTTP Request Handler

HTTP request handler for API server.
Uses standard library http.server for Phase 6 (simple implementation).

Per DIP Phase 6: HTTP API mirrors CLI exactly.
"""

import json
import logging
from http.server import BaseHTTPRequestHandler
from typing import Any, Optional
from urllib.parse import urlparse, parse_qs

from api.api_server import APIServer

logger = logging.getLogger(__name__)


class SiyaHTTPHandler(BaseHTTPRequestHandler):
    """
    HTTP request handler for Siya API.

    Per DIP Phase 6: Simple HTTP handler using standard library.
    """

    def __init__(
        self, *args, api_server: Optional[APIServer] = None, **kwargs
    ) -> None:
        """
        Initialize HTTP handler.

        Args:
            api_server: API server instance
            *args, **kwargs: Passed to BaseHTTPRequestHandler
        """
        self._api_server = api_server
        super().__init__(*args, **kwargs)

    def do_GET(self) -> None:
        """Handle GET requests."""
        parsed_path = urlparse(self.path)

        if parsed_path.path == "/health":
            # Health check
            response = self._api_server.handle_health_check() if self._api_server else {
                "status": "error",
                "message": "API server not initialized",
            }
            self._send_json_response(200, response)
        else:
            self._send_json_response(404, {"status": "error", "message": "Not found"})

    def do_OPTIONS(self) -> None:
        """Handle OPTIONS requests for CORS preflight."""
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_POST(self) -> None:
        """Handle POST requests."""
        parsed_path = urlparse(self.path)

        if parsed_path.path == "/command":
            # Command endpoint
            try:
                content_length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(content_length)
                request_data = json.loads(body.decode("utf-8"))

                response = (
                    self._api_server.handle_command(request_data)
                    if self._api_server
                    else {"status": "error", "message": "API server not initialized"}
                )

                self._send_json_response(200, response)

            except json.JSONDecodeError:
                self._send_json_response(
                    400, {"status": "error", "message": "Invalid JSON"}
                )
            except Exception as e:
                logger.error(f"POST /command failed: {e}", exc_info=True)
                self._send_json_response(
                    500, {"status": "error", "message": str(e)}
                )
        else:
            self._send_json_response(404, {"status": "error", "message": "Not found"})

    def _send_json_response(self, status_code: int, data: dict) -> None:
        """
        Send JSON response.

        Args:
            status_code: HTTP status code
            data: Response data dictionary
        """
        response_json = json.dumps(data, indent=2)
        response_bytes = response_json.encode("utf-8")

        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(response_bytes)))
        # Add CORS headers to allow web interface to access API
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(response_bytes)

    def log_message(self, format: str, *args: Any) -> None:
        """
        Override log_message to use our logger.

        Args:
            format: Log format string
            *args: Log arguments
        """
        logger.debug(f"{self.address_string()} - {format % args}")
