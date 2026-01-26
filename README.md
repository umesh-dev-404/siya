# Siya
## Local-First Personal Governance and Assistant Operating System

---

## PROJECT STATUS

**Status:** ✅ PRODUCTION BASELINE COMPLETE  
**Baseline Version:** 1.0.0  
**Release Tag:** `v1.0.0-baseline`  
**Production Lock:** ✅ FINALIZED

**Completed Phases:** 0, 1, 2, 3, 5, 6, 7, 8, 9  
**Deferred Phases:** 4A, 4 (require Raspberry Pi hardware)

**Completed Phases:**
- ✅ Phase 0 — Foundation & Tooling
- ✅ Phase 1 — Core Runtime Skeleton (No AI)

---

## WHAT IS SIYA?

Siya is a **local-first personal governance and assistant operating system**, designed to run primarily on a **Raspberry Pi 5 (8 GB)**, providing deterministic control, automation, and intelligence assistance to a single user.

Siya uses artificial intelligence **only as an interpretive and explanatory component**, never as an autonomous decision-maker or executor. All real-world actions are executed exclusively through deterministic, permission-gated tools under explicit user control.

---

## CORE PHILOSOPHY

> **Intelligence may assist, but authority must remain human and explicit.**

This philosophy is enforced architecturally rather than through prompts or trust.

---

## DOCUMENTATION

All authoritative documentation is in the `docs/` directory:

- **PRE PLANNING DEFINITION DOCUMENT.md** — Problem space, intent, scope
- **BUSINESS REQUIREMENTS DOCUMENT.md** — Business and functional requirements
- **CANONICAL SYSTEM LAWS.md** — Immutable system laws (18 laws)
- **DETAILED IMPLEMENTATION PLAN.md** — Phase-by-phase implementation guide
- **FINAL PROJECT DESCRIPTION.md** — Complete system overview
- **LAWS TO CODE MODULE MAPPING.md** — Law enforcement mapping
- **TECHNICAL REQUIREMENTS DOCUMENT.md** — Technical specifications
- **System Prompt.md** — AI component constraints
- **system_schema.json** — Canonical JSON schema (binding)
- **SYSTEM_SCHEMA_VERIFICATION_REPORT.md** — Schema verification report

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
4A. **Raspberry Pi Base Provisioning** — Pi setup and hardening (hardware)
4. **Pi Mirroring & Validation** — Read-only validation (hardware)
5. **AI Integration (Controlled)** ✅ — Intent parsing, schema enforcement
6. **Interfaces & UX Layer** ✅ — CLI, API, web interface
7. **Automation & Scheduling** ✅ — Automation modules, serial execution
8. **Failure Injection & Hardening** ✅ — Failure testing and recovery
9. **Production Lock & Baseline** ✅ — Final baseline and deployment
3. **Memory & Observability** — SQLite, logging, memory governance
4A. **Raspberry Pi Base Provisioning** — Pi setup and hardening
4. **Pi Mirroring & Validation** — Architecture validation on Pi
5. **AI Integration** — Controlled AI as intent parser
6. **Interfaces & UX Layer** — CLI, API, web interface
7. **Automation & Scheduling** — Automation modules, systemd timers
8. **Failure Injection & Hardening** — Failure testing and recovery
9. **Production Lock & Baseline** — Final baseline and deployment

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

Siya operates under 18 immutable laws (see CANONICAL SYSTEM LAWS.md):

1. Human Sovereignty
2. No Autonomous Execution
3. LLM Is Not An Agent
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

---

## DEVELOPMENT ENVIRONMENT

**Target Hardware:** Raspberry Pi 5 (8 GB RAM)  
**Primary Development:** PC (Windows/Linux/Mac)  
**Language:** Python  
**AI Runtime:** llama.cpp (CPU-only, quantized models)

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

**Last Updated:** 2026-01-26  
**Schema Version:** 1.0.0  
**Project Status:** ✅ PRODUCTION BASELINE COMPLETE (v1.0.0)
