# SIYA: THE COMPREHENSIVE SYSTEM ARCHITECTURE & EVOLUTION REPORT

**Date:** 2026-01-28
**Version:** 1.0.0 (Production Baseline)
**Status:** ✅ SYSTEM FEATURES COMPLETE
**Target:** Raspberry Pi 5 (8GB RAM)

---

## 1. EXECUTIVE SYSTEM OVERVIEW

**Siya** is not merely a chatbot; it is a **Personal Governance Operating System**. It fundamentally reimagines the relationship between user and AI by inverting the typical power dynamic. Instead of an autonomous agent that acts on your behalf with opaque logic, Siya is a **deterministic processor** that requires explicit human sovereignty for every significant state change.

It is architected as a **Model Context Protocol (MCP) Server**, a standard that decouples the "brain" (AI) from the "body" (Tools/System). This ensures that the AI model (Qwen 2.5 3B) is never trusted with direct execution authority. It allows the system to run **Local-First**, ensuring all data, logic, and execution happen physically on the user's Raspberry Pi 5, with the cloud (Supabase) used solely for encrypted synchronization.

---

## 2. DETAILED PHASE-BY-PHASE EVOLUTION

The project was executed in strict, gated phases. Each phase required verification against specific exit criteria before proceeding.

### 🔴 PHASE 0: FOUNDATION & GOVERNANCE
**Goal:** Establish the immutable laws and development environment.
*   **The Constitution:** We drafted the `CANONICAL SYSTEM LAWS.md`, defining the 19 immutable laws (e.g., **LAW 1: Human Sovereignty**, **LAW 19: Interface Consistency**). These are not guidelines; they are constraints hard-coded into the system.
*   **Environment:** Set up Python 3.11 virtual environment, established `pyproject.toml` with strict dependencies (`pydantic`, `fastapi`), and configured linting (`ruff`, `black`) to ensure code quality from line one.
*   **Safety:** Created `dev-rules.md` to govern AI coding behavior, ensuring no "autonomous" code was ever written.

### 🔴 PHASE 1: THE CORE RUNTIME SKELETON
**Goal:** Build the deterministic brain (Orchestrator) without AI.
*   **Orchestration Engine (`orchestrator/orchestrator.py`):** We built a state machine that transitions through `INIT` → `VALIDATE` → `EXECUTE` → `COMMIT`. It was designed to run *serially* (**LAW 10**), ensuring no two tasks ever race against each other.
*   **Context Foundation (`core/system_context.py`):** A thread-safe singleton (using `threading.RLock`) was created to hold the "truth" of the system. We implemented the initial L1 Memory (RAM) structures here.
*   **Outcome:** A system that could "run" a hardcoded task but had no intelligence.

### 🔴 PHASE 2: MODEL CONTROL PLANE (MCP) SERVER
**Goal:** create the standardized API layer.
*   **Server Implementation (`mcp/mcp_server.py`):** We implemented the MCP protocol, allowing external clients to discover tools and execute them.
*   **Schema Enforcement (`mcp/request_validator.py`):** We integrated `system_schema.json` (Draft-07) using `jsonschema`. Every request entering the system is validated against this strict contract. If a request doesn't match the schema, it is rejected before reaching any logic.
*   **Outcome:** A valid MCP server that could accept JSON commands.

### 🔴 PHASE 3: MEMORY & OBSERVABILITY
**Goal:** Give the system a persistent memory.
*   **Database (`memory/database.py`):** We chose SQLite for its reliability and single-file simplicity. We designed a normalized schema (`memory/database_schema.py`) to store Audit Logs, Memory Entries, and Tool Executions.
*   **Audit Logging (`audit/audit_logger.py`):** We built an immutable logging system. Every action (Intent Parsed, Tool Executed) is written to the DB. This satisfies **LAW 13 (Complete Auditability)**.
*   **Tier Manager (`memory/tier_manager.py`):** We architected the 3-tier memory system:
    *   **L1:** Active Context (RAM)
    *   **L2:** Short-term History (SQLite, 7-day retention)
    *   **L3:** Long-term Knowledge (Supabase sync design)

### 🔴 PHASE 4: SECURITY & PERMISSIONS
**Goal:** Enforce LAW 1 (Human Sovereignty) and LAW 15 (Secret Isolation).
*   **Confirmation Logic:** We added the `requires_confirmation` boolean to the `Tool` class. If true, the Orchestrator *suspends* execution and returns a `CONFIRMATION_REQUIRED` state.
*   **Path Locking:** implemented `tools/file/` security to prevent the system from reading/writing outside of specific allowed directories (preventing access to `/etc/shadow` or other OS files).

### 🟠 PHASE 5: AI INTEGRATION (INITIAL)
**Goal:** Connect the brain, initially using logic before the real model.
*   **Intent Parser (`ai/intent_parser.py`):** We built the module that takes natural language ("Check my files") and converts it into the JSON Intent Schema.
*   **Context Management (`ai/context_manager.py`):** Implemented the sliding window logic (4096 tokens) to manage what the AI "sees" of the conversation history.

