# Siya
## Local-First Personal Governance and Assistant Operating System

---

## PROJECT STATUS

**Status:** ✅ SYSTEM 1.0 COMPLETE (ALL PHASES)  
**Baseline Version:** 1.0.0  
**Deployment:** ✅ RASPBERRY PI 5  
**AI Readiness:** ✅ OPERATIONAL (10-30s response)  
**Tools:** ✅ 26+ CORE TOOLS IMPLEMENTED  
**Tests:** ✅ 107+ UNIT TESTS PASSING

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
- **EXAMPLE_COMMANDS.md** — Examples for testing 26+ tools

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
12. **System Context & Memory** ✅ (SystemContext, ContextManager, TierManager)
13. **Supabase Synchronization** ✅ (L3 cloud sync, offline-first)
14. **systemd Timer Integration** ✅ (Scheduled automations)
15. **Enhanced User Notifications** ✅ (Multi-channel + persistence)
16. **Voice Interface** ✅ (TTS/STT, Tools)
17. **Web Interface Redesign** ✅ (Neo-Brutalism, Full CLI Parity)
18. **Full-Screen TUI** ✅ (Textual UI, LAW 19)
19. **Interface Consistency** ✅ (LAW 19 Enforcement)

### v1.0.1 Enhancements (Completed)
20. **Decision Explanation Layer** ✅ Core Complete (LAW 20)
21. **Explicit User Intent Modes** ✅ Core Complete (LAW 21)
22. **Memory Quality Control** ✅ Core Complete (LAW 22)
23. **Operator Observability Dashboard** ✅ Core Complete (LAW 23)

---

## REMOTE GOVERNANCE

Siya can be governed remotely from your PC via the **PC MCP Client**:
```bash
siya-cli --transport http --url http://<PI_IP>:8080 list-tools
```

---

**Last Updated:** 2026-01-26  
**Schema Version:** 1.0.1 (v1.0.1 spec implemented)  
**Project Status:** ✅ v1.0.1 COMPLETE (ALL PHASES)  
**Current Phase:** Maintenance & Optimization
  

