# DEPLOYMENT GUIDE
## Project: Siya
## Version: 1.0.0 (Baseline)

---

## DEPLOYMENT STATUS

**Status:** ✅ DEPLOYED AND OPERATIONAL  
**Deployment Date:** 2026-01-27  
**Target:** Raspberry Pi 5  
**Service Status:** ✅ Running (systemd service active)  
**API Server:** ✅ Running on port 8080 (network accessible)  
**Web Interface:** ✅ Running on port 3000 (network accessible)

---

## OVERVIEW

This document describes the complete deployment process for Siya on Raspberry Pi 5, including:
- Initial setup and GitHub configuration
- Pi deployment and service configuration
- Network access configuration
- Model setup (see `AI_MODEL_GUIDE.md` for detailed model information)

**Platform scope:** Windows PC is the supported **client** (CLI/TUI/HTTP to Pi). No Mac in current plan. See `docs/EVOLUTION_ROADMAP.md` §4.1 and §3.7 (OpenClaw on Windows reference). OpenClaw-inspired capabilities (e.g. setup wizard) are adopted/adapted in Siya where law-aligned; product name remains Siya.

**Per DIP Phase 9: Production Lock & Baseline**

**Status:** ✅ Deployment completed and operational (2026-01-27)

## PREREQUISITES

### Hardware
- Raspberry Pi 5
- 8 GB RAM (minimum)
- MicroSD card (32 GB minimum, Class 10 or better)
- Power supply (official Pi 5 power supply recommended)

### Software
- Raspberry Pi OS Lite (64-bit)
- Python 3.11 through 3.14
- Git

---

## DEPLOYMENT STEPS

### 0. GitHub Setup (PC Side)

**Step 0.1: Initialize Git Repository**

```bash
# On PC
cd d:\Projects\siya
git init
git branch -M main

# Configure Git (if not already done)
git config user.name "Your Name"
git config user.email "your.email@example.com"
```

**Step 0.2: Create GitHub Repository**

1. Go to https://github.com/new
2. Repository name: `siya`
3. Visibility: Private (recommended) or Public
4. **DO NOT** initialize with README/.gitignore/license (we have these)
5. Click "Create repository"

**Step 0.3: Push to GitHub**

```bash
# Stage and commit
git add .
git commit -m "Initial commit: Siya v1.0.0-baseline"

# Add remote (replace YOUR_USERNAME)
git remote add origin https://github.com/YOUR_USERNAME/siya.git

# Push
git push -u origin main

# Optional: Create release tag
git tag -a v1.0.0-baseline -m "Siya v1.0.0-baseline"
git push origin v1.0.0-baseline
```

**Note:** For ongoing development, use:
```bash
git add .
git commit -m "Description"
git push origin main
```

### 1. Operating System Setup

1. Flash Raspberry Pi OS Lite (64-bit) to microSD card
2. Enable SSH (create `ssh` file in boot partition)
3. Configure WiFi (if needed) via `wpa_supplicant.conf`
4. Boot Pi and connect via SSH

### 2. System Hardening

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Enable firewall
sudo ufw enable
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Disable swap
sudo dphys-swapfile swapoff
sudo dphys-swapfile uninstall
sudo systemctl disable dphys-swapfile

# Enable automatic security updates
sudo apt install unattended-upgrades -y
```

### 3. Install Dependencies

**First, check available Python version:**
```bash
python3 --version
```

**Option A: If Python 3.11+ is available (recommended):**
```bash
# Install Python 3.11 and build tools
sudo apt install -y python3.11 python3.11-venv python3-pip git build-essential

# Install SQLite (WAL support)
sudo apt install -y sqlite3

# Install psutil for resource monitoring
pip3 install psutil
```

**Option B: If Python 3.11 is not available (use default Python 3):**
```bash
# Install default Python 3 and build tools
sudo apt install -y python3 python3-venv python3-pip git build-essential

# Install SQLite (WAL support)
sudo apt install -y sqlite3

# Install psutil for resource monitoring
pip3 install psutil

