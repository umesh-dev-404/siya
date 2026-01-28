==================== FILE START ====================

# DETAILED IMPLEMENTATION PLAN  
## Project: Siya  
## Strategy: PC-First Development with Deterministic Pi Execution

---

## 1. DOCUMENT PURPOSE

This document specifies the **exact implementation sequence, module breakdown, boot order, and development discipline** for Siya.

It exists to ensure:

- No architectural shortcuts are taken
- No phase is implemented out of order
- No capability is introduced without its governing laws and safeguards
- The system remains debuggable, deterministic, and Raspberry-Pi-safe
- Hardware never drives premature design decisions

This document is **binding**.  
Skipping, merging, or reordering phases is **not allowed** without explicit justification and documentation.

---

## 2. CORE IMPLEMENTATION PRINCIPLES

### 2.1 Architecture Before Hardware

All architectural, governance, and orchestration decisions must be finalized **before** any hardware-specific optimization or dependency.

### 2.2 PC as Design Authority

- The PC is the **primary development and design authority**
- The Raspberry Pi is a **runtime execution and validation target**
- No architectural decisions originate from hardware constraints

### 2.3 Hardware Constraints Are Verified, Not Assumed

All Pi constraints (RAM, CPU, thermals, I/O) are:
- **Measured**
- **Recorded**
- **Validated**

They are never guessed or baked in prematurely.

### 2.4 AI Is a Development Tool, Not a Runtime Authority

- AI assists design and coding under strict prompts and modes
- AI never:
  - Executes tools
  - Decides permissions
  - Writes memory autonomously
  - Controls runtime behavior

---

## 3. PHASE STRUCTURE OVERVIEW

Implementation is divided into **strict, sequential phases**.

No phase may begin until the previous phase is **complete, tested, and locked**.

| Phase | Name | Primary Environment |
|---|---|---|
| 0 | Foundation & Tooling | PC |
| 1 | Core Runtime Skeleton (No AI) | PC |
| 2 | Governance & Control Plane | PC |
| 3 | Memory & Observability | PC |
| 4A | Raspberry Pi Base Provisioning | Pi |
| 4 | Pi Mirroring & Validation | Pi (read-only) |
| 5 | AI Integration (Controlled) | PC + Pi |
| 6 | Interfaces & UX Layer | PC |
| 7 | Automation & Scheduling | PC + Pi |
| 8 | Failure Injection & Hardening | Pi |
| 9 | Production Lock & Baseline | Pi |

---

## 4. PHASE 0 — FOUNDATION & TOOLING (PC)

### Objective
Establish a **clean, governed development environment** before any system logic exists.

### Scope
- Repository setup
- Tooling
- Documentation enforcement
- AI governance

### Steps

1. Initialize version-controlled repository
2. Add:
   - Cursor rules (`alwaysApply`)
   - Developer System Prompt
3. Define fixed directory structure:
{name that suits}/
core/
orchestrator/
mcp/
tools/
memory/
logging/
security/
interfaces/
cli/
api/
web/
automations/
config/
system/
docs/
tests/
4. Lock Python version and virtual environment
5. Configure formatting, linting, and test runner
6. **No application logic allowed**

### Exit Criteria
- Repository builds
- Tests execute (even if empty)
- Cursor rules active
- No Pi involvement yet

---

## 5. PHASE 1 — CORE RUNTIME SKELETON (NO AI) (PC)

### Objective
Create the **deterministic execution backbone** without intelligence.

### Scope
- Orchestrator skeleton
- Execution lifecycle
- Serial task queue
- Failure propagation

### Steps

1. Implement orchestration engine skeleton
2. Define execution lifecycle:
- INIT
- VALIDATE
- EXECUTE
- VERIFY
- COMMIT
- FAIL
3. Enforce **single-task serial execution**
4. Implement explicit state transitions
5. Implement abort-on-failure semantics
6. Add exhaustive logging hooks

