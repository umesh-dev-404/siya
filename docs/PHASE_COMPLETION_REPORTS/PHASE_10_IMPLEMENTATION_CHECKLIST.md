# PHASE 10 — REAL AI MODEL INTEGRATION — IMPLEMENTATION CHECKLIST
## Project: Siya
## Date: 2026-01-27
## Status: ✅ COMPLETE (2026-01-27)

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
- [x] Add timeout handling for inference (120s timeout)
- [x] Add error handling for model operations
- [x] Create model configuration module
- [x] Update integration points (CLI, service)
- [x] Add auto-load model on service startup
- [x] Explicitly start Orchestrator and CLI in service_main.py (ensures proper initialization)
- [x] **Performance optimizations:** max_tokens=128, temperature=0.2, stop sequences
- [x] **JSON repair function** for robust parsing
- [x] **Simplified prompt structure** for faster inference
- [x] **Enhanced logging** throughout inference pipeline
- [x] **HTTP connection improvements:** socket timeout, keep-alive headers
- [x] **Web interface improvements:** processing indicator, better error handling

### ✅ 2. Model Acquisition (Pi) — COMPLETE
- [x] Download Qwen 2.5 3B Instruct model (Q4_K_M quantized) ✅
- [x] Store model in designated directory (`models/qwen2.5-3b-q4_k_m/`) ✅
- [x] Model file verified and accessible ✅

### ✅ 3. llama.cpp Build (Pi) — COMPLETE
- [x] Install build dependencies ✅
- [x] Install llama-cpp-python Python bindings ✅
- [x] Verify llama.cpp installation ✅

### ✅ 4. Integration Testing (Pi) — COMPLETE
- [x] Test model loading ✅
- [x] Test model inference ✅
- [x] Test intent parsing with real model ✅
- [x] Verify schema compliance ✅
- [x] Test resource limits (RAM usage) ✅
- [x] Test timeout handling ✅
- [x] Test error recovery ✅

### ✅ 5. Resource Management — COMPLETE
- [x] Full RAM loading implemented (`use_mmap=False`) ✅
- [x] Monitor RAM usage during inference ✅
- [x] Implement graceful degradation on resource exhaustion ✅
- [x] Model stays loaded in memory (faster inference) ✅
- [x] Add resource monitoring logs ✅

### ✅ 6. Performance Optimization — COMPLETE
- [x] Measure inference latency (10-30 seconds) ✅
- [x] Optimize context window usage (4096 tokens) ✅
- [x] Test with various input lengths ✅
- [x] Verify Pi memory budget respected (~3-4 GB total) ✅
- [x] Full RAM loading for faster inference ✅

### ✅ 7. Documentation — COMPLETE
- [x] Update model configuration documentation ✅
- [x] Document model download process ✅
- [x] Document llama.cpp build process ✅
- [x] Create comprehensive AI model guide (`AI_MODEL_GUIDE.md`) ✅
- [x] Document system prompt integration and location ✅
- [x] Update deployment guide with model setup ✅
- [x] Create Phase 10 completion report ✅

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
- **Max RAM Usage:** < 4GB (model + system) ✅ Verified
- **Inference Timeout:** 120 seconds (increased for Pi hardware)
- **Model Load Timeout:** 60 seconds
- **Expected Inference Time:** 10-30 seconds per query (optimized)

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
- [x] Performance optimizations implemented ✅
- [x] JSON repair function implemented ✅
- [x] HTTP connection improvements implemented ✅
- [x] Documentation complete ✅
- [x] Real AI model loads and runs on Pi ✅
- [x] Intent parsing produces valid schema-compliant output ✅
- [x] RAM usage within Pi constraints (~3-4 GB total) ✅
- [x] Inference latency acceptable (10-30 seconds, optimized for Pi hardware) ✅
- [x] Model stays loaded in memory (faster subsequent inferences) ✅
- [x] Error handling works correctly (JSON parsing errors handled gracefully) ✅
- [x] Natural language input supported ✅
- [x] Full RAM loading implemented (faster inference) ✅
- [x] Performance verified (first query: 30-60s, subsequent: 10-30s) ✅

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
**Status:** ✅ COMPLETE — Phase 10 Operational  
**Model:** Qwen 2.5 3B Instruct (Q4_K_M)  
**Performance:** 10-30 seconds per query (optimized)  
**RAM Usage:** ~3-4 GB (full RAM loading enabled)  
**Next Phase:** Phase 11 — Tool Implementations