# Verify Python version (must be >= 3.11)
python3 --version
```

**Note:** Siya requires Python >= 3.11. If your Raspberry Pi OS has Python < 3.11, you'll need to:
1. Upgrade to a newer Raspberry Pi OS version, OR
2. Build Python 3.11 from source (see troubleshooting section)

### 4. Clone Repository from GitHub

```bash
# Install Git (if not installed)
sudo apt install -y git

# Navigate to installation directory
cd /opt

# Clone Siya repository (replace YOUR_USERNAME with your GitHub username)
sudo git clone https://github.com/YOUR_USERNAME/siya.git

# Set ownership (replace YOUR_PI_USERNAME with your actual Pi username, e.g., umesh404)
sudo chown -R YOUR_PI_USERNAME:YOUR_PI_USERNAME /opt/siya

# Navigate to project directory
cd /opt/siya

# Verify clone
git log --oneline -5

# Checkout production baseline tag (optional, if you created the tag)
# git checkout v1.0.0-baseline
```

**For Updates After Initial Deployment:**
```bash
cd /opt/siya
git pull origin main
pip install -e .  # Reinstall if dependencies changed
sudo systemctl restart siya  # Restart service
```

### 5. Setup Python Environment

**Important:** You must be in the project directory (`/opt/siya`) before creating the venv.

```bash
# Ensure you're in the project directory
cd /opt/siya

# Create virtual environment (use python3, it will use your system Python)
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Verify Python version in venv (must be >= 3.11)
python --version

# Upgrade pip
pip install --upgrade pip

# Install project dependencies
pip install -e .
```

**Note:** 
- Python 3.11 through 3.14 are supported (Python 3.13.5 confirmed working)
- The venv must be created **inside** the project directory (`/opt/siya`)
- You must clone the repository first before running `pip install -e .`
- Replace `YOUR_PI_USERNAME` with your actual Pi username (e.g., `umesh404`) in all commands

### 6. Initialize Database

```bash
# Run database initialization
python -c "from memory.database import MemoryDatabase; db = MemoryDatabase(); db.initialize(); print('Database initialized')"
```

**Note:** If you get import errors, ensure all dependencies are installed:
```bash
pip install -e .
```

### 7. Lock Production Baseline

```bash
# Lock schema version and tool registry
python -c "
from system.production_lock import ProductionLock
from mcp.mcp_server import MCPServer

mcp = MCPServer()
lock = ProductionLock()
lock.lock_schema_version('1.0.0')
lock.lock_tool_registry(mcp.get_tool_registry())
lock.finalize_lock()
print('Production lock finalized')
"
```

**Note:** Use full module paths (e.g., `system.production_lock` not just `system`) to avoid import issues.

### 8. Verify Installation

```bash
# Run state consistency check
python -c "
from memory.database import MemoryDatabase
from system.state_checker import StateChecker

db = MemoryDatabase()
db.initialize()
checker = StateChecker(db)
result = checker.check_state_consistency()
print(f'State consistent: {result[\"consistent\"]}')
"
```

**Note:** Use full module paths for imports to ensure proper module resolution.

---

## CONFIGURATION

### Environment Variables

Create `.env` file or set environment variables.
**Note:** The system automatically loads `.env` files using `python-dotenv`.

```bash
# Database path
export SIYA_DB_PATH=/opt/siya/siya.db

# Log level
export SIYA_LOG_LEVEL=INFO

# API configuration (0.0.0.0 allows network access from PC)
export SIYA_API_HOST=0.0.0.0
export SIYA_API_PORT=8080

# Web configuration (0.0.0.0 allows network access from PC)
export SIYA_WEB_HOST=0.0.0.0
export SIYA_WEB_PORT=3000

