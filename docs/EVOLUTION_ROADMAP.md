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

## 11. MODE A — PHASE 24 DESIGN PROPOSAL (NON-BINDING)

*This section is **PROPOSAL / NON-BINDING**. It is the output of MODE A (Design/Exploration) for the evolution flow A→B→C→D. Nothing here is implemented until MODE B locks scope and MODE C implements.*

### 11.1 Phase 24 objective (from §6)

**Phase 24 — Tool System v2 (Capability-Driven Tools):** Tools grouped into capability domains; explicit permissions and side-effect scope; preconditions/postconditions; dry-run/inspect. **Must not:** tool execution without orchestration; implicit permissions.

### 11.2 Current state

- **ToolSchema** (`mcp/tool_schema.py`): `name`, `description`, `input_schema`, `output_schema`, `permission_level`, `requires_confirmation`, `category`, `version`. No capability domain or side-effect scope.
- **ToolRegistry** (`mcp/tool_registry.py`): Static registry; lock after bootstrap. LAW 4, 6 enforced.
- **Tools** (`tools/`): 26+ tools in categories (file, memory, system, automation, etc.) via `category` field.

### 11.3 Proposal: first slice (24.1) to reduce risk

**Option A — Minimal (recommended for first cycle):** Add **capability_domain** only.

- **Scope:** Add optional `capability_domain: Optional[str]` to `ToolSchema` (e.g. `"file"`, `"memory"`, `"system"`, `"automation"`, `"content"`, `"integration"`). Populate from existing `category` where present; default `"general"` for uncategorized. No change to execution path; no new permissions logic. Schema and registry only.
- **Rationale:** Establishes the domain concept without behavior change. Reversible. Enables later Phase 24 work (preconditions, dry-run) to be domain-scoped.
- **Laws:** LAW 4, 6 unchanged. No new law.

**Option B — Domain + side-effect scope:** Option A plus add **side_effect_scope** enum to ToolSchema (`READ_ONLY` | `WRITE` | `EXECUTE` | `EXTERNAL`), derived from current `permission_level` and tool semantics. Still no execution-path change in 24.1; descriptive only.

**Option C — Full Phase 24:** Capability domains, side-effect scope, preconditions/postconditions schema, dry-run/inspect modes. Large; better as multiple slices (24.1, 24.2, 24.3).

### 11.4 Dependencies and risks

- **Dependencies:** None for Option A. Existing tests (tool registry, MCP) should pass unchanged if domain is optional and backward-compatible.
- **Risks:** Option A — low. Option B — slight schema drift if side_effect_scope and permission_level ever diverge. Option C — high scope; recommend slicing.
- **Blind spots:** Dry-run and preconditions will require orchestrator and MCP contract changes; defer to 24.2+.

### 11.5 Suggested next step (MODE B)

Lock **Phase 24.1 — Capability domain (schema + registry only)** as the first implementation slice: add `capability_domain` to ToolSchema and populate from category; update `system_schema.json` if tool_request or tool listing exposes it; no execution or permission logic change. Then proceed to MODE B (specification) to lock exact fields and exit criteria.

---

## 12. MODE B — LOCKED SPECIFICATION: PHASE 24.1 (BINDING)

*The following scope is **locked** after MODE B. MODE C implementation must conform to this specification. Any change requires explicit approval.*

### 12.1 Phase 24.1 — Capability domain (schema + registry only)

**Objective:** Introduce **capability_domain** for tools so that tools are grouped by domain. No change to execution, permissions, or orchestration behavior.

### 12.2 Locked scope

| Item | Specification |
|------|----------------|
| **ToolSchema** | Add optional field `capability_domain: Optional[str] = None`. Allowed values: `"file"`, `"memory"`, `"system"`, `"automation"`, `"content"`, `"integration"`, `"general"`. If absent, treat as `"general"`. |
| **Population** | When registering tools, set `capability_domain` from existing `category` where mapping is obvious (e.g. category `"file"` → domain `"file"`); otherwise `"general"`. |
| **Registry** | No change to registry lock or registration API. Registry continues to store ToolSchema; new field is optional and backward-compatible. |
| **system_schema.json** | Optional update applied: added `capability_domain` definition (enum) and optional property on `tool_request`; verification report and checklist updated. |
| **Execution path** | No change. Orchestrator and MCP do not branch on capability_domain. |
| **Laws** | LAW 4, 6 unchanged. No new law. |

