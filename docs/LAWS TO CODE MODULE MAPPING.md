==================== FILE START ====================

# LAWS TO CODE MODULE MAPPING  
## Project: Siya

---

## 1. DOCUMENT PURPOSE

This document establishes a **one-to-one mapping between the Canonical System Laws and concrete code modules, boundaries, and enforcement points** within the Siya system.

Its purpose is to ensure:
- Laws are not symbolic
- Laws are enforceable
- Laws remain intact under refactoring
- AI-assisted development does not violate constraints

If a law cannot be mapped to code, the law is unenforced and therefore invalid.

---

## 2. MAPPING PHILOSOPHY

Each Canonical Law is mapped to:
- One or more **primary enforcement modules**
- One or more **secondary verification points**
- Explicit **failure behavior** if violated

No law relies on:
- Prompting
- Human discipline
- Documentation alone

Enforcement must be **structural**.

---

## 3. LAW-BY-LAW CODE MAPPING

---

### LAW 1 — HUMAN SOVEREIGNTY

**Law Statement:**  
The human user is the final and absolute authority.

**Primary Enforcement Modules:**
- `cli/cli.py`
- `api/api_server.py`
- `web/web_server.py`
- `web/static/app.js` — Confirmation modal for web UI (Phase 17)
- `pc_mcp_client/main.py` — Interactive CLI confirmation prompt
- `orchestrator/orchestrator.py`

**Enforcement Mechanisms:**
- All actions originate from explicit user or registered triggers
- Orchestrator requires confirmation tokens before execution
- CLI prompts user with y/N for confirmation-required tools
- Web UI displays modal dialog with Cancel/Yes buttons
- No automatic override paths

**Violation Handling:**
- Action rejected
- Logged as critical violation
- User notified

---

### LAW 2 — NO AUTONOMOUS EXECUTION

**Primary Enforcement Modules:**
- `orchestrator/task_queue.py`
- `automations/automation_manager.py`
- `automations/systemd_timer.py`
- `automations/schedule_manager.py`

**Enforcement Mechanisms:**
- Task queue only accepts registered triggers
- Background loops forbidden
- systemd timers call `siya-cli` → orchestrator (not direct execution)
- Schedule manager persists to SQLite, timers trigger via MCP

**Violation Handling:**
- Task not enqueued
- Security log entry created

---

### LAW 3 — LLM IS A CONTROLLED PROCESSOR

**Primary Enforcement Modules:**
- `ai/intent_parser.py`
- `ai/ai_interface.py`
- `mcp/request_validator.py`
- `ai/model_manager.py` (content processing runtime, when used by tools)

**Enforcement Mechanisms:**
- LLM outputs are data-only
- No autonomous execution hooks exist in AI layer
- AI runs in-process (current baseline); isolation can be added later if required
- Content processing occurs only within tool execution contexts
- All content processing is logged and auditable
- AI model runs locally only (no cloud inference)

**Violation Handling:**
- Output rejected
- Clarification requested
- AI restarted if necessary
- Content processing outside tool context blocked

---

### LAW 4 — TOOL-ONLY EXECUTION

**Primary Enforcement Modules:**
- `mcp/tool_registry.py`
- `mcp/authorization_layer.py`
- `orchestrator/orchestrator.py` (enforces tool-only execution path)

**Enforcement Mechanisms:**
- Only registered tools callable
- Tool registry is static
- No direct OS access outside tools
- Tools may invoke AI content processing within execution flows

**Violation Handling:**
- Execution blocked
- Logged as policy violation

---

### LAW 5 — EXPLICIT PERMISSIONS

**Primary Enforcement Modules:**
- `mcp/policy_engine.py`
- `mcp/authorization_layer.py`
- `mcp/tool_schema.py` (permission metadata)
- `cli/cli.py` / `api/api_server.py` / `web/static/index.html` (confirmation UX; expanded later)

**Enforcement Mechanisms:**
- Permission metadata per tool
- Confirmation required before execution
- No cached permissions unless explicitly configured

**Violation Handling:**
- Tool execution denied
- User prompted for explicit consent

---

### LAW 6 — NO FREE-FORM COMPUTATION

**Primary Enforcement Modules:**
- `security/` (guardrails; to be expanded in Phase 11)

**Enforcement Mechanisms:**
- No shell passthrough functions exist
- No eval/importlib usage
- Static code paths only

**Violation Handling:**
- Runtime exception
- Immediate task abort
- Security alert logged

---

### LAW 7 — MEMORY IS NON-AUTHORITATIVE

**Primary Enforcement Modules:**
- `memory/access_layer.py`
- `core/system_context.py` (Phase 12)
- `ai/context_manager.py` (Phase 12)