# API base URL for web interface (use Pi's IP address)
# IMPORTANT: Pi's IP address changes when router restarts. Find current IP with: hostname -I
export SIYA_API_BASE_URL=http://$(hostname -I | awk '{print $1}'):8080
```

**Important Notes:**
- Setting host to `0.0.0.0` allows access from your PC on the same network
- **Pi's IP address changes when router restarts** - you'll need to update `SIYA_API_BASE_URL` and reconnect from PC
- To find current IP: `hostname -I` (first IP shown is usually the one to use)
- See [Network Access](#network-access-from-pc) section below for details

---

## SERVICE SETUP (systemd)

The systemd service runs both API and web servers (`service_main.py`), which:
- Initializes all core components (MCP, AI Interface, Orchestrator, CLI)
- Starts the Orchestrator (enables task processing)
- Starts the CLI (enables command processing)
- Starts the HTTP API server on port 8080
- Starts the web interface server on port 3000
- Both servers run continuously in the background
- Automatically restarts on failure (with 10-second delay)
- Starts on system boot (if enabled)
- Accessible from your PC:
  - API: `http://<PI_IP>:8080`
  - Web Interface: `http://<PI_IP>:3000`

**Important Notes:**
- The service initializes Orchestrator and CLI components (required for command processing)
- The service does NOT run the interactive CLI. For interactive use, SSH into the Pi and run `python -m cli.main` manually.
- The service entry point is `service_main.py` (not `cli.main`)
- Orchestrator and CLI are started before servers to ensure proper initialization
- Both servers start automatically when the service starts
- All errors are logged to systemd journal (view with `sudo journalctl -u siya`)
- If service fails to start, check logs first: `sudo journalctl -u siya -n 50 --no-pager`

### Create Service File

Create `/etc/systemd/system/siya.service`:

```ini
[Unit]
Description=Siya Personal Assistant Platform
After=network.target

[Service]
Type=simple
User=YOUR_PI_USERNAME  # Replace with your actual Pi username (e.g., umesh404)
WorkingDirectory=/opt/siya
Environment="PATH=/opt/siya/venv/bin"
ExecStart=/opt/siya/venv/bin/python /opt/siya/service_main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Note:** The service runs the API server (not the interactive CLI). The API server starts on port 8080 and runs continuously. Access it from your PC at `http://<PI_IP>:8080`.

### Enable Service

```bash
sudo systemctl daemon-reload
sudo systemctl enable siya
sudo systemctl start siya
```

---

## VERIFICATION

### Check Service Status

```bash
sudo systemctl status siya
```

**Expected output:** Service should show `Active: active (running)` and the API server should be listening on port 8080.

### Check Logs

```bash
# View recent logs
sudo journalctl -u siya -n 50

# Follow logs in real-time
sudo journalctl -u siya -f
```

### Test API

```bash
# Test from Pi
curl http://localhost:8080/health

# Test from PC (replace with your Pi's IP)
curl http://192.168.1.39:8080/health
```

**Expected response:**
```json
{"status": "healthy", "service": "siya-api"}
```

### Test Web Interface

```bash
# Test from Pi
curl http://localhost:3000

# Test from PC (replace with your Pi's IP)
# Open in browser: http://192.168.1.39:3000
```

**Expected:** Web interface HTML page should load.

### Verify Servers are Running

```bash
# Check if ports 8080 and 3000 are listening
sudo netstat -tlnp | grep -E '8080|3000'

# Or using ss
sudo ss -tlnp | grep -E '8080|3000'
```

You should see:
- API server listening on `0.0.0.0:8080` (or `*:8080`)
- Web server listening on `0.0.0.0:3000` (or `*:3000`)

---

## NETWORK ACCESS FROM PC

### Overview

Siya's API and web interface are accessible over the network, allowing you to control the system from your PC while it runs on the Raspberry Pi.

**Current Status:**
- ✅ API Server: Running on port 8080 (network accessible)
- ✅ Web Interface: Running on port 3000 (network accessible)
- ✅ CORS: Configured (headers added to API server)

### Architecture

```
PC Browser/CLI → Pi IP:3000 (Web) or Pi IP:8080 (API) → Siya System
```

**Default Configuration:**
- API Host: `0.0.0.0` (all interfaces)
- API Port: `8080`
- Web Host: `0.0.0.0` (all interfaces)
- Web Port: `3000`

### ⚠️ CRITICAL: IP Address Management

**Your Raspberry Pi's IP address changes every time your router restarts.**

**Finding Current IP:**
```bash
# On Pi
hostname -I  # First IP shown is usually the one you need

# From PC (if you know Pi's hostname)
ssh YOUR_PI_USERNAME@raspberrypi "hostname -I"
```

