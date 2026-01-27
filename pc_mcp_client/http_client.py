"""
MCP HTTP Client

HTTP transport for MCP (Model Context Protocol).
Connects to Siya Pi server over HTTP for remote tool invocation.

Per DIP Phase 11: HTTP transport for PC client to Pi server over LAN.
"""

import json
import urllib.request
import urllib.error
from typing import Any, Dict, Optional


class MCPHttpClient:
    """
    HTTP client for MCP-over-HTTP transport.

    Connects to Siya Pi server over HTTP.
    Same interface as MCPStdioClient for interchangeability.
    """

    def __init__(
        self,
        base_url: str,
        api_key: Optional[str] = None,
        timeout: int = 300,
    ) -> None:
        """
        Initialize MCP HTTP client.

        Args:
            base_url: Base URL of Siya server (e.g., http://192.168.1.100:8080)
            api_key: Optional API key for X-Siya-Api-Key header
            timeout: Request timeout in seconds (default: 300 for slow AI inference)
        """
        # Normalize base URL
        self._base_url = base_url.rstrip("/")
        self._mcp_endpoint = f"{self._base_url}/mcp"
        self._api_key = api_key
        self._timeout = timeout
        self._next_id = 1
        self._initialized = False

    def __enter__(self) -> "MCPHttpClient":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        # Nothing to clean up for HTTP
        pass

    def initialize(self, protocol_version: str = "2025-03-26") -> Dict[str, Any]:
        """
        Initialize MCP session.

        Args:
            protocol_version: MCP protocol version to request

        Returns:
            Server capabilities response
        """
        result = self._request(
            method="initialize",
            params={
                "protocolVersion": protocol_version,
                "capabilities": {"roots": {"listChanged": False}, "sampling": {}},
                "clientInfo": {"name": "siya-pc-mcp-cli", "version": "1.0.0"},
            },
        )
        # Per MCP lifecycle, send notifications/initialized after success
        self._notify("notifications/initialized", params={})
        self._initialized = True
        return result

    def tools_list(self) -> Dict[str, Any]:
        """
        List available tools.

        Returns:
            Dict with 'tools' array
        """
        return self._request(method="tools/list", params={})

    def tools_call(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call a tool.

        Args:
            name: Tool name
            arguments: Tool arguments

        Returns:
            Tool execution result
        """
        return self._request(
            method="tools/call",
            params={"name": name, "arguments": arguments},
        )

    def _notify(self, method: str, params: Dict[str, Any]) -> None:
        """
        Send a notification (no response expected).

        For HTTP, we still send the request but ignore the response.
        """
        msg = {"jsonrpc": "2.0", "method": method, "params": params}
        self._send_http_request(msg)

    def _request(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send a JSON-RPC request and return the result.

        Args:
            method: JSON-RPC method name
            params: Method parameters

        Returns:
            Result from response

        Raises:
            RuntimeError: If request fails
        """
        msg_id = self._next_id
        self._next_id += 1

        req = {"jsonrpc": "2.0", "id": msg_id, "method": method, "params": params}
        resp = self._send_http_request(req)

        if "error" in resp:
            err = resp["error"]
            raise RuntimeError(f"MCP_ERROR {err.get('code')}: {err.get('message')}")

        return resp.get("result", {})

    def _send_http_request(self, msg: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send HTTP POST request to MCP endpoint.

        Args:
            msg: JSON-RPC message

        Returns:
            Parsed JSON response

        Raises:
            RuntimeError: If HTTP request fails
        """
        body = json.dumps(msg, ensure_ascii=False).encode("utf-8")

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        if self._api_key:
            headers["X-Siya-Api-Key"] = self._api_key

        req = urllib.request.Request(
            self._mcp_endpoint,
            data=body,
            headers=headers,
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=self._timeout) as response:
                response_body = response.read().decode("utf-8")
                return json.loads(response_body)
        except urllib.error.HTTPError as e:
            # Read error body if available
            try:
                error_body = e.read().decode("utf-8")
                error_data = json.loads(error_body)
                if "error" in error_data:
                    err = error_data["error"]
                    raise RuntimeError(f"MCP_HTTP_ERROR {e.code}: {err.get('message')}") from e
            except (json.JSONDecodeError, UnicodeDecodeError):
                pass
            raise RuntimeError(f"MCP_HTTP_ERROR {e.code}: {e.reason}") from e
        except urllib.error.URLError as e:
            raise RuntimeError(f"MCP_CONNECTION_ERROR: {e.reason}") from e
        except TimeoutError:
            raise RuntimeError("MCP_TIMEOUT: Request timed out") from None
