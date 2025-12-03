from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.db import engine
from sqlmodel import Session, select
from app.models.campaign import Campaign
from app.agents.prospector import ProspectorAgent
from app.agents.researcher import ResearcherAgent
from datetime import datetime
import asyncio

scheduler = AsyncIOScheduler()
prospector = ProspectorAgent()
researcher = ResearcherAgent()

async def run_auto_pilot():
    print("Running Auto-Pilot...")
    with Session(engine) as session:
        # Find active campaigns with auto-pilot enabled
        campaigns = session.exec(select(Campaign).where(
            Campaign.status == "Active",
            Campaign.auto_pilot_enabled == True
        )).all()
        
        print(f"Found {len(campaigns)} active auto-pilot campaigns.")
        
        for campaign in campaigns:
            print(f"Processing campaign: {campaign.name}")
            try:
                # Run deep search
                titles = campaign.target_titles
                
                if not (campaign.target_industry or campaign.target_keywords or titles):
                    print(f"Skipping {campaign.name}: No target criteria.")
                    continue

                # Run prospector
                # We limit to 5 per run to avoid blowing up quotas
                new_prospects = await prospector.deep_prospecting_flow(
                    industry=campaign.target_industry or "Technology",
                    size=campaign.target_size or "11-50",
                    keywords=campaign.target_keywords or "",
                    titles=titles,
                    limit=5,
                    campaign_id=campaign.id
                )
                
                print(f"Added {len(new_prospects)} prospects to {campaign.name}")
                
                # Automatically Enrich new prospects
                if new_prospects:
                    print(f"Enriching {len(new_prospects)} new prospects...")
                    for p in new_prospects:
                        try:
                            await researcher.enrich_prospect(p.id)
                        except Exception as e:
                            print(f"Error enriching prospect {p.id}: {e}")
                
                # Update last run time
                campaign.last_run_at = datetime.utcnow()
                session.add(campaign)
                session.commit()
                
            except Exception as e:
                print(f"Error processing campaign {campaign.name}: {e}")

def start_scheduler():
    # Run every 60 minutes
    scheduler.add_job(run_auto_pilot, 'interval', minutes=60)
    scheduler.start()
