import asyncio


from app.agents.coach import CoachAgent
from app.agents.outreach import OutreachAgent
from app.agents.prospector import ProspectorAgent
from app.agents.researcher import ResearcherAgent
from app.db import create_db_and_tables


async def main():
    print("--- STARTING SYSTEM HEALTH CHECK ---")
    create_db_and_tables()

    # Initialize Agents
    prospector = ProspectorAgent()
    researcher = ResearcherAgent()
    outreach = OutreachAgent()
    coach = CoachAgent()

    # 1. Test Prospector (Manual Add - Fastest way to get a valid prospect)
    print("\n[1/4] Testing Prospector (Manual Add)...")
    # Using a known entity to ensure data availability
    prospect = await prospector.manual_prospecting_flow(
        first_name="Derric", last_name="Lee", domain="snorkel.ai"
    )

    if prospect:
        print(
            f"✅ Prospector Success: Added {prospect.first_name} {prospect.last_name} (ID: {prospect.id})"
        )
    else:
        print("❌ Prospector Failed: Could not add prospect.")
        return

    # 2. Test Researcher (Enrich Company)
    print("\n[2/4] Testing Researcher (Enrich Company)...")
    if prospect.company_id:
        company = await researcher.enrich_company(prospect.company_id)
        if company and company.description:
            print(f"✅ Researcher Success: Enriched {company.name}")
            print(f"   Description: {company.description[:50]}...")
        else:
            print("❌ Researcher Failed: Could not enrich company.")
    else:
        print("⚠️ Skipping Researcher: No company ID found.")

    # 3. Test Outreach (Generate Email)
    print("\n[3/4] Testing Outreach (Generate Email)...")
    try:
        interaction = await outreach.generate_email_sequence(
            prospect_id=prospect.id,
            context="Reaching out to discuss usage-based billing challenges.",
        )
        if interaction and interaction.content:
            print(f"✅ Outreach Success: Generated Email Draft (ID: {interaction.id})")
            print(f"   Preview: {interaction.content[:50]}...")
        else:
            print("❌ Outreach Failed: No content generated.")
    except Exception as e:
        print(f"❌ Outreach Error: {e}")

    # 4. Test Coach (Analyze Transcript)
    print("\n[4/4] Testing Coach (Analyze Transcript)...")
    transcript = """
    Rep: Hi, this is John from Vayu.
    Prospect: I'm not interested, we use Stripe.
    Rep: That's great, Stripe is a good partner of ours. We actually help with the complex billing logic that sits on top of Stripe.
    Prospect: Oh, interesting. Tell me more.
    """
    try:
        feedback = await coach.analyze_call_transcript(transcript)
        if feedback and feedback.content:
            print("✅ Coach Success: Analyzed Transcript")
            print(f"   Feedback: {feedback.content[:50]}...")
        else:
            print("❌ Coach Failed: No feedback generated.")
    except Exception as e:
        print(f"❌ Coach Error: {e}")

    print("\n--- SYSTEM HEALTH CHECK COMPLETE ---")


if __name__ == "__main__":
    asyncio.run(main())
