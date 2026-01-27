# EXAMPLE COMMANDS FOR TESTING
## Testing Siya from Your PC

---

## OVERVIEW

This document provides example commands you can test from your PC while Siya runs on your Raspberry Pi.

**Current System Status:**
- ✅ API server running (port 8080)
- ✅ Web interface running (port 3000)
- ✅ Intent parsing (Phase 10: Real AI model operational - 10-30s response time)
- ✅ System prompt integrated (from `docs/System Prompt.md`)
- ✅ Orchestration flow (task queue working)
- ✅ Natural language input supported
- ✅ Tool execution (starter tools registered)

**Note:** This is only the initial starter set. Siya will scale to many more tools and features in later phases.

---

## QUICK START

**Replace `192.168.1.39` with your Pi's current IP address.**

Find Pi IP:
```bash
# From Pi
hostname -I

# Or from PC (if you know Pi hostname)
ssh YOUR_PI_USERNAME@raspberrypi "hostname -I"
```

---

## TEST 1: HEALTH CHECK

**Purpose:** Verify API server is running and accessible.

**Windows PowerShell:**
```powershell
Invoke-WebRequest -Uri http://192.168.1.39:8080/health
```

**Linux/Mac/Git Bash:**
```bash
curl http://192.168.1.39:8080/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "service": "siya-api"
}
```

---

## TEST 2: BASIC COMMAND FLOW

**Purpose:** Test the full command flow (API → CLI → Orchestrator → AI Intent Parsing → Tool Execution).

**Windows PowerShell:**
```powershell
$body = @{command="hello"} | ConvertTo-Json
Invoke-WebRequest -Uri http://192.168.1.39:8080/command -Method POST -Body $body -ContentType "application/json"
```

**Linux/Mac/Git Bash:**
```bash
curl -X POST http://192.168.1.39:8080/command \
  -H "Content-Type: application/json" \
  -d '{"command": "hello"}'
```

**Expected Response:**
```json
{
  "status": "success",
  "message": "OK: { ...tool output... }"
}
```

**What Happens:**
1. API receives command
2. CLI processes it
3. Orchestrator submits user input
4. AI parses intent (real model if loaded)
5. Tool request validated/authorized
6. Tool executes (starter tools)
7. Response returned

---

## TEST 2A: RUN A STARTER TOOL (SYSTEM STATUS)

**Purpose:** Verify tool execution is real.

```bash
curl -X POST http://192.168.1.39:8080/command \
  -H "Content-Type: application/json" \
  -d '{"command": "get system status"}'
```

**Expected:** Response includes `get_system_status` output (resources JSON).

---

## TEST 2B: LIST TOOLS

```bash
curl -X POST http://192.168.1.39:8080/command \
  -H "Content-Type: application/json" \
  -d '{"command": "list tools"}'
```

**Expected:** Response includes a tool list containing `get_system_status`, `tools_list`, `summarize_text`, `fetch_mails`, `summarize_mails`.

---

## TEST 2D: MAILS (OFFLINE-FIRST LOCAL STORE)

**Purpose:** Test the example “mails” integration without any network setup.

**Default mail store path (created in repo):** `data/mails.json`

**Format:** JSON array of objects; recommended fields:
- `id`, `from`, `to`, `subject`, `date`, `snippet`, `body`

**Fetch mails:**
```bash
curl -X POST http://192.168.1.39:8080/command \
  -H "Content-Type: application/json" \
  -d '{"command": "fetch mails"}'
```

**Summarize mails:**
```bash
curl -X POST http://192.168.1.39:8080/command \
  -H "Content-Type: application/json" \
  -d '{"command": "summarize mails"}'
```

**Note:** Network-based mail fetching (IMAP/Gmail API) will be added later with LAW 16 enforcement.

---

## TEST 2C: MCP STDIO (OPTIONAL)

**Purpose:** Run Siya as an MCP STDIO server (for MCP clients).