**Enforcement Mechanisms:**
- Memory is read-only to AI
- SystemContext provides read-only snapshots to tools
- ContextManager injects history as informational only
- Memory cannot influence tool selection
- No branching logic reads memory state

**Violation Handling:**
- Logic blocked
- Logged as architectural violation

---

### LAW 8 — MEMORY WRITE CONTROL

**Primary Enforcement Modules:**
- `memory/write_controller.py`
- `core/system_context.py` (Phase 12)
- `memory/tier_manager.py` (Phase 12)

**Enforcement Mechanisms:**
- Only orchestrator can write
- SystemContext verifies caller is in authorized_writers set
- TierManager enforces orchestrator-only retention operations
- Write operations require explicit call
- Memory writes logged and tagged

**Violation Handling:**
- Write rejected with PermissionError
- LAW 8 violation logged
- Audit event created

---

### LAW 9 — MEMORY DEGRADATION CONTROL

**Primary Enforcement Modules:**
- `memory/summarizer.py`
- `automations/` (maintenance hooks; timers in later phase)

**Enforcement Mechanisms:**
- Periodic summarization
- Lineage preserved
- No silent deletion

**Violation Handling:**
- Memory write blocked
- Maintenance error reported

---

### LAW 10 — SERIAL EXECUTION

**Primary Enforcement Modules:**
- `orchestrator/task_queue.py`

**Enforcement Mechanisms:**
- Single execution queue
- Locking around execution
- No parallel workers

**Violation Handling:**
- Task enqueue rejected
- Logged as concurrency violation

---

### LAW 11 — TRANSACTIONAL STEPS

**Primary Enforcement Modules:**
- `orchestrator/step_runner.py`

**Enforcement Mechanisms:**
- Step lifecycle enforced
- Commit only on verification
- Rollback on failure

**Violation Handling:**
- Task aborted
- State marked incomplete

---

### LAW 12 — FAILURE TRANSPARENCY

**Primary Enforcement Modules:**
- `system/failure_handler.py`
- `audit/audit_logger.py`
- `notifications/notification_manager.py` (Phase 15 failure notifications)
- `cli/cli.py` / `api/http_handler.py` (surface failures)

**Enforcement Mechanisms:**
- All failures logged
- User notification mandatory via Notification Manager
- No silent retries

**Violation Handling:**
- System halt until user acknowledgment

---

### LAW 13 — COMPLETE AUDITABILITY

**Primary Enforcement Modules:**
- `audit/audit_logger.py`
- `notifications/notification_store.py` (persisted notification history)
- `mcp/authorization_layer.py`
- `orchestrator/orchestrator.py`

**Enforcement Mechanisms:**
- Immutable log entries
- Correlated request IDs
- End-to-end traceability
- All user notifications persisted

**Violation Handling:**
- Action blocked
- Audit failure raised

---

### LAW 14 — LOG RETENTION DISCIPLINE

**Primary Enforcement Modules:**
- `audit/` (retention to be implemented; Phase 11+)
- `notifications/notification_store.py` (cleanup_old logic)
- `automations/` (timers in later phase)

**Enforcement Mechanisms:**
- Time-based log expiry
- Mandatory summarization
- Configurable retention policy
- Notification tools enforce cleanup confirmation

**Violation Handling:**
- Storage quota exceeded alertsenance alert issued

---

### LAW 15 — SECRET ISOLATION

**Primary Enforcement Modules:**
- `security/` (secret handling; to be expanded when integrations land)
- `sync/supabase_client.py` (Phase 13)

**Enforcement Mechanisms:**
- Secrets loaded at runtime only
- Never injected into prompts
- Never logged
- `SupabaseClient.get_connection_info()` excludes credentials
- `test_law_15_no_secrets_in_logs` verifies API key isolation

**Violation Handling:**
- Immediate abort
- Security incident recorded

---

### LAW 16 — NETWORK EXPLICITNESS

**Primary Enforcement Modules:**
- `security/` (network guard; to be expanded in Phase 11)
- `mcp/tool_schema.py` (network permission metadata; to be added)
- `sync/supabase_client.py` (Phase 13 - explicit connection)
- `sync/sync_queue.py` (Phase 13 - offline queue)
- `sync/sync_manager.py` (Phase 13 - explicit sync)
- `voice/stt_engine.py` (Phase 16 - Google Speech Recognition requires network)

**Enforcement Mechanisms:**
- Allow-list enforced
- No implicit outbound calls
- Offline-first default
- Network access declared per tool (explicit permissions)
- Network access depends on tool functionality
- MCP protocol transport: STDIO (local) and HTTP (remote via `pc_mcp_client`)
- `SyncQueue` queues operations for offline-first processing
- `SupabaseClient.connect()` is explicit, never auto-connects
- `STTEngine` checks for network before calling Google API (graceful failover needed)