### 12.3 Exit criteria

- [x] `ToolSchema` in `mcp/tool_schema.py` has `capability_domain: Optional[str] = None` with allowed values as above.
- [x] All tools registered in `tools/tool_registration.py` (and any other registration sites) pass a `capability_domain` consistent with their category (or `"general"`).
- [x] Existing tests pass (tool registry, MCP, phase 11 tool tests).
- [x] No new tests required for 24.1 unless a test explicitly asserts tool schema shape; then update assertion to allow capability_domain.

*Phase 24.1 implemented 2026-01-26. See `docs/PHASE_COMPLETION_REPORTS/PHASE_24.1_COMPLETION_STATUS.md`.*

### 12.4 Out of scope for 24.1

- side_effect_scope, preconditions, postconditions, dry-run, inspect. (Defer to 24.2+.)
- Changes to orchestration or permission logic.
- Changes to system_schema.json tool_request or tool execution flow.

---

## 13. MODE A — PHASE 24.2 DESIGN PROPOSAL (NON-BINDING)

*This section is **PROPOSAL / NON-BINDING**. Output of MODE A (Design/Exploration) for the next evolution slice. Nothing here is implemented until MODE B locks scope and MODE C implements.*

### 13.1 Phase 24.2 objective (from §11, §12.4)

Introduce **side-effect scope** for tools so that tools are explicitly classified by the kind of side effect they can cause. Descriptive only in 24.2: no execution or permission logic change (same constraint as 24.1).

### 13.2 Current state (post–Phase 24.1)

- **ToolSchema** has `capability_domain` (optional), `permission_level` (NONE, READ, WRITE, EXECUTE), `requires_confirmation`.
- **tool_request** in system_schema.json has optional `capability_domain`; orchestrator populates it from registry.
- No explicit "side-effect scope" field; permission_level is the closest.

### 13.3 Proposal: first slice (24.2) options

**Option 24.2a — side_effect_scope only (recommended for first cycle):**

- **Scope:** Add optional `side_effect_scope: Optional[str] = None` to ToolSchema. Allowed values: `"READ_ONLY"`, `"WRITE"`, `"EXECUTE"`, `"EXTERNAL"`. Populate from existing `permission_level` and tool semantics (e.g. READ → READ_ONLY, WRITE → WRITE, EXECUTE → EXECUTE; tools that call network/OS get EXTERNAL). No change to execution path; no new permission checks. Schema and registry only; optional on tool_request in system_schema if we want clients to display it.
- **Rationale:** Establishes side-effect classification without behavior change. Enables future dry-run or confirmation UX to be scope-aware. Reversible.
- **Risks:** Schema drift if side_effect_scope and permission_level ever diverge; keep them aligned by derivation from permission_level + tool name/semantics.

**Option 24.2b — side_effect_scope + system_schema + orchestrator:**

- Option 24.2a plus: add `side_effect_scope` definition to system_schema.json and optional property on tool_request; orchestrator populates it when building tool_request (same pattern as capability_domain).
- **Rationale:** Full contract and API consistency for clients (Web, TUI, CLI) to show or filter by side-effect scope.

**Option 24.2c — Defer Phase 24.2:**

- Do not implement side_effect_scope now. Move to another track (e.g. onboarding wizard, operator UX) and return to Phase 24.2 later.

### 13.4 Dependencies and risks

- **Dependencies:** Phase 24.1 complete. Existing tests should pass if field is optional.
- **Risks:** 24.2a/24.2b — low. Keeping side_effect_scope derived from permission_level and tool semantics avoids divergence.
- **Blind spots:** Preconditions, postconditions, dry-run remain out of scope for 24.2; they require orchestrator/MCP contract changes (24.3+).

### 13.5 Suggested next step (MODE B)

If you want to proceed with Phase 24.2: choose **24.2a** (schema + registry only) or **24.2b** (+ system_schema + orchestrator). Then MODE B will lock the chosen scope (allowed values, derivation rules, exit criteria). After your approval of the locked spec, MODE C implements; then MODE D reviews.