On the Pi:
```bash
cd /opt/siya
source venv/bin/activate
python -m mcp.stdio_main
```

**Note:** You can also enable STDIO inside the systemd runtime by setting:
`SIYA_ENABLE_MCP_STDIO=1` (advanced; typically STDIO servers are launched by the client).

---

## TEST 2E: PC MCP CLI CLIENT (COMPLETE)

**Purpose:** Use Siya's first-party PC MCP CLI client (Claude-like MCP client behavior) for full control.

**Status:** ✅ Complete (STDIO + HTTP transport)

### STDIO Transport (Local Testing)

Spawns a local MCP server process:

```bash
# List tools via STDIO (default)
python -m pc_mcp_client.main list-tools

# Call a tool via STDIO
python -m pc_mcp_client.main call get_system_status --args "{}"

# Raw JSON output
python -m pc_mcp_client.main list-tools --raw
```

### HTTP Transport (Remote Pi Connection)

Connects to Siya Pi server over LAN:

```bash
# List tools via HTTP (replace with your Pi's IP)
python -m pc_mcp_client.main --transport http --url http://192.168.1.39:8080 list-tools

# Call a tool via HTTP
python -m pc_mcp_client.main --transport http --url http://192.168.1.39:8080 call get_system_status --args "{}"

# With optional API key
python -m pc_mcp_client.main --transport http --url http://192.168.1.39:8080 --api-key YOUR_KEY list-tools

# With custom timeout (for slow AI inference)
python -m pc_mcp_client.main --transport http --url http://192.168.1.39:8080 --timeout 600 call summarize_text --args '{"text": "..."}'
```

### Expected Output

```json
{
  "status": "ok",
  "count": 5,
  "tools": [
    {"name": "get_system_status", "description": "..."},
    ...
  ]
}
```

### Configuration (Optional)

Set environment variables on the Pi to configure HTTP transport:

- `SIYA_MCP_ALLOWED_ORIGINS` — Comma-separated allowed origins (default: `*`)
- `SIYA_MCP_API_KEY` — Optional API key for authentication

---

## TEST 3: NATURAL LANGUAGE QUESTIONS

**Purpose:** Test AI intent parsing with natural language.

**Examples:**

```bash
# Question about capabilities
curl -X POST http://192.168.1.39:8080/command \
  -H "Content-Type: application/json" \
  -d '{"command": "what can you do?"}'

# Request for help
curl -X POST http://192.168.1.39:8080/command \
  -H "Content-Type: application/json" \
  -d '{"command": "help me with something"}'

# General inquiry
curl -X POST http://192.168.1.39:8080/command \
  -H "Content-Type: application/json" \
  -d '{"command": "I need assistance"}'
```

**Expected:** All commands will be parsed and queued. Intent parsing is in stub mode, so it will attempt to match tool names (none exist yet) and return a basic intent structure.

---

## TEST 4: TASK EXECUTION FLOW

**Purpose:** Test orchestrator task queue and execution flow.

**Examples:**

```bash
# Simple task request
curl -X POST http://192.168.1.39:8080/command \
  -H "Content-Type: application/json" \
  -d '{"command": "execute a task"}'

# Different phrasings
curl -X POST http://192.168.1.39:8080/command \
  -H "Content-Type: application/json" \
  -d '{"command": "I need to do something"}'

curl -X POST http://192.168.1.39:8080/command \
  -H "Content-Type: application/json" \
  -d '{"command": "perform an action"}'
```

**Expected:** Commands are parsed, tasks are queued, and execution flow is tested (though tool execution is stubbed).

---

## TEST 5: ERROR HANDLING

**Purpose:** Test system error handling and validation.

**Examples:**

```bash
# Missing command field
curl -X POST http://192.168.1.39:8080/command \
  -H "Content-Type: application/json" \
  -d '{}'

# Invalid JSON
curl -X POST http://192.168.1.39:8080/command \
  -H "Content-Type: application/json" \
  -d '{invalid json}'

# Empty command
curl -X POST http://192.168.1.39:8080/command \
  -H "Content-Type: application/json" \
  -d '{"command": ""}'
```

