import argparse
import json
import sys
from typing import Any, Dict

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


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="siya-mcp", description="Siya first-party PC MCP CLI client (stdio).")
    p.add_argument(
        "--protocol-version",
        default="2025-03-26",
        help="MCP protocol version to request in initialize (default: 2025-03-26).",
    )

    sub = p.add_subparsers(dest="cmd", required=True)

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

    with MCPStdioClient(default_stdio_server_cmd()) as client:
        client.initialize(protocol_version=args.protocol_version)

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