**After Router Restart:**
1. Find new IP: `hostname -I` (on Pi)
2. Update `SIYA_API_BASE_URL` on Pi: `export SIYA_API_BASE_URL=http://NEW_IP:8080`
3. Update browser bookmarks on PC
4. Restart service: `sudo systemctl restart siya`

**Recommended: Configure Static IP**
- Log into router admin panel
- Find "DHCP Reservations" or "Static IP Assignment"
- Assign fixed IP (e.g., `192.168.1.100`) to Pi's MAC address
- Pi will always get the same IP even after router restarts

### Access from PC

**Web Interface:**
1. Find Pi's IP: `ssh YOUR_PI_USERNAME@raspberrypi "hostname -I"`
2. Open browser: `http://<PI_IP>:3000`
3. Web interface connects to API at `http://<PI_IP>:8080`

**API Direct Access:**
```bash
# Health check (from PC)
curl http://192.168.1.39:8080/health

# Send command (from PC)
curl -X POST http://192.168.1.39:8080/command \
  -H "Content-Type: application/json" \
  -d '{"command": "what can you do?"}'
```

**Windows PowerShell:**
```powershell
# Health check
Invoke-WebRequest -Uri http://192.168.1.39:8080/health

# Send command
$body = @{command="what can you do?"} | ConvertTo-Json
Invoke-WebRequest -Uri http://192.168.1.39:8080/command -Method POST -Body $body -ContentType "application/json"
```

### Troubleshooting: Service Running But Not Accessible from PC

**1. Check Firewall (Most Common Issue):**
```bash
# Check firewall status
sudo ufw status

# Allow ports
sudo ufw allow 8080/tcp
sudo ufw allow 3000/tcp

# Verify rules
sudo ufw status numbered
```

**2. Verify Port is Listening:**
```bash
# Check if ports are listening
sudo netstat -tlnp | grep -E '8080|3000'
# Should show: 0.0.0.0:8080 and 0.0.0.0:3000
```

**3. Test from Pi (Localhost):**
```bash
curl http://localhost:8080/health
# Should return: {"status": "healthy", "service": "siya-api"}
```

**4. Check Pi's Current IP:**
```bash
hostname -I
# IP may have changed if router restarted
```

**5. Test Network Connectivity from PC:**
```bash
# From PC
ping 192.168.1.39  # Replace with Pi's IP

# Test port (Windows PowerShell)
Test-NetConnection -ComputerName 192.168.1.39 -Port 8080
```

**6. Check CORS Configuration:**
- Web interface shows "Disconnected" → Check CORS headers in API server
- Should see: `Access-Control-Allow-Origin: *` in response headers

**Common Solutions:**
- **Firewall blocking:** `sudo ufw allow 8080/tcp && sudo ufw allow 3000/tcp`
- **Wrong IP address:** Check with `hostname -I` after router restart
- **Network isolation:** Ensure PC and Pi are on same network
- **Router blocking:** Some routers block inter-device communication

### Security Considerations

**Current Implementation:**
- No authentication (anyone on network can access)
- HTTP only (not HTTPS)
- Firewall recommended (restrict to local network)

**For Production:**
- Add authentication (future phase)
- Use HTTPS (future phase)
- Restrict to local network via firewall
- Consider VPN for remote access (see Tailscale below)

---

## REMOTE ACCESS VIA TAILSCALE

Tailscale provides secure remote access to your Pi from anywhere without exposing ports to the internet.

### Setup Tailscale on Pi

```bash
# Install Tailscale
curl -fsSL https://tailscale.com/install.sh | sh

# Authenticate
sudo tailscale up

# Get Tailscale IP
tailscale ip -4
# Example output: 100.67.9.101
```

### Access Siya via Tailscale

| Service | Tailscale URL |
|---------|---------------|
| **API Server (CLI)** | `http://<tailscale-ip>:8080` |
| **Web Interface** | `http://<tailscale-ip>:3000` |

