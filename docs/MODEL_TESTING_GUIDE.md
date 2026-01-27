# MODEL TESTING GUIDE
## How to Run and Test the AI Model

---

## OVERVIEW

This guide explains how to run and test the AI model (Qwen 2.5 3B Instruct) in Siya.

**Model Status:**
- ✅ Model downloaded and ready
- ✅ Model auto-loads on service startup (if path configured)
- ✅ Model can be manually loaded/unloaded
- ✅ Model used automatically for intent parsing

---

## HOW THE MODEL WORKS

### Architecture Flow

1. **Service Startup** → `service_main.py` initializes components:
   - Creates Orchestrator and starts it (enables task processing)
   - Creates CLI and starts it (enables command processing)
   - Loads AI model (if configured)
   - Starts API and web servers
2. **User Input** → API/CLI receives command
3. **CLI** → Processes command through `run_single_command()`
4. **Orchestrator** → Submits user input to AI interface (via `submit_user_input()`)
5. **AI Interface** → Uses IntentParser to parse intent
6. **Intent Parser** → Checks if model is loaded
   - If loaded: Uses real AI model (`_ai_parse`)
     - Loads system prompt from `docs/System Prompt.md`
     - Builds full prompt (system prompt + task prompt)
     - Calls model for inference
   - If not loaded: Falls back to stub mode (`_stub_parse`)
7. **Model Manager** → Handles model loading/unloading
8. **Llama Wrapper** → Interfaces with llama-cpp-python
9. **Orchestrator** → Processes task and returns response

### System Prompt Integration

The system prompt from `docs/System Prompt.md` is **automatically loaded** and prepended to every AI inference. This ensures:

- ✅ AI follows Siya's canonical constraints (LAW 3)
- ✅ AI understands its role as intent parser, not executor
- ✅ AI respects authority rules and execution prohibitions
- ✅ AI output format requirements are enforced

The system prompt is:
- Loaded once and cached (efficient)
- Automatically included in every prompt
- Falls back to minimal prompt if file not found

**To Update the System Prompt:**
- **File Location:** `docs/System Prompt.md`
- **How it works:** The system prompt is automatically loaded by `ai/intent_parser.py` on first use
- **After editing:** Restart the service to reload the prompt (or wait for cache to expire)
- **Note:** The prompt is cached in memory, so changes require a service restart to take effect

### Key Components

- **`ai/model_manager.py`** — Manages model lifecycle (load/unload)
- **`ai/llama_wrapper.py`** — Wraps llama-cpp-python for inference
- **`ai/intent_parser.py`** — Parses user intent using AI model (includes system prompt)
- **`ai/ai_interface.py`** — Main AI interface coordinating components
- **`config/model_config.py`** — Model path configuration
- **`docs/System Prompt.md`** — Authoritative system prompt (loaded automatically)

---

## MODEL LOADING

### Automatic Loading (Service)

The model **automatically loads** when the service starts if:
1. Model path is configured (via `SIYA_MODEL_PATH` or default location)
2. `llama-cpp-python` is installed
3. Model file exists and is accessible

**Check if model loaded:**
```bash
# On Pi - Check service logs
sudo journalctl -u siya -n 50 | grep -i "model"
```

Look for:
- `✅ AI model loaded successfully` — Model loaded
- `⚠️  Model loading failed` — Model failed to load (using stub mode)
- `No model path configured` — No model path (using stub mode)

### Manual Loading (Testing)

You can manually load/unload the model for testing:

```python
# Python interactive session
from ai.model_manager import ModelManager
from config.model_config import get_model_path

model_path = get_model_path()
print(f"Model path: {model_path}")

manager = ModelManager(model_path=model_path)
if manager.load_model():
    print("✅ Model loaded!")
    print(f"Model size: {manager.get_model_size_mb()} MB")
    
    # Test inference
    response = manager.generate("What is 2+2?", max_tokens=50)
    print(f"Response: {response}")
    
    manager.unload_model()
else:
    print("❌ Model loading failed")
```

---

## TESTING THE MODEL

### Method 1: Via API (From PC)

**Test with natural language:**

```bash
# Replace 192.168.1.39 with your Pi's IP
curl -X POST http://192.168.1.39:8080/command \
  -H "Content-Type: application/json" \
  -d '{"command": "what can you do?"}'
```

**Test with specific intent:**

```bash
curl -X POST http://192.168.1.39:8080/command \
  -H "Content-Type: application/json" \
  -d '{"command": "help me with something"}'
```

**Expected Response:**
```json
{
  "status": "success",
  "message": "Command processed. Task ID: <uuid>"
}
```

**What Happens:**
1. Service initializes: Orchestrator and CLI are started (enables command processing)
2. API receives command
3. CLI processes it (CLI must be started)
4. Orchestrator submits to AI interface (Orchestrator must be started)
5. **AI model parses intent** (if loaded)
6. Intent validated against schema
7. Task queued and processed
8. Response returned

### Method 2: Via CLI (On Pi)

```bash
# On Pi
cd /opt/siya
source venv/bin/activate

# Run CLI
python -m cli.main

# In CLI, type commands:
> what can you do?
> help me with something
> I need assistance
```

### Method 3: Direct Python Testing

