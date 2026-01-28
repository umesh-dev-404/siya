"""
Migration 001: Add Memory Quality Columns

Adds Phase 22 (v1.0.1) memory quality columns to existing databases.
Per LAW 22 — MEMORY QUALITY PRESERVATION.

This migration is non-breaking:
- All new columns have defaults
- Existing data is preserved
- No data transformation required
"""

import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


# Migration metadata
MIGRATION_ID = "001_add_memory_quality_columns"
MIGRATION_VERSION = "1.0.1"
MIGRATION_DATE = "2026-01-28"


# Columns to add (compatible with SQLite ALTER TABLE)
NEW_COLUMNS = [
    ("confidence_original", "REAL DEFAULT 1.0"),
    ("confidence_current", "REAL DEFAULT 1.0"),
    ("last_evaluated", "TEXT"),
    ("last_accessed", "TEXT"),
    ("access_count", "INTEGER DEFAULT 0"),
    ("decay_rate", "REAL DEFAULT 0.05"),
    ("lineage_id", "TEXT"),
    ("is_summarized", "INTEGER DEFAULT 0"),
    ("summarization_level", "INTEGER DEFAULT 0"),
]


# Indexes to create
NEW_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_memory_lineage_id ON memory(lineage_id);",
    "CREATE INDEX IF NOT EXISTS idx_memory_confidence_current ON memory(confidence_current);",
    "CREATE INDEX IF NOT EXISTS idx_memory_last_evaluated ON memory(last_evaluated);",
    "CREATE INDEX IF NOT EXISTS idx_memory_is_summarized ON memory(is_summarized);",
]


def get_existing_columns(conn: sqlite3.Connection, table: str) -> set:
    """Get set of existing column names in a table."""
    cursor = conn.execute(f"PRAGMA table_info({table});")
    return {row[1] for row in cursor.fetchall()}


def migrate(db_path: str) -> bool:
    """
    Apply migration to database.
    
    Args:
        db_path: Path to SQLite database file
        
    Returns:
        True if migration succeeded, False otherwise
    """
    if not Path(db_path).exists():
        logger.warning(f"Database not found: {db_path}")
        return False
    
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        
        # Check if memory table exists
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='memory';"
        )
        if not cursor.fetchone():
            logger.info("Memory table not found, skipping migration")
            return True
        
        # Get existing columns
        existing_columns = get_existing_columns(conn, "memory")
        
        # Add missing columns
        added_count = 0
        for col_name, col_type in NEW_COLUMNS:
            if col_name not in existing_columns:
                sql = f"ALTER TABLE memory ADD COLUMN {col_name} {col_type};"
                conn.execute(sql)
                logger.info(f"Added column: {col_name}")
                added_count += 1
        
        # Create indexes
        for index_sql in NEW_INDEXES:
            conn.execute(index_sql)
        
        # Record migration
        conn.execute(
            """
            INSERT OR REPLACE INTO migrations (id, version, applied_at)
            VALUES (?, ?, ?)
            """,
            (MIGRATION_ID, MIGRATION_VERSION, datetime.utcnow().isoformat() + "Z"),
        )
        
        conn.commit()
        logger.info(f"Migration {MIGRATION_ID} complete: {added_count} columns added")
        return True
        
    except sqlite3.Error as e:
        logger.error(f"Migration failed: {e}")
        if conn:
            conn.rollback()
        return False
        
    finally:
        if conn:
            conn.close()


def create_migrations_table(db_path: str) -> None:
    """Create migrations tracking table if it doesn't exist."""
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS migrations (
                id TEXT PRIMARY KEY,
                version TEXT NOT NULL,
                applied_at TEXT NOT NULL
            );
            """
        )
        conn.commit()
    finally:
        conn.close()


def check_migration_applied(db_path: str) -> bool:
    """Check if this migration has already been applied."""
    if not Path(db_path).exists():
        return False
    
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.execute(
            "SELECT id FROM migrations WHERE id = ?",
            (MIGRATION_ID,),
        )
        return cursor.fetchone() is not None
    except sqlite3.OperationalError:
        # Migrations table doesn't exist
        return False
    finally:
        conn.close()


def main():
    """Run migration on default database location."""
    import os
    
    # Default database locations
    db_paths = [
        "data/siya.db",
        "siya.db",
        os.path.expanduser("~/.siya/siya.db"),
    ]
    
    for db_path in db_paths:
        if Path(db_path).exists():
            print(f"Found database: {db_path}")
            
            if check_migration_applied(db_path):
                print(f"  Migration already applied")
                continue
            
            create_migrations_table(db_path)
            
            if migrate(db_path):
                print(f"  Migration successful")
            else:
                print(f"  Migration failed")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
