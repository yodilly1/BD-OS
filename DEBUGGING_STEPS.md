# IMMEDIATE ACTION PLAN FOR DEBUGGING AGENT

## STEP 1: Commit URL Search Fix (DO THIS FIRST)

You've successfully fixed the URL search DetachedInstanceError. Commit this immediately:

```bash
cd c:/Users/leerg/OneDrive/Desktop/BD-OS
git add backend/app/agents/prospector.py
git commit -m "fix: Resolve URL search DetachedInstanceError with single session approach"
git push origin main
```

**Verify it works:**
```bash
python verify_system_health.py
```
The URL search test should now pass ✅

---

## STEP 2: Fix Deep Search Job Serialization Issue

The deep search is failing because **Prospect objects cannot be serialized to JSON** when stored in the in-memory job store.

### The Problem
In `backend/main.py`, the background task does this:
```python
results = await prospector.deep_prospecting_flow(...)
update_job(job_id, JobStatus.COMPLETED, result=results)  # ❌ FAILS - can't serialize Prospect objects
```

### The Solution
Convert Prospect objects to dictionaries before storing:

**File:** `backend/main.py`  
**Location:** Inside the `run_deep_search` function (around line 70-80)

**REPLACE THIS:**
```python
results = await prospector.deep_prospecting_flow(
    req.industry, 
    req.size, 
    req.keywords, 
    req.titles,
    req.limit
)
update_job(job_id, JobStatus.COMPLETED, result=results)
```

**WITH THIS:**
```python
results = await prospector.deep_prospecting_flow(
    req.industry, 
    req.size, 
    req.keywords, 
    req.titles,
    req.limit
)

# Convert Prospect objects to dicts for JSON serialization
result_dicts = [
    {
        "id": p.id,
        "first_name": p.first_name,
        "last_name": p.last_name,
        "title": p.title,
        "linkedin_url": p.linkedin_url,
        "company_id": p.company_id,
        "status": p.status,
        "email": p.email,
        "phone": p.phone
    }
    for p in results
]
update_job(job_id, JobStatus.COMPLETED, result=result_dicts)
```

---

## STEP 3: Apply Same Session Fix to Deep Search

Apply the same single-session approach you used for URL search to the `deep_prospecting_flow` method.

**File:** `backend/app/agents/prospector.py`  
**Method:** `deep_prospecting_flow` (around line 155-269)

**Key changes needed:**
1. Move the session creation OUTSIDE the loop
2. Expunge prospects within the same session where they're created
3. Use the same pattern as your URL search fix

**Example structure:**
```python
async def deep_prospecting_flow(self, industry: str, size: str, keywords: str, titles: List[str], limit: int = 20) -> List[Prospect]:
    # ... company finding logic ...
    
    all_prospects = []
    
    with Session(engine) as session:  # ✅ Single session for all prospects
        for company in all_companies:
            # ... employee finding and filtering ...
            
            for emp in enriched_candidates:
                # Check existing
                existing = session.exec(
                    select(Prospect).where(Prospect.linkedin_url == linkedin_url)
                ).first() if linkedin_url else None
                
                if existing:
                    session.refresh(existing)
                    session.expunge(existing)
                    all_prospects.append(existing)
                    continue
                
                # Create new
                prospect = Prospect(...)
                session.add(prospect)
                session.commit()
                session.refresh(prospect)
                session.expunge(prospect)  # ✅ Expunge in same session
                all_prospects.append(prospect)
    
    return all_prospects
```

---

## STEP 4: Test Everything

Run the verification script:
```bash
python verify_system_health.py
```

**Expected output:**
```
Testing /health endpoint... ✅ PASSED
Testing /api/prospect/url-search (Stripe)... ✅ PASSED
Testing /api/prospect/deep-search (Job System)...
  - Starting job... ✅ PASSED
  - Polling job status... ✅ PASSED (Completed)
  - Result count: X

=== Summary ===
🎉 All systems operational. No backend regressions detected.
```

---

## STEP 5: Commit Deep Search Fix

```bash
git add backend/main.py backend/app/agents/prospector.py
git commit -m "fix: Resolve deep search job serialization and session management issues

- Convert Prospect objects to dicts before storing in job results
- Apply single-session pattern to deep_prospecting_flow
- Ensure proper expunge within session context"
git push origin main
```

---

## TROUBLESHOOTING

### If Step 2 Still Fails:
Add debug logging to see what's happening:

```python
# In main.py, in run_deep_search:
try:
    results = await prospector.deep_prospecting_flow(...)
    print(f"DEBUG: Got {len(results)} results, type: {type(results[0]) if results else 'empty'}")
    
    result_dicts = [...]
    print(f"DEBUG: Converted to {len(result_dicts)} dicts")
    
    update_job(job_id, JobStatus.COMPLETED, result=result_dicts)
    print(f"DEBUG: Job {job_id} updated successfully")
except Exception as e:
    print(f"ERROR in background task: {e}")
    import traceback
    traceback.print_exc()
    update_job(job_id, JobStatus.FAILED, error=str(e))
```

### If Polling Still Fails:
Check the job store directly:

```python
# Add a debug endpoint in main.py:
@app.get("/api/jobs/debug")
async def debug_jobs():
    from app.models.job import jobs
    return {"job_count": len(jobs), "job_ids": list(jobs.keys())}
```

Then call: `curl http://localhost:8000/api/jobs/debug`

---

## SUCCESS CRITERIA

✅ URL search returns prospects without errors  
✅ Deep search creates job successfully  
✅ Job polling returns completed status  
✅ Results appear in frontend  
✅ `verify_system_health.py` shows all tests passing  

---

## NOTES

- The URL search fix you've already done is solid - commit it immediately
- The deep search issue is 99% likely the serialization problem described in Step 2
- If you still have issues after Step 2, the session management in Step 3 is the fallback
- Don't overthink it - these are the two root causes based on the symptoms

Good luck! 🚀
