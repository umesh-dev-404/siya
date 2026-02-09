# AI MODEL GUIDE
## Complete Guide to AI Model Setup, Testing, and Optimization

---

**Context:** Siya is adopting OpenClaw-inspired capabilities (e.g. setup wizard, operator workflows) where law-aligned; product name remains Siya. See `docs/EVOLUTION_ROADMAP.md`.

---

## OVERVIEW

This guide covers everything about the AI model in Siya:
- Model setup and installation
- Testing and verification
- Performance optimization
- RAM diagnostics and troubleshooting
- Model selection and alternatives

**Current Model:** Qwen 2.5 3B Instruct (Q4_K_M)  
**Status:** ✅ Operational  
**Performance:** 10-30 seconds per query (optimized)  
**RAM Usage:** ~3-4 GB when loaded (full RAM loading enabled)

---

## TABLE OF CONTENTS

1. [Model Setup](#model-setup)
2. [How It Works](#how-it-works)
3. [Testing](#testing)
4. [RAM Diagnostics](#ram-diagnostics)
5. [Performance Optimization](#performance-optimization)
6. [Model Selection](#model-selection)
7. [Troubleshooting](#troubleshooting)

---

## MODEL SETUP

### Prerequisites

- Raspberry Pi 5 with 8 GB RAM
- Python 3.11 through 3.14
- Siya project cloned and installed
- At least 4 GB free disk space

### Step 1: Install Build Dependencies

```bash
# On Raspberry Pi
sudo apt update
sudo apt install -y build-essential cmake git python3-dev
```

### Step 2: Install llama-cpp-python

```bash
# On Raspberry Pi
cd /opt/siya
source venv/bin/activate

# Install llama-cpp-python (builds from source on ARM64)
pip install llama-cpp-python
```

**Note:** This may take 30-60 minutes to build on Raspberry Pi 5.

### Step 3: Download Model

**Model:** Qwen 2.5 3B Instruct (Q4_K_M)  
**Size:** ~2-3 GB  
**Location:** `/opt/siya/models/qwen2.5-3b-q4_k_m/`

```bash
# On Raspberry Pi
cd /opt/siya
mkdir -p models/qwen2.5-3b-q4_k_m
cd models/qwen2.5-3b-q4_k_m

# Authenticate with Hugging Face (if not already done)
hf auth login

# Download model
hf download Qwen/Qwen2.5-3B-Instruct-GGUF \
  --include "*Q4_K_M*gguf" \
  --local-dir .
```

**Status:** ✅ Model download completed.

### Step 4: Configure Model Path

**Default Location:** `/opt/siya/models/qwen2.5-3b-q4_k_m/qwen2.5-3b-instruct-q4_k_m.gguf`

The system automatically detects the model in the default location. No configuration needed if:
- Model is in `/opt/siya/models/qwen2.5-3b-q4_k_m/`
- Filename contains `q4_k_m` or `q4_0`

**Manual Configuration (Optional):**

```bash
# Set environment variable
export SIYA_MODEL_PATH=/opt/siya/models/qwen2.5-3b-q4_k_m/qwen2.5-3b-instruct-q4_k_m.gguf

# Or add to systemd service file
sudo nano /etc/systemd/system/siya.service
# Add: Environment="SIYA_MODEL_PATH=/opt/siya/models/qwen2.5-3b-q4_k_m/qwen2.5-3b-instruct-q4_k_m.gguf"
```

### Step 5: Verify Installation

```bash
# Check llama-cpp-python
python -c "from llama_cpp import Llama; print('✅ llama-cpp-python available')"

# Check model path
python -c "from config.model_config import get_model_path; print(f'Model path: {get_model_path()}')"

# Test model loading
python -c "
from ai.model_manager import ModelManager
from config.model_config import get_model_path
manager = ModelManager(model_path=get_model_path())
if manager.load_model():
    print('✅ Model loaded successfully!')
    print(f'Model size: {manager.get_model_size_mb()} MB')
    manager.unload_model()
"
```

---

## HOW IT WORKS

### Architecture Flow

1. **Service Startup** → Model auto-loads (if configured)
2. **User Input** → API/CLI receives command
3. **Orchestrator** → Submits to AI interface
4. **AI Interface** → Uses IntentParser
5. **Intent Parser** → Calls model for inference
   - Loads system prompt from `docs/System Prompt.md`
   - Builds prompt (system prompt + task prompt)
   - Generates JSON response
6. **JSON Repair** → Fixes common malformations
7. **Orchestrator** → Processes parsed intent

### System Prompt Integration

The system prompt from `docs/System Prompt.md` is **automatically loaded** and prepended to every inference.

**To Update:**
1. Edit `docs/System Prompt.md`
2. Restart service: `sudo systemctl restart siya`

### Key Components

- **`ai/model_manager.py`** — Model lifecycle (load/unload)
- **`ai/llama_wrapper.py`** — llama-cpp-python wrapper
- **`ai/intent_parser.py`** — Intent parsing with AI
- **`config/model_config.py`** — Model path configuration

---

## TESTING

### Method 1: Via API (From PC)

```bash
# Replace IP with your Pi's IP
curl -X POST http://192.168.1.39:8080/command \
  -H "Content-Type: application/json" \
  -d '{"command": "what can you do?"}'
```

### Method 2: Via CLI (On Pi)

```bash
cd /opt/siya
source venv/bin/activate
python -m cli.main
# Then type commands in the CLI
```

### Method 3: Direct Python Testing

```python
from ai.ai_interface import AIInterface
from mcp import MCPServer
from config.model_config import get_model_path

mcp = MCPServer()
ai_interface = AIInterface(
    mcp.get_tool_registry(),
    mcp.get_request_validator(),
    model_path=get_model_path()
)
ai_interface.load_model()
result = ai_interface.parse_user_intent("what can you do?")
print(result)
```

### Verify Model Usage

```bash
# Check service logs
sudo journalctl -u siya -f | grep -E "Model loaded|Intent parsed|Model response"

# Check model status
python -c "
from ai.model_manager import ModelManager
from config.model_config import get_model_path
manager = ModelManager(model_path=get_model_path())
print(f'Model loaded: {manager.is_loaded()}')
"
```

---

## RAM DIAGNOSTICS

### Problem: Model "Loaded" But No RAM Increase

**Symptom:** RAM usage stays at 4-8% (~300-600 MB) instead of ~40-50% (~3-4 GB)

**Root Cause:** Model was using memory-mapped I/O (mmap), loading on-demand from disk

**Solution:** ✅ Fixed — Model now forces full RAM loading (`use_mmap=False`)

### Verify RAM Loading

```bash
# Check RAM before/after model load
sudo journalctl -u siya -n 100 | grep -E "RAM before|RAM after|Model loaded"
```

**Expected Output:**
```
RAM before model load: 5.6% used, 7610 MB available, ~451 MB used
Model loaded with use_mmap=False (full RAM loading)
RAM after model load: 33.2% used, 5387 MB available, ~2677 MB used
```

**Expected RAM Usage:**
- **Before:** ~4-8% (~300-600 MB)
- **After:** ~40-50% (~3-4 GB)
- **During inference:** Slight increase (~100-200 MB)

### Monitor RAM

```bash
# Real-time monitoring
watch -n 1 free -h

# Python check
python -c "
from system.resource_monitor import ResourceMonitor
monitor = ResourceMonitor()
resources = monitor.check_resources()
print(f'RAM Usage: {resources[\"ram_usage\"]*100:.1f}%')
print(f'RAM Available: {resources[\"ram_available_mb\"]:.0f} MB')
"
```

---

## PERFORMANCE OPTIMIZATION

### Current Optimizations

1. **Full RAM Loading** (`use_mmap=False`)
   - Entire model in RAM
   - Faster inference (no disk I/O)
   - 10-30 seconds per query (vs 60-90s with mmap)

2. **Reduced Token Generation**
   - `max_tokens=128` (reduced from 512)
   - Faster JSON responses

3. **Deterministic Output**
   - `temperature=0.2` (reduced from 0.7)
   - More consistent JSON generation

4. **Simplified Prompt**
   - Shorter, focused structure
   - Direct JSON format example

5. **JSON Repair Function**
   - Automatically fixes common JSON issues
   - Handles malformed responses gracefully

6. **Connection Handling**
   - HTTP socket timeout: 5 minutes
   - Keep-alive headers

### Performance Metrics

**Expected Performance:**
- **First inference:** 30-60 seconds (model warmup)
- **Subsequent inferences:** 10-30 seconds (optimized)
- **With mmap (old):** 60-90 seconds
- **With full RAM (new):** 10-30 seconds ✅

### Further Optimization Options

**Reduce Context Window:**
```bash
# In systemd service, add:
Environment="SIYA_MODEL_CTX=2048"
```

**Reduce Threads:**
```bash
# In systemd service, add:
Environment="SIYA_MODEL_THREADS=4"
```

**Use Q4_0 Quantization:**
- Smaller file (~2 GB vs ~2.5 GB)
- Faster inference
- Slightly lower quality

---

## MODEL SELECTION

### Current Model: Qwen 2.5 3B Instruct (Q4_K_M)

**Status:** ✅ Operational  
**Size:** ~2-3 GB  
**RAM Usage:** ~3-4 GB when loaded  
**Inference Time:** 10-30 seconds  
**Suitability:** ✅ Excellent for Pi 5

### Alternative Models

#### 3B Models (Recommended)

| Model | Size | RAM | Speed | Quality | Suitability |
|-------|------|-----|-------|---------|-------------|
| Qwen 2.5 3B Q4_K_M | 2.5 GB | 3-4 GB | 10-30s | Good | ✅ Excellent |
| Qwen 2.5 3B Q4_0 | 2.0 GB | 3-4 GB | 8-20s | Good | ✅ Excellent |
| Llama 3.2 3B | 2-3 GB | 3-4 GB | 10-30s | Good | ✅ Excellent |
| Phi-3 Mini 3.8B | 2-3 GB | 3-4 GB | 8-20s | Good | ✅ Excellent |

#### 7B Models (Not Recommended for Pi 5)

| Model | Size | RAM | Speed | Quality | Suitability |
|-------|------|-----|-------|---------|-------------|
| DeepSeek 7B Q4_0 | 3.5 GB | 5-6 GB | 30-60s | Better | ⚠️ Marginal |
| DeepSeek 7B Q4_K_M | 4.5 GB | 6-7 GB | 40-90s | Best | ❌ Not Recommended |

**7B Model Issues:**
- May exceed 8 GB RAM limit
- 2-3x slower inference
- Risk of OOM errors
- Requires swap space

### Recommendation

**Keep Qwen 2.5 3B (Current):**
- ✅ Fits comfortably in 8 GB RAM
- ✅ Fast enough (10-30s) for interactive use
- ✅ Already working and optimized
- ✅ Lower power consumption

**Only upgrade to 7B if:**
- Current model quality is insufficient
- You can accept 30-90 second response times
- You're willing to risk OOM errors
- You have swap space configured

---

## TROUBLESHOOTING

### Issue: Model Not Loading

**Check:**
1. Model path: `python -c "from config.model_config import get_model_path; print(get_model_path())"`
2. Model file exists: `ls -lh /opt/siya/models/qwen2.5-3b-q4_k_m/*.gguf`
3. llama-cpp-python: `python -c "from llama_cpp import Llama; print('OK')"`
4. RAM available: `free -h` (need at least 4 GB free)

### Issue: RAM Not Increasing

**Check logs:**
```bash
sudo journalctl -u siya | grep -E "RAM before|RAM after|use_mmap"
```

**Expected:** Should see "Model loaded with use_mmap=False" and RAM increase from ~5% to ~33%

**If RAM still low:**
- Check if `use_mmap` parameter is supported: `pip show llama-cpp-python`
- Verify model file is valid: `file /opt/siya/models/qwen2.5-3b-q4_k_m/*.gguf`

### Issue: Inference Too Slow

**Check:**
- First inference: 30-60 seconds (normal warmup)
- Subsequent: Should be 10-30 seconds
- If consistently slow: Check CPU usage (`htop`)

### Issue: Out of Memory

**Solutions:**
1. Check RAM: `free -h`
2. Close other applications
3. Use Q4_0 quantization (smaller)
4. Reduce context window: `SIYA_MODEL_CTX=2048`

### Issue: JSON Parsing Errors

**Status:** ✅ Fixed — JSON repair function handles common issues

**If still occurring:**
- Check logs: `sudo journalctl -u siya | grep -E "JSON|parsing"`
- Model may need better prompt engineering
- Consider upgrading to 7B model (if quality insufficient)

---

## EXAMPLE TEST SCENARIOS

### Test 1: Basic Intent Parsing

```bash
curl -X POST http://192.168.1.39:8080/command \
  -H "Content-Type: application/json" \
  -d '{"command": "hello"}'
```

### Test 2: Natural Language Question

```bash
curl -X POST http://192.168.1.39:8080/command \
  -H "Content-Type: application/json" \
  -d '{"command": "what can you do?"}'
```

### Test 3: Complex Request

```bash
curl -X POST http://192.168.1.39:8080/command \
  -H "Content-Type: application/json" \
  -d '{"command": "I need help with file management"}'
```

---

## MONITORING

### Check Inference Time

```bash
sudo journalctl -u siya | grep -E "inference_time|Model response|Intent parsed"
```

### Monitor RAM Usage

```bash
# Real-time
watch -n 1 free -h

# Process-specific
ps aux | grep python | grep siya | awk '{print "RSS: " $6/1024 " MB"}'
```

### Check Model Status

```bash
python -c "
from ai.model_manager import ModelManager
from config.model_config import get_model_path
from ai.llama_wrapper import is_llama_available

print(f'llama-cpp-python: {is_llama_available()}')
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

After model is operational:

1. ✅ Test various natural language inputs
2. ✅ Monitor resource usage during extended use
3. ✅ Verify schema compliance of AI outputs
4. ✅ Test error recovery (failures, timeouts, JSON errors)
5. ⏳ Extended testing and fine-tuning

---

**Last Updated:** 2026-01-27  
**Status:** ✅ Operational — Model running with full RAM loading and performance optimizations  
**Model:** Qwen 2.5 3B Instruct (Q4_K_M)  
**Performance:** 10-30 seconds per query (optimized)  
**RAM Usage:** ~3-4 GB (full RAM loading enabled)
