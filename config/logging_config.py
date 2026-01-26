"""
Logging Configuration

Basic logging configuration for Phase 1.
Per DIP Phase 1: Exhaustive logging hooks.
"""

import logging
import sys
from typing import Optional


def setup_logging(level: int = logging.INFO, log_file: Optional[str] = None) -> None:
    """
    Setup basic logging configuration.

    Args:
        level: Logging level (default: INFO)
        log_file: Optional log file path (logs to stdout if None)
    """
    handlers: list[logging.Handler] = [logging.StreamHandler(sys.stdout)]

    if log_file:
        handlers.append(logging.FileHandler(log_file))

    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=handlers,
    )

    # Set root logger level
    logging.getLogger().setLevel(level)

    # Phase 1: Basic logging only
    # In later phases, we'll add structured logging, audit logs, etc.
