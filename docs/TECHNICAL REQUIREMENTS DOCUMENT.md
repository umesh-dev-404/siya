==================== FILE START ====================

# TECHNICAL REQUIREMENTS DOCUMENT (TRD)  
## Project: Siya

---

## 1. DOCUMENT PURPOSE

This Technical Requirements Document (TRD) defines **how Siya must be built and operated from a technical standpoint**, independent of business intent or narrative framing.

It establishes:
- Hardware assumptions
- Software stack requirements
- Resource constraints
- Performance envelopes
- Reliability and recovery expectations
- Security boundaries

This document bridges **requirements** and **implementation**.

---

## 2. TARGET HARDWARE REQUIREMENTS

### 2.1 Primary Deployment Target

- Device: Raspberry Pi 5
- RAM: 8 GB
- CPU: ARM64
- Storage: SD card or SSD (recommended)
- Network: Ethernet or Wi-Fi (local network)

### 2.2 Always-On Operation

The system is designed for:
- Continuous uptime
- Long-running processes
- Graceful handling of power interruptions

---

## 3. OPERATING SYSTEM REQUIREMENTS

### 3.1 OS

- Linux-based OS (64-bit)
- systemd must be available
- POSIX-compliant environment

### 3.2 OS Responsibilities

- Process isolation
- Scheduling
- Resource enforcement
- Service supervision
- Timer execution

---

## 4. SOFTWARE STACK REQUIREMENTS

### 4.1 Core Language

- Python (primary orchestration and control logic)

### 4.2 AI Runtime

- llama.cpp
- CPU-only inference
- Quantized models only
- No GPU dependency

### 4.3 Web & API Layer

- Lightweight HTTP server
- No heavy server-side rendering
- Minimal memory footprint
- Static or client-rendered UI

### 4.4 Databases

#### Local Database
- SQLite
- WAL mode enabled
- Local filesystem storage
- Authoritative during runtime

#### Remote Database
- Supabase
- Used for long-term memory and synchronization
- Asynchronous access only
- Never required for execution

---

## 5. MEMORY ARCHITECTURE REQUIREMENTS

### 5.1 Memory Tiers

- L1: Runtime memory (in-process, ephemeral)
- L2: Local persistent memory (SQLite)
- L3: Long-term synchronized memory (Supabase)

### 5.2 Memory Constraints

- No unbounded growth
- Mandatory summarization
- Lineage tracking required

### 5.3 Memory Safety

- Memory must never:
  - Trigger execution
  - Select tools
  - Override logic

---

## 6. AI MODEL REQUIREMENTS

### 6.1 Model Selection

- Qwen 2.5 – 3B Instruct
- Quantization: Q4_K_M
- Context window: ≤ 4k tokens

### 6.2 AI Usage Constraints

The AI model:
- Must never execute code autonomously
- Must never access secrets
- Must never modify system state directly
- Must always produce structured output
- May process content (summarization, extraction, transformation) within explicit tool execution flows
- Content processing must be logged and auditable (LAW 13)
- AI model runs locally only (no cloud inference for security)

---

## 7. MODEL LIFECYCLE MANAGEMENT

### 7.1 Loading Strategy

- Load-on-demand for background tasks
- Persistent load during active interaction
- Full unload when idle

### 7.2 Resource Control

- AI inference must not starve system processes
- Timeouts must be enforced
- Inference must be interruptible

---

## 8. MCP SERVER (MODEL CONTEXT PROTOCOL) REQUIREMENTS

### 8.1 Functional Role

Siya operates as an **MCP Server (Model Context Protocol)**, which must:
- Expose tools and resources to MCP clients (first-party PC CLI client; optional external clients like Claude Desktop/Code)
- Validate tool requests from MCP clients
- Enforce permissions
- Enforce confirmation policies
- Reject malformed or unauthorized requests
- Maintain context of integrations (mails, third-party services)
- Process content through AI within tool execution flows
- Support selective output (filtered/processed results with user-configurable formats)

### 8.2 MCP Protocol Transport

- **Initial**: STDIO transport (local communication)
- **Future**: HTTP transport (remote communication)
- Protocol implementation must comply with MCP specification

### 8.2A MCP Client Requirements (PC CLI)

