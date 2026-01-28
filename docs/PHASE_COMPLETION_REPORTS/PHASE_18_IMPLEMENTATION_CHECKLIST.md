# Phase 18: Interactive CLI

## Status: ✅ COMPLETE

**Date:** 2026-01-28  
**Objective:** Transform CLI into interactive terminal application with simple wake command

---

## Deliverables

### New Files Created
| File | Description |
|------|-------------|
| `pc_mcp_client/ui/__init__.py` | UI package |
| `pc_mcp_client/ui/banner.py` | ASCII art banner with pyfiglet |
| `pc_mcp_client/ui/output.py` | Rich panels, tables, spinners |
| `pc_mcp_client/ui/menus.py` | Arrow-key menus with categories |
| `pc_mcp_client/ui/prompts.py` | Argument prompts, LAW 1 dialog |
| `pc_mcp_client/interactive.py` | Main interactive loop |
| `pc_mcp_client/wake.py` | Simple `siya` wake command with config |

### Modified Files
| File | Changes |
|------|---------|
| `pyproject.toml` | Added rich, InquirerPy, pyfiglet; added `siya` entry point |
| `pc_mcp_client/main.py` | Added `-i` flag for interactive mode |
| `docs/DEPLOYMENT.md` | Added Tailscale remote access section |

---

## Features

### 1. Simple Wake Command
```powershell
siya              # Auto-connects (first run prompts for URL)
siya --reset      # Reset saved config
```

Config saved to: `~/.siya/config.json`

### 2. ASCII Banner
```
   _____ ______  _____ 
  / ___//  _/\ \/ /   |
  \__ \ / /   \  / /| |
 ___/ // /    / / ___ |
/____/___/   /_/_/  |_|

Personal Assistant Platform v1.0.0
[+] Connected to http://<pi-ip>:8080
```

### 3. Arrow-Key Menus
- Categorized tools (System, Files, Sync, etc.)
- Separator lines between categories
- `(!)` indicator for confirmation-required tools
- Type to filter/search

### 4. Styled Output
- Green success panels
- Red error panels
- Yellow warning panels
- Animated spinners during execution

### 5. LAW 1 Confirmation
```
╭─ ⚠ CONFIRMATION REQUIRED ─────────────────────╮
│ Tool: trigger_sync                             │
│ Arguments:                                     │
│   Direction: push                              │
│                                                │
│ This action requires your explicit confirmation│
│ LAW 1: Human Sovereignty                       │
╰────────────────────────────────────────────────╯
? Proceed with execution? (y/N):
```

---

## Usage

### Simple Wake Command (Recommended)
```powershell
siya              # First run: prompts for Pi URL, saves config
siya              # Subsequent: auto-connects
siya --reset      # Reset config (e.g., switch from LAN to Tailscale)
```

### Traditional CLI (for scripts)
```powershell
siya-cli -i --transport http --url http://<pi-ip>:8080
siya-cli --transport http --url http://<pi-ip>:8080 call get_system_status
```

### Remote Access via Tailscale
```powershell
# Reset and reconfigure for Tailscale
siya --reset
siya
# Enter: http://100.67.9.101:8080 (your Tailscale IP, port 8080)
```

> **Note:** CLI uses port **8080** (API), Web interface uses port **3000**.

---

## Dependencies Added
- `rich>=13.0.0` — Styled terminal output
- `InquirerPy>=0.3.4` — Interactive menus
- `pyfiglet>=0.8` — ASCII art
