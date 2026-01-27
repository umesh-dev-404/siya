# EXAMPLE COMMANDS
## Project: Siya
## Tool: PC MCP Client (siya-cli)

This document provides example commands for verification and usage of the 13+ implemented tools.

**Prerequisite:**
Ensure the PC MCP Client is installed globally:
```powershell
cd D:\Projects\siya
pip install -e .
```
*Note: If `siya-cli` is not found, ensure your Python Scripts folder is in your PATH (see `SETUP.md`).*

All commands assume the Pi Server is running at `http://192.168.1.39:8080`. Update the URL as needed.

---

## 1. CONNECTION CHECK

### Verify Server Connectivity
```powershell
siya-cli --transport http --url http://192.168.1.39:8080 server-info
```
*Expected Output:* `✅ Connected to MCP Server... Server Status: Online`

### List Available Tools
```powershell
siya-cli --transport http --url http://192.168.1.39:8080 list-tools
```

---

## 2. SYSTEM TOOLS

### Get System Status
```powershell
siya-cli --transport http --url http://192.168.1.39:8080 call get_system_status
```

### Resource Monitor (with Processes)
```powershell
siya-cli --transport http --url http://192.168.1.39:8080 call resource_monitor --args "{\"include_processes\": true}"
```

### Query Logs
```powershell
siya-cli --transport http --url http://192.168.1.39:8080 call log_query --args "{\"limit\": 5}"
```

---

## 3. FILE OPERATIONS (SAFE)

### List Directory
```powershell
siya-cli --transport http --url http://192.168.1.39:8080 call directory_list --args "{\"path\": \"/opt/siya\"}"
```

### Read File
```powershell
siya-cli --transport http --url http://192.168.1.39:8080 call file_read --args "{\"path\": \"/opt/siya/README.md\"}"
```

### Write File (Requires Confirmation)
```powershell
siya-cli --transport http --url http://192.168.1.39:8080 call file_write --args "{\"path\": \"/opt/siya/test_write.txt\", \"content\": \"Hello Siya\"}"
```
*Expect:* `pending_confirmation` status (LAW 1).

---

## 4. AUTOMATION TOOLS

### List Automations
```powershell
siya-cli --transport http --url http://192.168.1.39:8080 call list_automations
```

### Trigger Automation
```powershell
siya-cli --transport http --url http://192.168.1.39:8080 call trigger_automation --args "{\"automation_id\": \"daily_summary\"}"
```
*Expect:* `pending_confirmation` status (LAW 1).

---

## 5. INTELLIGENCE TOOLS

### Fetch Mails (Offline)
```powershell
siya-cli --transport http --url http://192.168.1.39:8080 call fetch_mails
```

### Summarize Text
```powershell
siya-cli --transport http --url http://192.168.1.39:8080 call summarize_text --args "{\"text\": \"Siya is a local-first personal assistant operating system focused on privacy.\"}"
```

---

**Last Updated:** 2026-01-27
**Schema Version:** 1.0.0