### Explicit Exclusions
- No AI
- No tools
- No memory
- No scheduling

### Exit Criteria
- Deterministic task execution
- Explicit failure propagation
- Complete execution logs

---

## 6. PHASE 2 — GOVERNANCE & CONTROL PLANE (PC)

### Objective
Enforce **authority, permissions, and Canonical Law compliance**.

### Scope
- MCP Server (Model Context Protocol)
- Permission model
- Tool schema framework (no tools yet)
- MCP protocol implementation (STDIO transport initially)

### Steps

1. Implement MCP Server as **Model Context Protocol Server**
2. Define strict tool schema format
3. Implement permission enforcement
4. Implement confirmation gating
5. Reject malformed or unauthorized requests
6. Log every decision
7. Implement MCP protocol primitives (tools, resources)
8. Ensure CLI/API/Web connect to MCP Server internally (LAW 19)

### Explicit Exclusions
- No real tools
- No side effects
- No memory writes

### Exit Criteria
- No execution bypasses MCP Server
- All decisions are explainable
- Laws-to-code mapping holds
- MCP Server exposes tools and resources to clients

---

## 7. PHASE 3 — MEMORY & OBSERVABILITY (PC)

### Objective
Add **state, memory, and observability** without affecting execution authority.

### Scope
- SQLite runtime memory (L2)
- Logging system
- Memory governance layer
- Supabase sync (mocked)

### Steps

1. Implement SQLite schemas (WAL enabled)
2. Enforce orchestrator-only memory writes
3. Implement memory tagging, confidence, lineage
4. Implement log retention and summarization
5. Stub Supabase synchronization (no real network)

### Explicit Exclusions
- Memory must not influence execution
- AI cannot read memory for decisions

### Exit Criteria
- Offline-safe operation
- Persistent, queryable logs
- Deterministic memory behavior

---

## 8. PHASE 4A — RASPBERRY PI BASE PROVISIONING (MANDATORY)

### Objective
Prepare a **clean, deterministic, reproducible Pi execution substrate**.

No Siya logic is validated before this phase completes.

### Scope
- OS installation
- System hardening
- Runtime dependencies
- Toolchain setup
- Performance baselining

### Steps

#### 4A.1 Operating System
- Install **Raspberry Pi OS Lite (64-bit)**
- Ensure ARM64 userspace, systemd, SSH
- Set hostname, locale, timezone

#### 4A.2 System Hardening
- Disable unnecessary services
- Enable firewall (default deny inbound)
- Disable swap
- Safe filesystem mount options
- Enable OS-only security updates

#### 4A.3 Runtime Dependencies
Install:
- Python (version-matched with PC)
- venv support
- pip / uv / poetry (standardized)
- git
- build-essential
- curl / wget
- SQLite (WAL capable)

#### 4A.4 AI Prerequisites (No Models)
- llama.cpp build dependencies
- CMake
- BLAS / OpenBLAS (if used)
- CPU feature tools

#### 4A.5 systemd Validation
- Verify timers
- Verify restart semantics
- Verify journald retention
- Verify clock sync

#### 4A.6 Baseline Metrics
- Record idle RAM
- Record CPU temperature
- Verify throttling behavior

#### 4A.7 Repo Mirroring
- Clone Siya repository
- Read-only policy (no code edits)

### Explicit Exclusions
- No AI models
- No automations
- No background Siya services

### Exit Criteria
- Clean boot
- Dependencies installed
- Metrics recorded
- Ready to execute Siya

---

## 9. PHASE 4 — PI MIRRORING & VALIDATION (READ-ONLY)

### Objective
Validate architecture against **real Pi constraints** without modifying design.

### Steps
- Run unit tests
- Run orchestrator dry-runs
- Run memory operations
- Measure RAM, CPU, disk I/O

### Rules
- No code written on Pi
- Pi does not influence architecture