### 🟠 PHASE 6: INTERFACES (BASE)
**Goal:** Allow the user to talk to the system.
*   **CLI (`siya-cli`):** Built a Python CLI tool using `argparse` that talks HTTP to the MCP server.
*   **Web (`web/`):** Created a basic HTML/JS interface to prove the API worked from a browser.

### 🟠 PHASE 7: AUTOMATION FRAMEWORK
**Goal:** Enable the system to act on time, not just user input.
*   **Systemd Integration (`automations/systemd_timer.py`):** Instead of writing a fragile Python `while True` loop, we decided to generate native Linux `systemd` unit files. When a user says "Remind me daily", Siya generates a `.timer` file and reloads systemd. This ensures automations survive reboots and crashes.

### 🟠 PHASE 8: FAILURE HANDLING & HARDENING
**Goal:** Ensure the system degrades gracefully.
*   **Resource Monitoring (`system/resource_monitor.py`):** Added logic to check RAM/CPU. If RAM > 90%, the system refuses new large tasks.
*   **Offline Mode:** verified that if the internet is cut, the system continues to function locally (queuing syncs for later).

### 🟡 PHASE 9: PRODUCTION LOCK
**Goal:** Freeze the API.
*   We declared `v1.0.0` of the schema. From this point on, no breaking changes were allowed to the API contracts. This ensured the Frontend and Backend could evolve independently without breaking each other.

### 🟢 PHASE 10: REAL AI MODEL INTEGRATION
**Goal:** The "Brain Transplant".
*   **Model:** Qwen 2.5 3B Instruct (Quantized Q4_K_M). Chosen for its balance of reasoning capability and low RAM footprint (~3GB) suitable for Pi 5.
*   **Llama.cpp Wrapper (`ai/llama_wrapper.py`):** We replaced the stub AI with `llama-cpp-python`. We implemented **full RAM loading** (`use_mmap=False`) to force the model into memory for speed (10-30s inference vs minutes).
*   **JSON Repair:** We added a robustness layer that fixes common LLM JSON syntax errors (missing brackets, trailing commas) before parsing.

### 🟢 PHASE 11: TOOL IMPLEMENTATIONS
**Goal:** Give the system hands.
*   **Implemented 25+ Tools:**
    *   `system`: Status, Restart.
    *   `time`: Create/List Timers.
    *   `file`: Read/Write/List (Secure).
    *   `memory`: Search/Write.
    *   `voice`: Speak/Listen.
    *   `sync`: Trigger Sync, Get Status.

### 🟢 PHASE 12: SYSTEM CONTEXT REFINEMENT
**Goal:** Make the AI "aware" of state.
*   We refined `SystemContext` to inject **Session History**, **State Snapshots**, and **Relevant Memories** into the AI's prompt at runtime. This gives the AI "short-term memory" of what you just talked about.

### 🟢 PHASE 13: SUPABASE SYNCHRONIZATION (L3)
**Goal:** Cloud backup and multi-device readiness.
*   **Supabase Client (`sync/supabase_client.py`):** Implemented a real REST client for Supabase.
*   **Sync Queue (`sync/sync_queue.py`):** Built a persistent SQLite queue. Modifications are written here first. A background process flushes them to Supabase when online. This guarantees **Offline-First** reliability.

### 🟢 PHASE 14: AUTOMATION VERIFICATION
**Goal:** Verify Systemd timers used in Phase 7.
*   We verified that `schedule_automation` tools correctly created `/home/pi/.config/systemd/user/siya-*.timer` files and that they actually fired the CLI commands as expected.

### 🟢 PHASE 15: NOTIFICATIONS
**Goal:** detailed feedback.
*   **Notification Engine (`notifications/`):** Created a central hub for system alerts. Stores notifications in SQLite and pushes them to active interfaces (Web/CLI).

### 🟢 PHASE 16: VOICE INTERFACE
**Goal:** Hands-free interaction.
*   **STT/TTS (`voice/`):** Integrated `SpeechRecognition` (Microphone input) and `pyttsx3` (Speaker output). Added graceful degradation: if no microphone is found, the system logs a warning but continues to function text-only.

### 🟢 PHASE 17: WEB INTERFACE REDESIGN
**Goal:** Professional aesthetic.
*   **Neo-Brutalism UI:** Completely overwrote the basic web UI with a modern, high-contrast "Neo-Brutalism" design (Bold borders, hard shadows).
*   **Dynamic Forms:** The UI reads the MCP Tool Schema and dynamically generates input forms for every tool, ensuring the UI creates valid JSON requests.
*   **Confirmation Modal:** Implemented a dedicated modal for **LAW 1**, forcing users to click "YES" to confirm destructive actions.

