"""
Siya first-party PC MCP CLI client.

Supports two transports:
- stdio: Spawns local MCP server (default)
- http: Connects to remote Pi MCP server over HTTP

Per DIP Phase 11: First-party PC MCP CLI client with HTTP transport.
"""

import argparse
import json
import sys
from typing import Any, Dict, Union

from pc_mcp_client.http_client import MCPHttpClient
from pc_mcp_client.stdio_client import MCPStdioClient, default_stdio_server_cmd


def _print_json(obj: Any) -> None:
    sys.stdout.write(json.dumps(obj, ensure_ascii=False, indent=2) + "\n")


def _parse_args_json(s: str) -> Dict[str, Any]:
    if not s.strip():
        return {}
    try:
        data = json.loads(s)
    except Exception as e:
        raise RuntimeError(f"INVALID_ARGS_JSON: {e}") from e
    if not isinstance(data, dict):
        raise RuntimeError("INVALID_ARGS_JSON: must be a JSON object")
    return data


def _create_client(args: argparse.Namespace) -> Union[MCPStdioClient, MCPHttpClient]:
    """
    Create MCP client based on transport argument.

    Args:
        args: Parsed CLI arguments

    Returns:
        MCPStdioClient or MCPHttpClient instance
    """
    if args.transport == "http":
        if not args.url:
            raise RuntimeError("--url is required when using --transport http")
        return MCPHttpClient(
            base_url=args.url,
            api_key=args.api_key,
            timeout=args.timeout,
        )
    # Default: stdio transport
    return MCPStdioClient(default_stdio_server_cmd())


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        prog="siya-mcp",
        description="Siya first-party PC MCP CLI client.",
    )

    # Transport options
    p.add_argument(
        "--transport",
        choices=["stdio", "http"],
        default="stdio",
        help="Transport to use: stdio (local, default) or http (remote Pi).",
    )
    p.add_argument(
        "--url",
        default=None,
        help="URL of Siya Pi server (required for --transport http, e.g., http://192.168.1.100:8080).",
    )
    p.add_argument(
        "--api-key",
        default=None,
        help="Optional API key for X-Siya-Api-Key header (http transport only).",
    )
    p.add_argument(
        "--timeout",
        type=int,
        default=300,
        help="Request timeout in seconds (default: 300, for slow AI inference).",
    )
    p.add_argument(
        "--protocol-version",
        default="2025-03-26",
        help="MCP protocol version to request in initialize (default: 2025-03-26).",
    )

    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("server-info", help="Check connection and server status.")

    sub_list = sub.add_parser("list-tools", help="Initialize and list tools.")
    sub_list.add_argument("--raw", action="store_true", help="Print raw MCP response JSON.")

    sub_call = sub.add_parser("call", help="Initialize and call a tool.")
    sub_call.add_argument("tool_name", help="Tool name to call.")
    sub_call.add_argument(
        "--args",
        default="{}",
        help='Tool arguments as JSON object string (default: "{}").',
    )
    sub_call.add_argument("--raw", action="store_true", help="Print raw MCP response JSON.")

    args = p.parse_args(argv)

    try:
        client = _create_client(args)
    except RuntimeError as e:
        _print_json({"status": "error", "message": str(e)})
        return 1

    with client:
        client.initialize(protocol_version=args.protocol_version)

        if args.cmd == "server-info":
            print(f"✅ Connected to MCP Server via {args.transport}")
            if args.url:
                print(f"URL: {args.url}")
            
            try:
                # Use tools/list as a ping
                resp = client.tools_list()
                tools = resp.get("tools", [])
                print(f"Server Status: Online")
                print(f"Available Tools: {len(tools)}")
                for tool in tools:
                    print(f" - {tool['name']}: {tool.get('description', '')[:50]}...")
            except Exception as e:
                print(f"❌ Server check failed: {e}")
                return 1
            return 0

        if args.cmd == "list-tools":
            resp = client.tools_list()
            if args.raw:
                _print_json(resp)
                return 0
            tools = resp.get("tools", [])
            _print_json({"status": "ok", "count": len(tools), "tools": tools})
            return 0

        if args.cmd == "call":
            tool_args = _parse_args_json(args.args)
            resp = client.tools_call(args.tool_name, tool_args)
            if args.raw:
                _print_json(resp)
                return 0
            # Prefer structuredContent (when provided) for machine readability.
            structured = resp.get("structuredContent")
            if isinstance(structured, dict):
                _print_json({"status": "ok", "output": structured})
                return 0
            _print_json({"status": "ok", "result": resp})
            return 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