**Example with Tailscale IP `100.67.9.101`:**
```bash
# Web Interface (browser)
http://100.67.9.101:3000

# CLI Interactive Mode
siya --reset                    # Reset old config
siya                            # Enter new URL: http://100.67.9.101:8080

# CLI Direct Commands
siya-cli --transport http --url http://100.67.9.101:8080 call get_system_status
```

### Switching Between Networks

When switching between LAN and Tailscale:

```powershell
# Reset saved CLI config
siya --reset

# Run siya and enter new URL when prompted
siya
# Enter: http://100.67.9.101:8080 (Tailscale)
# Or:    http://192.168.1.39:8080 (LAN)
```

> **Important:** The CLI uses port **8080** (API), not port 3000 (Web).

---

---

## QUICK REFERENCE

### Common Mistakes to Avoid

❌ **Running `pip install -e .` from home directory**
- ✅ **Fix:** Must be in `/opt/siya` directory

❌ **Creating venv in wrong location**
- ✅ **Fix:** Create venv inside `/opt/siya` directory

❌ **Forgetting to activate venv**
- ✅ **Fix:** Always run `source venv/bin/activate` before pip commands

❌ **Using sudo with pip in venv**
- ✅ **Fix:** Never use `sudo pip` when venv is activated

### Verification Commands

```bash
# Check Python version
python3 --version

# Check if in project directory
pwd  # Should show: /opt/siya

# Check if venv is activated
which python  # Should show: /opt/siya/venv/bin/python

# Check if project is installed
pip list | grep siya

# Check database
ls -la /opt/siya/siya.db
```

---

## TROUBLESHOOTING

### Python 3.11 Not Available

**Problem:** `python3.11` package not found in repositories.

**Solution 1: Check Default Python Version**
```bash
# Check what Python version is installed
python3 --version

# If Python 3.11+ is available, use it:
python3 -m venv venv
```

**Solution 2: Install Python 3.11 from Debian Backports (if available)**
```bash
# Add backports repository (if your Pi OS supports it)
echo "deb http://deb.debian.org/debian bookworm-backports main" | sudo tee /etc/apt/sources.list.d/backports.list
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3.11-dev
```

**Solution 3: Build Python 3.11 from Source (Advanced)**
```bash
# Install build dependencies
sudo apt install -y build-essential zlib1g-dev libncurses5-dev libgdbm-dev libnss3-dev libssl-dev libreadline-dev libffi-dev libsqlite3-dev wget libbz2-dev

# Download Python 3.11 source
cd /tmp
wget https://www.python.org/ftp/python/3.11.9/Python-3.11.9.tgz
tar -xf Python-3.11.9.tgz
cd Python-3.11.9

# Configure and build (this takes 30-60 minutes on Pi)
./configure --enable-optimizations --prefix=/usr/local
make -j4  # Use 4 cores, adjust based on your Pi
sudo make altinstall

# Verify installation
python3.11 --version

# Use it for venv
python3.11 -m venv /opt/siya/venv
```

**Solution 4: Use Available Python 3 (if >= 3.11)**
```bash
# Check version
python3 --version

# If >= 3.11, proceed with default python3
python3 -m venv venv
source venv/bin/activate
python --version  # Verify in venv
pip install -e .
```

**Note:** Siya requires Python >= 3.11, < 3.15 (so 3.11, 3.12, 3.13, and 3.14 are all supported). Python 3.13.5 and 3.14.0 are confirmed working. If your Pi only has Python 3.9 or 3.10, you must upgrade to Python 3.11+ using one of the methods above.

### Other Common Issues

**Permission Denied:**
```bash
# Fix ownership
sudo chown -R YOUR_PI_USERNAME:YOUR_PI_USERNAME /opt/siya
```

**Database Initialization Fails:**
```bash
# Ensure SQLite is installed
sudo apt install -y sqlite3
python3 -c "import sqlite3; print(sqlite3.sqlite_version)"
```

**Import Errors:**

Common import errors and fixes:

1. **Missing `List` import:**
   ```bash
   # Error: NameError: name 'List' is not defined
   # Fix: Add to typing imports
   # Files affected: audit/audit_logger.py
   # Change: from typing import Any, Dict, Optional
   # To: from typing import Any, Dict, List, Optional
   ```

