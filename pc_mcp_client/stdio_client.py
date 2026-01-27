import json
import subprocess
import sys
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class MCPStdioServerProcess:
    proc: subprocess.Popen[str]

    def close(self) -> None:
        try:
            if self.proc.stdin:
                self.proc.stdin.close()
        finally:
            try:
                self.proc.terminate()
            except Exception:
                pass


class MCPStdioClient:
    """
    Minimal MCP stdio client.

    Notes:
    - Sends newline-delimited JSON-RPC messages to server stdin
    - Reads newline-delimited JSON-RPC responses from server stdout
    """

    def __init__(self, server_cmd: list[str]) -> None:
        self._server_cmd = server_cmd
        self._server: Optional[MCPStdioServerProcess] = None
        self._next_id = 1

    def __enter__(self) -> "MCPStdioClient":
        self.start()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.stop()

    def start(self) -> None:
        if self._server is not None:
            return
        proc: subprocess.Popen[str] = subprocess.Popen(
            self._server_cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=sys.stderr,
            text=True,
            encoding="utf-8",
            bufsize=1,
        )
        self._server = MCPStdioServerProcess(proc=proc)

    def stop(self) -> None:
        if self._server is None:
            return
        self._server.close()
        self._server = None

    def initialize(self, protocol_version: str = "2025-03-26") -> Dict[str, Any]:
        result = self._request(
            method="initialize",
            params={
                "protocolVersion": protocol_version,
                "capabilities": {"roots": {"listChanged": False}, "sampling": {}},
                "clientInfo": {"name": "siya-pc-mcp-cli", "version": "1.0.0"},
            },
        )
        # Per MCP lifecycle, client sends notifications/initialized after success
        self._notify("notifications/initialized", params={})
        return result

    def tools_list(self) -> Dict[str, Any]:
        return self._request(method="tools/list", params={})

    def tools_call(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        return self._request(method="tools/call", params={"name": name, "arguments": arguments})

    def _notify(self, method: str, params: Dict[str, Any]) -> None:
        if self._server is None or self._server.proc.stdin is None:
            raise RuntimeError("MCP client not started")
        msg = {"jsonrpc": "2.0", "method": method, "params": params}
        self._server.proc.stdin.write(json.dumps(msg, ensure_ascii=False) + "\n")
        self._server.proc.stdin.flush()

    def _request(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        if self._server is None or self._server.proc.stdin is None or self._server.proc.stdout is None:
            raise RuntimeError("MCP client not started")
        msg_id = self._next_id
        self._next_id += 1
        req = {"jsonrpc": "2.0", "id": msg_id, "method": method, "params": params}
        self._server.proc.stdin.write(json.dumps(req, ensure_ascii=False) + "\n")
        self._server.proc.stdin.flush()

        # Read responses until matching id is found (ignore other output)
        while True:
            line = self._server.proc.stdout.readline()
            if line == "":
                raise RuntimeError("MCP server closed connection")
            line = line.strip()
            if not line:
                continue
            try:
                resp = json.loads(line)
            except json.JSONDecodeError:
                continue
            if resp.get("id") != msg_id:
                continue
            if "error" in resp:
                err = resp["error"]
                raise RuntimeError(f"MCP_ERROR {err.get('code')}: {err.get('message')}")
            return resp.get("result", {})


def default_stdio_server_cmd() -> list[str]:
    """
    Default command to launch Siya MCP stdio server locally.

    Uses the current Python interpreter to run: python -m mcp.stdio_main
    """
    return [sys.executable, "-m", "mcp.stdio_main"]

