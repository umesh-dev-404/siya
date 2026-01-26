# EXAMPLE COMMANDS FOR TESTING
## Testing Siya from Your PC

---

## OVERVIEW

This document provides example commands you can test from your PC while Siya runs on your Raspberry Pi.

**Current System Status:**
- ✅ API server running (port 8080)
- ✅ Web interface running (port 3000)
- ✅ Intent parsing (stub mode)
- ✅ Orchestration flow (task queue working)
- ⚠️ Tool execution (stubbed - no tools registered yet)

**Note:** Commands will be parsed and queued, but actual tool execution is stubbed until tools are registered in later implementation phases.

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

**Purpose:** Test the full command flow (API → CLI → Orchestrator → AI Intent Parsing).

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
  "message": "Command processed. Task ID: <uuid>"
}
```

**What Happens:**
1. API receives command
2. CLI processes it
3. Orchestrator submits user input
4. AI parses intent (stub mode)
5. Task queued and processed
6. Response returned

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

1. **API Layer** (`/command` endpoint)
   - Receives HTTP POST request
   - Validates JSON format
   - Calls `APIServer.handle_command()`

2. **CLI Layer**
   - `CLI.run_single_command()` processes command
   - Calls `CLI.process_command()`

3. **Orchestrator**
   - `Orchestrator.submit_user_input()` receives command
   - Calls `AIInterface.parse_user_intent()` (stub mode)

4. **AI Intent Parsing** (Stub Mode)
   - `IntentParser.parse_intent()` attempts to match tool names
   - Returns intent structure (validated against schema)
   - Since no tools exist, returns "unknown" action

5. **Tool Request Conversion**
   - Orchestrator converts intent to tool request
   - Checks tool registry (empty - no tools registered)
   - Creates tool request with "unknown" tool

6. **Task Execution**
   - Task queued in `TaskQueue`
   - `Orchestrator.process_next_task()` processes task
   - Tool execution is stubbed (no actual tools to run)

7. **Response**
   - Success/error message returned through layers
   - All actions logged for auditability (LAW 13)

---

## CURRENT LIMITATIONS

**Phase 2 Status:**
- Tool registry framework exists but no tools registered
- Intent parsing is stub (will be replaced with actual AI model)
- Tool execution is stubbed (no tools to execute)

**What Works:**
- ✅ API server and endpoints
- ✅ Command flow (API → CLI → Orchestrator)
- ✅ Intent parsing (stub mode)
- ✅ Task queue and execution flow
- ✅ Error handling and validation
- ✅ Complete audit logging

**What's Stubbed:**
- ⚠️ AI model (using stub intent parser)
- ⚠️ Tool execution (no tools registered)
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