### Exit Criteria
- Identical behavior PC ↔ Pi
- No ARM-specific failures

---

## 10. PHASE 5 — AI INTEGRATION (CONTROLLED)

### Objective
Introduce AI **as an intent parser and content processor** (within tool execution flows).

### Scope
- llama.cpp
- Model lifecycle
- JSON schema enforcement
- Content processing capabilities (for tool execution flows)

### Steps

1. Stub llama.cpp on PC
2. Implement intent parsing interface
3. Enforce strict JSON schema
4. Implement content processing interface (for tool execution flows)
5. Integrate model on Pi
6. Measure RAM, CPU, latency
7. Implement load/unload on demand

### Rules
- AI output is untrusted
- AI cannot execute tools autonomously
- AI cannot write memory
- AI may process content within explicit tool execution flows
- Content processing must be logged and auditable (LAW 13)
- AI model runs locally only (no cloud inference for security)

### Exit Criteria
- Deterministic JSON output
- Pi memory budget respected
- Content processing operational within tool execution flows

---

## 11. PHASE 6 — INTERFACES & UX LAYER (PC)

### Scope
- MCP Server (core interface layer)
- MCP Clients:
  - **Siya PC MCP CLI client (first-party, Claude-like behavior)**
  - Optional external clients (Claude Desktop / Claude Code) for compatibility testing
- CLI (connects to MCP Server internally)
- HTTP API (connects to MCP Server internally)
- Local web interface (connects to MCP Server internally)

### Rules
- MCP Server is the core interface layer
- CLI, API, and Web interface connect to MCP Server internally (LAW 19)
- All interfaces expose identical functionality (LAW 19)
- CLI is primary debugging surface
- API mirrors CLI exactly
- Web UI is client-rendered
- Explicit confirmations only
- No interface drift allowed

### Exit Criteria
- Identical behavior across all interfaces
- No privilege escalation
- MCP Server operational
- CLI/API/Web synchronized with MCP Server

**Additional Exit Criteria (PC MCP client):**
- First-party PC MCP CLI client can:
  - Complete MCP initialization lifecycle (`initialize` → `notifications/initialized`)
  - List tools (`tools/list`)
  - Call tools (`tools/call`)
  - Display selective output consistently

---

## 12. PHASE 7 — AUTOMATION & SCHEDULING (PC + PI)

### Scope
- Automation modules
- systemd timers

### Steps
- One automation = one module
- Explicit entry point
- Serial execution enforced
- Persist execution state
- Abort on reboot + notify

### Exit Criteria
- No overlapping automations
- Complete audit trails

---

## 13. PHASE 8 — FAILURE INJECTION & HARDENING (PI)

### Scope
- Power loss
- Network loss
- AI crashes
- Tool failures
- Resource exhaustion

### Exit Criteria
- No silent failure
- No corrupted state
- User always notified

---

## 14. PHASE 9 — PRODUCTION LOCK & BASELINE (PI)

### Objective
Freeze a **known-good, reproducible baseline**.

### Steps
- Lock schema versions
- Lock tool registry
- Document deployment
- Create recovery checklist
- Tag release

### Exit Criteria
- System is reproducible
- System is auditable
- System is stable

---

## 15. PHASE 10 — REAL AI MODEL INTEGRATION (PI)

### Objective
Replace stub AI implementation with **real llama.cpp integration** for production intent parsing.

### Scope
- llama.cpp integration
- Model loading and lifecycle
- Resource management
- Performance optimization

### Steps

1. **Build llama.cpp on Pi**
   - Install llama.cpp dependencies
   - Build with CPU optimizations
   - Verify ARM64 compatibility

2. **Model Acquisition**
   - Download Qwen 2.5 3B Instruct (Q4_K_M quantized)
   - Verify model file integrity
   - Store in designated model directory

