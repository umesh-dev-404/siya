==================== FILE START ====================

# PRE PLANNING DEFINITION DOCUMENT  
## Project: Siya

---

## 1. DOCUMENT PURPOSE

This document formally defines the **problem space, intent, scope, and foundational constraints** of the project named **Siya**.

It exists to ensure that:
- The problem being solved is **precisely understood**
- The motivation is **explicit and non-ambiguous**
- The scope is **intentionally constrained**
- No downstream design or implementation deviates from the original intent

This document must be read and agreed upon **before** any requirement, law, or implementation document is considered valid.

---

## 2. PROJECT OVERVIEW

### 2.1 Project Name
**Siya**

### 2.2 High-Level Description

Siya is a **local-first personal governance and assistant operating system**, designed to run primarily on a **Raspberry Pi 5 (8 GB)**, providing deterministic control, automation, and intelligence assistance to a single user.

**Siya operates as a Model Context Protocol (MCP) Server**, exposing tools and resources to MCP clients (first-party Siya PC MCP CLI client; optional external clients like Claude Desktop/Code). The Pi server maintains context of all integrations (mails, third-party services) and processes user requests through controlled AI content processing within tool execution flows.

Siya is not a chatbot, not a cloud assistant, and not an autonomous agent.  
It is a **structured control system** where intelligence assists interpretation and content processing, but **never governs execution autonomously**.

---

## 3. PROBLEM STATEMENT

Modern AI assistants and automation platforms suffer from the following systemic issues:

1. **Non-deterministic behavior**
2. **Hidden execution paths**
3. **Hallucinated actions**
4. **Opaque decision-making**
5. **Cloud dependency**
6. **Lack of user sovereignty**
7. **Unbounded background activity**
8. **Unrecoverable failure modes**

These systems optimize for convenience and engagement rather than:
- Safety
- Predictability
- Recoverability
- Auditability
- Local ownership

There exists a gap for a system that:
- Is fully controlled by the user
- Runs locally
- Operates deterministically
- Uses AI as a tool, not as an authority
- Can be reasoned about, audited, and trusted

---

## 4. PROJECT INTENT

The intent of Siya is to create:

- A **personal governance layer** for computation, automation, and decision support
- A **local assistant operating system** that interprets intent but never acts autonomously
- A **foundation system** that can later be extended into a product without architectural rework

The system is explicitly designed to:
- Eliminate hallucinated execution
- Make all authority visible and explicit
- Keep the user as the final decision-maker
- Remain operational even without internet connectivity

---

## 5. TARGET USER MODEL

### 5.1 User Scope
- Single-user only
- The system is designed exclusively for **one primary human operator**

There are:
- No personas
- No role hierarchies
- No multi-user concurrency requirements

Future multi-user support must not require changes to core architecture—only configuration.

---

## 6. OPERATING ENVIRONMENT

### 6.1 Primary Hardware
- Raspberry Pi 5
- 8 GB RAM

### 6.2 Deployment Characteristics
- Always-on operation
- Local network (home Wi-Fi)
- No reliance on external compute for core functionality

### 6.3 Supporting Interfaces (Planned)
- **MCP Clients** (primary): Siya PC MCP CLI client (first-party, Claude-like behavior)
- External MCP clients (optional): Claude Desktop / Claude Code
- **Local Interfaces** (on Pi):
  - Local web interface (hosted on the Pi)
  - CLI
  - HTTP API
- Mobile and desktop apps (future): **own Android app** planned; **no** third-party messaging; **no Mac** in current plan. See `docs/EVOLUTION_ROADMAP.md` §4.1. OpenClaw-inspired capabilities (e.g. setup wizard) are adopted/adapted in Siya where law-aligned; product name remains Siya.

**Interface Architecture:**
- MCP Server is the core interface layer
- CLI, API, and Web interface connect to MCP Server internally
- All interfaces expose identical functionality (LAW 19)
- All interfaces are **clients**, not authorities

---

## 7. DATA & MEMORY PHILOSOPHY

### 7.1 Local-First Principle
All critical execution and state must function **without internet access**.

### 7.2 Dual Database Model
- **Local Database (Authoritative at runtime)**
- **Supabase Database (Synchronized, long-term memory)**

Synchronization is:
- Asynchronous
- Conflict-aware
- Non-blocking

The system must continue to function if:
- Supabase is unreachable
- Internet connectivity is lost

---

## 8. AI USAGE PHILOSOPHY

AI within Siya is used **only** for:
- Intent interpretation (parsing user input into structured intent)
- Argument extraction
- Explanation
- Natural language interaction
- **Content processing** (summarization, extraction, transformation) within explicit tool execution flows

AI is **never** used for:
- Autonomous execution
- Decision authority
- Policy enforcement
- Safety overrides
- Processing content outside of explicit tool execution contexts

**Content Processing Constraints:**
- Content processing occurs only within tool execution contexts
- All AI-processed content is logged and auditable (LAW 13)
- AI model runs locally only (no cloud inference for security)
- Content processing is subject to permission and confirmation requirements (LAW 5)

AI is treated as a **component**, not an agent.

---

## 9. CONSTRAINTS (INTENTIONAL)

The following constraints are intentional design choices:

- No autonomous execution
- No background AI reasoning
- No parallel automations
- No hidden state
- No dynamic code execution
- No cloud dependency for core behavior

These constraints exist to **increase trust, not limit capability**.

---

## 10. SUCCESS CRITERIA

This project is considered successful if:

1. Every action taken by the system is explainable
2. No action occurs without explicit authorization
3. Failures are visible and recoverable
4. The system remains usable offline
5. The user retains full control at all times
6. The system operates within Raspberry Pi 5 resource limits

---

## 11. NON-GOALS

The following are explicitly **out of scope**:

- Replacing human decision-making
- Autonomous long-term planning
- Cloud-scale multi-user support (initially)
- High-frequency real-time systems
- Social or conversational optimization
- Third-party messaging channels (WhatsApp, Telegram, Discord, iMessage, Slack, etc.); Mac in current plan (future only). See `docs/EVOLUTION_ROADMAP.md` §4.1.

---

## 12. FINAL STATEMENT

Siya is conceived not as an assistant that acts *for* the user, but as a system that acts **with the user, under strict rules**.

This document establishes the philosophical and structural foundation upon which all subsequent documents are built.

No requirement, law, or implementation may contradict this document.

---

==================== FILE END ====================