**Violation Handling:**
- Network request blocked
- Logged as violation

---

### LAW 17 — NO ARCHITECTURAL DRIFT

**Primary Enforcement Modules:**
- `tests/` + docs discipline (future CI/static checks)

**Enforcement Mechanisms:**
- Static analysis rules
- CI checks (future)
- Module boundary enforcement

**Violation Handling:**
- Build rejected
- Manual override required

---

### LAW 18 — FORWARD COMPATIBILITY

**Primary Enforcement Modules:**
- `config/` (schema + versioning policies)

**Enforcement Mechanisms:**
- Versioned configs
- Backward compatibility checks
- Explicit migrations only

**Violation Handling:**
- Upgrade blocked
- Migration required

---

### LAW 19 — INTERFACE CONSISTENCY

**Primary Enforcement Modules:**
- `cli/cli.py`
- `api/api_server.py`
- `web/web_server.py`
- `pc_mcp_client/` (first-party PC MCP CLI client; implemented with STDIO/HTTP)
- `service_main.py` (composition root wiring)

**Enforcement Mechanisms:**
- CLI, API, and Web connect to MCP Server internally
- All interfaces expose identical functionality
- Interface synchronization checks
- No interface-specific privilege escalation
- MCP Server is the single source of truth for tool capabilities

**Violation Handling:**
- Interface functionality must be synchronized
- Discrepancies must be resolved immediately
- Logged as architectural violation
- Interface access blocked until synchronization restored

---

---

## 3B. v1.0.1 ENHANCEMENT LAW MAPPINGS (PHASES 20–23)

---

### LAW 20 — POST-HOC EXPLANATION ONLY

**Primary Enforcement Modules:**
- `audit/explanation_service.py` (Phase 20)
- `tools/explanation_tools.py` (Phase 20)
- `audit/audit_logger.py`

**Enforcement Mechanisms:**
- Explanations derived from audit logs only
- No state mutation during explanation generation
- Explanation tool is read-only (no side effects)
- Confidence score reflects data availability

**Violation Handling:**
- Explanation refused if data insufficient
- "Explanation unavailable" response returned
- No speculative reasoning permitted

---

### LAW 21 — USER-DECLARED INTENT SUPREMACY

**Primary Enforcement Modules:**
- `core/intent_mode.py` (Phase 21)
- `orchestrator/orchestrator.py`
- `mcp/mcp_server.py`
- CLI/Web/TUI interfaces (LAW 19 parity)

**Enforcement Mechanisms:**
- Intent mode must be explicitly declared in request
- Default to `informational` if unspecified
- AI parser forbidden from inferring intent mode
- Intent mode logged with every request

**Violation Handling:**
- AI-inferred intent rejected
- Request blocked if intent mode invalid
- Logged as policy violation

---

### LAW 22 — MEMORY QUALITY PRESERVATION

**Primary Enforcement Modules:**
- `memory/memory_quality.py` (Phase 22)
- `memory/memory_summarizer.py` (Phase 22)
- `memory/tier_manager.py`
- `memory/database_schema.py`

**Enforcement Mechanisms:**
- Confidence decay is deterministic (configurable rate)
- Summarization triggered at threshold
- Lineage preserved through parent_memory_id
- Direct deletion blocked (must summarize first)

**Violation Handling:**
- Delete without summary rejected
- Lineage missing flagged as error
- Memory write without orchestrator rejected

---

### LAW 23 — OBSERVABILITY WITHOUT CONTROL

**Primary Enforcement Modules:**
- `system/observability_service.py` (Phase 23)
- `tools/observability_tools.py` (Phase 23)
- CLI/Web/TUI interfaces (LAW 19 parity)

**Enforcement Mechanisms:**
- `get_system_posture` tool is read-only
- No execution triggers exposed
- Identical data across all interfaces
- Works offline (LAW 16)

**Violation Handling:**
- Action attempts denied
- Interface drift logged as violation
- Hidden controls rejected

---

---

## 4. FINAL GUARANTEE

If all mappings in this document are implemented and enforced:

- Siya cannot hallucinate execution
- Siya cannot act autonomously
- Siya cannot hide failures
- Siya cannot drift from its laws
- Siya remains understandable to both humans and AI

---

## 5. FINAL DECLARATION

This document completes the Siya documentation set.

From this point forward:
- Any code written is an implementation detail
- Any deviation is a violation
- Any shortcut is a risk

Siya is now **fully specified**.

---

==================== FILE END ====================