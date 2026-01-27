# NEXT PHASES ROADMAP
## Project: Siya
## Date: 2026-01-27
## Status: Post-Baseline Implementation Plan

---

## OVERVIEW

This document outlines the **next phases of implementation** following the completion of Phase 9 (Production Lock & Baseline) and Phase 4A (Deployment).

**Current Status:**
- ✅ Baseline complete (v1.0.0)
- ✅ System deployed and operational on Raspberry Pi 5
- ⏳ Ready for post-baseline enhancements

---

## PHASE 10 — REAL AI MODEL INTEGRATION

### Priority: HIGH
### Status: ⏳ IN PROGRESS (2026-01-27)

**Objective:** Replace stub AI implementation with real llama.cpp integration.

**Completed Tasks:**
1. ✅ Created `ai/llama_wrapper.py` for llama.cpp integration
2. ✅ Updated `ai/model_manager.py` with real implementation
3. ✅ Updated `ai/intent_parser.py` with real AI inference
4. ✅ Integrated system prompt from `docs/System Prompt.md`
5. ✅ Created model configuration module (`config/model_config.py`)
6. ✅ Implemented auto-detection of model path
7. ✅ Added model auto-loading on service startup
8. ✅ Acquired Qwen 2.5 3B Instruct model (Q4_K_M quantized) ✅
9. ✅ Created comprehensive testing guide (`MODEL_TESTING_GUIDE.md`)
10. ✅ Updated `.gitignore` to exclude model files

**Pending Tasks (Pi):**
1. ⏳ Build llama-cpp-python on Raspberry Pi 5
2. ⏳ Test model loading on Pi
3. ⏳ Test inference and intent parsing
4. ⏳ Verify schema compliance
5. ⏳ Test resource limits and performance

**Success Criteria:**
- Real AI model operational ✅ (code complete)
- Intent parsing produces valid schema-compliant output ⏳ (pending Pi testing)
- RAM usage within Pi constraints (< 4GB for model + system) ⏳ (pending testing)
- Inference latency acceptable (< 5 seconds) ⏳ (pending testing)
- System prompt integrated ✅

**Dependencies:**
- Phase 9 complete ✅
- Phase 4A complete (Pi deployment) ✅

**Estimated Complexity:** Medium-High  
**Current Status:** Code complete, Pi testing pending

---

## PHASE 11 — TOOL IMPLEMENTATIONS

### Priority: HIGH
### Status: ⏳ Pending

**Objective:** Implement actual tool executions replacing framework stubs.

**Key Tasks:**
1. Define tool categories (system, file, automation, memory)
2. Implement core system tools (status, monitoring, logs)
3. Implement file operations (read, write, list, metadata)
4. Implement automation tools (trigger, list, status)
5. Register all tools in tool registry
6. Lock tool registry after registration

**Success Criteria:**
- Core tools implemented and operational
- Permission system enforced
- Confirmation flows working
- All executions auditable

**Dependencies:**
- Phase 10 (for AI-enhanced tool selection)
- Phase 2 (MCP framework)

**Estimated Complexity:** Medium

---

## PHASE 12 — SUPABASE SYNCHRONIZATION

### Priority: MEDIUM
### Status: ⏳ Pending

**Objective:** Implement real Supabase synchronization for L3 memory.

**Key Tasks:**
1. Set up Supabase project and authentication
2. Design L3 memory schema
3. Implement Supabase Python client integration
4. Implement sync-to-Supabase and sync-from-Supabase
5. Handle conflicts (local wins with logging)
6. Implement offline-first operation (queue sync operations)

**Success Criteria:**
- Supabase sync operational
- L3 memory synchronized
- Offline operation works
- Security requirements met (LAW 15)

**Dependencies:**
- Phase 11 (tools for sync operations)
- Supabase account and project

**Estimated Complexity:** Medium

---

## PHASE 13 — SYSTEMD TIMER INTEGRATION

### Priority: MEDIUM
### Status: ⏳ Pending

**Objective:** Integrate systemd timers for scheduled automations.

**Key Tasks:**
1. Design timer configuration format
2. Implement timer generation and installation
3. Link automations to timers
4. Implement timer management (list, enable/disable)
5. Persist timer state across reboots
6. Handle timer failures

**Success Criteria:**
- systemd timers operational
- Automations scheduled via timers
- Timer state persists across reboots
- All timer operations auditable

**Dependencies:**
- Phase 7 (automation framework)
- Phase 11 (tools)

**Estimated Complexity:** Medium

---

## PHASE 14 — ENHANCED USER NOTIFICATIONS

### Priority: MEDIUM
### Status: ⏳ Pending

**Objective:** Implement user notification system beyond logging.

**Key Tasks:**
1. Define notification types and framework
2. Implement notification delivery (web, API, CLI)
3. Implement notification persistence and history
4. Implement user interaction (acknowledge, filter, search)
5. Integrate with error handling and confirmation system

**Success Criteria:**
- Notification system operational
- Critical errors notify user (LAW 12)
- Notifications persist and searchable
- User can interact with notifications

**Dependencies:**
- Phase 6 (interfaces)
- Phase 8 (failure handling)

