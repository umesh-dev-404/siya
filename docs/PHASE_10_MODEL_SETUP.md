# PHASE 10 — MODEL SETUP GUIDE
## Project: Siya
## Date: 2026-01-27

---

## OVERVIEW

This guide provides step-by-step instructions for setting up the AI model on Raspberry Pi 5 for Phase 10 implementation.

---

## PREREQUISITES

- Raspberry Pi 5 with 8 GB RAM
- Python 3.11+ installed
- Siya project cloned and installed
- At least 4 GB free disk space

---

## STEP 1: INSTALL BUILD DEPENDENCIES

```bash
# On Raspberry Pi
sudo apt update
sudo apt install -y build-essential cmake git python3-dev
```

---

## STEP 2: INSTALL llama-cpp-python

### Option A: Install from PyPI (Recommended)

```bash
# On Raspberry Pi
cd /opt/siya
source venv/bin/activate

# Install llama-cpp-python (this will build from source on ARM64)
pip install llama-cpp-python
```

**Note:** This may take 30-60 minutes to build on Raspberry Pi 5.

### Option B: Build with Optimizations

```bash
# Set environment variables for optimization
export CMAKE_ARGS="-DLLAMA_BLAS=ON -DLLAMA_BLAS_VENDOR=OpenBLAS"
export FORCE_CMAKE=1

# Install OpenBLAS (optional, for better performance)
sudo apt install -y libopenblas-dev

# Install llama-cpp-python
pip install llama-cpp-python
```

---

## STEP 3: DOWNLOAD MODEL ✅ COMPLETE

### Model Details
- **Model:** Qwen 2.5 3B Instruct
- **Quantization:** Q4_K_M (recommended)
- **Expected Size:** ~2-3 GB
- **Source:** Hugging Face

### Download Steps

```bash
# On Raspberry Pi
cd /opt/siya
mkdir -p qwen2.5-3b-q4_k_m
cd qwen2.5-3b-q4_k_m

# Authenticate with Hugging Face (if not already done)
hf auth login

# Download model files
hf download Qwen/Qwen2.5-3B-Instruct-GGUF \
  --include "*Q4_K_M*gguf" \
  --local-dir .
```

**Note:** This downloads all quantization levels. You'll need to identify the Q4_K_M file for use.

### Verify Model File

```bash
# List downloaded files
ls -lh *.gguf

# Identify Q4_K_M file (usually named like qwen2.5-3b-instruct-q4_k_m.gguf)
# Check file size (should be ~2-3 GB)
ls -lh *q4_k_m*.gguf

# Verify file integrity (if checksum available)
# sha256sum qwen2.5-3b-instruct-q4_k_m.gguf
```

**Status:** ✅ Model download completed successfully.

---

## STEP 4: CONFIGURE MODEL PATH

### Option A: Environment Variable

```bash
# On Raspberry Pi
# Update path to match your actual model file location
# First, identify the exact .gguf filename in the folder:
ls -lh /opt/siya/models/qwen2.5-3b-q4_k_m/qwen2.5-3b-instruct-q4_k_m.gguf

# Then set the environment variable (replace with actual filename):
export SIYA_MODEL_PATH=/opt/siya/qwen2.5-3b-q4_k_m/qwen2.5-3b-instruct-q4_k_m.gguf

# Or if you moved it to models directory:
# export SIYA_MODEL_PATH=/opt/siya/models/qwen2.5-3b-instruct-q4_k_m.gguf
```

### Option B: Use Default Configuration

The system will automatically check for the model in the default location if `SIYA_MODEL_PATH` is not set:

**Default location:** `/opt/siya/qwen2.5-3b-q4_k_m/qwen2.5-3b-instruct-q4_k_m.gguf`

The `config/model_config.py` module will:
1. First check the `SIYA_MODEL_PATH` environment variable
2. If not set, check the default location above
3. If default file doesn't exist, search for any `.gguf` file in `/opt/siya/qwen2.5-3b-q4_k_m/`
4. Prefer Q4_K_M quantized files if multiple are found

**No configuration needed** if your model is in the default location with the expected filename.

