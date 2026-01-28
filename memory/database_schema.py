"""
Database Schema Definitions

SQLite schema definitions for L2 (local persistent memory).
Per DIP Phase 3: SQLite runtime memory (WAL enabled).

Memory tiers:
- L1: Runtime memory (in-process, ephemeral) - not persisted
- L2: Local persistent memory (SQLite) - this module
- L3: Long-term synchronized memory (Supabase) - stubbed in Phase 3
"""

from enum import Enum
from typing import Final

# SQL schema strings for table creation

MEMORY_TABLE_SCHEMA: Final[str] = """
CREATE TABLE IF NOT EXISTS memory (
    id TEXT PRIMARY KEY,
    key TEXT NOT NULL,
    value TEXT NOT NULL,
    memory_tier TEXT NOT NULL CHECK(memory_tier IN ('L1', 'L2', 'L3')),
    tags TEXT,  -- JSON array of strings
    confidence REAL CHECK(confidence >= 0.0 AND confidence <= 1.0),
    created_at TEXT NOT NULL,  -- ISO 8601 timestamp
    updated_at TEXT NOT NULL,  -- ISO 8601 timestamp
    expires_at TEXT,  -- ISO 8601 timestamp, NULL if no expiration
    source_request_id TEXT,
    source_type TEXT CHECK(source_type IN ('intent_parsing', 'tool_execution', 'user_input', 'automation')),
    parent_memory_id TEXT,  -- For summaries (LAW 9)
    suggested_by TEXT CHECK(suggested_by IN ('AI', 'ORCHESTRATOR', 'TOOL')),
    -- Phase 22: Memory Quality Control (v1.0.1)
    confidence_original REAL DEFAULT 1.0 CHECK(confidence_original >= 0.0 AND confidence_original <= 1.0),
    confidence_current REAL DEFAULT 1.0 CHECK(confidence_current >= 0.0 AND confidence_current <= 1.0),
    last_evaluated TEXT,  -- ISO 8601 timestamp of last quality evaluation
    last_accessed TEXT,  -- ISO 8601 timestamp of last access
    access_count INTEGER DEFAULT 0,
    decay_rate REAL DEFAULT 0.05,  -- Default 5% per day
    lineage_id TEXT,  -- Reference to original memory before summarization
    is_summarized INTEGER DEFAULT 0 CHECK(is_summarized IN (0, 1)),
    summarization_level INTEGER DEFAULT 0,  -- 0 = original, 1+ = summarized
    FOREIGN KEY (parent_memory_id) REFERENCES memory(id),
    FOREIGN KEY (lineage_id) REFERENCES memory(id)
);
"""


MEMORY_INDEXES: Final[list[str]] = [
    "CREATE INDEX IF NOT EXISTS idx_memory_key ON memory(key);",
    "CREATE INDEX IF NOT EXISTS idx_memory_tier ON memory(memory_tier);",
    "CREATE INDEX IF NOT EXISTS idx_memory_created_at ON memory(created_at);",
    "CREATE INDEX IF NOT EXISTS idx_memory_expires_at ON memory(expires_at);",
    "CREATE INDEX IF NOT EXISTS idx_memory_source_request_id ON memory(source_request_id);",
    "CREATE INDEX IF NOT EXISTS idx_memory_parent_memory_id ON memory(parent_memory_id);",
    # Phase 22: Memory Quality Control (v1.0.1)
    "CREATE INDEX IF NOT EXISTS idx_memory_lineage_id ON memory(lineage_id);",
    "CREATE INDEX IF NOT EXISTS idx_memory_confidence_current ON memory(confidence_current);",
    "CREATE INDEX IF NOT EXISTS idx_memory_last_evaluated ON memory(last_evaluated);",
    "CREATE INDEX IF NOT EXISTS idx_memory_is_summarized ON memory(is_summarized);",
]

