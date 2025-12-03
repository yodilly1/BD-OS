import asyncio

from sqlmodel import Session, select

from app.agents.outreach import OutreachAgent
from app.agents.prospector import ProspectorAgent
from app.db import create_db_and_tables, engine
from app.models.prospect import Prospect


async def main():
    create_db_and_tables()
    prospector = ProspectorAgent()
    outreach = OutreachAgent()

    print("\n--- 1. Testing Search Candidates (Review Flow) ---")
    # Should return dicts, NOT save to DB
    candidates = await prospector.search_candidates(
        industry="AI Software",
        size="50-200 employees",
        keywords="generative ai",
        titles=["CEO"],
        limit=2,
    )
    print(f"Found {len(candidates)} candidates.")
    if candidates:
        print(
            f"Sample: {candidates[0].get('first_name')} {candidates[0].get('last_name')} - {candidates[0].get('company_name')}"
        )

    # Verify NOT in DB (checking by linkedin_url)
    if candidates:
        with Session(engine) as session:
            url = candidates[0]["linkedin_url"]
            exists = session.exec(
                select(Prospect).where(Prospect.linkedin_url == url)
            ).first()
            if not exists:
                print("SUCCESS: Candidate not yet in DB.")
            else:
                print("WARNING: Candidate already in DB (might be from previous run).")

    print("\n--- 2. Testing Save Candidates ---")
    if candidates:
        saved = await prospector.save_candidates(candidates[:1])
        print(f"Saved {len(saved)} prospects.")
        print(f"Saved ID: {saved[0].id}, Status: {saved[0].status}")

    print("\n--- 3. Testing URL Search (Multi-Title) ---")
    # Use a known company
    url_prospects = await prospector.url_prospecting_flow(
        "https://snorkel.ai", titles=["CEO", "CTO"]
    )
    print(f"Found {len(url_prospects)} prospects from URL search.")
    for p in url_prospects:
        print(f"- {p.first_name} {p.last_name} ({p.title})")

    print("\n--- 4. Testing Outreach Prompt Fix ---")
    if candidates:
        # Use the prospect we just saved
        p_id = saved[0].id
        print(f"Generating email for Prospect ID {p_id}...")
        interaction = await outreach.generate_email_sequence(p_id, "Testing prompt fix")
        print("--- Email Content Start ---")
        print(interaction.content[:200] + "...")
        print("--- Email Content End ---")

        if "Critique:" in interaction.content or "Analysis:" in interaction.content:
            print("FAIL: Output still contains analysis.")
        else:
            print("SUCCESS: Output looks clean.")


if __name__ == "__main__":
    asyncio.run(main())