3. **Replace Stub Implementation**
   - Replace `ai/model_manager.py` stub with real llama.cpp bindings
   - Implement model loading/unloading
   - Implement inference with timeout handling
   - Maintain strict JSON schema enforcement

4. **Resource Management**
   - Implement load-on-demand strategy
   - Monitor RAM usage during inference
   - Implement graceful degradation on resource exhaustion
   - Unload model when idle

5. **Performance Optimization**
   - Measure inference latency
   - Optimize context window usage
   - Implement caching where appropriate
   - Ensure Pi memory budget respected

6. **Integration Testing**
   - Test intent parsing with real model
   - Verify schema compliance
   - Test resource limits
   - Verify graceful failure handling

### Rules
- AI output remains untrusted (LAW 3)
- All outputs validated against system_schema.json
- Model must not exceed Pi RAM limits
- Inference must be interruptible

### Exit Criteria
- Real AI model integrated and operational
- Intent parsing produces valid schema-compliant output
- RAM usage within Pi constraints
- Inference latency acceptable (< 5 seconds for typical queries)

---

## 16. PHASE 11 — TOOL IMPLEMENTATIONS

### Objective
Implement **actual tool executions** replacing framework-only stubs, integrated with MCP Server.

### Scope
- Core system tools
- File system tools
- System control tools
- Network tools (with explicit permissions)
- Content processing tools (AI-powered summarization, extraction, transformation)
- Third-party integration tools (mails, APIs)

**Important:** Tools like **"summarize mails"** are **only initial example tools** to validate end-to-end flow.  
Phase 11 is intentionally designed to scale to **many tools and features** over time (new tool categories, new resources, new integrations) without changing the core governance/laws.

### Steps

1. **Define Tool Categories**
   - System information tools
   - File operations tools
   - Automation trigger tools
   - Memory query tools
   - Content processing tools (AI-powered)
   - Third-party integration tools (mails, APIs)
   - Remote execution tools (PC agent/client, future)

2. **Implement Core Tools**
   - System status tool
   - Resource monitoring tool
   - Log query tool
   - Memory read tool

3. **Implement File Operations**
   - File read tool (with permission checks)
   - File write tool (with confirmation)
   - Directory listing tool
   - File metadata tool
   - Remote file operations (PC agent/client, future)

4. **Implement Content Processing Tools**
   - Summarize text tool (AI-powered)
   - Extract information tool (AI-powered)
   - Transform data tool (AI-powered)
   - Selective output formatting (filtered/processed results)

5. **Implement Third-Party Integration Tools**
   - Fetch mails tool (with explicit network permissions)
   - Summarize mails tool (fetches + AI processes)
   - Other third-party API tools (with explicit permissions)

6. **Implement Automation Tools**
   - Trigger automation tool
   - List automations tool
   - Automation status tool

7. **Tool Registration**
   - Register all tools in MCP Server tool registry
   - Define permission levels
   - Set confirmation requirements
   - Set network access requirements (LAW 16)
   - Lock registry after registration

8. **MCP Server Integration**
   - Expose tools via MCP protocol
   - Expose resources (mail content, third-party data)
   - Implement selective output formatting
   - Ensure CLI/API/Web connect to MCP Server internally (LAW 19)

9. **Testing & Validation**
   - Test each tool execution
   - Verify permission enforcement
   - Test confirmation flows
   - Test content processing flows
   - Test third-party integrations
   - Verify audit logging
   - Verify interface consistency (LAW 19)

### Rules
- All tools must be pre-declared (LAW 4, LAW 6)
- Permission levels enforced (LAW 5)
- Confirmations required where specified (LAW 1)
- All executions logged (LAW 13)
- Content processing occurs within tool execution flows (LAW 3)
- Network access is explicit and permission-based (LAW 16)
- Tools exposed via MCP Server protocol

### Exit Criteria
- Core tools implemented and operational
- Content processing tools operational
- Third-party integration tools operational
- Tools registered and locked in MCP Server
- Permission system working
- All tool executions auditable
- MCP Server exposes tools and resources
- Interface consistency maintained (LAW 19)