If you prefer to **defer 24.2** (Option 24.2c), say so and we can run MODE A for a different phase (e.g. onboarding wizard, operator doctor UX) instead.

---

## 14. MODE B — LOCKED SPECIFICATION: PHASE 24.2 (BINDING)

*The following scope is **locked** for Phase 24.2 (Option 24.2a). MODE C implementation must conform. Any change requires explicit approval.*

### 14.1 Phase 24.2 — Side-effect scope (schema + registry only)

**Objective:** Introduce **side_effect_scope** for tools so that tools are explicitly classified by the kind of side effect they can cause. Descriptive only: no change to execution, permissions, or orchestration behavior.

### 14.2 Locked scope

| Item | Specification |
|------|----------------|
| **ToolSchema** | Add optional field `side_effect_scope: Optional[str] = None`. Allowed values: `"READ_ONLY"`, `"WRITE"`, `"EXECUTE"`, `"EXTERNAL"`. If absent, treat as `"READ_ONLY"`. |
| **Population** | When registering tools, set `side_effect_scope` from `permission_level` and tool semantics: NONE/READ → `"READ_ONLY"`; WRITE → `"WRITE"`; EXECUTE → `"EXECUTE"` for local execution tools, `"EXTERNAL"` for tools that trigger sync, automation, or network/OS (e.g. trigger_sync, trigger_automation, speak, listen). |
| **Registry** | No change to registry lock or API. New field optional and backward-compatible. |
| **system_schema.json** | No change for 24.2a (optional in a later slice). |
| **Orchestrator** | No change. Does not populate or branch on side_effect_scope in 24.2a. |
| **Execution path** | No change. |
| **Laws** | LAW 4, 6 unchanged. No new law. |

### 14.3 Exit criteria

- [x] `ToolSchema` in `mcp/tool_schema.py` has `side_effect_scope: Optional[str] = None` with allowed values READ_ONLY, WRITE, EXECUTE, EXTERNAL.
- [x] All tools registered pass a `side_effect_scope` consistent with derivation rules above.
- [x] Existing tests pass. No new tests required unless a test asserts tool schema shape; then update assertion.

### 14.4 Out of scope for 24.2a

- Adding side_effect_scope to system_schema.json or tool_request (defer to 24.2b or later).
- Orchestrator populating side_effect_scope on tool_request.
- Preconditions, postconditions, dry-run, inspect (24.3+).

---

## 15. MODE A — NEXT PHASE DESIGN PROPOSAL (NON-BINDING)

*This section is **PROPOSAL / NON-BINDING**. Output of MODE A for the next evolution slice. Nothing here is implemented until MODE B locks scope and MODE C implements.*

### 15.1 Current state (post–Phase 24.2 and 24.2b)

- **ToolSchema** has `capability_domain`, `side_effect_scope` (optional), `permission_level`, `requires_confirmation`.
- **tool_request** has optional `capability_domain` and `side_effect_scope`; orchestrator populates both from registry (Phase 24.1, 24.2b).
- **L3 schema:** `scripts/supabase_schema.sql` is idempotent (Phase 22 columns, RLS policies, trigger); aligned with `memory/database_schema.py`.
- No tool preconditions/postconditions, no dry-run or inspect in orchestrator/MCP.

### 15.2 Candidate next phases

| Option | Scope | Effort | Notes |
|--------|--------|--------|--------|
| **24.2b** | Add `side_effect_scope` to system_schema.json and orchestrator (populate on tool_request, same pattern as capability_domain) | Small | Natural follow-on to 24.2a; no execution change. |
| **24.3** | Tool preconditions, postconditions, dry-run, inspect (orchestrator + MCP contract) | Large | Requires schema for pre/post, dry-run mode in execution path, LAW 2/4 alignment. |
| **Onboarding wizard** | OpenClaw-inspired: guided first-run setup (config, paths, optional services), no autonomy | Medium | LAW 1, 2; explicit steps, user confirms each. |
| **Operator doctor UX** | OpenClaw-inspired: health narrative, “doctor” checks (config, migrations, logs, connectivity), read-only diagnostics | Medium | LAW 23 alignment; no remediation without user action. |