### 🟢 PHASE 18/19: INTERACTIVE CLI & CONSISTENCY
**Goal:** A beautiful terminal experience matching the Web.
*   **TUI (`pc_mcp_client/tui/`):** Used `textual` to build a full-screen terminal app. It has mouse support, menus, and the same "Neo-Brutalism" style (using ASCII block characters) as the web.
*   **Argument Modal:** Added `ArgumentModal` class that prompts for required tool arguments before execution, matching the Web interface's form behavior.
*   **Consistency (LAW 19):** We verified that the CLI and Web interface expose the *exact same* set of tools and follow the exact same confirmation logic.

---

## 3. FILE-LEVEL CODEBASE ANALYSIS

### `core/`
*   **`system_context.py`**: The singleton beating heart. Uses `threading.active_count()` and `psutil` to provide real-time health snapshots.
*   **`logging_config.py`**: Centralized logging configuration, ensuring logs go to both file (rotated) and stderr.

### `orchestrator/`
*   **`orchestrator.py`**: Contains the `execute_step()` method, which is the atomic unit of work in Siya. It wraps every execution in a `try...except` block to capture errors and write them to the `AuditLog`.
*   **`task_queue.py`**: A simple FIFO queue implementation. While Siya is currently single-threaded serial (LAW 10), this queue structure allows future expansion if strict serial execution laws are relaxed.

### `ai/`
*   **`llama_wrapper.py`**: Contains the `Llama` class instantiation. Key setting: `n_ctx=4096` (Context window) and `n_gpu_layers=0` (CPU only for Pi).
*   **`intent_parser.py`**: The `parse()` method contains the critical **System Prompt** injection. It constructs the prompt: `[System Instructions] + [Context] + [User Input]`.

### `memory/`
*   **`database.py`**: Uses `sqlite3` context managers. Contains the `init_db()` SQL scripts that create the `audit_logs`, `memories`, and `automation_state` tables if they don't exist.
*   **`tier_manager.py`**: The `promote_to_l3()` method exists here, handling the logic of moving important memories from local SQLite to the Sync Queue.

### `sync/`
*   **`sync_queue.py`**: Implements `enqueue(item)` and `dequeue()`. Uses a generic JSON payload structure so it can sync any type of data (Memory, Logs, Settings) in the future.
*   **`supabase_client.py`**: Contains the specific Supabase API calls (`client.table('...').insert(...)`).

### `mcp/`
*   **`tool_registry.py`**: A dictionary checking mechanism. `register_tool(name, func, schema)` stores the callable. `get_tool(name)` retrieves it. Simple, static, safe.

### `automations/`
*   **`systemd_timer.py`**: Pure string manipulation to generate valid `.service` and `.timer` file content. It then uses `subprocess.run(['systemctl', '--user', ...])` to install them.

### `web/`
*   **`web_server.py`**: Inherits from `http.server.SimpleHTTPRequestHandler`. Serves `index.html` for root, and proxies `/api/*` requests to the internal MCP handler.
*   **`static/app.js`**: 500+ lines of Vanilla JS. Handles the `fetch()` calls to the API, renders the DOM elements for tools, and manages the WebSocket-like polling for status.

### `pc_mcp_client/`
*   **`wake.py`**: The entry point. It checks for a `.siya/config.json`. If missing, it runs the "First Run Wizard". If present, it autoloads the URL and key.
*   **`interactive.py`**: The event loop for the TUI. Listens for keypresses and renders the `rich` Layout panels.

---

## 4. FEATURE IMPLEMENTATION SUMMARY

| Feature | Implementation Status | Technical Detail |
| :--- | :--- | :--- |
| **Parsing** | ✅ **Complete** | Parses natural language to JSON. Uses JSON Repair. |
| **Execution** | ✅ **Complete** | Validates schema, tracks state, executes Python functions. |
| **Memory** | ✅ **Complete** | 3-Tier System (RAM, SQLite, Cloud). |
| **Sync** | ✅ **Complete** | Offline-first, Conflict-solving sync engine. |
| **Voice** | ✅ **Complete** | Local STT/TTS with hardware degradation. |
| **Web UI** | ✅ **Complete** | Responsive, modern, full system control. |
| **TUI** | ✅ **Complete** | Terminal app with mouse support and menus. |
| **Timers** | ✅ **Complete** | Native systemd integration for reliability. |
| **Safety** | ✅ **Complete** | Confirmation modals, path locking, secret redaction. |

---

## 5. CONCLUSION

Siya has evolved from a set of abstract "Laws" into a concrete, functioning operating system. Every phase defined in the `DETAILED IMPLEMENTATION PLAN` has been executed, verified, and documented. The codebase contains no "stubs" or "placeholders" in its critical paths. It is a fully realized implementation of a deterministic, human-sovereign AI system running on the edge.
