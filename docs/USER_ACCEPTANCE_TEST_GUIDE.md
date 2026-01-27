# USER ACCEPTANCE TEST GUIDE (UAT)

**Target:** Siya System v1.0.0
**Client:** PC (Powershell/CMD)
**Server:** Raspberry Pi 5

---

## 1. Prerequisites

### On the Raspberry Pi
Ensure the server is running:
```bash
cd /opt/siya
source venv/bin/activate
# Start the server (API + Web + MCP)
python service_main.py
```
*Note the IP address displayed (e.g., `192.168.1.39`).*

### On the PC
Ensure `siya-cli` is installed:
```powershell
siya-cli --help
```

---

## 2. Test Commands

Replace `http://192.168.1.39:8080` with your actual Pi IP and port.

### Test 1: Connectivity & Discovery (Phase 6/11)
Verify the PC can reach the Pi and list available tools.

**Check Server Status:**
```powershell
siya-cli --transport http --url http://192.168.1.39:8080 server-info
```
*Expected Output: `✅ Connected... Server Status: Online`*

**List All Tools:**
```powershell
siya-cli --transport http --url http://192.168.1.39:8080 list-tools
```
*Expected Output: A list of ~29 tools including `get_system_status`, `speak_text`, etc.*

---

### Test 2: Core System Status (Phase 11)
Verify the system can read its own state.

```powershell
siya-cli --transport http --url http://192.168.1.39:8080 call get_system_status
```
*Expected Output: JSON showing CPU, RAM, and uptime.*

---

### Test 3: Notification System (Phase 15)
Verify the notification engine is active.

**PowerShell:**
```powershell
siya-cli --transport http --url http://192.168.1.39:8080 call send_notification --args '{"title": "UAT Test", "message": "Hello from PC!"}'
```

**Command Prompt (cmd.exe):**
```cmd
siya-cli --transport http --url http://192.168.1.39:8080 call send_notification --args "{\"title\": \"UAT Test\", \"message\": \"Hello from PC!\"}"
```
*Expected Output: `Notification sent (ID: ...)`*

**Read Back Notifications:**
```powershell
siya-cli --transport http --url http://192.168.1.39:8080 call list_notifications
```
*Expected Output: Should list the "UAT Test" notification.*

---

### Test 4: Voice Interface (Phase 16)
Verify audio output on the Pi.

**PowerShell:**
```powershell
siya-cli --transport http --url http://192.168.1.39:8080 call speak_text --args '{"text": "System verified. Welcome to Siya."}'
```

**Command Prompt (cmd.exe):**
```cmd
siya-cli --transport http --url http://192.168.1.39:8080 call speak_text --args "{\"text\": \"System verified. Welcome to Siya.\"}"
```
*Expected Output: You should hear the Pi speak "System verified..."*

**Note:** If no speakers are connected, you will receive:
```json
{
  "status": "ok",
  "output": {
    "success": false,
    "error": "TTS failed or unavailable"
  }
}
```
**This is a PASS.** It confirms the system handled the hardware failure gracefully (LAW 12).

---

### Test 5: Sync Status (Phase 13)
Verify Supabase connection.

```powershell
siya-cli --transport http --url http://192.168.1.39:8080 call get_sync_status
```
siya-cli --transport http --url http://192.168.1.39:8080 call get_sync_status
```
*Expected Output: Connection status (Online/Offline) and queue size.*

### Test 6: Interactive Confirmation (LAW 1)
Verify that sensitive tools prompt for confirmation.

```powershell
siya-cli --transport http --url http://192.168.1.39:8080 call trigger_sync --args "{\"direction\": \"push\"}"
```
*Expected Output:*
```text
⚠️  CONFIRMATION REQUIRED (LAW 1)
Tool: trigger_sync
...
Do you want to proceed? [y/N]:
```
*Type `y` to confirm and execute.*

---

## 3. Troubleshooting

- **Connection Refused?** Check if `service_main.py` is running on the Pi. Check firewall (Port 8080).
- **Tool Not Found?** Ensure `register_all_tools` was called (Phase 11 completion).
- **Voice Error?** Ensure `pyttsx3` is installed and audio drivers are configured on the Pi.

---

## 4. Web Interface Tests (Phase 17)

The Neo-Brutalism web interface runs on port 3000 and provides full CLI parity.

### Test 7: Web Interface Connectivity
1. Open browser: `http://192.168.1.39:3000`
2. *Expected:* Header shows "SIYA", footer shows "● Connected"
3. Sidebar displays tool categories (System, Files, Mail, Sync, etc.)

### Test 8: Tool Execution via Web
1. Click "SYNC" category in sidebar → Click "Get Sync Status"
2. Click "EXECUTE TOOL"
3. *Expected:* Human-readable output with status badges (e.g., `CONNECTED` in green)

### Test 9: Confirmation Modal (LAW 1)
1. Click "SYNC" → "Trigger Sync"
2. Select direction: `push`
3. Click "EXECUTE TOOL"
4. *Expected:* Modal appears with:
   - Warning: "This action requires your explicit confirmation"
   - Tool name and arguments displayed
   - LAW 1 notice in red
   - Cancel / Yes, Execute buttons
5. Click "Cancel" → Modal closes, output shows "Action cancelled"
6. Click "Yes, Execute" → Modal closes, sync result displayed

### Test 10: Human-Readable Output
1. Execute any tool (e.g., `get_system_status`)
2. *Expected:* Output formatted with:
   - Labels on left (e.g., "Status:", "Is Connected:")
   - Status badges with colors (CONNECTED=green, ERROR=red)
   - Boolean values as ✓ Yes / ✗ No
   - Nested objects formatted inline

### 5. Interactive CLI Tests (Phase 18)
Test 11: Interactive Mode Launch
- Run `siya` in terminal
- Verify ASCII "SIYA" banner appears
- Verify menu navigation with arrow keys

Test 12: Tool Execution (Interactive)
- Select `get_system_status` from menu
- Verify spinner appears during execution
- Verify rich-formatted output panel appears visible ABOVE the menu after execution
- Verify menu reappears below output

Test 13: Interactive Confirmation (LAW 1)
- Select `trigger_sync`
- Verify styled confirmation dialog appears
- Select "No" -> Verify cancellation
- Select "Yes" -> Verify execution
