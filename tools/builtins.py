"""
Built-in tools (initial).

These are intentionally minimal “starter tools” to prove end-to-end execution.
More tools/integrations will be added in Phase 11+.
"""

from typing import Any, Dict

from system.resource_monitor import ResourceMonitor


def get_system_status(_args: Dict[str, Any]) -> Dict[str, Any]:
    monitor = ResourceMonitor()
    resources = monitor.check_resources()
    return {
        "status": "ok",
        "resources": resources,
    }