AUDIT_LOG_TABLE_SCHEMA: Final[str] = """
CREATE TABLE IF NOT EXISTS audit_log (
    id TEXT PRIMARY KEY,
    request_id TEXT NOT NULL,
    timestamp TEXT NOT NULL,  -- ISO 8601 timestamp
    event_type TEXT NOT NULL CHECK(event_type IN (
        'USER_INPUT',
        'INTENT_PARSED',
        'TOOL_REQUESTED',
        'TOOL_EXECUTED',
        'TOOL_FAILED',
        'CONFIRMATION_REQUESTED',
        'CONFIRMATION_GRANTED',
        'CONFIRMATION_DENIED',
        'PERMISSION_CHECKED',
        'PERMISSION_DENIED',
        'MEMORY_READ',
        'MEMORY_WRITTEN',
        'ORCHESTRATION_STARTED',
        'ORCHESTRATION_COMPLETED',
        'ORCHESTRATION_FAILED',
        'ERROR_OCCURRED',
        'AUTOMATION_TRIGGERED',
        'SCHEDULED_EVENT'
    )),
    event_data TEXT NOT NULL,  -- JSON object (no secrets)
    correlation_id TEXT NOT NULL,
    user_id TEXT,
    interface TEXT CHECK(interface IN ('CLI', 'WEB', 'API', 'VOICE')),
    layer TEXT CHECK(layer IN ('AI', 'MCP', 'ORCHESTRATOR', 'TOOL', 'MEMORY', 'INTERFACE', 'SYSTEM'))
);
"""

AUDIT_LOG_INDEXES: Final[list[str]] = [
    "CREATE INDEX IF NOT EXISTS idx_audit_log_request_id ON audit_log(request_id);",
    "CREATE INDEX IF NOT EXISTS idx_audit_log_timestamp ON audit_log(timestamp);",
    "CREATE INDEX IF NOT EXISTS idx_audit_log_event_type ON audit_log(event_type);",
    "CREATE INDEX IF NOT EXISTS idx_audit_log_correlation_id ON audit_log(correlation_id);",
]

LOG_SUMMARY_TABLE_SCHEMA: Final[str] = """
CREATE TABLE IF NOT EXISTS log_summary (
    id TEXT PRIMARY KEY,
    summary_period_start TEXT NOT NULL,  -- ISO 8601 timestamp
    summary_period_end TEXT NOT NULL,  -- ISO 8601 timestamp
    summary_content TEXT NOT NULL,  -- Summarized log content
    original_log_count INTEGER NOT NULL,
    created_at TEXT NOT NULL,  -- ISO 8601 timestamp
    parent_summary_id TEXT,  -- For hierarchical summaries (LAW 9)
    FOREIGN KEY (parent_summary_id) REFERENCES log_summary(id)
);
"""

LOG_SUMMARY_INDEXES: Final[list[str]] = [
    "CREATE INDEX IF NOT EXISTS idx_log_summary_period ON log_summary(summary_period_start, summary_period_end);",
    "CREATE INDEX IF NOT EXISTS idx_log_summary_parent ON log_summary(parent_summary_id);",
]


class MemoryTier(str, Enum):
    """Memory tier enum. Per system_schema.json and TRD."""

    L1 = "L1"
    """Runtime memory (in-process, ephemeral)."""

    L2 = "L2"
    """Local persistent memory (SQLite)."""

    L3 = "L3"
    """Long-term synchronized memory (Supabase)."""


def get_all_schemas() -> list[str]:
    """
    Get all SQL schema definitions.

    Returns:
        List of SQL CREATE TABLE statements
    """
    return [
        MEMORY_TABLE_SCHEMA,
        AUDIT_LOG_TABLE_SCHEMA,
        LOG_SUMMARY_TABLE_SCHEMA,
    ]


def get_all_indexes() -> list[str]:
    """
    Get all SQL index definitions.

    Returns:
        List of SQL CREATE INDEX statements
    """
    return MEMORY_INDEXES + AUDIT_LOG_INDEXES + LOG_SUMMARY_INDEXES
