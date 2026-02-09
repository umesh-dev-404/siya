# Client Distribution Guide
## How to install Siya CLI on a separate PC

This guide explains how to package and install the `siya-cli` client on a computer that does not have the source code.

## Option 1: Cloud Install (Direct from GitHub)

**Prerequisite:** `git` must be installed.

Run this single command on the new PC:
```powershell
pip install "git+https://github.com/YOUR_USERNAME/siya.git"
```
**Benefits:**
- ✅ No need to build or copy files manually.
- ✅ Consumes no disk space for a project folder (installs locally to Python).
- ✅ Updates easily (run the command again).

---

## Option 2: Manual Build (Offline / USB Transfer)

Use this if you cannot connect to GitHub or prefer manual control.

### 1. On the Developer Machine (With Source Code)

You will generate a Python package file (`.whl`) that acts as a standalone installer.

### A. Run the Build Script
From the project root (`siya/`):
```powershell
python scripts/build_release.py
```
*This automatically cleans old builds, installs dependencies, and generates the new package.*

### B. Locate the Artifact
Check the `dist/` directory. You will see a file similar to:
`dist/siya-0.1.0-py3-none-any.whl`

---

### 2. On the Target Machine (No Source Code)

### A. Prerequisites
- Python 3.11+ installed
- `pip` installed

### B. Transfer and Install
1. Copy the `.whl` file from the developer machine to the target machine.
2. Open a terminal in the folder where you copied the file.
3. Install it:
   ```powershell
   pip install siya-0.1.0-py3-none-any.whl
   ```
   *(Note: Adjust the filename if the version differs)*

### C. Verify Installation
Run the CLI to confirm it works:
```powershell
siya-cli --help
```

---

## Usage

You can now use `siya-cli` normally from any folder on the new PC.

**Connect to Pi:**
```powershell
siya-cli --transport http --url http://<PI_IP>:8080 server-info
```

**Platform scope:** Mobile interface will be a **Siya-owned Android app** (planned). No third-party messaging (WhatsApp, Telegram, etc.). See `docs/EVOLUTION_ROADMAP.md` §4.1. OpenClaw-inspired capabilities (e.g. setup wizard) are adopted/adapted in Siya where law-aligned; product name remains Siya.

---

**Last Updated:** 2026-01-26
