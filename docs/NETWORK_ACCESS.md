# NETWORK ACCESS CONFIGURATION
## Project: Siya
## Purpose: Access Siya from PC while running on Raspberry Pi

---

## OVERVIEW

Siya's API and web interface are designed to be accessible over the network, allowing you to control and interact with the system from your PC while it runs on the Raspberry Pi.

---

## CURRENT STATUS

**Code Status:** ✅ Ready  
**Network Configuration:** ⚠️ Needs configuration  
**Pi Deployment:** ⚠️ Not yet deployed (Phase 4A pending)

---

## HOW IT WORKS

### Architecture
1. **Siya runs on Raspberry Pi** — All core systems execute on Pi
2. **API Server** — Listens on port 8080 (configurable)
3. **Web Interface** — Listens on port 3000 (configurable)
4. **PC Access** — Connect to Pi's IP address from your PC

### Network Flow
```
PC Browser/CLI → Pi IP:3000 (Web) or Pi IP:8080 (API) → Siya System
```

---

## CONFIGURATION

### Default Configuration
- **API Host:** `0.0.0.0` (all interfaces) - allows network access
- **API Port:** `8080`
- **Web Host:** `0.0.0.0` (all interfaces) - allows network access
- **Web Port:** `3000`

### Environment Variables

Set these on the Pi before starting Siya:

```bash
# On Raspberry Pi
export SIYA_API_HOST=0.0.0.0      # Allow network access
export SIYA_API_PORT=8080
export SIYA_WEB_HOST=0.0.0.0      # Allow network access
export SIYA_WEB_PORT=3000
export SIYA_API_BASE_URL=http://<PI_IP>:8080  # For web interface
```

Replace `<PI_IP>` with your Pi's actual IP address (e.g., `192.168.1.100`).

---

## ACCESS FROM PC

### Web Interface
1. Find Pi's IP address: `ssh pi@raspberrypi "hostname -I"`
2. Open browser on PC: `http://<PI_IP>:3000`
3. Web interface will connect to API at `http://<PI_IP>:8080`

### API Direct Access
```bash
# From PC
curl http://<PI_IP>:8080/health

# Send command
curl -X POST http://<PI_IP>:8080/command \
  -H "Content-Type: application/json" \
  -d '{"command": "your command here"}'
```

### CLI (via SSH)
```bash
# SSH into Pi and run CLI
ssh pi@raspberrypi
cd /opt/siya
source venv/bin/activate
python -m cli.main
```

---

## SECURITY CONSIDERATIONS

### Current Implementation (Phase 6)
- **No authentication** — Anyone on network can access
- **No encryption** — HTTP only (not HTTPS)
- **Firewall recommended** — Restrict access to local network

### For Production
- Add authentication (future phase)
- Use HTTPS (future phase)
- Restrict to local network via firewall
- Consider VPN for remote access

---

## DEPLOYMENT STEPS

### 1. Deploy to Pi (Phase 4A)
Follow `DEPLOYMENT.md` to:
- Set up Raspberry Pi OS
- Install dependencies
- Clone repository
- Configure system

### 2. Configure Network Access
```bash
# On Pi, set environment variables
export SIYA_API_HOST=0.0.0.0
export SIYA_WEB_HOST=0.0.0.0
export SIYA_API_BASE_URL=http://$(hostname -I | awk '{print $1}'):8080
```

### 3. Start Services
```bash
# Start API server
python -m api.server

# Or start web server (includes API)
python -m web.web_server

# Or use systemd service (see DEPLOYMENT.md)
sudo systemctl start siya
```

### 4. Access from PC
- Web: `http://<PI_IP>:3000`
- API: `http://<PI_IP>:8080`

---

## TROUBLESHOOTING

### Cannot Connect from PC

1. **Check Pi IP:**
   ```bash
   ssh pi@raspberrypi "hostname -I"
   ```

2. **Check Firewall:**
   ```bash
   # On Pi
   sudo ufw status
   sudo ufw allow 8080/tcp
   sudo ufw allow 3000/tcp
   ```

3. **Check Services:**
   ```bash
   # On Pi
   sudo systemctl status siya
   netstat -tlnp | grep -E '8080|3000'
   ```

4. **Check Network:**
   ```bash
   # From PC
   ping <PI_IP>
   telnet <PI_IP> 8080
   ```

---

## CURRENT LIMITATIONS

### Phase 6 Implementation
- **No authentication** — Open access on network
- **HTTP only** — No HTTPS encryption
- **Basic security** — Firewall recommended

### Future Enhancements
- Authentication system
- HTTPS support
- Access control
- Rate limiting

---

**Last Updated:** 2026-01-26  
**Status:** Ready for network access (after Pi deployment)
