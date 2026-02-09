==================== FILE START ====================

# CANONICAL SYSTEM LAWS  
## Project: Siya

---

## 1. PURPOSE OF THIS DOCUMENT

This document defines the **absolute, immutable laws** that govern the design, behavior, execution, and evolution of the Siya system.

These laws exist to:
- Constrain AI behavior
- Prevent hallucinations
- Prevent authority drift
- Preserve determinism
- Guarantee user sovereignty

These laws are **above**:
- Requirements
- Implementations
- Optimizations
- Convenience

If any component violates a law in this document, that component is **invalid by definition**.

**OpenClaw-inspired work:** Any capability adopted or adapted from OpenClaw (see `docs/EVOLUTION_ROADMAP.md`) must comply with these laws; no exception.

---

## 2. LAW HIERARCHY

The laws are ordered by **precedence**.

Higher-numbered laws may never override lower-numbered laws.

---

## 3. PRIMARY CONSTITUTIONAL LAWS

---

### LAW 1 — HUMAN SOVEREIGNTY

**The human user is the final and absolute authority.**

- No component may override user intent
- No component may reinterpret intent without confirmation
- No component may act “on behalf of” the user autonomously

This law overrides all others.

---

### LAW 2 — NO AUTONOMOUS EXECUTION

**The system shall never initiate real-world actions without an explicit trigger.**

Valid triggers are:
- Direct user input
- Registered scheduled events
- Explicit system events approved by the user

Background autonomy is forbidden.

---

### LAW 3 — LLM IS A CONTROLLED PROCESSOR

**The Large Language Model (LLM) is a parser, explainer, and content processor, but never an autonomous executor.**

The LLM may:
- Interpret intent
- Extract arguments
- Generate explanations
- Produce minimal user-facing text
- Process content (e.g., summarize text, extract information, transform data) when explicitly invoked by a tool execution flow
- Transform or filter data as part of a tool's execution pipeline

The LLM may never:
- Execute tools autonomously
- Decide policies
- Override permissions
- Initiate actions without explicit tool invocation
- Access secrets or sensitive data directly
- Process content outside of explicit tool execution flows

**Content Processing Constraints:**
- Content processing must occur within a tool execution context
- All AI-processed content must be logged and auditable (LAW 13)
- AI model runs locally only (no cloud inference for security)
- Content processing is subject to the same permission and confirmation requirements as tool execution (LAW 5)

---

### LAW 4 — TOOL-ONLY EXECUTION

**All side effects must occur exclusively through explicitly declared tools.**

- No implicit execution paths
- No hidden side effects
- No compound or multi-action tools

One tool equals one real-world effect.

---

### LAW 5 — EXPLICIT PERMISSIONS

**Every tool that causes a side effect must require explicit permission.**

- Permissions are tool-scoped
- There are no global permissions
- Permission escalation is forbidden

Default stance: **deny**.

---

### LAW 6 — NO FREE-FORM COMPUTATION

**Dynamic code execution is forbidden.**

This includes:
- Shell passthrough
- Eval or reflection-based execution
- Generated scripts
- Recursive tool invocation without orchestration control

All computation must be pre-declared and bounded.

---

---

## 4. MEMORY GOVERNANCE LAWS

---

### LAW 7 — MEMORY IS NON-AUTHORITATIVE

**Memory may inform, but never decide.**

Memory must never:
- Select tools
- Branch execution
- Override logic
- Bypass permissions

Memory exists only to support the user and explain context.

---

### LAW 8 — MEMORY WRITE CONTROL

**Only the orchestration layer may write to memory.**

- The LLM may suggest memory content
- MCP may not write memory
- Tools may not write memory directly

All memory writes are explicit and logged.

---

### LAW 9 — MEMORY DEGRADATION CONTROL

**Memory must decay through summarization, not deletion.**

- Raw logs expire
- Summaries persist
- Lineage must be preserved

Memory must never grow unbounded.

---

---

## 5. EXECUTION & ORCHESTRATION LAWS

---

### LAW 10 — SERIAL EXECUTION

**Only one automation or task may execute at a time.**

- No parallel execution
- No preemption
- No interruption

Predictability is valued over throughput.

---

### LAW 11 — TRANSACTIONAL STEPS

**Every task must be executed as a sequence of explicit steps.**

Each step must:
- Be independently verifiable
- Have clear failure boundaries
- Be logged before and after execution

---

### LAW 12 — FAILURE TRANSPARENCY