### 15.3 Suggested next step (MODE B)

- ~~To **extend 24.2** with API/contract consistency: choose **24.2b**~~ — **Done.** Phase 24.2b complete (§16).
- To **defer tool metadata** and invest in operator/onboarding UX: choose **Onboarding wizard** or **Operator doctor UX** and run MODE A in more detail for the chosen track, then MODE B lock.
- To **invest in tool safety/audit** (dry-run, pre/post): choose **24.3** and run a focused MODE A for 24.3 (scope slice, risks, exit criteria) before MODE B.

### 15.4 Next action

Choose one of the three tracks above and say which to proceed with. Then MODE A will expand that track (scope, risks, exit criteria); after your approval, MODE B locks the spec and MODE C implements.

---

## 17. MODE A — ONBOARDING WIZARD DESIGN PROPOSAL (NON-BINDING)

*This section is **PROPOSAL / NON-BINDING**. Output of MODE A for the Onboarding wizard track. Nothing here is implemented until MODE B locks scope and MODE C implements.*

### 17.1 Objective

OpenClaw-inspired **guided first-run setup** for Siya: a wizard that walks the user through initial configuration (paths, optional services, model location) with **explicit steps and user confirmation at each step**. No autonomous decisions; no execution without user approval. Product name remains **Siya**.

### 17.2 Laws and constraints

- **LAW 1 (Human sovereignty):** Every wizard step that writes config or state requires explicit user confirmation. No auto-apply.
- **LAW 2 (No autonomous execution):** Wizard does not trigger tools or automations on its own; it only suggests and waits for user to confirm.
- **LAW 4, 6:** Any persistent change goes through declared tools or explicit config write; no hidden paths.

### 17.3 Candidate scope (pick one or subset for first slice)

| Item | Description | Effort |
|------|-------------|--------|
| **Detection** | Detect “first run” (e.g. no config file or empty, or explicit “onboard” command). Skip wizard if already onboarded. | Small |
| **Steps (minimal)** | (1) Welcome / what the wizard does; (2) Data directory path (where Siya stores DB, logs); (3) Optional: Supabase (L3) — use or skip; (4) Optional: AI model path (or use default); (5) Summary and “Apply” (writes config only after user confirms). | Medium |
| **CLI entry** | e.g. `siya onboard` or `siya wizard` (or first run of `siya` prompts “Run onboarding?”). | Small |
| **Persistence** | Write only to agreed config (e.g. `config/server_config.py` or env file); no tool execution. | Small |
| **Idempotency** | User can re-run wizard to change choices; overwrites config with confirmation. | Small |

### 17.4 Out of scope for this proposal

- Operator doctor (health checks); separate track (§15).
- 24.3 (dry-run, pre/post); separate track.
- Web/TUI wizard UI (can be Phase 2 after CLI wizard exists).

### 17.5 Risks and dependencies

- **Risks:** Wizard logic must not bypass confirmation; config write must be explicit and logged (LAW 13). First-run detection must be reliable so wizard doesn’t re-run every time.
- **Dependencies:** Existing config loading (e.g. `config/server_config.py`, `.env`); no new persistence layer.

### 17.6 Suggested next step (MODE B)

If you want to implement the Onboarding wizard: choose a **first slice** (e.g. detection + 2–3 steps: data path, optional Supabase, apply). Then MODE B will lock that slice (exit criteria, steps, config contract); MODE C implements; MODE D reviews. If you prefer **Operator doctor UX** or **24.3** first, say so and we expand that track instead.

---

## 18. MODE B — LOCKED SPECIFICATION: ONBOARDING WIZARD FIRST SLICE (BINDING)

*The following scope is **locked** for the Onboarding wizard first slice. MODE C implementation must conform. Any change requires explicit approval.*

### 18.1 Objective

Guided first-run setup for Siya (OpenClaw-inspired): CLI wizard that collects data directory path and optional Supabase preference, then writes config only after explicit user confirmation. No autonomous execution; no tool invocation. Product name: **Siya**.

### 18.2 Locked scope

