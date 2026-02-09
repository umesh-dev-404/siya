"""
HTTP API Server

HTTP API that mirrors CLI exactly.
Per DIP Phase 6: API mirrors CLI exactly.
Per dev-rules §6.6: CLI/Web parity — onboarding and other CLI flows exposed via API.

Enforces:
- LAW 1 — HUMAN SOVEREIGNTY (explicit confirmations)
- LAW 13 — COMPLETE AUDITABILITY (all actions logged)
- Identical behavior to CLI
"""

import logging
from typing import Any, Dict

from cli.cli import CLI
from cli.onboard import apply_onboarding, is_onboarded

logger = logging.getLogger(__name__)


class APIServer:
    """
    HTTP API server for Siya.

    Per DIP Phase 6:
    - API mirrors CLI exactly
    - Identical behavior across interfaces
    - Explicit confirmations only

    Enforces:
    - LAW 1 — HUMAN SOVEREIGNTY
    - LAW 13 — COMPLETE AUDITABILITY
    """

    def __init__(self, cli: CLI) -> None:
        """
        Initialize API server.

        Args:
            cli: CLI instance (API mirrors CLI)
        """
        self._cli = cli

    def handle_command(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle a command request.

        Args:
            request_data: Request data with 'command' field

        Returns:
            Response dictionary with 'status' and 'message' fields

        Note:
            Per DIP Phase 6: API mirrors CLI exactly.
            This method calls CLI.run_single_command().
        """
        if "command" not in request_data:
            return {
                "status": "error",
                "message": "Missing required field: command",
            }

        command = request_data["command"]

        if not isinstance(command, str):
            return {
                "status": "error",
                "message": "Command must be a string",
            }

        try:
            logger.info(f"Processing command: {command}")
            # Mirror CLI behavior exactly
            response_message = self._cli.run_single_command(command)
            logger.info(f"Command processed successfully: {response_message[:100]}")

            return {
                "status": "success",
                "message": response_message,
            }

        except Exception as e:
            logger.error(f"API command failed: {e}", exc_info=True)
            return {
                "status": "error",
                "message": str(e),
            }

    def handle_health_check(self) -> Dict[str, Any]:
        """
        Handle health check request.

        Returns:
            Health status dictionary
        """
        return {
            "status": "healthy",
            "service": "siya-api",
        }

    def handle_onboard_status(self) -> Dict[str, Any]:
        """
        Return onboarding status (same as CLI: marker file exists).
        Per LAW 19: equivalent to CLI onboarding detection.
        """
        return {"onboarded": is_onboarded()}

    def handle_onboard_apply(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply onboarding config. Requires confirm=true (LAW 1).
        Delegates to cli.onboard.apply_onboarding (same logic as CLI wizard).
        """
        if request_data.get("confirm") is not True:
            return {"status": "error", "message": "confirm is required and must be true (LAW 1)"}
        data_dir = request_data.get("data_dir")
        if not data_dir or not str(data_dir).strip():
            return {"status": "error", "message": "data_dir is required"}
        use_supabase = bool(request_data.get("use_supabase"))
        supabase_url = str(request_data.get("supabase_url", "") or "")
        supabase_key = str(request_data.get("supabase_key", "") or "")
        try:
            apply_onboarding(
                data_dir=str(data_dir).strip(),
                use_supabase=use_supabase,
                supabase_url=supabase_url,
                supabase_key=supabase_key,
            )
            return {"status": "success", "message": "Onboarding applied."}
        except ValueError as e:
            return {"status": "error", "message": str(e)}
        except Exception as e:
            logger.error(f"Onboard apply failed: {e}", exc_info=True)
            return {"status": "error", "message": str(e)}
