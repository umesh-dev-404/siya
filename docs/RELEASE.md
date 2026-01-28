# RELEASE INFORMATION
## Project: Siya
## Version: 1.0.0 (Baseline)

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

**Last Updated:** 2026-01-27  
**Deployment Status:** ✅ Deployed and Operational
