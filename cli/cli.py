"""
Command-Line Interface

Primary debugging surface for Siya.
Per DIP Phase 6: CLI is primary debugging surface.

Enforces:
- LAW 1 — HUMAN SOVEREIGNTY (explicit confirmations)
- LAW 13 — COMPLETE AUDITABILITY (all actions logged)
"""

import logging
import sys
from typing import Optional
from uuid import UUID

from ai.ai_interface import AIInterface
from mcp.mcp import ModelControlPlane
from orchestrator.orchestrator import Orchestrator

logger = logging.getLogger(__name__)


class CLI:
    """
    Command-line interface for Siya.

    Per DIP Phase 6:
    - CLI is primary debugging surface
    - Explicit confirmations only
    - Identical behavior to other interfaces

    Enforces:
    - LAW 1 — HUMAN SOVEREIGNTY
    - LAW 13 — COMPLETE AUDITABILITY
    """

    def __init__(
        self,
        orchestrator: Orchestrator,
        mcp: ModelControlPlane,
        ai_interface: AIInterface,
    ) -> None:
        """
        Initialize CLI.

        Args:
            orchestrator: Orchestrator instance
            mcp: Model Control Plane instance
            ai_interface: AI Interface instance
        """
        self._orchestrator = orchestrator
        self._mcp = mcp
        self._ai_interface = ai_interface
        self._running = False

    def start(self) -> None:
        """Start the CLI."""
        self._orchestrator.start()
        self._running = True
        logger.info("CLI started")

    def stop(self) -> None:
        """Stop the CLI."""
        self._orchestrator.stop()
        self._running = False
        logger.info("CLI stopped")

    def process_command(self, command: str) -> str:
        """
        Process a command.

        Args:
            command: User command string

        Returns:
            Response message

        Note:
            Per DIP Phase 6: CLI processes user input through orchestrator.
        """
        if not self._running:
            return "Error: CLI is not running. Call start() first."

        try:
            # Submit user input through orchestrator
            task_id = self._orchestrator.submit_user_input(command)

            # Process the task
            processed = self._orchestrator.process_next_task()

            if processed:
                return f"Command processed. Task ID: {task_id}"
            else:
                return f"Command queued. Task ID: {task_id}"

        except ValueError as e:
            # Clarification needed or validation error
            return f"Clarification needed: {e}"

        except RuntimeError as e:
            # Execution error
            return f"Error: {e}"

        except Exception as e:
            logger.error(f"CLI command failed: {e}", exc_info=True)
            return f"Error: {str(e)}"

    def run_interactive(self) -> None:
        """
        Run interactive CLI loop.

        Per DIP Phase 6: CLI provides interactive debugging interface.
        """
        if not self._running:
            self.start()

        print("Siya CLI - Type 'exit' or 'quit' to exit")
        print("=" * 50)

        while self._running:
            try:
                command = input("siya> ").strip()

                if not command:
                    continue

                if command.lower() in ["exit", "quit"]:
                    break

                # Process command
                response = self.process_command(command)
                print(response)

            except KeyboardInterrupt:
                print("\nExiting...")
                break
            except EOFError:
                print("\nExiting...")
                break

        self.stop()

    def run_single_command(self, command: str) -> str:
        """
        Run a single command and return result.

        Args:
            command: Command to execute

        Returns:
            Response message

        Note:
            Used for non-interactive execution (e.g., from API).
        """
        if not self._running:
            self.start()

        try:
            return self.process_command(command)
        finally:
            # Don't stop after single command (may be used in API context)
            pass
