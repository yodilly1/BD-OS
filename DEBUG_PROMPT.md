# Debug & Fix BD-OS Prospecting System

## Context
You're working on BD-OS, a multi-agent sales automation system. The previous agent implemented an async job system, parallel processing, and settings page, but encountered persistent bugs in the prospecting endpoints that need debugging.

## Current State
- **Backend:** FastAPI running on `http://localhost:8000`
- **Frontend:** Next.js running on `http://localhost:3000`
- **Database:** SQLite with SQLModel
- **APIs:** LeadMagic (employee finder), Serper (search), Gemini/Claude (LLMs)

## Critical Issues to Debug

### 1. URL Search 500 Error (HIGH PRIORITY)
**Endpoint:** `POST /api/prospect/url-search`
**Symptom:** Returns 500 Internal Server Error when called with `{"url": "stripe.com"}`
**What We Know:**
- LeadMagic API is successfully finding employees (logs show "Found 5 employees")
- Error occurs during prospect creation/return process
- SQLAlchemy DetachedInstanceError was partially fixed but issue persists
- Traceback isn't printing to console despite error handling being added

**Files to Investigate:**
- `backend/app/agents/prospector.py` - `url_prospecting_flow()` method (lines 271-368)
- `backend/main.py` - `/api/prospect/url-search` endpoint (lines 93-100)
- `backend/app/tools/leadmagic_client.py` - `find_employees()` method

**Debugging Steps:**
1. Run `python verify_system_health.py` to reproduce the error
2. Check uvicorn logs for the full traceback (command ID: 7ba5ffa1-0fea-45fe-b331-fb043cc9000b)
3. Add print statements in `url_prospecting_flow` to isolate where it fails:
   - After LeadMagic call
   - After asyncio.gather
   - During prospect creation loop
4. Verify LeadMagic response structure matches what the code expects
5. Check if the issue is with session handling, data serialization, or response model validation

### 2. Deep Search Job Polling Failure
**Endpoint:** `POST /api/prospect/deep-search` + `GET /api/jobs/{job_id}`
**Symptom:** Job is created successfully but polling returns empty/error
**What We Know:**
- Job creation works (returns job_id)
- Background task starts (logs show company search beginning)
- Polling endpoint returns but status isn't updating correctly

**Files to Investigate:**
- `backend/app/models/job.py` - Job model and in-memory store
- `backend/main.py` - `deep_search()` and `get_job_status()` endpoints
- `frontend/src/components/ProspectorView.tsx` - `handleDeepSearch()` polling logic

**Debugging Steps:**
1. Add logging to `update_job()` to confirm it's being called
2. Verify the job_id being polled matches the one created
3. Check if the background task is completing or erroring silently
4. Test job polling manually: `curl http://localhost:8000/api/jobs/{job_id}`

## Testing Requirements

### Verification Script
Run `python verify_system_health.py` - it tests:
- Health endpoint (should pass ✅)
- URL search with Stripe (currently fails ❌)
- Deep search job lifecycle (currently fails ❌)

### Manual Testing
1. **URL Search:** 
   ```bash
   # PowerShell
   Invoke-WebRequest -Uri "http://localhost:8000/api/prospect/url-search" -Method POST -ContentType "application/json" -Body '{"url":"stripe.com"}'
   ```

2. **Deep Search:**
   - Use the frontend at `http://localhost:3000`
   - Fill in: Industry="FinTech", Size="Any Size", Keywords="payments", Titles="Engineer", Limit=5
   - Click "Launch Campaign"
   - Observe job polling in browser console

## Expected Behavior
- **URL Search:** Should return a list of Prospect objects with first_name, last_name, title, linkedin_url
- **Deep Search:** Should create a job, poll every 2 seconds, and display results when status="completed"

## Success Criteria
1. `verify_system_health.py` shows all tests passing (✅✅✅)
2. URL search returns prospects without 500 errors
3. Deep search jobs complete and results appear in the UI
4. No SQLAlchemy DetachedInstanceError or session-related errors

## Additional Context
- The system uses `asyncio.gather` for parallel LinkedIn lookups
- Prospects must be expunged from their session before returning
- LeadMagic returns employee data but NOT LinkedIn URLs (those are fetched via Serper)
- The job store is in-memory (not persisted to DB)

## Your Task
1. Reproduce both errors using the verification script
2. Capture full tracebacks (add more logging if needed)
3. Identify root causes
4. Implement fixes
5. Verify all tests pass
6. Document what you found and fixed

Good luck! The codebase is clean and well-structured, so the bugs should be straightforward once you see the full error messages.
