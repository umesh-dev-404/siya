"""
HTTP API Server

HTTP API that mirrors CLI exactly.
Per DIP Phase 6: API mirrors CLI exactly.

Enforces:
- LAW 1 — HUMAN SOVEREIGNTY (explicit confirmations)
- LAW 13 — COMPLETE AUDITABILITY (all actions logged)
- Identical behavior to CLI
"""

import json
import logging
from typing import Dict, Any
from uuid import UUID

from cli.cli import CLI

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
