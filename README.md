# Siya
## Local-First Personal Governance and Assistant Operating System

---

## PROJECT STATUS

**Status:** ✅ PRODUCTION BASELINE COMPLETE  
**Baseline Version:** 1.0.0  
**Release Tag:** `v1.0.0-baseline`  
**Production Lock:** ✅ FINALIZED

**Completed Phases:** 0, 1, 2, 3, 5, 6, 7, 8, 9, 10  
**In Progress:** Phase 11 (Tool Implementations - Pending)  
**Deferred Phases:** 4A, 4 (require Raspberry Pi hardware)

**Completed Phases:**
- ✅ Phase 0 — Foundation & Tooling
- ✅ Phase 1 — Core Runtime Skeleton (No AI)
- ✅ Phase 2 — Governance & Control Plane
- ✅ Phase 3 — Memory & Observability
- ✅ Phase 5 — AI Integration (Controlled)
- ✅ Phase 6 — Interfaces & UX Layer
- ✅ Phase 7 — Automation & Scheduling
- ✅ Phase 8 — Failure Injection & Hardening
- ✅ Phase 9 — Production Lock & Baseline

**Completed (Continued):**
- ✅ Phase 10 — Real AI Model Integration (Operational - 10-30s response time)

**Deployment Status:**
- ✅ Deployed to Raspberry Pi 5
- ✅ API server running (port 8080)
- ✅ Web interface running (port 3000)
- ✅ Network access configured
- ✅ systemd service active
- ✅ AI model operational (Qwen 2.5 3B, 10-30s response time)

---

## WHAT IS SIYA?

Siya is a **local-first personal governance and assistant operating system**, designed to run primarily on a **Raspberry Pi 5 (8 GB)**, providing deterministic control, automation, and intelligence assistance to a single user.

**Siya operates as a Model Context Protocol (MCP) Server**, exposing tools and resources to MCP clients (e.g., Claude Desktop on PC). The Pi server maintains context of all integrations (mails, third-party services) and processes user requests through controlled AI content processing within tool execution flows.

Siya uses artificial intelligence as an **interpretive, explanatory, and content processing component** within explicit tool execution contexts, never as an autonomous decision-maker or executor. All real-world actions are executed exclusively through deterministic, permission-gated tools under explicit user control.

---

## CORE PHILOSOPHY

> **Intelligence may assist, but authority must remain human and explicit.**

This philosophy is enforced architecturally rather than through prompts or trust.

---

## DOCUMENTATION

All authoritative documentation is in the `docs/` directory:

- **PRE PLANNING DEFINITION DOCUMENT.md** — Problem space, intent, scope
- **BUSINESS REQUIREMENTS DOCUMENT.md** — Business and functional requirements
- **CANONICAL SYSTEM LAWS.md** — Immutable system laws (19 laws)
- **DETAILED IMPLEMENTATION PLAN.md** — Phase-by-phase implementation guide
- **FINAL PROJECT DESCRIPTION.md** — Complete system overview
- **LAWS TO CODE MODULE MAPPING.md** — Law enforcement mapping
- **TECHNICAL REQUIREMENTS DOCUMENT.md** — Technical specifications
- **System Prompt.md** — AI component constraints
- **system_schema.json** — Canonical JSON schema (binding)
- **SYSTEM_SCHEMA_VERIFICATION_REPORT.md** — Schema verification report
- **DEPLOYMENT.md** — Complete deployment guide (includes GitHub setup, network access)
- **AI_MODEL_GUIDE.md** — Complete AI model guide (setup, testing, optimization, selection)
- **EXAMPLE_COMMANDS.md** — Example commands for testing from PC
- **NEXT_PHASES_ROADMAP.md** — Post-baseline implementation roadmap (Phases 11-15)
- **System Prompt.md** — AI system prompt (authoritative, auto-loaded by intent parser)

---

## DEVELOPMENT RULES

See `.cursor/rules/dev-rules.mdc` for complete development discipline.

**Key Principles:**
- Correctness > Elegance
- Explicitness > Cleverness
- Traceability > Convenience
- Law compliance is mandatory

---

## IMPLEMENTATION PHASES

