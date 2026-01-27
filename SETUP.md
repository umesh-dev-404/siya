# Siya Development Environment Setup
## Phase 0 — Foundation & Tooling

---

## PREREQUISITES

- Python 3.11 through 3.14
- Git
- pip (Python package manager)

---

## SETUP INSTRUCTIONS

### 1. Clone Repository (if not already done)
```bash
git clone <repository-url>
cd siya
```

### 2. Create Virtual Environment

**Using venv (recommended):**
```bash
python -m venv .venv
```

**Using uv (faster, optional):**
```bash
uv venv
```

### 3. Activate Virtual Environment

**Windows (PowerShell):**
```powershell
.\.venv\Scripts\Activate.ps1
```

**Windows (CMD):**
```cmd
.venv\Scripts\activate.bat
```

**Linux/Mac:**
```bash
source .venv/bin/activate
```

### 4. Install Development Dependencies

```bash
pip install -e ".[dev]"
```

Or if using uv:
```bash
uv pip install -e ".[dev]"
```

This installs:
- `black` — Code formatter
- `ruff` — Fast linter
- `pytest` — Test framework
- `pytest-cov` — Coverage reporting
- `mypy` — Static type checker
- `supabase` — Cloud synchronization
- `SpeechRecognition` — Speech-to-Text
- `pyttsx3` — Text-to-Speech
- `sounddevice` — Audio capture
- `PyAudio` — Audio I/O (Windows)

### 5. Voice Interface Prerequisites (Linux/Pi)

If running on Linux/Raspberry Pi, you need system audio libraries:
```bash
sudo apt-get update
sudo apt-get install python3-pyaudio portaudio19-dev espeak alsa-utils
```

### 5. Verify Setup

**Run tests:**
```bash
pytest tests/ -v
```

**Check formatting:**
```bash
black --check .
```

**Run linter:**
```bash
ruff check .
```

**Type checking:**
```bash
mypy .
```

---

## DEVELOPMENT WORKFLOW

### Format Code
```bash
black .
```

### Lint Code
```bash
ruff check .
ruff check . --fix  # Auto-fix issues
```

### Run Tests
```bash
pytest tests/ -v
pytest tests/ --cov=. --cov-report=html  # With coverage
```

### Type Check
```bash
mypy .
```



### Build Release (Standalone CLI)
```bash
python scripts/build_release.py
```
*Generates a `.whl` in `dist/` for distribution to other PCs.*

---

## PROJECT STRUCTURE

```
siya/
├── core/              # Core system components
├── orchestrator/      # Orchestration engine
├── mcp/              # Model Control Plane
├── tools/            # Tool implementations
├── memory/           # Memory system
├── audit/            # Audit logging system
├── security/         # Security components
├── interfaces/       # Interface layer
├── cli/              # CLI interface
├── api/              # HTTP API
├── web/              # Web interface
├── automations/      # Automation modules
├── config/           # Configuration
├── system/           # System-level components
├── tests/            # Test suite
├── docs/             # Documentation
│   └── PHASE_COMPLETION_REPORTS/  # Phase completion reports
├── pyproject.toml    # Project configuration
├── .python-version   # Python version lock
├── .gitignore        # Git ignore patterns
└── README.md         # Project overview
```

---

## PHASE STATUS

### ✅ Phase 0 — Foundation & Tooling: COMPLETE
- ✅ Directory structure created
- ✅ Python environment configured
- ✅ Development tooling configured
- ✅ Tests can execute

### ✅ Phase 1 — Core Runtime Skeleton: COMPLETE
- ✅ Orchestration engine skeleton
- ✅ Execution lifecycle (INIT, VALIDATE, EXECUTE, VERIFY, COMMIT, FAIL, ABORT)
- ✅ Serial task execution (LAW 10)
- ✅ Transactional steps (LAW 11)
- ✅ Failure propagation (LAW 12)
- ✅ Logging hooks (LAW 13)

### ✅ Phase 2 — Governance & Control Plane: COMPLETE
- ✅ MCP as pure gatekeeper
- ✅ Tool schema framework
- ✅ Permission enforcement (LAW 5)
- ✅ Confirmation gating
- ✅ Request validation (LAW 3, LAW 4)
- ✅ Tool registry (LAW 4, LAW 6)
- ✅ Decision logging (LAW 13)

### ✅ Phase 3 — Memory & Observability: COMPLETE
- ✅ SQLite schemas (WAL enabled)
- ✅ Orchestrator-only memory writes (LAW 8)
- ✅ Memory tagging, confidence, lineage (LAW 9)
- ✅ Log retention and summarization (LAW 14)
- ✅ Audit logging (LAW 13)
- ✅ Supabase sync (stubbed)
- ✅ Memory access layer (read-only - LAW 7)