---

## 17. PHASE 12 — SUPABASE SYNCHRONIZATION

### Objective
Implement **real Supabase synchronization** replacing stub implementation.

### Scope
- Supabase client integration
- L3 memory synchronization
- Conflict resolution
- Offline-first operation

### Steps

1. **Supabase Setup**
   - Create Supabase project
   - Configure authentication
   - Design L3 memory schema
   - Set up API keys (secure storage)

2. **Client Integration**
   - Install Supabase Python client
   - Implement connection handling
   - Implement retry logic
   - Handle network failures gracefully

3. **L3 Memory Sync**
   - Implement sync-to-Supabase
   - Implement sync-from-Supabase
   - Handle conflicts (local wins, with logging)
   - Implement incremental sync

4. **Offline-First Design**
   - Queue sync operations when offline
   - Resume sync when online
   - Never block execution for sync
   - Log sync failures

5. **Security**
   - Store API keys securely (LAW 15)
   - Encrypt sensitive data
   - Never expose secrets in logs
   - Implement secure authentication

6. **Testing**
   - Test online sync
   - Test offline operation
   - Test conflict resolution
   - Test failure recovery

### Rules
- Sync is asynchronous (LAW 16)
- Never required for execution (LAW 16)
- Secrets isolated (LAW 15)
- All sync operations logged (LAW 13)

### Exit Criteria
- Supabase sync operational
- L3 memory synchronized
- Offline operation works
- Security requirements met

---

## 18. PHASE 13 — SYSTEMD TIMER INTEGRATION

### Objective
Integrate **systemd timers** for scheduled automations.

### Scope
- systemd timer configuration
- Automation scheduling
- Timer management
- State persistence

### Steps

1. **Timer Framework**
   - Design timer configuration format
   - Implement timer generation
   - Implement timer installation
   - Implement timer removal

2. **Automation Integration**
   - Link automations to timers
   - Implement timer triggers
   - Handle timer execution
   - Persist timer state

3. **Timer Management**
   - List active timers
   - Enable/disable timers
   - View timer status
   - Handle timer failures

4. **State Persistence**
   - Persist timer configuration
   - Restore timers on reboot
   - Handle timer conflicts
   - Log timer events

5. **Testing**
   - Test timer creation
   - Test timer execution
   - Test timer persistence
   - Test failure handling

### Rules
- Serial execution enforced (LAW 10)
- All timer actions logged (LAW 13)
- User must approve timer creation (LAW 1)
- Timers must be explicit (LAW 2)

### Exit Criteria
- systemd timers operational
- Automations scheduled via timers
- Timer state persists across reboots
- All timer operations auditable

---

## 19. PHASE 14 — ENHANCED USER NOTIFICATIONS

### Objective
Implement **user notification system** beyond logging.

### Scope
- Notification delivery
- Notification channels
- Notification persistence
- User acknowledgment

### Steps

1. **Notification Framework**
   - Define notification types
   - Implement notification queue
   - Implement notification delivery
   - Handle notification failures

2. **Notification Channels**
   - Web interface notifications
   - API notification endpoint
   - CLI notification display
   - Email notifications (optional)

3. **Notification Persistence**
   - Store unread notifications
   - Implement notification history
   - Implement notification cleanup
   - Link notifications to audit logs

4. **User Interaction**
   - Mark notifications as read
   - Acknowledge critical notifications
   - Filter notifications
   - Search notification history

5. **Integration**
   - Integrate with error handling
   - Integrate with confirmation system
   - Integrate with automation system
   - Integrate with failure detection

### Rules
- Critical errors must notify user (LAW 12)
- Notifications must be explicit (LAW 1)
- All notifications logged (LAW 13)
- User can acknowledge notifications