2. **Missing `Any` import:**
   ```bash
   # Error: NameError: name 'Any' is not defined
   # Fix: Add to typing imports
   # Files affected: 
   #   - api/http_handler.py
   #   - system/resource_monitor.py
   # Change: from typing import Optional
   # To: from typing import Any, Optional
   ```

3. **General import errors:**
   ```bash
   # Ensure virtual environment is activated
   source /opt/siya/venv/bin/activate
   
   # Reinstall dependencies
   pip install -e .
   
   # Verify imports work
   python -c "from api import APIServer; print('Imports OK')"
   ```

### Service Won't Start

**Step 1: Check logs for the actual error:**
```bash
# View recent logs
sudo journalctl -u siya -n 50 --no-pager

# Follow logs in real-time
sudo journalctl -u siya -f
```

**Common errors and fixes:**

**Error: `status=217/USER`**
- **Cause:** Wrong username in service file
- **Fix:** Ensure `User=YOUR_PI_USERNAME` (e.g., `User=umesh404`) with no comments on that line

**Error: `NameError: name 'Any' is not defined`**
- **Cause:** Missing `Any` import in `api/http_handler.py` or `system/resource_monitor.py`
- **Fix:** Add `Any` to typing imports: `from typing import Any, Optional`

**Error: `NameError: name 'List' is not defined`**
- **Cause:** Missing `List` import in `audit/audit_logger.py`
- **Fix:** Add `List` to typing imports: `from typing import Any, Dict, List, Optional`

**Error: Commands not processing / No response from API**
- **Cause:** Orchestrator or CLI not started before servers
- **Fix:** Ensure `service_main.py` explicitly calls `orchestrator.start()` and `cli.start()` before starting servers (already fixed in latest code)

**Error: AI inference taking too long (> 2 minutes)**
- **Cause:** Model inference is slow on Pi hardware
- **Fix:** Optimizations already implemented (max_tokens=128, temperature=0.2, timeout=120s). Expected response time: 10-30 seconds after warmup.

**Error: JSON parsing errors from AI model**
- **Cause:** AI model sometimes generates malformed JSON
- **Fix:** JSON repair function automatically fixes common issues. Falls back to stub mode if repair fails (graceful degradation).

**Error: `status=1/FAILURE` (general failure)**
- **Cause:** Python script error (check logs for details)
- **Fix:** See Step 2 below

**Step 2: Test service script manually:**
```bash
cd /opt/siya
source venv/bin/activate
python service_main.py
```
This will show the exact error. Fix any import or initialization errors.

**Step 3: Verify service file:**
```bash
sudo cat /etc/systemd/system/siya.service
```
- Ensure `User=YOUR_PI_USERNAME` (replace with your actual username, e.g., `umesh404`)
- Ensure `ExecStart=/opt/siya/venv/bin/python /opt/siya/service_main.py`
- **Remove any comments from the `User=` line** (systemd doesn't like comments there)

**Step 4: Check file permissions:**
```bash
ls -la /opt/siya/service_main.py
sudo chown YOUR_PI_USERNAME:YOUR_PI_USERNAME /opt/siya/service_main.py
sudo chown -R YOUR_PI_USERNAME:YOUR_PI_USERNAME /opt/siya
```

**Step 5: Verify Python environment:**
```bash
source /opt/siya/venv/bin/activate
python --version  # Should be 3.11+
which python  # Should point to venv
```

**Step 6: After fixing errors, restart service:**
```bash
sudo systemctl daemon-reload
sudo systemctl restart siya
sudo systemctl status siya
```

### Database Issues

1. Check database integrity: Run state consistency check
2. Check permissions: `ls -la /opt/siya/siya.db`
3. Check disk space: `df -h`

---

## ROLLBACK PROCEDURE

If deployment fails:

1. Stop service: `sudo systemctl stop siya`
2. Restore from backup (if available)
3. Check logs for errors
4. Fix issues and redeploy

---

**Last Updated:** 2026-01-27
**Baseline Version:** 1.0.0
**Service Entry Point:** `service_main.py` (runs API server on port 8080 and web server on port 3000)
**Deployment Status:** ✅ COMPLETED AND OPERATIONAL