### ✅ Phase 5 — AI Integration (Controlled): COMPLETE
- ✅ Intent parsing interface (LAW 3)
- ✅ Strict JSON schema enforcement
- ✅ Model lifecycle management (stub)
- ✅ AI output validation
- ✅ AI cannot execute tools (LAW 3)
- ✅ AI cannot write memory (LAW 3)

### ✅ Phase 6 — Interfaces & UX Layer: COMPLETE
- ✅ CLI interface (primary debugging surface)
- ✅ HTTP API (mirrors CLI exactly)
- ✅ Local web interface (client-rendered)
- ✅ Identical behavior across interfaces
- ✅ No privilege escalation
- ✅ Explicit confirmations only (LAW 1)

### ✅ Phase 7 — Automation & Scheduling: COMPLETE
- ✅ Automation module framework
- ✅ Explicit entry points
- ✅ Serial execution enforced (LAW 10)
- ✅ Execution state persistence
- ✅ Abort on reboot + notify
- ✅ No overlapping automations
- ✅ Complete audit trails (LAW 13)

### ✅ Phase 8 — Failure Injection & Hardening: COMPLETE
- ✅ Failure detection framework (LAW 12)
- ✅ Power loss handling (structure)
- ✅ Network loss handling
- ✅ AI crash handling
- ✅ Tool failure handling
- ✅ Resource exhaustion handling
- ✅ State consistency checking
- ✅ No silent failures (LAW 12)
- ✅ User notification framework

### ✅ Phase 9 — Production Lock & Baseline: COMPLETE
- ✅ Schema version locked (1.0.0)
- ✅ Tool registry locked
- ✅ Deployment documentation
- ✅ Recovery checklist
- ✅ Release information
- ✅ System reproducible
- ✅ System auditable
- ✅ System stable

**Status: ✅ PRODUCTION BASELINE COMPLETE**

**Production Lock:**
- ✅ Schema version 1.0.0 locked
- ✅ Tool registry locked
- ✅ Production lock finalized

**Ready for Deployment:**
- See `docs/DEPLOYMENT.md` for deployment instructions
- See `docs/RECOVERY_CHECKLIST.md` for recovery procedures
- See `docs/RELEASE.md` for release information

---

## NOTES

- No application logic exists yet (per Phase 0 requirements)
- Only `__init__.py` files and placeholder test exist
- All dependencies are development-only (no runtime deps in Phase 0)
- Python version is consistent with 3.11-3.14

---

---

## RUNNING THE PC MCP CLIENT (GLOBAL CLI)

To make the CLI accessible from anywhere (not just the project root), install the package in editable mode:

### 1. Install CLI Globally
```powershell
# From project root
pip install -e .
```
This registers the `siya-cli` command in your environment.

### ⚠️ Troubleshooting: Command Not Found?
If you see a warning about the script directory not being on PATH, or if `siya-cli` is not recognized, add the Python Scripts directory to your PATH.

**Windows (PowerShell) - Add Permanently:**
```powershell
[Environment]::SetEnvironmentVariable("Path", $env:Path + ";$env:APPDATA\Python\Python314\Scripts", "User")
```
*Restart your terminal after running this command.*

**Temporary Fix (Current Session):**
```powershell
$env:PATH += ";$env:APPDATA\Python\Python314\Scripts"
```

### 2. Usage (From Anywhere)
Now you can run commands from any folder:

**Check Connectivity:**
```powershell
siya-cli --transport http --url http://192.168.1.39:8080 server-info
```

**List Tools:**
```powershell
siya-cli --transport http --url http://192.168.1.39:8080 list-tools
```

**Call a Tool:**
```powershell
siya-cli --transport http --url http://192.168.1.39:8080 call get_system_status
```

*Note: You can still use `python -m pc_mcp_client.main ...` from the project root if preferred.*

---

## SUPABASE CONFIGURATION (PHASE 13)

Phase 13 adds cloud synchronization via Supabase for L3 memory tier.

### 1. Create Supabase Project

1. Go to [supabase.com](https://supabase.com) and create a free account
2. Create a new project
3. Wait for the project to initialize

### 2. Run Database Schema

1. In Supabase Dashboard → **SQL Editor** → **New Query**
2. Copy content from `scripts/supabase_schema.sql`
3. Run the query to create all tables

### 3. Get API Credentials

From Supabase Dashboard → **Settings** → **API**:
- Copy **Project URL** (e.g., `https://abc123.supabase.co`)
- Copy **anon/public key** (safe for client-side)

### 4. Configure Environment

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and add your credentials:
   ```
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_ANON_KEY=your-anon-key
   ```

> **⚠️ IMPORTANT (LAW 15):** Never commit `.env` to version control!

---

**Last Updated:** 2026-01-27

