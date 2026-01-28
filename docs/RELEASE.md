# RELEASE INFORMATION
## Project: Siya
## Version: 1.0.1

---

## RELEASE SUMMARY

**Release Date:** 2026-01-26  
**Baseline Tag:** `v1.0.0-baseline`  
**Status:** Production Baseline  
**Deployment Date:** 2026-01-27  
**Deployment Status:** ✅ Deployed and Operational on Raspberry Pi 5

---

## WHAT'S INCLUDED

### Core Components
- ✅ Orchestration engine (Phase 1)
- ✅ Model Control Plane (Phase 2)
- ✅ Memory & Observability (Phase 3)
- ✅ AI Integration (Phase 10 - Real llama.cpp)
- ✅ Interfaces (Phase 17 - Web/CLI Parity)
- ✅ Automation Framework (Phase 14 - Systemd Timers)
- ✅ Failure Handling (Phase 8)
- ✅ Voice Interface (Phase 16)
- ✅ Supabase Sync (Phase 13)

### Locked Components
- **Schema Version:** 1.0.0
- **Tool Registry:** Populated (Phase 11)
- **Python Version:** 3.11.9 (compatible with 3.11-3.12)

---

## DEPLOYMENT

See `DEPLOYMENT.md` for complete deployment instructions.

---

## RECOVERY

See `RECOVERY_CHECKLIST.md` for recovery procedures.

---

## KNOWN LIMITATIONS

### Hardware Requirements
- Raspberry Pi 5 (8 GB RAM minimum)
- Full testing requires Pi hardware

### Performance
- AI Inference: 10-30s latency per query
- Boot time: ~15s cold start

---

## CHANGELOG

### v1.0.0-baseline (2026-01-26)

**Initial Production Baseline**

- Phase 0: Foundation & Tooling
- Phase 1: Core Runtime Skeleton
- Phase 2: Governance & Control Plane
- Phase 3: Memory & Observability
- Phase 5: AI Integration (Controlled)
- Phase 6: Interfaces & UX Layer
- Phase 7: Automation & Scheduling
- Phase 8: Failure Injection & Hardening

---

## SUPPORT

For issues or questions:
1. Check `RECOVERY_CHECKLIST.md`
2. Review audit logs
3. Check system documentation

---

## PLANNED RELEASES

### v1.0.1 (Implemented)

**Status:** ✅ Complete  
**Release Date:** 2026-01-28  
**Features:**
- Phase 20: Decision Explanation Layer (LAW 20) ✅
- Phase 21: Explicit User Intent Modes (LAW 21) ✅
- Phase 22: Memory Quality Control (LAW 22) ✅
- Phase 23: Operator Observability Dashboard (LAW 23) ✅

**Pre-Release Checklist:**
- [x] All test cases pass
- [x] No schema changes break v1.0.0
- [x] No new background services
- [x] RAM usage unchanged at idle
- [x] CPU idle load unchanged
- [x] Offline mode verified
- [x] Logs show new features dormant by default
- [x] Version tagged (v1.0.1)
- [x] Rollback snapshot taken

**Rollback Triggers:**
- Law violation detected
- Memory corruption
- Interface inconsistency
- Performance regression

**Rollback Steps:**
1. Stop Siya services
2. Restore previous release snapshot
3. Restore SQLite DB backup
4. Clear sync queue (do not replay)
5. Restart services
6. Notify user explicitly
7. Log rollback event

---

**Last Updated:** 2026-01-28  
**Deployment Status:** ✅ v1.0.1 Deployed

