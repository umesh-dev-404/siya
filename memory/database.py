"""
Database Connection and Management

SQLite database connection management with WAL mode.
Per DIP Phase 3: SQLite runtime memory (WAL enabled).
"""

import logging
import sqlite3
from pathlib import Path
from typing import Optional

from memory.database_schema import get_all_indexes, get_all_schemas

logger = logging.getLogger(__name__)


class Database:
    """
    SQLite database connection manager.

    Per DIP Phase 3:
    - WAL mode enabled
    - Offline-safe operation
    - Persistent, queryable logs
    """

    def __init__(self, db_path: str = "siya.db") -> None:
        """
        Initialize database connection.

        Args:
            db_path: Path to SQLite database file
        """
        self._db_path = Path(db_path)
        self._connection: Optional[sqlite3.Connection] = None

    def connect(self) -> None:
        """
        Connect to database and initialize schema.

        Raises:
            sqlite3.Error: If connection or schema initialization fails
        """
        if self._connection is not None:
            return

        # Create parent directory if needed
        self._db_path.parent.mkdir(parents=True, exist_ok=True)

        # Connect to database
        self._connection = sqlite3.connect(
            str(self._db_path),
            check_same_thread=False,  # Phase 3: Single-threaded, will be enhanced later
        )

        # Enable WAL mode (Write-Ahead Logging)
        # Per TRD: WAL mode enabled for better concurrency and performance
        self._connection.execute("PRAGMA journal_mode=WAL;")
        self._connection.execute("PRAGMA foreign_keys=ON;")  # Enable foreign key constraints

        # Initialize schema
        self._initialize_schema()

        logger.info(
            f"Database connected: {self._db_path}",
            extra={"db_path": str(self._db_path)},
        )

    def _initialize_schema(self) -> None:
        """Initialize database schema."""
        if self._connection is None:
            raise RuntimeError("Database not connected")

        cursor = self._connection.cursor()

        # Create tables
        for schema in get_all_schemas():
            cursor.execute(schema)

        # Create indexes
        for index_sql in get_all_indexes():
            cursor.execute(index_sql)

        self._connection.commit()

        logger.info("Database schema initialized")

    def get_connection(self) -> sqlite3.Connection:
        """
        Get database connection.

        Returns:
            SQLite connection

        Raises:
            RuntimeError: If database is not connected
        """
        if self._connection is None:
            raise RuntimeError("Database not connected. Call connect() first.")

        return self._connection

    def close(self) -> None:
        """Close database connection."""
        if self._connection:
            self._connection.close()
            self._connection = None
            logger.info("Database connection closed")

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