```python
# On Pi
cd /opt/siya
source venv/bin/activate
python

# In Python:
from ai.ai_interface import AIInterface
from mcp import ModelControlPlane, ToolRegistry, RequestValidator
from config.model_config import get_model_path

# Setup
mcp = ModelControlPlane()
tool_registry = mcp.get_tool_registry()
request_validator = mcp.get_request_validator()
model_path = get_model_path()

# Create AI interface
ai_interface = AIInterface(tool_registry, request_validator, model_path=model_path)

# Load model
if model_path:
    print("Loading model...")
    ai_interface.load_model()

# Test intent parsing
result = ai_interface.parse_user_intent("what can you do?")
print(result)

# Check if model is loaded
print(f"Model loaded: {ai_interface.is_model_loaded()}")
```

---

## VERIFYING MODEL USAGE

### Check Service Logs

```bash
# On Pi - Real-time logs
sudo journalctl -u siya -f

# Look for:
# - "Model loaded successfully" — Model loaded on startup
# - "Intent parsed: <action>" — Intent parsing happened
# - "AI parsing failed, falling back to stub" — Model failed, using stub
```

### Check Model Status

```bash
# On Pi - Check if model is loaded
python -c "
from ai.model_manager import ModelManager
from config.model_config import get_model_path

model_path = get_model_path()
if model_path:
    manager = ModelManager(model_path=model_path)
    print(f'Model loaded: {manager.is_loaded()}')
    if manager.is_loaded():
        print(f'Model size: {manager.get_model_size_mb()} MB')
else:
    print('No model path configured')
"
```

### Monitor Resource Usage

```bash
# On Pi - Monitor RAM usage
watch -n 1 free -h

# Model should use ~2-3 GB RAM when loaded
# Total system RAM should stay under 7 GB (Pi has 8 GB)
```

---

## TROUBLESHOOTING

### Issue: Model Not Loading

**Symptoms:**
- Service logs show "Model loading failed"
- Intent parsing uses stub mode

**Solutions:**
1. **Check model path:**
   ```bash
   python -c "from config.model_config import get_model_path; print(get_model_path())"
   ```

2. **Verify model file exists:**
   ```bash
   ls -lh /opt/siya/qwen2.5-3b-q4_k_m/*.gguf
   ```

3. **Check llama-cpp-python:**
   ```bash
   python -c "from llama_cpp import Llama; print('llama-cpp-python available')"
   ```

4. **Check RAM:**
   ```bash
   free -h
   # Need at least 4 GB free RAM
   ```

### Issue: Model Loading But Not Used

**Symptoms:**
- Model loads successfully
- But intent parsing still uses stub mode

**Check:**
1. Verify model is actually loaded:
   ```python
   from ai.model_manager import ModelManager
   from config.model_config import get_model_path
   manager = ModelManager(model_path=get_model_path())
   print(manager.is_loaded())  # Should be True
   ```

2. Check service logs for "AI parsing failed" messages

3. Verify model manager is passed to intent parser correctly

### Issue: Inference Too Slow

**Solutions:**
- Model loading takes 30-60 seconds (normal)
- First inference may be slower (model initialization)
- Subsequent inferences should be faster
- If consistently slow, check CPU usage: `htop`

### Issue: Out of Memory

**Symptoms:**
- Model loading fails with memory error
- System becomes unresponsive

**Solutions:**
1. Check available RAM: `free -h`
2. Close other applications
3. Consider using smaller quantization (Q4_0 instead of Q4_K_M)
4. Unload model when not needed: `manager.unload_model()`

---

## EXAMPLE TEST SCENARIOS

### Test 1: Basic Intent Parsing

```bash
# From PC
curl -X POST http://192.168.1.39:8080/command \
  -H "Content-Type: application/json" \
  -d '{"command": "hello"}'
```

**Expected:** Intent parsed, task queued, response returned

### Test 2: Natural Language Question

```bash
curl -X POST http://192.168.1.39:8080/command \
  -H "Content-Type: application/json" \
  -d '{"command": "what tools are available?"}'
```

**Expected:** AI parses intent, returns appropriate action

### Test 3: Complex Request

```bash
curl -X POST http://192.168.1.39:8080/command \
  -H "Content-Type: application/json" \
  -d '{"command": "I need help with file management"}'
```

**Expected:** AI parses intent, may request clarification if unclear

---

## MONITORING MODEL PERFORMANCE

### Check Inference Time

Model logs include inference timing. Check logs:
```bash
sudo journalctl -u siya | grep -i "inference\|model"
```

### Monitor RAM Usage

```bash
# Before model load
free -h

# Load model
# (happens automatically on service start)

# After model load
free -h

# Should see ~2-3 GB increase in used RAM
```

### Check Model Status

```bash
# Quick status check
python -c "
from ai.model_manager import ModelManager
from config.model_config import get_model_path
from ai.llama_wrapper import is_llama_available

print(f'llama-cpp-python available: {is_llama_available()}')
model_path = get_model_path()
print(f'Model path: {model_path}')
if model_path:
    manager = ModelManager(model_path=model_path)
    print(f'Model loaded: {manager.is_loaded()}')
    if manager.is_loaded():
        print(f'Model size: {manager.get_model_size_mb()} MB')
"
```

---

## NEXT STEPS

After model is working:

1. **Test various natural language inputs**
2. **Monitor resource usage** during extended use
3. **Verify schema compliance** of AI outputs
4. **Test error recovery** (model failures, timeouts)
5. **Optimize performance** if needed

---

**Last Updated:** 2026-01-27  
**Status:** Ready for testing  
**Model:** Qwen 2.5 3B Instruct (Q4_K_M)
