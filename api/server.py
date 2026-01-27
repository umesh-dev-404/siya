"""
API Server

HTTP server for Siya API.
Per DIP Phase 6: HTTP API mirrors CLI exactly.
Per DIP Phase 11: HTTP transport for MCP (PC client to Pi server).
"""

import logging
from http.server import HTTPServer
from typing import TYPE_CHECKING, Optional

from api.api_server import APIServer
from api.http_handler import SiyaHTTPHandler
from config.server_config import get_api_host, get_api_port

if TYPE_CHECKING:
    from mcp.mcp_http_handler import MCPHttpHandler

logger = logging.getLogger(__name__)


class SiyaAPIServer:
    """
    HTTP server for Siya API.

    Per DIP Phase 6:
    - API mirrors CLI exactly
    - Simple HTTP server using standard library

    Per DIP Phase 11:
    - MCP HTTP transport for PC client to Pi server
    """

    def __init__(
        self,
        api_server: APIServer,
        host: Optional[str] = None,
        port: Optional[int] = None,
        mcp_http_handler: Optional["MCPHttpHandler"] = None,
    ) -> None:
        """
        Initialize API server.

        Args:
            api_server: API server instance
            host: Server host (default: from config, 0.0.0.0 for network access)
            port: Server port (default: from config, 8080)
            mcp_http_handler: Optional MCP HTTP handler for /mcp endpoint (Phase 11)
        """
        self._api_server = api_server
        self._host = host or get_api_host()
        self._port = port or get_api_port()
        self._mcp_http_handler = mcp_http_handler
        self._server: Optional[HTTPServer] = None

    def start(self) -> None:
        """Start the HTTP server."""
        mcp_handler = self._mcp_http_handler

        def handler_factory(*args, **kwargs):
            return SiyaHTTPHandler(*args, api_server=self._api_server, mcp_http_handler=mcp_handler, **kwargs)

        self._server = HTTPServer((self._host, self._port), handler_factory)
        
        # Set socket timeout to 5 minutes to handle slow AI inference
        self._server.timeout = 300  # 5 minutes
        
        # Set socket options to keep connections alive
        import socket
        self._server.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._server.socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)

        logger.info(f"API server started on {self._host}:{self._port}")
        print(f"Siya API server running on http://{self._host}:{self._port}")

    def serve_forever(self) -> None:
        """Serve forever (blocking)."""
        if self._server is None:
            raise RuntimeError("Server not started. Call start() first.")

        try:
            self._server.serve_forever()
        except KeyboardInterrupt:
            logger.info("API server stopped by user")
            self.stop()

    def stop(self) -> None:
        """Stop the HTTP server."""
        if self._server:
            self._server.shutdown()
            self._server = None
            logger.info("API server stopped")