**Estimated Complexity:** Low-Medium

---

## PHASE 15 — VOICE INTERFACE (OPTIONAL)

### Priority: LOW (Optional)
### Status: ⏳ Optional

**Objective:** Implement voice input and audio feedback.

**Key Tasks:**
1. Design voice input interface
2. Integrate speech-to-text (offline preferred)
3. Route voice input to orchestrator
4. Integrate text-to-speech for audio feedback
5. Handle audio resource management

**Success Criteria:**
- Voice interface operational
- Voice commands processed correctly
- Audio feedback working
- All voice interactions auditable

**Dependencies:**
- Phase 6 (interfaces)
- Phase 10 (AI model)

**Estimated Complexity:** High

**Note:** This phase is **optional** and may be deferred based on user needs.

---

## IMPLEMENTATION ORDER

**Recommended Sequence:**

1. **Phase 10** — Real AI Model Integration (enables better intent parsing)
2. **Phase 11** — Tool Implementations (core functionality)
3. **Phase 12** — Supabase Synchronization (enhances memory)
4. **Phase 13** — systemd Timer Integration (scheduled automations)
5. **Phase 14** — Enhanced User Notifications (improves UX)
6. **Phase 15** — Voice Interface (optional, if needed)

**Rationale:**
- Phase 10 provides real AI capabilities needed for better tool selection
- Phase 11 implements actual functionality (high value)
- Phase 12 enhances memory system (medium value)
- Phase 13 enables scheduled automations (medium value)
- Phase 14 improves user experience (medium value)
- Phase 15 is optional enhancement (low priority)

---

## PHASE DEPENDENCIES

```
Phase 10 (AI Model)
  └─> Phase 11 (Tools) ──> Phase 12 (Supabase)
                          └─> Phase 13 (Timers)
Phase 6 (Interfaces) ──> Phase 14 (Notifications)
Phase 6 (Interfaces) ──> Phase 15 (Voice) [Optional]
Phase 10 (AI Model) ──> Phase 15 (Voice) [Optional]
```

---

## CURRENT STUBBED/INCOMPLETE COMPONENTS

### AI Model (Phase 10)
- **Current:** Stub implementation in `ai/model_manager.py`
- **Target:** Real llama.cpp integration with Qwen 2.5 3B model

### Tools (Phase 11)
- **Current:** Tool registry framework exists, no actual tools
- **Target:** Core tools implemented (system, file, automation, memory)

### Supabase Sync (Phase 12)
- **Current:** Stub in `memory/supabase_sync.py`
- **Target:** Real Supabase client with L3 memory sync

### systemd Timers (Phase 13)
- **Current:** Automation framework ready, timers not implemented
- **Target:** systemd timer integration for scheduled automations

### User Notifications (Phase 14)
- **Current:** Logging only
- **Target:** Notification system with persistence and user interaction

### Voice Interface (Phase 15)
- **Current:** Not implemented
- **Target:** Voice input/output interface (optional)

---

## SUCCESS METRICS

### Phase 10 Success
- ✅ Real AI model loads and runs on Pi
- ✅ Intent parsing accuracy > 80%
- ✅ Inference latency < 5 seconds
- ✅ RAM usage < 4GB total

### Phase 11 Success
- ✅ At least 10 core tools implemented
- ✅ All tools registered and locked
- ✅ Permission system working
- ✅ 100% tool executions audited

### Phase 12 Success
- ✅ L3 memory syncs to Supabase
- ✅ Offline operation works
- ✅ Conflict resolution tested
- ✅ Security requirements met

### Phase 13 Success
- ✅ Timers created and managed
- ✅ Automations scheduled via timers
- ✅ Timer state persists
- ✅ All timer operations logged

### Phase 14 Success
- ✅ Critical errors notify user
- ✅ Notifications persist
- ✅ User can acknowledge notifications
- ✅ Notification history searchable

### Phase 15 Success (if implemented)
- ✅ Voice commands processed
- ✅ Audio feedback working
- ✅ Offline operation supported
- ✅ All voice interactions logged

---

## RISKS AND MITIGATION

### Phase 10 Risks
- **Risk:** Model too large for Pi RAM
- **Mitigation:** Use quantized model (Q4_K_M), implement load/unload

- **Risk:** Inference too slow
- **Mitigation:** Optimize context window, implement caching

### Phase 11 Risks
- **Risk:** Tool execution security issues
- **Mitigation:** Strict permission checks, confirmation requirements

### Phase 12 Risks
- **Risk:** Network dependency
- **Mitigation:** Offline-first design, queue operations

### Phase 13 Risks
- **Risk:** Timer conflicts
- **Mitigation:** Serial execution enforced, state checking

---

## DOCUMENTATION UPDATES

As each phase completes:
- Update `DETAILED IMPLEMENTATION PLAN.md` with completion status
- Create phase completion report in `docs/PHASE_COMPLETION_REPORTS/`
- Update `PROJECT_STATUS.md` with phase completion
- Update `README.md` with phase status
- Update this roadmap with completion dates

---

**Last Updated:** 2026-01-27  
**Next Phase:** Phase 10 — Real AI Model Integration  
**Status:** Ready to begin Phase 10
