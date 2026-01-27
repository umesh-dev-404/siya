# MODEL RAM DIAGNOSTICS
## Troubleshooting Model Loading and RAM Usage

---

## PROBLEM: Model "Loaded" But No RAM Increase

**Symptom:**
- Logs show "Model loaded successfully"
- RAM usage stays at 4-8% (~300-600 MB)
- Expected RAM usage: 40-50% (~3-4 GB)

**Root Cause:**
- llama.cpp may be using **memory-mapped I/O (mmap)** by default
- mmap loads model on-demand from disk, not into RAM
- This is efficient but doesn't show up in RAM usage

---

## SOLUTION: Force Full RAM Loading

### Changes Made

1. **Disabled mmap** (`use_mmap=False`)
   - Forces entire model into RAM
   - Faster inference (no disk I/O)
   - Higher RAM usage (expected)

2. **Enabled mlock** (`use_mlock=True`)
   - Locks model in RAM (prevents swapping)
   - Ensures consistent performance

3. **Enhanced RAM Monitoring**
   - Logs RAM before/after model load
   - Warns if RAM increase is less than expected

---

## VERIFYING THE FIX

### Step 1: Pull Latest Code

```bash
# On Pi
cd /opt/siya
git pull
pip install -e .
```

### Step 2: Restart Service

```bash
sudo systemctl restart siya
```

### Step 3: Check Logs for RAM Change

```bash
sudo journalctl -u siya -n 100 | grep -E "RAM before|RAM after|Model loaded"
```

**Expected Output:**
```
RAM before model load: 4.6% used, 7694 MB available, ~370 MB used
Loading model...
Model loaded successfully
RAM after model load: 45.2% used, 4200 MB available, ~3600 MB used
```

**If RAM still doesn't increase:**
- Check if `use_mmap` parameter is supported
- Verify model file is valid
- Check for errors in logs

### Step 4: Monitor RAM During Load

```bash
# In one terminal - watch RAM
watch -n 0.5 'free -h'

# In another terminal - restart service
sudo systemctl restart siya
```

**Expected:** RAM should jump from ~400 MB to ~3.5 GB when model loads.

---

## TROUBLESHOOTING

### Issue: `use_mmap` Parameter Not Recognized

**Error:** `TypeError: __init__() got an unexpected keyword argument 'use_mmap'`

**Solution:** Your llama-cpp-python version may not support these parameters. Check version:

```bash
pip show llama-cpp-python
```

**If version < 0.2.0:**
- Parameters may not be supported
- Model will use default behavior (likely mmap)
- This is OK - model still works, just uses less RAM

### Issue: Model Still Not Using RAM

**Check:**
1. Model file exists and is valid:
   ```bash
   ls -lh /opt/siya/models/qwen2.5-3b-q4_k_m/*.gguf
   file /opt/siya/models/qwen2.5-3b-q4_k_m/*.gguf
   ```

2. Process memory usage:
   ```bash
   ps aux | grep python | grep siya
   # Check RSS column (Resident Set Size) - should be ~3-4 GB
   ```

3. System memory mapping:
   ```bash
   sudo pmap -x $(pgrep -f "python.*siya") | tail -1
   # Should show significant memory allocated
   ```

### Issue: OOM (Out of Memory) Errors

**If RAM increases too much:**
- Model may be loading multiple times
- Check for duplicate model loading in logs
- Verify model is only loaded once at startup

---

## EXPECTED BEHAVIOR AFTER FIX

**Before Model Load:**
- RAM: ~4-8% (~300-600 MB)
- Process RSS: ~100-200 MB

**After Model Load:**
- RAM: ~40-50% (~3-4 GB)
- Process RSS: ~3-4 GB
- Model stays in RAM (not swapped)

**During Inference:**
- RAM: Slight increase (~100-200 MB)
- Process RSS: Stable
- Fast inference (no disk I/O)

---

## ALTERNATIVE: Keep mmap Enabled

If you want to use mmap (less RAM, slower inference):

**Edit `ai/llama_wrapper.py`:**
```python
self._model = Llama(
    model_path=self._model_path,
    n_ctx=self._n_ctx,
    n_threads=self._n_threads,
    n_gpu_layers=self._n_gpu_layers,
    verbose=self._verbose,
    use_mmap=True,   # Enable mmap (default)
    use_mlock=False, # Disable mlock
)
```

**Tradeoffs:**
- ✅ Less RAM usage (~500 MB vs ~3.5 GB)
- ✅ Can load larger models
- ❌ Slower inference (disk I/O)
- ❌ Higher disk wear

---

**Last Updated:** 2026-01-27  
**Status:** Fix applied - awaiting verification
