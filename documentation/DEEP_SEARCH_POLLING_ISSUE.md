# Deep Search Job Polling Failure

## 1. The Symptom

- **Endpoint:** `POST /api/prospect/deep-search`
- **Behavior:**
  - Job creation works (returns a `job_id`).
  - Background task starts (logs show activity).
  - Polling `GET /api/jobs/{job_id}` returns the job, but the status often remains `RUNNING` indefinitely or fails to transition to `COMPLETED` with results.
  - `verify_system_health.py` fails at the polling stage.

## 2. The Context

- **Job Store:** In-memory dictionary in `backend/app/models/job.py`.
- **Background Task:** `run_deep_search` in `backend/main.py`.
- **Core Logic:** `ProspectorAgent.deep_prospecting_flow` in `backend/app/agents/prospector.py`.

## 3. Recent Changes & Current State

- **URL Search Fixed:** We fixed `url_prospecting_flow` by ensuring a single session is used and prospects are expunged before return.
- **Serialization Handling:** In `backend/main.py`, we explicitly convert `Prospect` objects to dictionaries before calling `update_job` to avoid JSON serialization errors with Pydantic models.
- **LeadMagic Fix:** We fixed the `LeadMagicClient` to handle both list and dict responses.

## 4. Hypotheses & Potential Causes

### A. Shared Session Concurrency Issue (Most Likely)

In `backend/app/agents/prospector.py`, the `deep_prospecting_flow` opens a single session:

```python
with Session(engine) as session:
    # ...
    tasks = [process_company_prospects(c) for c in all_companies]
    results_nested = await asyncio.gather(*tasks)
```

The inner function `process_company_prospects` uses this **same shared `session` object** to check for existing prospects and add new ones.
Since `asyncio.gather` runs these tasks concurrently, multiple tasks might be trying to use the `session` simultaneously. SQLAlchemy sessions are generally **not thread/async-safe** for concurrent operations. This could lead to:

- Race conditions.
- Silent failures.
- Database locking issues.

### B. Background Task Exception Swallowing

If an error occurs inside `deep_prospecting_flow` that isn't caught by the inner try/except blocks, it might bubble up. While `main.py` has a try/except block for the background task, if the error is a severe DB session error, it might behave unpredictably.

## 5. Suggested Debugging Steps for Agent

1.  **Verify Concurrency Hypothesis:**

    - Temporarily disable `asyncio.gather` in `deep_prospecting_flow` and run the loop sequentially:
      ```python
      # Instead of gather:
      results_nested = []
      for c in all_companies:
          results_nested.append(await process_company_prospects(c))
      ```
    - Run `verify_system_health.py`. If this works, the issue is definitely the shared session.

2.  **Fixing the Concurrency Issue:**

    - **Option A (Recommended):** Separate Data Gathering from DB Saving.
      - Refactor `process_company_prospects` to **only** fetch data from APIs (LeadMagic, Serper) and return raw data (dicts), **without** touching the DB.
      - Run this data gathering in parallel using `asyncio.gather`.
      - After gathering all data, iterate through the results and save them to the DB sequentially using the single session.
    - **Option B:** Create a new session inside each `process_company_prospects` call (but be careful with the `company` object being attached to a different session).

3.  **Add More Logging:**
    - Add print statements inside `process_company_prospects` to see if it starts and finishes for each company.
    - Add print statements in `main.py` before and after `update_job`.

## 6. Goal

- `verify_system_health.py` should pass completely (Health, URL Search, and Deep Search Job Polling).
