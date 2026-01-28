# Phase 19: Full-Screen TUI

## Status: ✅ COMPLETE

**Date:** 2026-01-28  
**Objective:** Transform CLI into full-screen Terminal User Interface like Gemini CLI

---

## Technology

**Textual** v7.4.0 - Python framework for building rich terminal UIs

---

## Deliverables

### New Files Created
| File | Description |
|------|-------------|
| `pc_mcp_client/tui/__init__.py` | TUI package |
| `pc_mcp_client/tui/app.py` | Main Textual app with sidebar, output, modals |
| `pc_mcp_client/tui/styles.tcss` | CSS-like styling for layout |
| `pc_mcp_client/tui/widgets/__init__.py` | Widgets package |
| `pc_mcp_client/tui/modals/__init__.py` | Modals package |

### Modified Files
| File | Changes |
|------|---------|
| `pyproject.toml` | Added `textual>=0.95.0` |
| `pc_mcp_client/wake.py` | Launch TUI instead of old interactive mode |

---

## Layout

```
┌─ SIYA ─────────────────────────────────────────────────┐
│ Header: Title + Clock                                   │
├─────────────────┬───────────────────────────────────────┤
│ 📂 TOOLS        │ OUTPUT                                │
│ ───────         │ ────────                              │
│ ▸ System        │ [Scrollable results]                  │
│   get_system... │                                       │
│ ▸ Files         │                                       │
│ ▸ Sync          │                                       │
├─────────────────┴───────────────────────────────────────┤
│ > Input bar                                             │
├─────────────────────────────────────────────────────────┤
│ Footer: q Quit | ? Help | ↑↓ Navigate | Enter Execute   │
└─────────────────────────────────────────────────────────┘
```

---

## Features

### 1. Full-Screen Mode
- Takes over entire terminal viewport
- Responsive layout adapts to terminal resize

### 2. Sidebar Navigation
- Collapsible tool categories (System, Files, Sync, etc.)
- Tree view with arrow key navigation
- `(!)` indicator for confirmation-required tools

### 3. Scrollable Output
- RichLog widget for formatted output
- Full terminal scrollback support

### 4. Keyboard Shortcuts
| Key | Action |
|-----|--------|
| `q` | Quit |
| `?` | Help |
| `r` | Refresh tools |
| `Ctrl+L` | Clear output |
| `↑↓` | Navigate tree |
| `Enter` | Execute selected tool |
| `Escape` | Unfocus |

### 5. LAW 1 Confirmation Modal
- Modal overlay for confirmation-required tools
- `y` to confirm, `n` or `Escape` to cancel

---

## Usage

```powershell
# Launch full-screen TUI
siya

# Reset config if needed
siya --reset
```

---

## Dependencies Added
- `textual>=0.95.0` — Full-screen TUI framework
