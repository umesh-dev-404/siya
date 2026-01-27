"""
Web Server

Simple web server for Siya web interface.
Serves static files and proxies API requests.

Per DIP Phase 6: Web UI is client-rendered.
"""

import logging
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

from config.server_config import get_api_port, get_web_host, get_web_port

logger = logging.getLogger(__name__)


class WebHandler(BaseHTTPRequestHandler):
    """
    Web server handler.

    Serves static files and proxies API requests.
    """

    def __init__(
        self, *args, static_dir: Optional[Path] = None, api_port: int = 8080, **kwargs
    ) -> None:
        """
        Initialize web handler.

        Args:
            static_dir: Directory containing static files
            api_port: Port of API server
            *args, **kwargs: Passed to BaseHTTPRequestHandler
        """
        self._static_dir = static_dir or (Path(__file__).parent / "static")
        self._api_port = api_port
        super().__init__(*args, **kwargs)

    def do_GET(self) -> None:
        """Handle GET requests."""
        parsed_path = urlparse(self.path)

        if parsed_path.path == "/" or parsed_path.path == "/index.html":
            # Serve index.html
            self._serve_file("index.html")
        else:
            # Try to serve static file
            file_path = parsed_path.path.lstrip("/")
            if self._serve_file(file_path):
                return
            else:
                self._send_response(404, "text/plain", b"Not found")

    def _serve_file(self, filename: str) -> bool:
        """
        Serve a static file.

        Args:
            filename: Filename to serve

        Returns:
            True if file was served, False otherwise
        """
        file_path = self._static_dir / filename

        if not file_path.exists() or not file_path.is_file():
            return False

        try:
            with open(file_path, "rb") as f:
                content = f.read()

            # Determine content type
            if filename.endswith(".html"):
                content_type = "text/html; charset=utf-8"
            elif filename.endswith(".css"):
                content_type = "text/css; charset=utf-8"
            elif filename.endswith(".js"):
                content_type = "application/javascript; charset=utf-8"
            elif filename.endswith(".json"):
                content_type = "application/json; charset=utf-8"
            elif filename.endswith(".png"):
                content_type = "image/png"
            elif filename.endswith(".svg"):
                content_type = "image/svg+xml"
            elif filename.endswith(".ico"):
                content_type = "image/x-icon"
            elif filename.endswith(".woff2"):
                content_type = "font/woff2"
            elif filename.endswith(".woff"):
                content_type = "font/woff"
            else:
                content_type = "application/octet-stream"

            self._send_response(200, content_type, content)
            return True

        except Exception as e:
            logger.error(f"Failed to serve file {filename}: {e}", exc_info=True)
            return False

    def _send_response(self, status_code: int, content_type: str, content: bytes) -> None:
        """
        Send HTTP response.

        Args:
            status_code: HTTP status code
            content_type: Content type
            content: Response content
        """
        self.send_response(status_code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def log_message(self, format: str, *args) -> None:
        """
        Override log_message to use our logger.

        Args:
            format: Log format string
            *args: Log arguments
        """
        logger.debug(f"{self.address_string()} - {format % args}")


class WebServer:
    """
    Web server for Siya web interface.

    Per DIP Phase 6: Web UI is client-rendered.
    """

    def __init__(self, host: Optional[str] = None, port: Optional[int] = None, api_port: Optional[int] = None) -> None:
        """
        Initialize web server.

        Args:
            host: Server host (default: from config, 0.0.0.0 for network access)
            port: Server port (default: from config, 3000)
            api_port: API server port (default: from config, 8080)
        """
        self._host = host or get_web_host()
        self._port = port or get_web_port()
        self._api_port = api_port or get_api_port()
        self._server: Optional[HTTPServer] = None

    def start(self) -> None:
        """Start the web server."""
        def handler_factory(*args, **kwargs):
            return WebHandler(*args, api_port=self._api_port, **kwargs)

        self._server = HTTPServer((self._host, self._port), handler_factory)

        logger.info(f"Web server started on {self._host}:{self._port}")
        print(f"Siya web interface: http://{self._host}:{self._port}")

    def serve_forever(self) -> None:
        """Serve forever (blocking)."""
        if self._server is None:
            raise RuntimeError("Server not started. Call start() first.")

        try:
            self._server.serve_forever()
        except KeyboardInterrupt:
            logger.info("Web server stopped by user")
            self.stop()

    def stop(self) -> None:
        """Stop the web server."""
        if self._server:
            self._server.shutdown()
            self._server = None
            logger.info("Web server stopped")