Siya must provide a **first-party PC MCP CLI client** that replicates Claude-like MCP client behavior:
- Implement MCP lifecycle: `initialize` → `notifications/initialized` → normal operation
- Support tool discovery: `tools/list`
- Support tool invocation: `tools/call`
- Enforce request timeouts and clear error reporting
- Provide selective output formatting at the client layer (human-readable + structured output passthrough)
- Support transport targets:
  - STDIO (spawn local MCP server process for development/testing)
  - HTTP (connect to Pi-hosted MCP endpoint in later phase)

### 8.3 MCP Primitives

- **Tools**: Executable functions exposed to MCP clients
- **Resources**: Data sources (e.g., mail content, third-party data)
- **Prompts**: Templates (future phase)

### 8.4 Structural Constraints

- Stateless design
- Restartable without data loss
- Versioned tool schemas
- Interface consistency (CLI/API/Web connect to MCP Server internally, LAW 19)

### 8.5 Platform & channel strategy (locked)

- Interfaces today: CLI, HTTP API, Web, TUI. **Own Android app** planned; **no** third-party messaging (WhatsApp, Telegram, Discord, iMessage, Slack, etc.). **No Mac** in current plan. See `docs/EVOLUTION_ROADMAP.md` §4.1.
- OpenClaw-inspired capabilities (setup wizard, operator UX, tooling) are adopted/adapted in Siya where law-aligned; product name remains Siya.

---

## 9. TOOL SYSTEM REQUIREMENTS

### 9.1 Tool Definition

Each tool must:
- Be explicitly declared
- Have typed input and output schemas
- Perform exactly one side effect

### 9.2 Tool Safety

- No dynamic tool generation
- No shell passthrough
- No recursive execution outside orchestration
- Tools may invoke AI content processing within execution flows
- Tools may execute remotely on PC via agent/client (future)
- Tools may access third-party integrations (mails, APIs) with explicit network permissions

---

## 10. ORCHESTRATION ENGINE REQUIREMENTS

### 10.1 Execution Model

- Single execution queue
- Serial execution only
- No concurrency

### 10.2 Step Execution

Each step must:
- Be independently verifiable
- Have defined success and failure states
- Be logged before and after execution

---

## 11. AUTOMATION & SCHEDULING REQUIREMENTS

### 11.1 Scheduling Mechanism

- systemd timers only
- No polling loops
- No background schedulers

### 11.2 Automation Behavior

- Reactive and scheduled automations supported
- Automations must be interrupt-safe
- Mid-execution reboot must result in abort + notify

---

## 12. PERFORMANCE REQUIREMENTS

### 12.1 RAM Budget (Maximum)

| Component | RAM |
|--------|-----|
| OS & base services | ~1.3 GB |
| AI model (loaded) | ~3.0 GB |
| MCP | ~120 MB |
| Orchestrator | ~100 MB |
| Buffers / overhead | ~1.2 GB |

Total must remain under **7 GB**.

---

### 12.2 CPU Usage

- No sustained 100% CPU usage
- AI inference must be bounded
- Serialized workloads only

---

## 13. THERMAL & POWER CONSTRAINTS

- System must tolerate thermal throttling
- No design assumes peak CPU indefinitely
- Power instability must not corrupt state
- Frequent writes must be minimized

---

## 14. FAILURE & RECOVERY REQUIREMENTS

### 14.1 Failure Handling

- Explicit failure detection
- Retry with backoff
- User notification required

### 14.2 Recovery

- No automatic continuation after failure
- User must explicitly decide next step

---

## 15. LOGGING & AUDIT REQUIREMENTS

### 15.1 Logging Scope

- Inputs
- Tool calls
- Permissions
- Confirmations
- Failures
- System health

### 15.2 Retention

- Raw logs: 30 days
- Summaries persisted to memory

---

## 16. SECURITY REQUIREMENTS

### 16.1 Secrets Management

- Secrets stored encrypted
- Injected at runtime
- Never logged
- Never visible to AI

---

### 16.2 Network Security

- Explicit allow-list
- No implicit outbound traffic
- Offline-first behavior
- Network access for tools is explicit and permission-based (LAW 16)
- Network access depends on tool functionality (not all tools require network)
- MCP protocol transport: initially STDIO (local), later HTTP (remote)

---

## 17. COMPATIBILITY & PORTABILITY

- Hardware-agnostic core logic
- Pi-specific concerns isolated
- Reproducible installs required

---

## 18. COMPLIANCE STATEMENT

Any implementation that violates these technical requirements is non-compliant with the Siya system definition.

---

==================== FILE END ====================