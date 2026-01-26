# Siya Development Environment Setup
## Phase 0 — Foundation & Tooling

---

## PREREQUISITES

- Python 3.11 or 3.12 (locked to 3.11.9 in `.python-version`)
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
- Python version is locked to 3.11.9 (compatible with 3.11-3.12)

---

**Last Updated:** 2026-01-26
