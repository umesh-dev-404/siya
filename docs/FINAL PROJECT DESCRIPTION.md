==================== FILE START ====================

# FINAL PROJECT DESCRIPTION  
## Project: Siya

---

## 1. PROJECT SUMMARY

**Siya** is a **local-first personal governance and assistant operating system** designed to run primarily on a **Raspberry Pi 5 (8 GB)**. It provides structured automation, intent interpretation, and system control while enforcing strict determinism, transparency, and user sovereignty.

**Siya operates as a Model Context Protocol (MCP) Server**, exposing tools and resources to MCP clients (e.g., Claude Desktop, Claude Code, and Siya’s own first-party PC MCP CLI client). The Pi server maintains context of all integrations (mails, third-party services) and processes user requests through controlled AI content processing within tool execution flows.

Siya uses artificial intelligence as an **interpretive, explanatory, and content processing component** within explicit tool execution contexts, never as an autonomous decision-maker or executor. All real-world actions are executed exclusively through deterministic, permission-gated tools under explicit user control.

---

## 2. CORE PHILOSOPHY

Siya is built on a single, uncompromising principle:

> **Intelligence may assist, but authority must remain human and explicit.**

This philosophy is enforced architecturally rather than through prompts or trust.

---

## 3. WHAT SIYA IS

Siya is:

- A **local AI operating layer**
- A **deterministic automation control plane**
- A **personal governance system**
- A **local assistant operating system**
- A **foundation for future productization**

Siya coordinates multiple subsystems—AI, automation, memory, scheduling, and interfaces—under a strict set of laws that prevent hallucinated actions, hidden authority, and unpredictable behavior.

---

## 4. WHAT SIYA IS NOT

Siya is **not**:

- A chatbot
- An autonomous agent
- A background AI
- A cloud-dependent assistant
- A conversational engagement system
- A system that acts without explicit authorization

Any system exhibiting the above behaviors is explicitly **out of scope**.

---

## 5. SYSTEM OVERVIEW

At a high level, Siya operates as follows:

1. The user issues an intent via an MCP client (PC) or local interface (CLI/Web/API on Pi).
2. The intent is interpreted by a constrained local AI model (intent parsing).
3. The AI requests a specific tool using structured output.
4. The MCP Server validates the request against system laws.
5. A deterministic orchestration engine executes the approved action.
6. If the tool requires content processing (e.g., "summarize my mails"):
   - Tool fetches data (e.g., mail content)
   - AI model processes the content (summarization, extraction, transformation)
   - Processed content is returned as selective output
7. All actions and outcomes are logged and summarized into memory.
8. The user receives explicit feedback through the MCP client or local interface.

**MCP Server Architecture:**
- Siya on Pi acts as an MCP Server (Model Context Protocol)
- Exposes tools and resources to MCP clients
- Maintains context of all integrations (mails, third-party services)
- Processes content through AI within tool execution flows
- CLI, API, and Web interface connect to MCP Server internally (LAW 19)

At no point does the AI bypass control layers or execute actions autonomously. Content processing occurs only within explicit tool execution contexts.

---

## 6. PRIMARY SYSTEM COMPONENTS

### 6.1 Input Interfaces
- **MCP Clients** (primary):
  - **Siya PC MCP CLI client** (first-party, Claude-like behavior)
  - Claude Desktop / Claude Code (optional external MCP clients)
- **Local Interfaces** (on Pi):
  - Command-line interface
  - Local web interface
  - HTTP API
- Voice (future)
- Mobile and desktop applications (future)

**Interface Architecture:**
- MCP Server is the core interface layer
- CLI, API, and Web interface connect to MCP Server internally
- All interfaces expose identical functionality (LAW 19)
- All interfaces are treated equally and carry no implicit privileges

---

### 6.2 Intent Parsing & Content Processing Layer
- Uses a local, quantized large language model
- Interprets natural language into structured intent (intent parsing)
- Processes content (summarization, extraction, transformation) within tool execution flows
- Produces no side effects outside of explicit tool execution contexts

---

### 6.3 Model Context Protocol (MCP) Server
- Siya operates as an MCP Server, exposing tools and resources
- Validates tool requests from MCP clients
- Enforces permissions
- Requires explicit confirmation where necessary
- Provides audit hooks
- Maintains context of integrations (mails, third-party services)
- Processes content through AI within tool execution flows

---

### 6.4 Orchestration Engine
- Executes tasks serially
- Manages retries and failures
- Coordinates tool execution
- Controls memory writes

---

### 6.5 Tool System
- Composed of small, explicit, typed tools
- Each tool performs exactly one side effect
- No dynamic or implicit behavior
- Tools may invoke AI content processing (e.g., summarize text, extract information)
- Tools may execute remotely on PC via agent/client (future)
- Tools may access third-party integrations (mails, APIs) with explicit network permissions

**Note:** “Summarize mails” is an initial example tool used to validate the architecture. Siya is designed to expand to many additional tools and features over time without changing core governance.

---

### 6.6 Memory System
- Multi-tier memory architecture
- Local authoritative memory
- Long-term synchronized memory via Supabase
- Memory informs but never controls execution

---

## 7. OPERATING ENVIRONMENT

### 7.1 Primary Deployment
- Raspberry Pi 5
- 8 GB RAM
- Always-on operation

### 7.2 Network Model
- **MCP Protocol Transport**: Initially STDIO (local), later HTTP (remote)
- Local network first
- Internet optional
- Core functions fully offline-capable
- Network access for tools is explicit and permission-based (LAW 16)

---

## 8. SYNCHRONIZATION MODEL

Siya maintains both:

- A **local database** for authoritative runtime state
- A **Supabase-backed database** for long-term memory and cross-device synchronization

Synchronization is:
- Asynchronous
- Non-blocking
- Conflict-aware

Local execution always takes precedence.

---

## 9. FAILURE & RECOVERY BEHAVIOR

- All failures are explicit
- Partial execution is aborted
- The user is notified and consulted
- No silent recovery is permitted

This ensures trust and predictability.

---

## 10. RESOURCE CONSTRAINTS

Siya is designed to operate comfortably within the resource envelope of a Raspberry Pi 5:

- Bounded RAM usage
- No background AI inference
- Serialized execution
- Controlled storage growth

Performance predictability is prioritized over raw throughput.

---

## 11. FUTURE EVOLUTION

Although Siya is initially a personal system, its architecture supports:

- Multi-user configurations
- Additional interfaces
- Expanded tool libraries
- Productization

All future evolution must comply with the Canonical System Laws.

---

## 12. FINAL DECLARATION

Siya is a system designed to be **understood, trusted, and controlled**.

It does not rely on probabilistic behavior for safety.  
It relies on **architecture, laws, and explicit authority**.

This document defines Siya in its complete and final form.

---

==================== FILE END ====================