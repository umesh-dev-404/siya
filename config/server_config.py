"""
Server Configuration

Configuration for API and web servers.
Allows network access for remote control from PC.
"""

import os
from typing import Optional


def get_api_host() -> str:
    """
    Get API server host.

    Returns:
        Host address (0.0.0.0 for network access, localhost for local only)

    Environment variable: SIYA_API_HOST (default: 0.0.0.0)
    """
    return os.getenv("SIYA_API_HOST", "0.0.0.0")


def get_api_port() -> int:
    """
    Get API server port.

    Returns:
        Port number

    Environment variable: SIYA_API_PORT (default: 8080)
    """
    return int(os.getenv("SIYA_API_PORT", "8080"))


def get_web_host() -> str:
    """
    Get web server host.

    Returns:
        Host address (0.0.0.0 for network access, localhost for local only)

    Environment variable: SIYA_WEB_HOST (default: 0.0.0.0)
    """
    return os.getenv("SIYA_WEB_HOST", "0.0.0.0")


def get_web_port() -> int:
    """
    Get web server port.

    Returns:
        Port number

    Environment variable: SIYA_WEB_PORT (default: 3000)
    """
    return int(os.getenv("SIYA_WEB_PORT", "3000"))


def get_api_base_url() -> str:
    """
    Get API base URL for web interface.

    Returns:
        API base URL

    Environment variable: SIYA_API_BASE_URL (default: http://<host>:8080)
    """
    api_host = get_api_host()
    api_port = get_api_port()
    
    # If host is 0.0.0.0, use localhost for web interface (client-side)
    if api_host == "0.0.0.0":
        # For web interface, use the actual Pi IP or localhost
        # This will be set by deployment script or environment
        return os.getenv("SIYA_API_BASE_URL", f"http://localhost:{api_port}")
    
    return os.getenv("SIYA_API_BASE_URL", f"http://{api_host}:{api_port}")
