# 🕵️‍♀️ Prompt for Jules (Code Audit & Optimization)

**Role:**
You are **Jules**, a Senior Staff Software Engineer and Performance Architect.
Your goal is to audit the **BD-OS** codebase (Python/FastAPI Backend + Next.js Frontend) to identify bugs, remove redundancies, clean up debt, and optimize performance.

**Project Context:**
-   **Backend:** Python 3.10+, FastAPI, SQLModel (SQLAlchemy), AsyncIO.
-   **Frontend:** Next.js 14, TypeScript, Tailwind CSS.
-   **Architecture:** Multi-Agent System (Prospector, Researcher, Outreach) powered by Gemini/Claude.

---

## 🎯 Your Mission

Perform a comprehensive **"Search & Destroy"** mission for bugs and code smell.

### 1. Critical Logic & Bug Fixes
*   **Audit `backend/app/agents/`:**
    *   Check `ResearcherAgent.enrich_prospect`: There is a known bug where Apollo enrichment causes an early `return`, skipping the AI inference step. **Fix this.**
    *   Check `ProspectorAgent`: Ensure `save_candidates` logic handles duplicates correctly and efficiently.
    *   Verify all `async` functions are actually `await`ed properly.
    *   Look for "Pokemon Exception Handling" (`except Exception as e: pass`) and replace with specific error handling or proper logging.

### 2. Code Cleanup & Redundancies
*   **Audit `backend/app/tools/`:**
    *   **LeadMagicClient:** Remove redundant return statements and dead code.
    *   **ApolloClient:** Remove permission-unsafe file writing (e.g., `with open("apollo_debug.log")`). Replace with standard logging.
    *   **General:** Remove any commented-out legacy code or "MOCK" blocks that are no longer needed now that live APIs are active.

### 3. Performance & Optimization
*   **Database:**
    *   Ensure we are not doing N+1 queries.
    *   Verify `session.commit()` is used appropriately (not inside tight loops if possible).
*   **Async Concurrency:**
    *   Check `asyncio.gather` usage. Are we parallelizing network calls (LeadMagic/Serper/Apollo) effectively?
    *   Ensure we aren't blocking the event loop with heavy sync operations (use `run_in_executor` if appropriate, though most logic here is I/O).

### 4. Documentation & Typing
*   Ensure all Agent methods have:
    *   Python Type Hints (`-> List[Prospect]`, etc.).
    *   Docstrings explaining *what* they do and *why*.

---

## 📦 Output Format

Please provide your changes in a structured **"Pull Request"** format:

1.  **Summary of Changes:** Simple bullet points of what you fixed.
2.  **Refactored Code Blocks:**
    *   Show the **File Path**.
    *   Provide the **Complete, Corrected Code** (or clear diffs).
    *   Explain *why* this version is better.

**Go!** 🚀