To customize the default, edit `config/model_config.py` and modify the `get_model_path()` function.

---

## STEP 5: UPDATE CODE AND TEST MODEL LOADING

### Step 5a: Pull Latest Code

```bash
# On Raspberry Pi
cd /opt/siya
source venv/bin/activate

# Pull latest changes from git
git pull

# Reinstall package in editable mode to pick up new files
pip install -e .
```

### Step 5b: Test Model Loading

```bash
# On Raspberry Pi
cd /opt/siya
source venv/bin/activate

# Test model loading using config module (will use default path if not set)
python -c "
from ai.model_manager import ModelManager
from ai.llama_wrapper import is_llama_available
from config.model_config import get_model_path

print(f'llama-cpp-python available: {is_llama_available()}')

model_path = get_model_path()
print(f'Model path: {model_path}')

if is_llama_available() and model_path:
    manager = ModelManager(model_path=model_path)
    print('Loading model...')
    if manager.load_model():
        print('✅ Model loaded successfully!')
        print(f'Model size: {manager.get_model_size_mb()} MB')
        manager.unload_model()
    else:
        print('❌ Model loading failed')
elif not is_llama_available():
    print('⚠️  llama-cpp-python not available - install with: pip install llama-cpp-python')
elif not model_path:
    print('⚠️  Model path not found - check configuration or set SIYA_MODEL_PATH')
"
```

---

## STEP 6: VERIFY RESOURCE USAGE

```bash
# Monitor RAM usage during model loading
watch -n 1 free -h

# In another terminal, load the model and observe RAM usage
# Should stay under 4 GB total (model + system)
```

---

## STEP 7: UPDATE SERVICE CONFIGURATION

If running as a systemd service, update the service file to include model path:

```bash
# Edit service file
sudo nano /etc/systemd/system/siya.service

# Add environment variable (update path to match actual model file):
[Service]
Environment="SIYA_MODEL_PATH=/opt/siya/qwen2.5-3b-q4_k_m/qwen2.5-3b-instruct-q4_k_m.gguf"

# Reload and restart
sudo systemctl daemon-reload
sudo systemctl restart siya
```

---

## TROUBLESHOOTING

### Issue: llama-cpp-python build fails

**Solution:**
- Ensure all build dependencies are installed
- Check available RAM (build needs ~2 GB free)
- Try building with fewer threads: `CMAKE_BUILD_PARALLEL_LEVEL=2 pip install llama-cpp-python`

### Issue: Model loading fails with "out of memory"

**Solution:**
- Check available RAM: `free -h`
- Ensure at least 4 GB free RAM
- Close other applications
- Consider using smaller quantization (Q4_0 instead of Q4_K_M)

### Issue: Inference is too slow

**Solution:**
- Ensure model is loaded (not loading on each request)
- Check CPU usage: `htop`
- Consider using fewer threads if CPU is saturated
- Verify model quantization (Q4_K_M is good balance)

### Issue: Model file not found

**Solution:**
- Verify model path: `ls -lh /opt/siya/qwen2.5-3b-q4_k_m/`
- Check file permissions: `chmod 644 /opt/siya/qwen2.5-3b-q4_k_m/*.gguf`
- Verify environment variable: `echo $SIYA_MODEL_PATH`
- Confirm exact filename: `ls -lh /opt/siya/qwen2.5-3b-q4_k_m/*.gguf`

---

## VERIFICATION CHECKLIST

- [ ] Build dependencies installed
- [ ] llama-cpp-python installed and importable
- [x] Model file downloaded and verified ✅
- [ ] Model path configured
- [ ] Model loads successfully
- [ ] RAM usage acceptable (< 4 GB total)
- [ ] Inference works (test with simple prompt)
- [ ] Service configuration updated (if using systemd)

---

## NEXT STEPS

After model setup is complete:
1. Test intent parsing with real model
2. Verify schema compliance
3. Monitor resource usage
4. Optimize performance if needed
5. Complete Phase 10 implementation

---

**Last Updated:** 2026-01-27  
**Status:** Model download complete ✅ — Ready for configuration and testing