**Expected:** Appropriate error responses with clear error messages.

---

## TEST 6: WEB INTERFACE

**Purpose:** Test web interface connectivity and API integration.

1. **Open browser on PC:** `http://192.168.1.39:3000`
2. **Check connection status:** Should show "Connected" (after CORS fix applied)
3. **Try sending commands through web UI**

**Note:** Web interface uses the same API endpoints internally.

---

## UNDERSTANDING THE RESPONSES

### Success Response
```json
{
  "status": "success",
  "message": "Command processed. Task ID: <uuid>"
}
```

### Error Response
```json
{
  "status": "error",
  "message": "Error description here"
}
```

---

## WHAT'S HAPPENING UNDER THE HOOD

When you send a command:

1. **Service Initialization** (on startup)
   - `service_main.py` creates Orchestrator and calls `orchestrator.start()`
   - `service_main.py` creates CLI and calls `cli.start()`
   - This ensures Orchestrator and CLI are ready to process commands

2. **API Layer** (`/command` endpoint)
   - Receives HTTP POST request
   - Validates JSON format
   - Calls `APIServer.handle_command()`

3. **CLI Layer**
   - `CLI.run_single_command()` processes command (ensures CLI is started)
   - Calls `CLI.process_command()`
   - Calls `Orchestrator.submit_user_input()`

4. **Orchestrator**
   - `Orchestrator.submit_user_input()` receives command (orchestrator must be started)
   - Calls `AIInterface.parse_user_intent()` (real AI model if loaded, otherwise stub mode)

5. **AI Intent Parsing** (Real AI Model or Stub Mode)
   - `IntentParser.parse_intent()` uses real AI model if loaded
   - Loads system prompt from `docs/System Prompt.md`
   - Builds prompt and calls model for inference
   - Returns intent structure (validated against schema)
   - Falls back to stub mode if model not loaded

6. **Tool Request Conversion**
   - Orchestrator converts intent to tool request
   - Checks tool registry
   - Creates tool request with parsed action

7. **Task Execution**
   - Task queued in `TaskQueue`
   - `Orchestrator.process_next_task()` processes task
   - Tool execution runs (if tool exists) or returns appropriate response

8. **Response**
   - Success/error message returned through layers
   - All actions logged for auditability (LAW 13)

---

## CURRENT LIMITATIONS

**Current Status:**
- Intent parsing uses real AI model (Qwen 2.5 3B Instruct)
- Natural language input supported
- Starter tools are registered and execute (system/status, list_tools, summarize_text, mails demo)

**What Works:**
- ✅ Service initialization (Orchestrator and CLI started automatically)
- ✅ API server and endpoints
- ✅ Command flow (API → CLI → Orchestrator)
- ✅ Intent parsing (real AI model if loaded, stub mode otherwise)
- ✅ Task queue and execution flow
- ✅ Error handling and validation
- ✅ Complete audit logging

**What's Stubbed:**
- ⚠️ Confirmation UX (requires_confirmation path not implemented end-to-end yet)
- ⚠️ Memory operations (Phase 3)
- ⚠️ Scheduling (Phase 7)

---

## MONITORING ON PI

**View service logs:**
```bash
# On Pi
sudo journalctl -u siya -f
```

**Check service status:**
```bash
# On Pi
sudo systemctl status siya
```

**View recent logs:**
```bash
# On Pi
sudo journalctl -u siya -n 50 --no-pager
```

---

## NEXT STEPS

Once tools are registered in later phases, you'll be able to:
- Execute actual tool operations
- See tool-specific responses
- Test permission and authorization flows
- Verify tool execution results

**Last Updated:** 2026-01-27  
**Status:** Ready for testing (stub mode)
