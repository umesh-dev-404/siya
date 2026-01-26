# DEPLOYMENT GUIDE
## Project: Siya
## Version: 1.0.0 (Baseline)

---

## OVERVIEW

This document describes the deployment process for Siya on Raspberry Pi 5.

**Per DIP Phase 9: Production Lock & Baseline**

---

## PREREQUISITES

### Hardware
- Raspberry Pi 5
- 8 GB RAM (minimum)
- MicroSD card (32 GB minimum, Class 10 or better)
- Power supply (official Pi 5 power supply recommended)

### Software
- Raspberry Pi OS Lite (64-bit)
- Python 3.11, 3.12, or 3.13
- Git

---

## DEPLOYMENT STEPS

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

### 4. Clone Repository

```bash
# Navigate to installation directory
cd /opt

# Clone Siya repository (replace YOUR_USERNAME with your GitHub username)
sudo git clone https://github.com/YOUR_USERNAME/siya.git

# Set ownership (replace YOUR_PI_USERNAME with your actual Pi username, e.g., umesh404)
sudo chown -R YOUR_PI_USERNAME:YOUR_PI_USERNAME /opt/siya

# Navigate to project directory
cd /opt/siya

# Checkout production baseline tag (optional, if you created the tag)
# git checkout v1.0.0-baseline
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
- Python 3.11, 3.12, or 3.13 are supported (Python 3.13.5 confirmed working)
- The venv must be created **inside** the project directory (`/opt/siya`)
- You must clone the repository first before running `pip install -e .`
- Replace `YOUR_PI_USERNAME` with your actual Pi username (e.g., `umesh404`) in all commands

### 6. Initialize Database

```bash
# Run database initialization
python -c "from memory import Database; db = Database('siya.db'); db.connect(); print('Database initialized')"
```

### 7. Lock Production Baseline

```bash
# Lock schema version and tool registry
python -c "
from system import ProductionLock
from mcp import ModelControlPlane

mcp = ModelControlPlane()
lock = ProductionLock()
lock.lock_schema_version('1.0.0')
lock.lock_tool_registry(mcp.get_tool_registry())
lock.finalize_lock()
print('Production lock finalized')
"
```

### 8. Verify Installation

```bash
# Run state consistency check
python -c "
from memory import Database
from system import StateChecker

db = Database('siya.db')
db.connect()
checker = StateChecker(db)
result = checker.check_state_consistency()
print(f'State consistent: {result[\"consistent\"]}')
"
```

---

## CONFIGURATION

### Environment Variables

Create `.env` file or set environment variables:

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
- See `NETWORK_ACCESS.md` for details on network access

---

## SERVICE SETUP (systemd)

The systemd service runs the API server (`service_main.py`), which:
- Starts the HTTP API server on port 8080
- Runs continuously in the background
- Automatically restarts on failure
- Starts on system boot (if enabled)
- Is accessible from your PC at `http://<PI_IP>:8080`

**Note:** The service does NOT run the interactive CLI. For interactive use, SSH into the Pi and run `python -m cli.main` manually.

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

### Verify API Server is Running

```bash
# Check if port 8080 is listening
sudo netstat -tlnp | grep 8080

# Or using ss
sudo ss -tlnp | grep 8080
```

You should see the API server listening on `0.0.0.0:8080` (or `*:8080`).

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

**Note:** Siya requires Python >= 3.11, < 3.14 (so 3.11, 3.12, and 3.13 are all supported). Python 3.13.5 has been tested and works. If your Pi only has Python 3.9 or 3.10, you must upgrade to Python 3.11+ using one of the methods above.

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
```bash
# Ensure virtual environment is activated
source /opt/siya/venv/bin/activate
# Reinstall dependencies
pip install -e .
```

### Service Won't Start

1. **Check logs for errors:**
   ```bash
   sudo journalctl -u siya -n 50
   ```

2. **Verify service file:**
   ```bash
   sudo cat /etc/systemd/system/siya.service
   ```
   - Ensure `User=umesh404` (or your actual username)
   - Ensure `ExecStart` points to `/opt/siya/service_main.py`
   - Remove any comments from the `User=` line

3. **Verify Python environment:**
   ```bash
   source /opt/siya/venv/bin/activate
   python --version
   python /opt/siya/service_main.py  # Test manually
   ```

4. **Check file permissions:**
   ```bash
   ls -la /opt/siya/service_main.py
   sudo chown umesh404:umesh404 /opt/siya/service_main.py
   ```

5. **Check database:**
   ```bash
   ls -la /opt/siya/siya.db
   ```

6. **Verify API server starts manually:**
   ```bash
   cd /opt/siya
   source venv/bin/activate
   python service_main.py
   ```
   (Press Ctrl+C to stop, then check if it started without errors)

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
**Service Entry Point:** `service_main.py` (runs API server on port 8080)