Implementation follows strict sequential phases (see DETAILED IMPLEMENTATION PLAN):

0. **Foundation & Tooling** ✅ — Development environment setup
1. **Core Runtime Skeleton** ✅ — Deterministic execution backbone (no AI)
2. **Governance & Control Plane** ✅ — MCP, permissions, law enforcement
3. **Memory & Observability** ✅ — SQLite, logging, memory governance
4A. **Raspberry Pi Base Provisioning** ✅ — Pi setup and hardening (completed)
4. **Pi Mirroring & Validation** — Read-only validation (hardware - optional)
5. **AI Integration (Controlled)** ✅ — Intent parsing, schema enforcement (stub)
6. **Interfaces & UX Layer** ✅ — CLI, API, web interface
7. **Automation & Scheduling** ✅ — Automation modules, serial execution (framework)
8. **Failure Injection & Hardening** ✅ — Failure testing and recovery
9. **Production Lock & Baseline** ✅ — Final baseline and deployment
10. **Real AI Model Integration** ✅ — llama.cpp integration (Operational, 10-30s response time)
11. **Tool Implementations** ⏳ — Actual tool executions
12. **Supabase Synchronization** ⏳ — L3 memory sync
13. **systemd Timer Integration** ⏳ — Scheduled automations
14. **Enhanced User Notifications** ⏳ — Notification system
15. **Voice Interface** ⏳ — Voice input/output (optional)

---

## SYSTEM SCHEMA

The canonical system schema (`docs/system_schema.json`) defines all system outputs:

- AI Intent Parsing Output
- Tool Request
- Error Response
- Confirmation Request
- Memory Write Suggestion
- Audit Log Entry
- Orchestration Step Report

**All outputs must conform to this schema. It is binding.**

---

## CANONICAL SYSTEM LAWS

Siya operates under 19 immutable laws (see CANONICAL SYSTEM LAWS.md):

1. Human Sovereignty
2. No Autonomous Execution
3. LLM Is A Controlled Processor (updated: allows content processing within tool execution flows)
4. Tool-Only Execution
5. Explicit Permissions
6. No Free-Form Computation
7. Memory Is Non-Authoritative
8. Memory Write Control
9. Memory Degradation Control
10. Serial Execution
11. Transactional Steps
12. Failure Transparency
13. Complete Auditability
14. Log Retention Discipline
15. Secret Isolation
16. Network Explicitness
17. No Architectural Drift
18. Forward Compatibility
19. Interface Consistency (new: CLI/API/Web must match MCP Server)

---

## PC MCP CLI CLIENT (FIRST-PARTY)

Siya includes a planned **first-party PC MCP CLI client** that replicates Claude-like MCP client behavior:
- MCP lifecycle: `initialize` → `notifications/initialized`
- Tool discovery: `tools/list`
- Tool invocation: `tools/call`

Claude Desktop / Claude Code are optional external MCP clients for compatibility testing; the first-party PC client is the primary long-term interface.

## DEVELOPMENT ENVIRONMENT

**Target Hardware:** Raspberry Pi 5 (8 GB RAM) ✅ Deployed  
**Primary Development:** PC (Windows/Linux/Mac)  
**Language:** Python 3.13.5 (compatible with 3.11+)  
**AI Runtime:** llama.cpp (CPU-only, quantized models) ✅ Operational (Qwen 2.5 3B, 10-30s response time)

---

## GETTING STARTED

1. Read all documentation in `docs/`
2. Review `.cursor/rules/dev-rules.mdc`
3. Understand Canonical System Laws
4. Follow Detailed Implementation Plan strictly
5. Never skip phases

---

## LICENSE

[To be determined]

---

## CONTACT

[To be determined]

---

**Last Updated:** 2026-01-27  
**Schema Version:** 1.0.0 (Locked)  
**Project Status:** ✅ PRODUCTION BASELINE COMPLETE (v1.0.0)  
**Deployment Status:** ✅ DEPLOYED AND RUNNING ON RASPBERRY PI 5  
**Phase 10 Status:** ✅ COMPLETE — AI Model Operational (10-30s response time)  
**Current Phase:** Phase 11 — Tool Implementations (Pending)
