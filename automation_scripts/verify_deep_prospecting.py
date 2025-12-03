import asyncio
import os
import sys

from dotenv import load_dotenv

sys.path.append(os.path.join(os.getcwd(), "backend"))

from sqlmodel import Session

from app.agents.outreach import OutreachAgent
from app.agents.prospector import ProspectorAgent
from app.db import create_db_and_tables, engine
from app.models.prospect import Prospect

# Force load env vars
load_dotenv("backend/.env")


async def test_deep_prospecting():
    print("--- Starting Deep Prospecting Test ---")
    create_db_and_tables()

    prospector = ProspectorAgent()
    outreach = OutreachAgent()

    # 1. Test Deep Prospecting Flow
    print("\n1. Testing Deep Prospecting Flow...")
    industry = "FinTech"
    size = "50-200 employees"
    keywords = "usage-based billing"
    titles = ["VP of Sales", "Head of RevOps"]

    print(f"   Criteria: {industry}, {size}, {keywords}")
    print(f"   Titles: {titles}")

    try:
        # We'll limit the internal search in the agent if possible, but for now we run the full flow
        # Note: This consumes API credits, so we hope the agent finds something quickly.
        prospects = await prospector.deep_prospecting_flow(
            industry, size, keywords, titles
        )

        print(f"   Result: Found {len(prospects)} prospects.")

        if len(prospects) == 0:
            print(
                "   WARNING: No prospects found. This might be due to API limits or mock data."
            )
        else:
            for p in prospects:
                print(f"   - Found: {p.first_name} {p.last_name} ({p.title})")

            # Verify DB persistence
            with Session(engine) as session:
                saved_prospect = session.get(Prospect, prospects[0].id)
                if saved_prospect:
                    print("   SUCCESS: Prospect verified in Database.")
                else:
                    print("   ERROR: Prospect NOT found in Database.")

            # 2. Test Outreach Generation (Vayu Context)
            print("\n2. Testing Outreach Generation (Vayu Context)...")
            target_prospect = prospects[0]
            context = "Pitching our new revenue recognition module."

            interaction = await outreach.generate_email_sequence(
                target_prospect.id, context
            )

            print("   Generated Email Draft:")
            print("-" * 40)
            print(interaction.content)
            print("-" * 40)

            if (
                "Vayu" in interaction.content
                or "usage-based" in interaction.content.lower()
            ):
                print("   SUCCESS: Vayu context detected in email.")
            else:
                print("   WARNING: Vayu context NOT clearly detected.")

    except Exception as e:
        print(f"   CRITICAL ERROR: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_deep_prospecting())
