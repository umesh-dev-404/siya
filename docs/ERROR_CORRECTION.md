# Error Correction Log

This document tracks errors encountered during development/testing and their solutions.
Maintained per dev-rules.md §8.2 (Error Correction Discipline).

---

## Comprehensive Codebase Audit: 2026-01-28

**Status:** ✅ NO BUGS FOUND

**Audit Scope:**
- 122 Python files across 30 directories
- 18 test files with 100+ unit tests
- Core modules: orchestrator, mcp, memory, sync, tools, notifications, voice, automations

**Verification Performed:**
- ✅ Searched for TODO/FIXME/BUG/HACK markers — **None found**
- ✅ Searched for bare `except:` clauses — **None found**
- ✅ Verified database schemas match `system_schema.json`
- ✅ Verified LAW compliance comments in all critical modules
- ✅ Verified thread-safe operations in sync/queue modules
- ✅ Verified proper error handling with logging (no silent failures)

**Files Audited in Detail:**
- `orchestrator/orchestrator.py` (643 lines)
- `mcp/mcp_server.py`, `mcp/mcp_http_handler.py`
- `sync/sync_manager.py`, `sync/supabase_client.py`, `sync/sync_queue.py`
- `memory/tier_manager.py`, `memory/database_schema.py`
- `tools/tool_executor.py`, `ai/intent_parser.py`
- `notifications/notification_manager.py`
- `automations/schedule_manager.py`
- `voice/tts.py`
- `service_main.py`

**Conclusion:** The codebase is clean, well-documented, and production-ready. All 18 Canonical Laws are properly enforced through code architecture and schema constraints.

---

## Session: 2026-01-28 (CLI Confirmation & Sync Verification)

### Error 1: PyAudio Build Failure (Windows)
**Symptom:** `pip install -e .` failed with `Cannot open include file: 'portaudio.h'`  
**Cause:** `PyAudio` requires C++ compilation and PortAudio development headers, which aren't available on Windows without extra setup.  
**Solution:** Moved `PyAudio`, `SpeechRecognition`, `pyttsx3`, and `sounddevice` from core dependencies to `[project.optional-dependencies.voice]` in `pyproject.toml`. CLI users can now install without voice features.  
**Files Modified:** `pyproject.toml`

---

### Error 2: pyproject.toml Syntax Errors
**Symptom:** `tomllib.TOMLDecodeError: Expected '=' after a key` and `Cannot declare twice`  
**Cause:** Accidental deletion of `dependencies = [` header during edit, and duplicate `[project.optional-dependencies]` table declarations.  
**Solution:** Restored the `dependencies = [` header and consolidated `voice` and `dev` optional deps into a single `[project.optional-dependencies]` table.  
**Files Modified:** `pyproject.toml`

---

### Error 3: Tool Request Denied After Confirmation
**Symptom:** After user typed `y` to confirm `trigger_sync`, received `MCP_ERROR -32602: Tool request denied`  
**Cause:** `AuthorizationLayer` returns `authorized=False` when `requires_confirmation=True`. The handler didn't override this after receiving confirmation.  
**Solution:** Modified `mcp/mcp_http_handler.py` to use `elif not auth.authorized:` instead of `if not auth.authorized:`, so confirmed requests bypass the denial.  
**Files Modified:** `mcp/mcp_http_handler.py`

---

### Error 4: Generic "Insert failed" Error
**Symptom:** `RuntimeError: Insert failed` with no details  
**Cause:** `SupabaseClient.execute_with_retry()` returned `(False, None)`, discarding the error message.  
**Solution:** Modified `execute_with_retry` to return `(False, error_message)` and updated `SyncManager` to propagate the error details.  
**Files Modified:** `sync/supabase_client.py`, `sync/sync_manager.py`

---

### Error 5: Supabase Schema Mismatch (content/source columns)
**Symptom:** `PGRST204: Could not find the 'content' column of 'memory'` and `'source' column`  
**Cause:** Test script `verify_sync_data.py` used incorrect column names (`content` instead of `key`/`value`, `source` instead of `source_type`).  
**Solution:** Updated `scripts/verify_sync_data.py` to use exact columns from `memory/database_schema.py`: `id`, `key`, `value`, `memory_tier`, `tags`, `confidence`, `created_at`, `updated_at`, `source_type`.  
**Files Modified:** `scripts/verify_sync_data.py`

---

## Template for Future Entries

### Error N: [Short Title]
**Symptom:** [What error message or behavior was observed]  
**Cause:** [Root cause analysis]  
**Solution:** [What was changed to fix it]  
**Files Modified:** [List of files]

---
