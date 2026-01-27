# Siya
## Local-First Personal Governance and Assistant Operating System

---

## PROJECT STATUS

**Status:** ✅ PHASE 11 COMPLETE — AI & TOOLS OPERATIONAL  
**Baseline Version:** 1.0.0  
**Deployment:** ✅ RASPBERRY PI 5  
**AI Readiness:** ✅ OPERATIONAL (10-30s response)  
**Tools:** ✅ 13+ CORE TOOLS IMPLEMENTED

---

## WHAT IS SIYA?

Siya is a **local-first personal governance and assistant operating system**, designed to run primarily on a **Raspberry Pi 5 (8 GB)**, providing deterministic control, automation, and intelligence assistance to a single user.

**Siya operates as a Model Context Protocol (MCP) Server**, exposing tools and resources to MCP clients. The system enforces **Human Sovereignty (LAW 1)** via explicit confirmation flows for all sensitive actions (`WRITE`/`EXECUTE`).

---

## CORE PHILOSOPHY

> **Intelligence may assist, but authority must remain human and explicit.**

This philosophy is enforced architecturally rather than through prompts or trust.

---

## DOCUMENTATION

All authoritative documentation is in the `docs/` directory:

- **PROJECT_STATUS.md** — Latest implementation progress
- **CANONICAL SYSTEM LAWS.md** — Immutable system laws (19 laws)
- **DEPLOYMENT.md** — Complete deployment guide (includes PC-to-Pi bridge)
- **AI_MODEL_GUIDE.md** — AI setup and optimization
- **EXAMPLE_COMMANDS.md** — Examples for testing 13+ tools
- **NEXT_PHASES_ROADMAP.md** — Roadmap for Phases 12-15

---

## IMPLEMENTATION PHASES

0. **Foundation & Tooling** ✅
1. **Core Runtime Skeleton** ✅
2. **Governance & Control Plane** ✅
3. **Memory & Observability** ✅
4. **Pi Mirroring & Validation** ✅
5. **AI Integration (Controlled)** ✅
6. **Interfaces & UX Layer** ✅
7. **Automation & Scheduling** ✅ (Framework)
8. **Failure Injection & Hardening** ✅
9. **Production Lock & Baseline** ✅
10. **Real AI Model Integration** ✅ (Qwen 2.5 3B)
11. **Tool Implementations** ✅ (13+ Tools, LAW 1 active)
12. **Supabase Synchronization** ⏳ (Next)

---

## REMOTE GOVERNANCE

Siya can be governed remotely from your PC via the **PC MCP Client**:
```bash
siya-cli --transport http --url http://<PI_IP>:8080 list-tools
```

---

**Last Updated:** 2026-01-27  
**Schema Version:** 1.0.0 (Locked)  
**Project Status:** ✅ PHASE 11 COMPLETE  
**Current Phase:** Phase 12 — Supabase Synchronization  
