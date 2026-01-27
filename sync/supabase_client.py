"""
Supabase Client - L3 Memory Tier Connection

Manages authenticated connection to Supabase for cloud memory synchronization.
Per Phase 13: Supabase Synchronization.

LAW Compliance:
- LAW 15: API keys never logged or exposed
- LAW 16: All network calls explicit, offline-first design

Features:
- Connection management with health checks
- Retry logic with exponential backoff
- Graceful offline handling
"""

import logging
import os
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Final, Optional

logger = logging.getLogger(__name__)


class ConnectionStatus(str, Enum):
    """Supabase connection status."""

    DISCONNECTED = "DISCONNECTED"
    CONNECTING = "CONNECTING"
    CONNECTED = "CONNECTED"
    ERROR = "ERROR"


@dataclass
class SyncConfig:
    """Sync configuration from environment."""

    supabase_url: str = ""
    supabase_anon_key: str = ""  # Never log this (LAW 15)
    device_id: str = ""
    sync_interval_seconds: int = 300
    sync_enabled: bool = True
    max_retries: int = 3

    @classmethod
    def from_env(cls) -> "SyncConfig":
        """
        Load configuration from environment variables.

        LAW 15: API keys loaded but never logged.
        """
        device_id = os.getenv("DEVICE_ID", "")
        if not device_id:
            # Generate device ID if not set
            device_id = str(uuid.uuid4())

        return cls(
            supabase_url=os.getenv("SUPABASE_URL", ""),
            supabase_anon_key=os.getenv("SUPABASE_ANON_KEY", ""),
            device_id=device_id,
            sync_interval_seconds=int(os.getenv("SYNC_INTERVAL_SECONDS", "300")),
            sync_enabled=os.getenv("SYNC_ENABLED", "true").lower() == "true",
            max_retries=int(os.getenv("SYNC_MAX_RETRIES", "3")),
        )

    def is_configured(self) -> bool:
        """Check if Supabase is properly configured."""
        return bool(self.supabase_url and self.supabase_anon_key)


