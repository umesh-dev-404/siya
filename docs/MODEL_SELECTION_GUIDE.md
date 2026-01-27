# MODEL SELECTION GUIDE
## Choosing the Right AI Model for Siya on Raspberry Pi 5

---

## CURRENT MODEL: Qwen 2.5 3B Instruct (Q4_K_M)

**Status:** ✅ Operational (RAM loading issue fixed)  
**Size:** ~2-3 GB  
**RAM Usage:** ~3-4 GB when loaded (with `use_mmap=False`)  
**Inference Time:** 10-30 seconds per query (optimized)  
**Performance:** Acceptable for Pi 5 hardware

**Note:** Model now forces full RAM loading. See `MODEL_RAM_DIAGNOSTICS.md` for troubleshooting.

---

## VERIFYING MODEL IS LOADED

### Check RAM Usage

The model stays loaded in memory after startup. Check actual RAM usage:

```bash
# On Pi - Check total RAM usage
free -h

# Check Python process RAM usage
ps aux | grep python | grep siya

# Monitor RAM in real-time
watch -n 1 free -h

# Check if model is actually loaded
sudo journalctl -u siya | grep -i "model loaded"
```

**Expected RAM Usage:**
- **Before model load:** ~500 MB - 1 GB (system + Python)
- **After model load:** ~3-4 GB total (model stays in RAM)
- **During inference:** Slight increase (~100-200 MB)

If you're seeing < 1 GB total RAM usage, the model might not be loading properly.

### Verify Model is Actually Running

```bash
# Check if model is loaded
sudo journalctl -u siya | grep -E "Model loaded|llama_wrapper"

# Check inference logs
sudo journalctl -u siya | grep -E "Result type|Extracted text|Model response"

# Check process memory
ps aux | grep python | grep siya | awk '{print $6/1024 " MB"}'
```

---

## MODEL SIZE COMPARISON

### 3B Models (Current)
- **Qwen 2.5 3B:** ~2-3 GB, 10-30s inference
- **Llama 3.2 3B:** ~2-3 GB, similar performance
- **Phi-3 Mini:** ~2-3 GB, faster inference

### 7B Models (Larger)
- **DeepSeek 7B:** ~4-5 GB (Q4_K_M), 30-60s+ inference
- **Llama 3.1 8B:** ~4-5 GB (Q4_K_M), 30-60s+ inference
- **Qwen 2.5 7B:** ~4-5 GB (Q4_K_M), 30-60s+ inference

### Performance Impact

**7B models on Pi 5:**
- **RAM Usage:** ~5-6 GB total (model + system)
- **Inference Time:** 30-90 seconds per query (2-3x slower)
- **Risk:** May exceed 8 GB RAM limit, causing swap/performance degradation
- **Benefit:** Better accuracy, more capable reasoning

---

## RECOMMENDATIONS

### Option 1: Keep Qwen 2.5 3B (Recommended)
**Pros:**
- ✅ Fits comfortably in 8 GB RAM
- ✅ Fast enough (10-30s) for interactive use
- ✅ Already working and optimized
- ✅ Lower power consumption

**Cons:**
- ⚠️ Less capable than 7B models
- ⚠️ May struggle with complex reasoning

### Option 2: Try Smaller/Faster 3B Models
**Alternatives:**
- **Phi-3 Mini 3.8B:** Faster inference, similar size
- **Llama 3.2 3B:** Good balance of speed/quality

### Option 3: Upgrade to 7B Model (Not Recommended for Pi 5)
**If you still want 7B:**

**Requirements:**
- ✅ 8 GB RAM minimum (may need swap)
- ✅ Accept 30-90 second response times
- ✅ Monitor for OOM (Out of Memory) errors
- ✅ Consider Q4_0 quantization (smaller, faster) instead of Q4_K_M

**Recommended 7B Models:**
- **DeepSeek 7B Instruct (Q4_0):** ~3.5 GB, faster than Q4_K_M
- **Qwen 2.5 7B Instruct (Q4_0):** ~3.5 GB, good balance

**Download Command:**
```bash
# DeepSeek 7B Q4_0 (smaller, faster)
hf download deepseek-ai/DeepSeek-V2.5-7B-Instruct-GGUF \
  --include "*Q4_0*gguf" \
  --local-dir /opt/siya/models/deepseek-7b-q4_0

# Or Qwen 2.5 7B Q4_0
hf download Qwen/Qwen2.5-7B-Instruct-GGUF \
  --include "*Q4_0*gguf" \
  --local-dir /opt/siya/models/qwen2.5-7b-q4_0
```

---

## OPTIMIZATION BEFORE UPGRADING

Before switching models, try optimizing the current setup:

### 1. Verify Model is Actually Using RAM

```bash
# Check if psutil is installed (needed for RAM monitoring)
pip list | grep psutil

# If not installed:
pip install psutil

# Then check RAM usage properly
python -c "
from system.resource_monitor import ResourceMonitor
monitor = ResourceMonitor()
resources = monitor.check_resources()
print(f'RAM Usage: {resources[\"ram_usage\"]*100:.1f}%')
print(f'RAM Available: {resources[\"ram_available_mb\"]:.0f} MB')
"
```

### 2. Optimize Current Model

**Reduce Context Window:**
- Current: 4096 tokens
- Try: 2048 tokens (faster, less RAM)

**Reduce Threads:**
- Current: Auto (uses all cores)
- Try: 2-4 threads (may be faster, less CPU contention)

**Use Q4_0 Instead of Q4_K_M:**
- Smaller file (~2 GB vs ~2.5 GB)
- Faster inference
- Slightly lower quality

### 3. Check if Model is Actually Running

The logs show inference is happening (~82 seconds). This suggests:
- ✅ Model IS loaded
- ✅ Model IS running inference
- ⚠️ But it's slow (expected for 3B on Pi)

---

## DECISION MATRIX

| Model | Size | RAM | Speed | Quality | Pi 5 Suitability |
|-------|------|-----|-------|---------|------------------|
| Qwen 2.5 3B Q4_K_M | 2.5 GB | 3-4 GB | 10-30s | Good | ✅ Excellent |
| Qwen 2.5 3B Q4_0 | 2.0 GB | 3-4 GB | 8-20s | Good | ✅ Excellent |
| DeepSeek 7B Q4_0 | 3.5 GB | 5-6 GB | 30-60s | Better | ⚠️ Marginal |
| DeepSeek 7B Q4_K_M | 4.5 GB | 6-7 GB | 40-90s | Best | ❌ Not Recommended |

---

## RECOMMENDATION

**Before upgrading to 7B:**

1. ✅ **Verify current model RAM usage** - Check if it's actually using RAM
2. ✅ **Optimize current model** - Try Q4_0 quantization, reduce context window
3. ✅ **Measure actual performance** - Current 10-30s might be acceptable
4. ⚠️ **Consider 7B only if:**
   - Current model quality is insufficient
   - You can accept 30-90 second response times
   - You're willing to risk OOM errors
   - You have swap space configured

**If upgrading to 7B:**
- Use Q4_0 quantization (not Q4_K_M)
- Reduce context window to 2048
- Monitor RAM usage closely
- Configure swap space as backup

---

**Last Updated:** 2026-01-27  
**Current Model:** Qwen 2.5 3B Instruct (Q4_K_M) - Operational  
**Recommendation:** Optimize current model before upgrading
