-- ============================================
-- SIYA L3 (SUPABASE) DATABASE SCHEMA
-- Version: 1.0.0
-- Generated from: docs/system_schema.json
-- Compatible with: memory/database_schema.py
-- ============================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================
-- MEMORY TABLE (L3 - Cloud Synchronized)
-- Matches SQLite L2 schema for seamless sync
-- ============================================
CREATE TABLE IF NOT EXISTS memory (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    key TEXT NOT NULL,
    value TEXT NOT NULL,
    memory_tier TEXT NOT NULL CHECK(memory_tier IN ('L1', 'L2', 'L3')),
    tags JSONB DEFAULT '[]'::jsonb,  -- JSON array of strings
    confidence REAL CHECK(confidence >= 0.0 AND confidence <= 1.0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ,  -- NULL if no expiration
    source_request_id UUID,
    source_type TEXT CHECK(source_type IN ('intent_parsing', 'tool_execution', 'user_input', 'automation')),
    parent_memory_id UUID REFERENCES memory(id),
    suggested_by TEXT CHECK(suggested_by IN ('AI', 'ORCHESTRATOR', 'TOOL')),
    
    -- Phase 22: Memory Quality Control (v1.0.1)
    confidence_original REAL DEFAULT 1.0 CHECK(confidence_original >= 0.0 AND confidence_original <= 1.0),
    confidence_current REAL DEFAULT 1.0 CHECK(confidence_current >= 0.0 AND confidence_current <= 1.0),
    last_evaluated TIMESTAMPTZ,
    last_accessed TIMESTAMPTZ,
    access_count INTEGER DEFAULT 0,
    decay_rate REAL DEFAULT 0.05,
    lineage_id UUID REFERENCES memory(id),
    is_summarized INTEGER DEFAULT 0 CHECK(is_summarized IN (0, 1)),
    summarization_level INTEGER DEFAULT 0,
    
    -- Sync metadata
    synced_at TIMESTAMPTZ,  -- When last synced from device
    device_id TEXT  -- Source device identifier
);

-- Indexes for L3 memory
CREATE INDEX IF NOT EXISTS idx_memory_key ON memory(key);
CREATE INDEX IF NOT EXISTS idx_memory_tier ON memory(memory_tier);
CREATE INDEX IF NOT EXISTS idx_memory_created_at ON memory(created_at);
CREATE INDEX IF NOT EXISTS idx_memory_expires_at ON memory(expires_at);
CREATE INDEX IF NOT EXISTS idx_memory_source_request_id ON memory(source_request_id);
CREATE INDEX IF NOT EXISTS idx_memory_parent_memory_id ON memory(parent_memory_id);
CREATE INDEX IF NOT EXISTS idx_memory_synced_at ON memory(synced_at);
CREATE INDEX IF NOT EXISTS idx_memory_device_id ON memory(device_id);

-- Phase 22 Indexes
CREATE INDEX IF NOT EXISTS idx_memory_lineage_id ON memory(lineage_id);
CREATE INDEX IF NOT EXISTS idx_memory_confidence_current ON memory(confidence_current);
CREATE INDEX IF NOT EXISTS idx_memory_last_evaluated ON memory(last_evaluated);
CREATE INDEX IF NOT EXISTS idx_memory_is_summarized ON memory(is_summarized);

-- ============================================
-- AUDIT LOG TABLE
-- Per system_schema.json audit_log_entry
-- ============================================
CREATE TABLE IF NOT EXISTS audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    request_id UUID NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
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
    event_data JSONB NOT NULL DEFAULT '{}'::jsonb,  -- No secrets (LAW 15)
    correlation_id UUID NOT NULL,
    user_id TEXT,
    interface TEXT CHECK(interface IN ('CLI', 'WEB', 'API', 'VOICE')),
    layer TEXT CHECK(layer IN ('AI', 'MCP', 'ORCHESTRATOR', 'TOOL', 'MEMORY', 'INTERFACE', 'SYSTEM')),
    
    -- Sync metadata
    synced_at TIMESTAMPTZ,
    device_id TEXT
);

-- Indexes for audit log
CREATE INDEX IF NOT EXISTS idx_audit_log_request_id ON audit_log(request_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_timestamp ON audit_log(timestamp);
CREATE INDEX IF NOT EXISTS idx_audit_log_event_type ON audit_log(event_type);
CREATE INDEX IF NOT EXISTS idx_audit_log_correlation_id ON audit_log(correlation_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_synced_at ON audit_log(synced_at);

-- ============================================
-- LOG SUMMARY TABLE (LAW 9 - Memory Degradation)
-- ============================================
CREATE TABLE IF NOT EXISTS log_summary (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    summary_period_start TIMESTAMPTZ NOT NULL,
    summary_period_end TIMESTAMPTZ NOT NULL,
    summary_content TEXT NOT NULL,
    original_log_count INTEGER NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    parent_summary_id UUID REFERENCES log_summary(id),
    
    -- Sync metadata
    synced_at TIMESTAMPTZ,
    device_id TEXT
);

-- Indexes for log summary
CREATE INDEX IF NOT EXISTS idx_log_summary_period ON log_summary(summary_period_start, summary_period_end);
CREATE INDEX IF NOT EXISTS idx_log_summary_parent ON log_summary(parent_summary_id);

-- ============================================
-- SYNC QUEUE TABLE (For offline-first operation)
-- ============================================
CREATE TABLE IF NOT EXISTS sync_queue (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    operation_type TEXT NOT NULL CHECK(operation_type IN ('INSERT', 'UPDATE', 'DELETE')),
    table_name TEXT NOT NULL CHECK(table_name IN ('memory', 'audit_log', 'log_summary')),
    record_id UUID NOT NULL,
    payload JSONB NOT NULL,
    device_id TEXT NOT NULL,
    queued_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    processed_at TIMESTAMPTZ,
    status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending', 'processing', 'completed', 'failed')),
    error_message TEXT,
    retry_count INTEGER NOT NULL DEFAULT 0
);

-- Indexes for sync queue
CREATE INDEX IF NOT EXISTS idx_sync_queue_status ON sync_queue(status);
CREATE INDEX IF NOT EXISTS idx_sync_queue_queued_at ON sync_queue(queued_at);
CREATE INDEX IF NOT EXISTS idx_sync_queue_device_id ON sync_queue(device_id);

-- ============================================
-- ROW LEVEL SECURITY (RLS) - Single User System
-- Enable RLS but allow all for single user
-- ============================================
ALTER TABLE memory ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE log_summary ENABLE ROW LEVEL SECURITY;
ALTER TABLE sync_queue ENABLE ROW LEVEL SECURITY;

-- Allow all operations for authenticated users (single-user system)
CREATE POLICY "Allow all for authenticated users" ON memory
    FOR ALL TO authenticated USING (true) WITH CHECK (true);

CREATE POLICY "Allow all for authenticated users" ON audit_log
    FOR ALL TO authenticated USING (true) WITH CHECK (true);

CREATE POLICY "Allow all for authenticated users" ON log_summary
    FOR ALL TO authenticated USING (true) WITH CHECK (true);

CREATE POLICY "Allow all for authenticated users" ON sync_queue
    FOR ALL TO authenticated USING (true) WITH CHECK (true);

-- ============================================
-- FUNCTIONS
-- ============================================

-- Auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_memory_updated_at
    BEFORE UPDATE ON memory
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- VERIFICATION QUERY
-- Run this to verify schema was created correctly
-- ============================================
-- SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';
