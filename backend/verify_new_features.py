import asyncio
from app.db import create_db_and_tables, engine
from sqlmodel import Session, select
from app.models.campaign import Campaign
from app.models.prospect import Prospect
from app.scheduler import run_auto_pilot

async def main():
    print("--- VERIFYING NEW FEATURES ---")
    create_db_and_tables()
    
    # 1. Create a Campaign
    print("\n[1/3] Creating Campaign...")
    with Session(engine) as session:
        campaign = Campaign(
            name="Test Campaign",
            target_industry="Artificial Intelligence",
            target_size="11-50",
            target_titles=["Founder", "CEO"],
            status="Active",
            auto_pilot_enabled=True
        )
        session.add(campaign)
        session.commit()
        session.refresh(campaign)
        print(f"✅ Created Campaign: {campaign.name} (ID: {campaign.id})")
        campaign_id = campaign.id

    # 2. Add a Prospect to Campaign
    print("\n[2/3] Adding Prospect to Campaign...")
    with Session(engine) as session:
        # Create a dummy prospect first
        prospect = Prospect(
            first_name="Test",
            last_name="User",
            title="CEO",
            company_id=1,
            status="New"
        )
        session.add(prospect)
        session.commit()
        session.refresh(prospect)
        
        # Add to campaign
        prospect.campaign_id = campaign_id
        session.add(prospect)
        session.commit()
        print(f"✅ Added Prospect {prospect.id} to Campaign {campaign_id}")

    # 3. Run Auto-Pilot
    print("\n[3/3] Running Auto-Pilot (Dry Run)...")
    # This will actually run the search, so it might take a moment
    try:
        await run_auto_pilot()
        print("✅ Auto-Pilot run completed successfully.")
    except Exception as e:
        print(f"❌ Auto-Pilot Failed: {e}")

    print("\n--- VERIFICATION COMPLETE ---")

if __name__ == "__main__":
    asyncio.run(main())
