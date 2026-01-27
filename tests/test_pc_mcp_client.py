import json
import subprocess
import sys


def test_pc_mcp_client_list_tools_stdio_smoke() -> None:
    """
    Smoke test: run the PC MCP CLI client and ensure it can list tools via stdio.
    """
    proc = subprocess.run(
        [sys.executable, "-m", "pc_mcp_client.main", "list-tools", "--raw"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
    )
    # The command prints a JSON object. It must contain a tools array.
    data = json.loads(proc.stdout)
    assert "tools" in data
    assert isinstance(data["tools"], list)

