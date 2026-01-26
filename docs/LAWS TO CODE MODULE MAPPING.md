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
- `interfaces/*`
- `core/orchestrator/decision_gate.py`

**Enforcement Mechanisms:**
- All actions originate from explicit user or registered triggers
- Orchestrator requires confirmation tokens before execution
- No automatic override paths

**Violation Handling:**
- Action rejected
- Logged as critical violation
- User notified

---

### LAW 2 — NO AUTONOMOUS EXECUTION

**Primary Enforcement Modules:**
- `core/orchestrator/task_queue.py`
- `system/timers/`

**Enforcement Mechanisms:**
- Task queue only accepts registered triggers
- Background loops forbidden
- systemd timers must be explicitly declared

**Violation Handling:**
- Task not enqueued
- Security log entry created

---

### LAW 3 — LLM IS NOT AN AGENT

**Primary Enforcement Modules:**
- `core/ai/intent_parser.py`
- `core/mcp/request_validator.py`

**Enforcement Mechanisms:**
- LLM outputs are data-only
- No execution hooks exist in AI layer
- AI process runs in isolated subprocess

**Violation Handling:**
- Output rejected
- Clarification requested
- AI restarted if necessary

---

### LAW 4 — TOOL-ONLY EXECUTION

**Primary Enforcement Modules:**
- `core/tools/registry.py`
- `core/mcp/authorization_layer.py`

**Enforcement Mechanisms:**
- Only registered tools callable
- Tool registry is static
- No direct OS access outside tools

**Violation Handling:**
- Execution blocked
- Logged as policy violation

---

### LAW 5 — EXPLICIT PERMISSIONS

**Primary Enforcement Modules:**
- `core/mcp/policy_engine.py`
- `interfaces/*/confirmation_handler.py`

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
- `core/security/execution_guard.py`

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
- `core/memory/access_layer.py`

**Enforcement Mechanisms:**
- Memory is read-only to AI
- Memory cannot influence tool selection
- No branching logic reads memory state

**Violation Handling:**
- Logic blocked
- Logged as architectural violation

---

### LAW 8 — MEMORY WRITE CONTROL

**Primary Enforcement Modules:**
- `core/memory/write_controller.py`

**Enforcement Mechanisms:**
- Only orchestrator can write
- Write operations require explicit call
- Memory writes logged and tagged

**Violation Handling:**
- Write rejected
- Audit event created

---

### LAW 9 — MEMORY DEGRADATION CONTROL

**Primary Enforcement Modules:**
- `core/memory/summarizer.py`
- `system/timers/memory_maintenance.timer`

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
- `core/orchestrator/task_queue.py`

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
- `core/orchestrator/step_runner.py`

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
- `core/logging/failure_logger.py`
- `interfaces/*/notification_dispatcher.py`

**Enforcement Mechanisms:**
- All failures logged
- User notification mandatory
- No silent retries

**Violation Handling:**
- System halt until user acknowledgment

---

### LAW 13 — COMPLETE AUDITABILITY

**Primary Enforcement Modules:**
- `core/logging/audit_logger.py`

**Enforcement Mechanisms:**
- Immutable log entries
- Correlated request IDs
- End-to-end traceability

**Violation Handling:**
- Action blocked
- Audit failure raised

---

### LAW 14 — LOG RETENTION DISCIPLINE

**Primary Enforcement Modules:**
- `core/logging/log_retention.py`
- `system/timers/log_maintenance.timer`

**Enforcement Mechanisms:**
- Time-based log expiry
- Mandatory summarization
- Configurable retention policy

**Violation Handling:**
- Logging halted
- Maintenance alert issued

---

### LAW 15 — SECRET ISOLATION

**Primary Enforcement Modules:**
- `core/security/secret_manager.py`

**Enforcement Mechanisms:**
- Secrets loaded at runtime only
- Never injected into prompts
- Never logged

**Violation Handling:**
- Immediate abort
- Security incident recorded

---

### LAW 16 — NETWORK EXPLICITNESS

**Primary Enforcement Modules:**
- `core/security/network_guard.py`

**Enforcement Mechanisms:**
- Allow-list enforced
- No implicit outbound calls
- Offline-first default

**Violation Handling:**
- Network request blocked
- Logged as violation

---

### LAW 17 — NO ARCHITECTURAL DRIFT

**Primary Enforcement Modules:**
- `core/validation/architecture_checker.py`

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
- `config/schema_versioning.py`

**Enforcement Mechanisms:**
- Versioned configs
- Backward compatibility checks
- Explicit migrations only

**Violation Handling:**
- Upgrade blocked
- Migration required

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