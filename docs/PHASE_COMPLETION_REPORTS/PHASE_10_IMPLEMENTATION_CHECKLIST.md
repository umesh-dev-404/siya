# PHASE 10 — REAL AI MODEL INTEGRATION — IMPLEMENTATION CHECKLIST
## Project: Siya
## Date: 2026-01-27
## Status: ⏳ IN PROGRESS

---

## PHASE 10 OBJECTIVE

Replace stub AI implementation with **real llama.cpp integration** for production intent parsing.

---

## IMPLEMENTATION CHECKLIST

### ✅ 1. Code Preparation (PC) — COMPLETE
- [x] Update `pyproject.toml` with llama-cpp-python dependency
- [x] Create `ai/llama_wrapper.py` for llama.cpp integration
- [x] Update `ai/model_manager.py` to use real llama.cpp
- [x] Update `ai/intent_parser.py` to use real model
- [x] Integrate system prompt from `docs/System Prompt.md`
- [x] Add system prompt caching for efficiency
- [x] Add resource monitoring for model loading
- [x] Add timeout handling for inference
- [x] Add error handling for model operations
- [x] Create model configuration module
- [x] Update integration points (CLI, service)
- [x] Add auto-load model on service startup
- [x] Explicitly start Orchestrator and CLI in service_main.py (ensures proper initialization)

### ⏳ 2. Model Acquisition (Pi)
- [x] Download Qwen 2.5 3B Instruct model (Q4_K_M quantized) ✅
- [ ] Verify model file integrity (checksum)
- [x] Store model in designated directory (`qwen2.5-3b-q4_k_m/`) ✅
- [ ] Set appropriate file permissions

### ⏳ 3. llama.cpp Build (Pi)
- [ ] Install build dependencies (CMake, build-essential, etc.)
- [ ] Clone or install llama.cpp
- [ ] Build llama.cpp with ARM64 optimizations
- [ ] Verify llama.cpp installation
- [ ] Install llama-cpp-python Python bindings

### ⏳ 4. Integration Testing (Pi)
- [ ] Test model loading
- [ ] Test model inference
- [ ] Test intent parsing with real model
- [ ] Verify schema compliance
- [ ] Test resource limits (RAM usage)
- [ ] Test timeout handling
- [ ] Test error recovery

### ⏳ 5. Resource Management
- [ ] Implement load-on-demand strategy
- [ ] Monitor RAM usage during inference
- [ ] Implement graceful degradation on resource exhaustion
- [ ] Implement model unloading when idle
- [ ] Add resource monitoring logs

### ⏳ 6. Performance Optimization
- [ ] Measure inference latency
- [ ] Optimize context window usage
- [ ] Test with various input lengths
- [ ] Verify Pi memory budget respected (< 4GB total)

### ⏳ 7. Documentation
- [x] Update model configuration documentation ✅
- [x] Document model download process ✅
- [x] Document llama.cpp build process ✅
- [x] Create comprehensive model testing guide ✅
- [x] Document system prompt integration and location ✅
- [x] Update deployment guide with model setup ✅
- [ ] Create Phase 10 completion report (pending Pi testing)

---

## TECHNICAL SPECIFICATIONS

### Model Details
- **Model:** Qwen 2.5 3B Instruct
- **Quantization:** Q4_K_M
- **Context Window:** ≤ 4k tokens
- **Expected Size:** ~2-3 GB
- **Expected RAM Usage:** ~3-4 GB when loaded

### llama.cpp Requirements
- **Version:** Latest stable
- **Build:** ARM64 optimized
- **Python Bindings:** llama-cpp-python
- **Dependencies:** CMake, build-essential, Python dev headers

### Resource Constraints
- **Max RAM Usage:** < 4GB (model + system)
- **Inference Timeout:** 30 seconds
- **Model Load Timeout:** 60 seconds

---

## IMPLEMENTATION STEPS

### Step 1: Code Updates (PC)
1. Add llama-cpp-python to dependencies
2. Create llama.cpp wrapper module
3. Update ModelManager to use real model
4. Update IntentParser to use real inference
5. Add resource monitoring

### Step 2: Pi Setup
1. Install build dependencies
2. Build llama.cpp
3. Install Python bindings
4. Download model
5. Verify installation

### Step 3: Integration
1. Configure model path
2. Test model loading
3. Test inference
4. Test intent parsing
5. Verify schema compliance

### Step 4: Optimization
1. Measure performance
2. Optimize context window
3. Test resource limits
4. Fine-tune timeouts

---

## SUCCESS CRITERIA

- [x] Code changes complete (PC) ✅
- [x] System prompt integrated ✅
- [x] Model auto-loading on startup implemented ✅
- [x] Documentation complete ✅
- [ ] Real AI model loads and runs on Pi
- [ ] Intent parsing produces valid schema-compliant output
- [ ] RAM usage within Pi constraints (< 4GB total)
- [ ] Inference latency acceptable (< 5 seconds for typical queries)
- [ ] Model can be loaded/unloaded on demand
- [ ] Error handling works correctly
- [ ] All tests pass

---

## RISKS AND MITIGATION

### Risk 1: Model too large for Pi RAM
- **Mitigation:** Use Q4_K_M quantization, implement load/unload

### Risk 2: Inference too slow
- **Mitigation:** Optimize context window, implement caching

### Risk 3: llama.cpp build issues
- **Mitigation:** Document build process, test on clean Pi

### Risk 4: Schema validation failures
- **Mitigation:** Implement prompt engineering, add retry logic

---

**Last Updated:** 2026-01-27  
**Status:** ⏳ IN PROGRESS (PC Code Complete, Pi Testing Pending)  
**Next Step:** Pull latest code on Pi, reinstall package, test model loading