| Item | Specification |
|------|----------------|
| **Onboarded detection** | Consider onboarded if marker file exists. Marker: project root `.siya_onboarded` or `~/.siya/.onboarded`. Wizard can be re-run by user request (e.g. `siya onboard` again) to update choices. |
| **CLI entry** | New entry point: `python -m cli.main onboard` or `siya onboard` (script). No change to existing interactive CLI unless we add `onboard` as subcommand. Prefer separate entry `cli/onboard.py` with `main()` and script `siya-onboard = "cli.onboard:main"`. |
| **Steps (order)** | (1) Welcome — what the wizard does; (2) Data directory — path where Siya stores DB (default `data` relative to project root or `~/.siya`); (3) Optional Supabase — skip or enter URL + key (stored in .env); (4) Summary — show choices; (5) Confirm — "Write config? (y/n)"; only on y proceed. |
| **Persistence** | On confirm: write or append to `.env` in project root (or user home `~/.siya` if no project root): `SIYA_DATA_DIR`, `SUPABASE_URL`, `SUPABASE_KEY` (optional). Create marker file so first-run detection works. Do not execute tools; do not start services. |
| **Laws** | LAW 1: explicit confirm before any write. LAW 13: log that config was written (audit). LAW 2: no autonomous execution. |

### 18.3 Exit criteria

- [x] Wizard runnable via `python -m cli.onboard` or `siya-onboard`.
- [x] Steps: welcome, data dir, optional Supabase, summary, confirm; config written only after confirm.
- [x] Marker file created after successful write; first-run detection documented.
- [x] No tool execution from wizard; no change to orchestrator/MCP from wizard.
- [x] Existing tests pass.
- [x] **CLI/Web parity (LAW 19, dev-rules §6.6):** Onboarding available via API (`GET /onboard/status`, `POST /onboard`) and web UI (wizard shown when not onboarded); core logic in `cli.onboard` shared by CLI and API.

### 18.4 Out of scope for first slice

- Web/TUI wizard UI.
- Operator doctor or health checks.
- Writing to config/server_config.py (use .env only for first slice).

---

## 16. MODE B — LOCKED SPECIFICATION: PHASE 24.2b (BINDING)

*The following scope is **locked** for Phase 24.2b. MODE C implementation must conform. Any change requires explicit approval.*

### 16.1 Phase 24.2b — side_effect_scope in system_schema + orchestrator

**Objective:** Add `side_effect_scope` to the system contract and API so clients (Web, TUI, CLI) can display or filter by it. Same pattern as `capability_domain`. No change to execution or permission logic.

### 16.2 Locked scope

| Item | Specification |
|------|----------------|
| **system_schema.json** | Add definition `side_effect_scope` (type string, enum READ_ONLY, WRITE, EXECUTE, EXTERNAL). Add optional property `side_effect_scope` on `tool_request` with `$ref` to that definition. Description: optional; when present, may be used for display or filtering. |
| **Orchestrator** | When building `tool_request` in `_intent_to_tool_request`, read `side_effect_scope` from tool registry (tool_schema.side_effect_scope). If not None, set `tool_request["side_effect_scope"] = tool_schema.side_effect_scope`. Same pattern as capability_domain. |
| **Execution path** | No change. |
| **Laws** | No change. |

### 16.3 Exit criteria

- [x] system_schema.json has `side_effect_scope` definition and optional `side_effect_scope` on tool_request.
- [x] Orchestrator populates `side_effect_scope` on tool_request from registry when present.
- [x] Existing tests pass.

### 16.4 Out of scope for 24.2b

- Preconditions, postconditions, dry-run, inspect (24.3+).
- Any branch or logic that uses side_effect_scope for execution or permission decisions.

---

**Document version:** 1.9  
**Last updated:** 2026-01-26  
**Status:** Phase 24.1, 24.2, 24.2b complete. §18 Onboarding wizard first slice implemented (MODE C). Next: MODE D review; or 24.3 / Operator doctor.  
**Changelog (v1.9):** §18 MODE B locked, MODE C implemented: cli/onboard.py, siya-onboard script, SIYA_DATA_DIR in memory/database.py.  
**Changelog (v1.8):** Added §17 MODE A — Onboarding wizard design proposal (non-binding); scope, laws, risks, suggested next step.
