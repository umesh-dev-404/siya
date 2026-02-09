# Siya Evolution Roadmap
## Post–Phase 23: OpenClaw-Inspired, Law-Aligned Capability Expansion

**Status:** MODE A (Design / Proposal — non-binding)  
**Reference:** [OpenClaw docs](https://docs.openclaw.ai/) · [OpenClaw GitHub](https://github.com/openclaw/openclaw)  
**Audience:** Future contributors, auditors, and AI developers. Rationale and law references are explicit throughout.

---

## 1. PURPOSE

This document plans how Siya can reach **most of what OpenClaw can do** in terms of capabilities. **OpenClaw-like capabilities are being adopted/adapted in Siya** (setup wizard, operator UX, tooling, capability packs) where law-aligned; product name remains Siya. The roadmap guides that adoption. Specifically:

- Remaining **personalized** to your constraints and requirements
- Keeping **local AI only** (no required cloud models)
- **Never violating** the 23 Canonical System Laws
- Deciding **out-of-scope** items one by one as we go

*(OpenClaw-inspired work is implemented in Siya under this roadmap; name stays Siya.)*

**Governance rules for implementation:**

- **Always state what is being implemented** in any phase or PR so nothing is added without your awareness.
- **If any existing law must change** during implementation, it will be proposed clearly (what, why, how); you decide what and how to change.

---

## 2. TRUTH CHECK: WHERE SIYA STANDS TODAY

| Dimension | OpenClaw | Siya |
|-----------|----------|------|
| **Governance** | Config-driven; sandbox per session | Law-driven; explicit confirmation (LAW 1, 5); no autonomy (LAW 2) |
| **Determinism** | Best-effort, streaming | Serial queue (LAW 10), transactional steps (LAW 11), explicit failure (LAW 12) |
| **Auditability** | Logs, presence | Full audit log (LAW 13), explanation layer (LAW 20), posture (LAW 23) |
| **AI** | Cloud (Anthropic/OpenAI) preferred | **Local** (e.g. Qwen on Pi) |
| **Channels** | WhatsApp, Telegram, Discord, iMessage, Slack, etc. | CLI, HTTP API, Web, TUI today; **own Android app** planned. **No** third-party messaging; **no Mac** in current plan (future only). |
| **Tools** | Browser, canvas, nodes, cron, sessions, process, etc. | 26+ tools (file, time, memory, sync, voice, system, etc.) — correct but less “professional” surface |
| **Event model** | WebSocket control plane, push, streaming | HTTP-centric, pull-based, stateless |
| **Operator UX** | Control UI, doctor, onboarding wizard | Observability, posture, logs — no workflows or health narratives |
| **Extensibility** | Skills (bundled/managed/workspace), npm-style | None; all tools in-tree |

**Summary:** Siya is **ahead** on governance and determinism, **behind** on surface capabilities (tool polish, events, operator workflows, extensibility). **Channel strategy:** Siya will **not** use third-party messaging (WhatsApp, Telegram, Discord, iMessage, Slack, etc.). Instead, a **Siya-owned Android app** is planned. Mac is a future plan only — nothing about it now. The goal is to close the capability gap **without** copying autonomy or authority drift.

---

## 3. OPENCLAW CAPABILITY MAP (REFERENCE)

*Source: [OpenClaw docs](https://docs.openclaw.ai/), [GitHub README](https://github.com/openclaw/openclaw).*

### 3.1 Core platform

- Gateway (single process, WebSocket control plane)
- CLI: `gateway`, `agent`, `send`, wizard, `doctor`
- Pi agent in RPC mode; tool streaming; session model (main, groups, activation, queue)
- Media pipeline (images, audio, video, transcription, size caps)
- Control UI + WebChat from Gateway

### 3.2 Channels (OpenClaw reference; Siya does not use these)

- **Messaging (OpenClaw):** WhatsApp, Telegram, Slack, Discord, Google Chat, Signal, BlueBubbles (iMessage), iMessage legacy, Microsoft Teams, Matrix, Zalo, WebChat
- **Group rules:** mention gating, reply tags, per-channel routing
- **Security:** DM pairing, allowlists (`allowFrom`), group allowlists  
- **Siya:** No third-party messaging. **Own Android app** planned. No Mac in current plan.

### 3.3 Apps and nodes (OpenClaw reference; Siya differs)

- **macOS app:** menu bar, Voice Wake/PTT, Talk Mode, WebChat, remote gateway — *Siya: no Mac in current plan (future only).*
- **iOS/Android nodes:** Canvas, Voice Wake, Talk Mode, camera, screen recording, pairing — *Siya: own Android app planned; no third-party messaging.*
- **Node capabilities:** `system.run`, `system.notify`, canvas, camera, screen record, `location.get`, notifications
- **Windows:** No native OpenClaw companion app on Windows; Gateway runs in WSL2. See §3.7.

### 3.4 Tools and automation

- **Browser:** dedicated Chrome/Chromium, CDP, snapshots, actions, uploads, profiles
- **Canvas:** A2UI push/reset, eval, snapshot
- **Nodes:** camera, screen record, location, notifications
- **Cron + webhooks;** Gmail Pub/Sub
- **Skills:** bundled, managed, workspace skills; install gating; ClawHub registry
- **Sessions:** `sessions_list`, `sessions_history`, `sessions_send` (agent-to-agent)

### 3.5 Runtime and safety

- Channel routing, retry, streaming/chunking
- Presence, typing indicators, usage tracking
- Model failover, session pruning
- Sandbox: non-main sessions in Docker; allowlist/denylist per session

### 3.6 Ops and packaging

- Tailscale Serve/Funnel, SSH tunnels, token/password auth
- Nix, Docker
- Doctor, migrations, logging

### 3.7 OpenClaw on Windows (reference)

*Source: [OpenClaw — Windows (WSL2)](https://docs.openclaw.ai/platforms/windows).*

- **Recommended path:** WSL2 (Ubuntu preferred). CLI and Gateway run **inside Linux** for runtime consistency and compatibility (Node/Bun/pnpm, Linux binaries, skills). Native Windows is “trickier” and not the supported path.
- **Install:** `wsl --install`; enable **systemd** in WSL (required for Gateway daemon install); then follow Linux Getting Started inside WSL (`openclaw onboard`, etc.).
- **Gateway service:** `openclaw onboard --install-daemon` or `openclaw gateway install` inside WSL; repair/migrate with `openclaw doctor`.
- **Exposing WSL to LAN:** Windows portproxy (PowerShell as Admin) to forward a Windows port to WSL IP; firewall rule; WSL IP changes after restarts so portproxy may need refresh (or Scheduled Task at login).
- **No native Windows companion app:** OpenClaw has no Windows desktop/menu-bar app; “Native Windows companion apps are planned.” Control UI is used from browser (local or via portproxy). No macOS-style features (Voice Wake, menu bar, etc.) on Windows.
- **Implication for Siya:** On Windows, Siya’s **PC client** (CLI, TUI, HTTP) already connects to a Siya server (e.g. Pi). If Siya server ever runs on Windows, options are native Python or WSL2; OpenClaw’s Windows story is WSL2-only for the Gateway.

---

## 4. COMPARATIVE TABLE: OPENCLAW FEATURE → SIYA-STANCE

For each area we classify: **Adopt** (implement in a law-compliant way), **Adapt** (implement with strict constraints), **Reject** (do not implement; violates laws or constraints), or **Defer** (decide later, one by one).

| OpenClaw feature | Siya stance | Rationale / law |
|------------------|------------|-----------------|
| **Gateway as single control plane** | **Adapt** | Siya already has a single MCP server + orchestrator. We can add an explicit event/streaming plane that is **read-only push** (no execution triggers). LAW 2, 10. |
| **Multi-channel messaging (WhatsApp, Telegram, Discord, iMessage, Slack, etc.)** | **Reject** | Siya will **not** use third-party messaging channels. Replaced by own Android app (see below). LAW 19, 1 still apply to any future interface. |
| **WebSocket / push events** | **Adapt** | Add **explicit event streams** (e.g. posture, logs, task state). Events **must not** trigger execution or scheduling. LAW 2, 23. |
| **Browser tool (CDP, snapshots, actions)** | **Adapt** | Browser as a **tool family** with explicit confirmation for actions (LAW 1, 5). No autonomous browsing. Scope smaller than OpenClaw initially. |
| **Canvas / A2UI** | **Defer** | Visual workspace is a large surface. Decide later whether to adopt a minimal “display only” or reject. |
| **Node model (iOS/Android, device actions)** | **Defer** | Device nodes imply remote execution and permissions. Decide per platform; must not bypass orchestration (LAW 4). |
| **Cron + webhooks** | **Adapt** | Siya already has systemd timers (Phase 14). Webhooks as **explicit triggers** (user-configured, logged). LAW 2. |
| **Skills / ClawHub (installable extensions)** | **Adapt** | **Capability Packs** only: declarative, versioned, audited, permission-scoped. No arbitrary code loading, no npm-exec. LAW 4, 6. |
| **Sessions tools (sessions_list, sessions_send, etc.)** | **Reject** (as agent-to-agent) | Agent-to-agent messaging implies multiple authorities. Siya is single-user, single authority. LAW 1. Alternative: “session list” as observability only (read-only). |
| **Multi-agent routing / workspaces** | **Reject** | Multiple agents with isolated sessions violates single-sovereignty model. LAW 1. |
| **Sandbox (Docker per non-main session)** | **Defer** | Siya has no “main vs non-main” yet (no messaging channels). If we add channels later, sandboxing may be in scope. |
| **Control UI / Web dashboard** | **Adapt** | Siya has Web + TUI. Enhance with operator workflows and health narratives (read-only, LAW 23). |
| **Doctor / health diagnostics** | **Adapt** | Operator UX track: “why is Siya idle?”, “what failed?”, “what’s blocking?”. Read-only, no execution. LAW 23. |
| **Onboarding wizard** | **Adapt** | **Behave like OpenClaw’s wizard** (guided steps: model/auth, workspace, gateway, daemon, health check, etc.) but **product name stays Siya** (e.g. `siya onboard` or `siya wizard`). No implicit changes without user confirmation. LAW 1. See [OpenClaw onboarding](https://docs.openclaw.ai/start/wizard). |
| **Voice Wake / Talk Mode** | **Defer** | Siya has voice (Phase 16). Always-on wake and continuous talk are a product choice; decide later. |
| **OAuth / API keys (Anthropic, OpenAI)** | **Reject** (as primary) | Siya is local-AI-first. Cloud models may be optional later; not in core plan. |
| **Tailscale / remote access** | **Defer** | Deployment concern. Current doc: DEPLOYMENT.md, network access. Can add remote-access patterns later. |
| **Own Android app** | **Adopt** (future) | Siya will provide its **own Android app** as the mobile interface instead of third-party messaging. When implemented, **always stated** in phase/PR. LAW 19 (parity with other interfaces). |
| **macOS / Mac app** | **Defer** (future only) | Nothing about Mac in current plan; future only. Not in scope now. |

---

## 4.1 PLATFORM AND CHANNEL STRATEGY (LOCKED)

| Decision | Choice | Notes |
|----------|--------|-------|
| **Messaging channels** | **Not used** | No WhatsApp, Telegram, Discord, iMessage, Slack, or other third-party messaging. |
| **Mobile / remote UI** | **Own Android app** (planned) | Siya will develop its **own Android app**; when implemented, it will be explicitly stated in phase/PR. |
| **Mac** | **Out of scope for now** | Future plan only; nothing about Mac in current roadmap. |
| **Setup wizard** | **Like OpenClaw, name Siya** | Guided onboarding (model/auth, workspace, gateway, daemon, health check, etc.) similar to `openclaw onboard`; CLI and product name remain **Siya** (e.g. `siya onboard`). |
| **Windows (Siya)** | **PC = client today** | Today: Windows PC runs Siya CLI/TUI/HTTP client connecting to Siya server (e.g. Pi). Windows-as-server (native Python vs WSL2) TBD if needed. OpenClaw on Windows is WSL2-only for Gateway; no native Windows companion app. |

---

## 5. FOUR TRACKS (THEMES)

Tracks are **themes** of work. Phases (24, 25, …) are concrete deliverables under these themes.

### 5.1 Track order (what “order” means)

**“Track order”** means: in what **sequence** we design and implement the four themes, so that dependencies are clear and we don’t build events before we have a solid tool layer, etc.

**Suggested order:**

1. **Track 1 — Professional Tooling Layer** first.  
   Reason: Events and operator UX need well-defined tools and capability descriptors. Tool v2 is the foundation.

2. **Track 2 — Explicit Event & Streaming Plane** second.  
   Reason: Once tools are capability-scoped, we can define what “events” they (and the orchestrator) emit, without allowing events to trigger execution.

3. **Track 3 — Operator UX & Diagnostics** third.  
   Reason: Health narratives and workflows consume events and posture; better after the event plane exists.

4. **Track 4 — Capability Packs (Safe Extensibility)** fourth.  
   Reason: Extensibility builds on the tool v2 contract (domains, permissions, descriptors). So we do it after the tool system is upgraded.

If you want a different order (e.g. Operator UX before Events), we can adjust; the roadmap will state the chosen order explicitly.

---

### Track 1 — Professional Tooling Layer

**Goal:** Upgrade Siya tools from “functions you can call” to **capability-scoped, professional system interfaces**.

**OpenClaw overlap:** First-class tools (browser, canvas, nodes, cron, sessions).  
**Siya difference:** Tool families, explicit permissions and side-effect scope, preconditions/postconditions, dry-run/inspect modes. No autonomous tool use.

**Law alignment:** LAW 4 (tool-only execution), LAW 5 (explicit permissions), LAW 6 (no free-form computation).

**Outcome:** Siya Tool v2 architecture (capability domains, contracts, descriptors).

---

### Track 2 — Explicit Event & Streaming Plane

**Goal:** Let Siya **emit information** (posture, logs, task state) in real time, without events **triggering** execution or scheduling.

**OpenClaw overlap:** WebSocket control plane, push, streaming.  
**Siya difference:** Events are **observable only**. No event-driven execution, no bypass of confirmation or serial queue.

**Law alignment:** LAW 2 (no autonomous execution), LAW 10 (serial execution), LAW 23 (observability without control).

**Outcome:** Explicit event streams (e.g. subscriptions, push notifications, streaming logs) with strict “no trigger” rules.

---

### Track 3 — Operator UX & Diagnostics

**Goal:** **Operator workflows** and **health narratives** so operators (and you) can answer “why idle?”, “why did this fail?”, “what’s blocking?”, “what changed?”.

**OpenClaw overlap:** Control UI, doctor, onboarding.  
**Siya difference:** All read-only; no execution triggers; no implicit config changes. LAW 23.

**Law alignment:** LAW 13 (auditability), LAW 23 (observability without control).

**Outcome:** Operator workflows, failure playbooks, system self-inspection, health narratives (documented in this repo).

---

### Track 4 — Capability Packs (Safe Extensibility)

**Goal:** Extend Siya with **installable capability packs**: declarative, versioned, audited, permission-scoped. No arbitrary code loading, no agent-chosen plugins.

**OpenClaw overlap:** Skills, ClawHub.  
**Siya difference:** No npm-installed executables; no dynamic agent behavior; compatibility and permission checks; declarative registration only.

**Law alignment:** LAW 4, LAW 6, LAW 17 (no architectural drift).

**Outcome:** Siya Capability Packs (e.g. “Browser Pack”, “Email Pack”) — not “skills” in the OpenClaw sense.

---

## 6. PHASES 24–27 (HIGH-LEVEL OUTLINE)

These are **proposed** phases. Nothing is locked until you approve.

| Phase | Name | Objective | Must not |
|-------|------|-----------|----------|
| **24** | Tool System v2 (Capability-Driven Tools) | Tools grouped into capability domains; explicit permissions and side-effect scope; preconditions/postconditions; dry-run/inspect. | No tool execution without orchestration; no implicit permissions. |
| **25** | Explicit Event & Streaming Plane | Event subscriptions; push notifications; real-time posture; streaming logs. | Events must not trigger execution, scheduling, or confirmation bypass. |
| **26** | Operator Workflows & Health Narratives | “Why idle?”, “Why failed?”, “What’s blocking?”, “What changed?”. **Setup wizard** (like OpenClaw; name Siya): guided onboarding, daemon install, health check. | No execution triggers; no control surface; read-only. Wizard: no implicit config without confirmation. |
| **27** | Capability Packs (Safe Extensibility) | Declarative, versioned, audited extensions (e.g. Browser Pack, Email Pack). | No arbitrary code loading; no agent-installed executables; no autonomy. |

---

## 7. WHAT WE DO NOT COPY (EXPLICIT)

Siya **must not** adopt the following; they violate the stated laws.

| Practice | Why forbidden |
|----------|----------------|
| Autonomous message handling | LAW 2 (no autonomous execution) |
| Agent-initiated actions | LAW 1, 2, 3 |
| Implicit background polling that triggers actions | LAW 2 |
| Multi-agent or multi-workspace authority | LAW 1 |
| Shell/exec without going through orchestration | LAW 4 |
| Browser (or any tool) actions without explicit confirmation where required | LAW 1, 5 |
| Tool allow/deny decided by config alone (no human confirmation for sensitive tools) | LAW 5 |
| Events that schedule or execute tasks | LAW 2, 10 |
| Installable plugins that run arbitrary code | LAW 4, 6 |
| Session-to-session messaging as “agent-to-agent” authority | LAW 1 |

---

## 8. WHAT WE ADOPT OR ADAPT (SUMMARY)

- **Professional tool layer:** capability domains, contracts, dry-run (Track 1).
- **Event plane:** push/streaming for observability only (Track 2).
- **Operator UX:** health narratives, workflows, diagnostics, read-only (Track 3).
- **Capability Packs:** declarative extensions, no arbitrary code (Track 4).
- **Channels:** **No** third-party messaging (WhatsApp, Telegram, etc.). **Own Android app** planned; when implemented, **always stated** in the phase/PR. **No Mac** in current plan (future only).
- **Setup wizard:** Works like OpenClaw’s onboarding wizard; **name stays Siya** (e.g. `siya onboard`).

---

## 9. REFERENCES AND CROSS-DOCS

- **Laws:** `docs/CANONICAL SYSTEM LAWS.md`
- **Current status:** `docs/PROJECT_STATUS.md`
- **Continuation (Phases 20–23):** `docs/CONTINUATION_PLAN.md`
- **OpenClaw:** [docs.openclaw.ai](https://docs.openclaw.ai/), [github.com/openclaw/openclaw](https://github.com/openclaw/openclaw)

---

## 10. NEXT STEPS (YOUR DECISION)

1. **Confirm or change track order** (currently: Tool v2 → Events → Operator → Packs).
2. **Confirm or change** any row in the comparative table (Section 4).
3. **Lock Phase 24** (or another phase) as the next design target — then we can produce a Phase 24 design doc (still MODE A until you approve).

When implementation starts for any phase:

- The **exact scope** of what is being implemented will be stated in the phase doc and in PRs.
- Any **proposed change to an existing law** will be written out clearly for your decision.

---

**Document version:** 1.1  
**Last updated:** 2026-01-26  
**Status:** Proposal (MODE A). Not binding until explicitly approved.  
**Changelog (v1.1):** Channel strategy locked: no third-party messaging; own Android app planned; no Mac now. Setup wizard: like OpenClaw, name Siya. Added OpenClaw Windows (WSL2) research (§3.7) and platform/channel strategy (§4.1).