@dataclass
class SupabaseClient:
    """
    Supabase client for L3 memory synchronization.

    Provides authenticated connection management with:
    - Health checks
    - Retry logic with exponential backoff
    - Offline-first operation (never blocks on network)

    LAW 15: API keys never logged.
    LAW 16: All network calls explicit.
    """

    config: SyncConfig = field(default_factory=SyncConfig.from_env)
    _status: ConnectionStatus = field(default=ConnectionStatus.DISCONNECTED)
    _client: Optional[Any] = field(default=None)
    _last_health_check: Optional[datetime] = field(default=None)
    _consecutive_failures: int = field(default=0)

    # Retry configuration
    BASE_RETRY_DELAY: Final[float] = 1.0
    MAX_RETRY_DELAY: Final[float] = 60.0
    HEALTH_CHECK_INTERVAL: Final[int] = 60  # seconds

    def __post_init__(self) -> None:
        """Initialize client after dataclass creation."""
        if not self.config.is_configured():
            logger.warning(
                "Supabase not configured. L3 sync disabled. "
                "Set SUPABASE_URL and SUPABASE_ANON_KEY in .env"
            )

    @property
    def status(self) -> ConnectionStatus:
        """Get current connection status."""
        return self._status

    @property
    def is_connected(self) -> bool:
        """Check if client is connected."""
        return self._status == ConnectionStatus.CONNECTED

    @property
    def is_configured(self) -> bool:
        """Check if Supabase is configured."""
        return self.config.is_configured()

    def connect(self) -> bool:
        """
        Establish connection to Supabase.

        Returns:
            True if connected successfully, False otherwise.

        LAW 15: Connection logs do not expose credentials.
        LAW 16: Connection is explicit, not implicit.
        """
        if not self.config.is_configured():
            logger.debug("Supabase not configured, skipping connection")
            return False

        self._status = ConnectionStatus.CONNECTING
        # LAW 15: Log URL but never the key
        logger.info(
            "Connecting to Supabase",
            extra={"url_configured": bool(self.config.supabase_url)},
        )

        try:
            # Import supabase only when needed
            from supabase import create_client

            self._client = create_client(
                self.config.supabase_url,
                self.config.supabase_anon_key,
            )
            self._status = ConnectionStatus.CONNECTED
            self._consecutive_failures = 0
            logger.info("Supabase connection established")
            return True

        except ImportError:
            logger.error(
                "supabase-py not installed. Run: pip install supabase"
            )
            self._status = ConnectionStatus.ERROR
            return False

        except Exception as e:
            # LAW 15: Never log credentials in error messages
            logger.error(
                f"Supabase connection failed: {type(e).__name__}",
                extra={"recoverable": True},
            )
            self._status = ConnectionStatus.ERROR
            self._consecutive_failures += 1
            return False

    def disconnect(self) -> None:
        """Disconnect from Supabase."""
        self._client = None
        self._status = ConnectionStatus.DISCONNECTED
        logger.info("Supabase disconnected")

    def health_check(self, force: bool = False) -> bool:
        """
        Perform health check on connection.

        Args:
            force: Force health check even if recently checked

        Returns:
            True if healthy, False otherwise
        """
        if not self.is_configured:
            return False

        # Skip if recently checked (unless forced)
        if not force and self._last_health_check:
            elapsed = (
                datetime.now(timezone.utc) - self._last_health_check
            ).total_seconds()
            if elapsed < self.HEALTH_CHECK_INTERVAL:
                return self.is_connected

        if not self._client:
            return self.connect()

        try:
            # Simple query to verify connection
            # Use a lightweight operation
            self._client.table("memory").select("id").limit(1).execute()
            self._last_health_check = datetime.now(timezone.utc)
            self._status = ConnectionStatus.CONNECTED
            self._consecutive_failures = 0
            return True

        except Exception as e:
            logger.warning(
                f"Supabase health check failed: {type(e).__name__}"
            )
            self._status = ConnectionStatus.ERROR
            self._consecutive_failures += 1
            return False

    def execute_with_retry(
        self,
        operation: str,
        func: callable,
        *args: Any,
        **kwargs: Any,
    ) -> tuple[bool, Optional[Any]]:
        """
        Execute an operation with retry logic and exponential backoff.

        Args:
            operation: Name of operation (for logging)
            func: Callable to execute
            *args: Positional arguments for func
            **kwargs: Keyword arguments for func

        Returns:
            Tuple of (success, result)

        LAW 16: Network operation is explicit.
        """
        if not self.is_connected and not self.connect():
            logger.warning(f"Cannot execute {operation}: not connected")
            return False, None

        last_error: Optional[Exception] = None

        for attempt in range(self.config.max_retries):
            try:
                result = func(*args, **kwargs)
                self._consecutive_failures = 0
                return True, result

            except Exception as e:
                last_error = e
                self._consecutive_failures += 1

                # Calculate backoff delay
                delay = min(
                    self.BASE_RETRY_DELAY * (2 ** attempt),
                    self.MAX_RETRY_DELAY,
                )

                logger.warning(
                    f"{operation} failed (attempt {attempt + 1}/{self.config.max_retries}): "
                    f"{type(e).__name__}. Retrying in {delay:.1f}s"
                )

                if attempt < self.config.max_retries - 1:
                    time.sleep(delay)

        logger.error(
            f"{operation} failed after {self.config.max_retries} attempts: "
            f"{type(last_error).__name__}"
        )
        self._status = ConnectionStatus.ERROR
        return False, None

    # ==========================================
    # L3 Memory Operations
    # ==========================================

    def insert_memory(self, record: dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        Insert a memory record to L3.

        Args:
            record: Memory record to insert

        Returns:
            Tuple of (success, inserted_id)
        """
        if not self._client:
            return False, None

        def _insert() -> str:
            response = self._client.table("memory").insert(record).execute()
            # Supabase-py 2.x raises errors for 4xx/5xx, but logic errors might be in response
            # Note: execute() usually raises postgrest.exceptions.APIError on failure
            if hasattr(response, "data") and response.data:
                return response.data[0].get("id")
            
            # If we got here with no data and no exception, it might be an RLS policy issue
            logger.error(f"Supabase insert returned no data: {response}")
            raise RuntimeError(f"Insert returned no data (Possible RLS blocking): {response}")

        return self.execute_with_retry("insert_memory", _insert)

    def update_memory(
        self, record_id: str, updates: dict[str, Any]
    ) -> tuple[bool, Optional[dict]]:
        """
        Update a memory record in L3.

        Args:
            record_id: ID of record to update
            updates: Fields to update

        Returns:
            Tuple of (success, updated_record)
        """
        if not self._client:
            return False, None

        def _update() -> dict:
            response = (
                self._client.table("memory")
                .update(updates)
                .eq("id", record_id)
                .execute()
            )
            if response.data:
                return response.data[0]
            return None

        return self.execute_with_retry("update_memory", _update)

    def delete_memory(self, record_id: str) -> tuple[bool, None]:
        """
        Delete a memory record from L3.

        Args:
            record_id: ID of record to delete

        Returns:
            Tuple of (success, None)
        """
        if not self._client:
            return False, None

        def _delete() -> None:
            self._client.table("memory").delete().eq("id", record_id).execute()
            return None

        return self.execute_with_retry("delete_memory", _delete)

    def fetch_memories_since(
        self, since: datetime, limit: int = 100
    ) -> tuple[bool, Optional[list[dict]]]:
        """
        Fetch memories updated since a given timestamp.

        Args:
            since: Fetch records updated after this time
            limit: Maximum records to fetch

        Returns:
            Tuple of (success, list of records)
        """
        if not self._client:
            return False, None

        def _fetch() -> list[dict]:
            response = (
                self._client.table("memory")
                .select("*")
                .gte("updated_at", since.isoformat())
                .order("updated_at")
                .limit(limit)
                .execute()
            )
            return response.data or []

        return self.execute_with_retry("fetch_memories_since", _fetch)

    def get_connection_info(self) -> dict[str, Any]:
        """
        Get connection info for diagnostics.

        LAW 15: Never expose credentials.
        """
        return {
            "status": self._status.value,
            "is_connected": self.is_connected,
            "is_configured": self.is_configured,
            "device_id": self.config.device_id,
            "sync_enabled": self.config.sync_enabled,
            "sync_interval_seconds": self.config.sync_interval_seconds,
            "consecutive_failures": self._consecutive_failures,
            "last_health_check": (
                self._last_health_check.isoformat()
                if self._last_health_check
                else None
            ),
            # LAW 15: Never include credentials
        }


# Singleton instance
_supabase_client: Optional[SupabaseClient] = None


def get_supabase_client() -> SupabaseClient:
    """
    Get the singleton SupabaseClient instance.

    Returns:
        SupabaseClient instance
    """
    global _supabase_client
    if _supabase_client is None:
        _supabase_client = SupabaseClient()
    return _supabase_client


def reset_supabase_client() -> None:
    """Reset the singleton (for testing)."""
    global _supabase_client
    if _supabase_client:
        _supabase_client.disconnect()
    _supabase_client = None
