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
        prog="siya-cli",
        description="Siya PC Client — Control your Personal Assistant remotely from this computer.",
        epilog="Example: siya-cli --transport http --url http://192.168.1.39:8080 call get_system_status"
    )

    # Transport options
    p.add_argument(
        "--transport",
        choices=["stdio", "http"],
        default="stdio",
        help="Connection mode: 'http' for a remote Pi (recommended), or 'stdio' for local testing.",
    )
    p.add_argument(
        "--url",
        default=None,
        help="The address of your Pi server (Required for http mode). Example: http://192.168.1.39:8080",
    )
    p.add_argument(
        "--api-key",
        default=None,
        help="Your API Key (if authentication is enabled on the server).",
    )
    p.add_argument(
        "--timeout",
        type=int,
        default=300,
        help="Max wait time in seconds (Default: 300s). Increase this if AI responses are slow.",
    )
    p.add_argument(
        "--protocol-version",
        default="2025-03-26",
        help=argparse.SUPPRESS, # Hide this advanced option from normal help
    )
    p.add_argument(
        "-i", "--interactive",
        action="store_true",
        help="Launch interactive mode with arrow-key menus and styled output.",
    )

    sub = p.add_subparsers(dest="cmd", required=False, title="Available Commands")

    # Friendlier command help
    sub.add_parser(
        "server-info", 
        help="Check connectivity. Verifies if your Pi is online and reachable."
    )

    sub_list = sub.add_parser(
        "list-tools", 
        help="Show all capabilities (tools) available on your Siya system."
    )
    sub_list.add_argument("--raw", action="store_true", help="Show the raw JSON response instead of a summarized list.")

    sub_call = sub.add_parser(
        "call", 
        help="Execute a specific tool/action."
    )
    sub_call.add_argument("tool_name", help="Name of the tool to run (e.g., get_system_status).")
    sub_call.add_argument(
        "--args",
        default="{}",
        help='Tool arguments as a JSON string (e.g., \'{"path": "/opt"}\'). Default is empty "{}"',
    )
    sub_call.add_argument("--raw", action="store_true", help="Show raw JSON response.")

    # Phase 20: Explanation
    sub_explain = sub.add_parser("explain", help="Explain a specific decision or action (LAW 20).")
    sub_explain.add_argument("request_id", help="The UUID of the request to explain.")

    # Phase 21: Intent Mode
    sub_mode = sub.add_parser("mode", help="Get or set the User Intent Mode (LAW 21).")
    sub_mode.add_argument("mode", nargs="?", choices=["informational", "operational", "destructive"], help="Mode to set (optional). If omitted, shows current mode.")

    # Phase 23: Observability Posture
    sub_posture = sub.add_parser("posture", help="Get the current System Posture (LAW 23).")

    args = p.parse_args(argv)

    # Validate: either interactive mode or a command must be specified
    if not args.interactive and not args.cmd:
        p.print_help()
        return 1

    try:
        client = _create_client(args)
    except RuntimeError as e:
        _print_json({"status": "error", "message": str(e)})
        return 1

    with client:
        client.initialize(protocol_version=args.protocol_version)

        # Interactive mode
        if args.interactive:
            from pc_mcp_client.interactive import interactive_main
            return interactive_main(client, server_url=args.url)

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
            
            # Check for confirmation requirement (LAW 1)
            result = resp.get("result", {}) if not args.raw else resp.get("result", {})
            # Handle both raw response wrappers and direct result access depending on client impl
            # For HTTP client, resp IS the result object already extracted in _request
            # But let's be robust
            
            # If "confirmationNeeded" is in resp (since http_client returns 'result' key from JSON-RPC)
            if resp.get("confirmationNeeded"):
                # Confirmation Loop
                print("\n⚠️  CONFIRMATION REQUIRED (LAW 1)")
                print(f"Tool: {resp.get('tool')}")
                print(f"Args: {json.dumps(resp.get('arguments'), indent=2)}")
                print(f"Message: {resp.get('message')}")
                
                try:
                    choice = input("\nDo you want to proceed? [y/N]: ").strip().lower()
                except KeyboardInterrupt:
                    print("\nAborted.")
                    return 1
                
                if choice == 'y':
                    print("Confirming execution...")
                    resp = client.tools_call(args.tool_name, tool_args, confirmed=True)
                else:
                    print("Execution cancelled.")
                    return 1
            
            if args.raw:
                _print_json(resp)
                return 0
            # Prefer structuredContent (when provided) for machine readability.
            structured = resp.get("structuredContent")
            if isinstance(structured, dict):
                _print_json({"status": "ok", "output": structured})
                return 0
            _print_json({"status": "ok", "result": resp})
            _print_json({"status": "ok", "result": resp})
            return 0

        if args.cmd == "explain":
            print(f"Generating explanation for {args.request_id}...")
            resp = client.tools_call("explain_decision", {"request_id": args.request_id})
            result = resp.get("result", {})
            
            # Try to print just the explanation text if possible
            if "content" in result:
                try:
                     content_text = result["content"][0]["text"]
                     data = json.loads(content_text)
                     print(f"\nEXPLANATION:\n{data.get('explanation', content_text)}")
                     return 0
                except:
                     pass
            
            _print_json(resp)
            return 0

        if args.cmd == "mode":
            if args.mode:
                # Set mode
                resp = client.tools_call("set_user_intent_mode", {"mode": args.mode})
                print(f"✅ Mode set to: {args.mode.upper()}")
            else:
                # Get mode
                resp = client.tools_call("get_user_intent_mode", {})
                result = resp.get("result", {})
                if "content" in result:
                    try:
                        content_text = result["content"][0]["text"]
                        data = json.loads(content_text)
                        print(f"Current Mode: {data.get('mode', 'UNKNOWN').upper()}")
                        return 0
                    except:
                        pass
                _print_json(resp)
            return 0

        if args.cmd == "posture":
            resp = client.tools_call("get_system_posture", {})
            result = resp.get("result", {})
            if "content" in result:
                try:
                    content_text = result["content"][0]["text"]
                    data = json.loads(content_text)
                    print(f"System Posture: {data.get('posture_level', 'UNKNOWN')}")
                    components = data.get('components', {})
                    for k, v in components.items():
                         print(f" - {k}: {v}")
                    return 0
                except:
                    pass
            _print_json(resp)
            return 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