**No failure may be silent.**

On failure:
1. Retry (if safe)
2. Notify the user
3. Await instruction

Guessing or silent recovery is forbidden.

---

---

## 6. OBSERVABILITY & LOGGING LAWS

---

### LAW 13 — COMPLETE AUDITABILITY

**Every action must be observable and traceable.**

This includes:
- Inputs
- Tool calls
- Permissions
- Confirmations
- Failures
- Outcomes

Logs are mandatory.

---

### LAW 14 — LOG RETENTION DISCIPLINE

**Logs must be retained, summarized, and expired according to policy.**

- Raw logs are temporary
- Summaries are persistent
- Nothing is silently discarded

---

---

## 7. SECURITY & ISOLATION LAWS

---

### LAW 15 — SECRET ISOLATION

**Secrets must never be visible to the LLM.**

- No direct access
- No indirect leakage
- No prompt injection exposure

Secrets exist outside AI visibility.

---

### LAW 16 — NETWORK EXPLICITNESS

**Network access must be explicitly declared and allowed.**

- No implicit outbound access
- No background calls
- No undisclosed dependencies

Offline operation is the default.

---

---

## 8. SYSTEM EVOLUTION LAWS

---

### LAW 17 — NO ARCHITECTURAL DRIFT

**No feature may violate existing laws to enable convenience.**

If a feature requires breaking a law, the feature is invalid.

---

### LAW 18 — FORWARD COMPATIBILITY

**All designs must allow future extension without refactoring core laws.**

Scalability must be achieved through configuration, not redesign.

---

### LAW 19 — INTERFACE CONSISTENCY

**All user-facing interfaces (CLI, API, Web) must expose identical functionality and remain synchronized with the MCP Server.**

- CLI, HTTP API, and Web interface are clients of the MCP Server
- All interfaces must reflect the same tool capabilities, resources, and behaviors
- No interface may have privileged access or different behavior
- Interface implementations must stay up-to-date with MCP Server changes
- Any discrepancy between interfaces is a violation

This law ensures:
- No interface drift
- Consistent user experience
- No hidden capabilities in any interface
- Maintainability and clarity

**Violation Handling:**
- Interface functionality must be synchronized
- Discrepancies must be resolved immediately
- Logged as architectural violation

---

## 8B. v1.0.1 ENHANCEMENT LAWS (PHASES 20–23)

---

### LAW 20 — POST-HOC EXPLANATION ONLY

**System explanations must reflect reality, not influence it.**

Explanations must:
- Reflect actual logged decisions
- Never influence execution
- Never introduce new logic
- Never mask uncertainty

If an explanation cannot be generated truthfully, the system must respond:
> "Explanation unavailable due to insufficient data."

Explanations are derived from audit logs, never speculated.

---

### LAW 21 — USER-DECLARED INTENT SUPREMACY

**Intent posture must be explicitly declared, never inferred.**

Intent posture:
- Must be explicitly declared by the user
- Must never be inferred by AI
- May only constrain, never expand, permissions

Valid intent modes:
- `informational` (default) — read-only queries
- `operational` — normal permission flow
- `destructive` — extra confirmation required

The system may restrict tools based on intent mode but may never skip confirmations or escalate permissions.

---

### LAW 22 — MEMORY QUALITY PRESERVATION

**Memory must decay gracefully, never disappear abruptly.**

Memory systems must:
- Degrade confidence before summarization
- Preserve lineage through all transformations
- Never delete without a summarized successor

Confidence decay is deterministic and configurable.
Summarization is logged and trigger is auditable.
AI may suggest summarization; Orchestrator decides.

---

### LAW 23 — OBSERVABILITY WITHOUT CONTROL

**Observability interfaces must be read-only.**

Observability interfaces:
- Must be read-only
- Must not expose execution triggers
- Must not bypass MCP
- Must not alter state

All interfaces (CLI, Web, API) must expose identical operator data.
No privileged interface is allowed (LAW 19 enforced).

---

---

## 9. AI-SPECIFIC ENFORCEMENT GUIDELINES

These guidelines are binding for AI behavior:

- Never assume authority
- Never infer permissions
- Never invent tools
- Never repair malformed outputs silently
- Always prefer clarification over action

---

## 10. FINAL DECLARATION

These laws define Siya’s identity.

They are not suggestions.  
They are not preferences.  
They are constraints.

Any system that violates these laws is **not Siya**, regardless of naming.

---

==================== FILE END ====================