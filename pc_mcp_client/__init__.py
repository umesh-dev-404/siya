"""
First-party PC MCP CLI client package.

This is the PC-side MCP client that replicates Claude-like MCP client behavior:
- initialize -> notifications/initialized
- tools/list
- tools/call

Supports two transports:
- MCPStdioClient: Local STDIO transport (spawns local server)
- MCPHttpClient: HTTP transport (connects to remote Pi server)
"""

from pc_mcp_client.http_client import MCPHttpClient
from pc_mcp_client.stdio_client import MCPStdioClient

__all__ = ["MCPStdioClient", "MCPHttpClient"]