### Exit Criteria
- Notification system operational
- Critical errors notify user
- Notifications persist and searchable
- User can interact with notifications

---

## 20. PHASE 15 — VOICE INTERFACE (OPTIONAL)

### Objective
Implement **voice input interface** for hands-free interaction.

### Scope
- Voice input capture
- Speech-to-text
- Voice command processing
- Audio feedback

### Steps

1. **Voice Input Framework**
   - Design voice input interface
   - Implement audio capture
   - Handle audio processing
   - Manage audio resources

2. **Speech-to-Text**
   - Integrate speech recognition
   - Handle offline operation
   - Implement wake word (optional)
   - Handle audio quality issues

3. **Command Processing**
   - Route voice input to orchestrator
   - Handle voice-specific errors
   - Provide voice feedback
   - Maintain conversation context

4. **Audio Feedback**
   - Text-to-speech integration
   - Audio response generation
   - Handle audio playback
   - Manage audio resources

5. **Testing**
   - Test voice input
   - Test speech recognition
   - Test command processing
   - Test audio feedback

### Rules
- Voice interface treated equally (no privilege escalation)
- All voice commands logged (LAW 13)
- Voice input requires confirmation for actions (LAW 1)
- Offline operation supported (LAW 16)

### Exit Criteria
- Voice interface operational
- Voice commands processed correctly
- Audio feedback working
- All voice interactions auditable

**Note:** This phase is **optional** and may be deferred based on user needs.

---

## 21. PHASE STRUCTURE OVERVIEW (UPDATED)

| Phase | Name | Primary Environment | Status |
|---|---|---|---|
| 0 | Foundation & Tooling | PC | ✅ Complete |
| 1 | Core Runtime Skeleton (No AI) | PC | ✅ Complete |
| 2 | Governance & Control Plane | PC | ✅ Complete |
| 3 | Memory & Observability | PC | ✅ Complete |
| 4A | Raspberry Pi Base Provisioning | Pi | ✅ Complete |
| 4 | Pi Mirroring & Validation | Pi (read-only) | ✅ Complete |
| 5 | AI Integration (Controlled) | PC + Pi | ✅ Complete |
| 6 | Interfaces & UX Layer | PC | ✅ Complete |
| 7 | Automation & Scheduling | PC + Pi | ✅ Complete |
| 8 | Failure Injection & Hardening | Pi | ✅ Complete |
| 9 | Production Lock & Baseline | Pi | ✅ Complete |
| 10 | Real AI Model Integration | Pi | ✅ Complete |
| 11 | Tool Implementations | Pi | ✅ Complete |
| 12 | System Context & Memory | Pi | ✅ Complete |
| 13 | Supabase Synchronization | Pi | ✅ Complete |
| 14 | systemd Timer Integration | Pi | ✅ Complete |
| 15 | Enhanced User Notifications | Pi | ✅ Complete |
| 16 | Voice Interface | Pi | ✅ Complete |
| 17 | Web Interface Redesign | PC + Pi | ✅ Complete |
| 18 | Full-Screen TUI | PC | ✅ Complete |
| 19 | Interface Consistency | PC + Pi | ✅ Complete |

### v1.0.1 Enhancement Phases (Pending)

| Phase | Name | Primary Environment | Status |
|---|---|---|---|
| 20 | Decision Explanation Layer | PC + Pi | ⏳ Pending |
| 21 | Explicit User Intent Modes | PC + Pi | ⏳ Pending |
| 22 | Memory Quality Control | PC + Pi | ⏳ Pending |
| 23 | Operator Observability Dashboard | PC + Pi | ⏳ Pending |

---

## 22. FINAL IMPLEMENTATION STATEMENT

This plan enforces:

- Determinism over convenience
- Governance over autonomy
- Architecture over hardware
- Safety over speed

Any deviation must be:
- Explicit
- Documented
- Justified

Otherwise, it is invalid.

---

==================== FILE END ====================

