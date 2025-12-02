import asyncio
import os
import sys
from dotenv import load_dotenv

# Add backend directory to path so we can import app modules
sys.path.append(os.path.join(os.getcwd(), "backend"))

from app.agents.prospector import ProspectorAgent
from app.agents.researcher import ResearcherAgent
from app.agents.outreach import OutreachAgent
from app.models.prospect import Prospect
from app.models.company import Company
from app.db import engine
from sqlmodel import Session, select

load_dotenv()

async def verify_full_flow():
    print("\n=== Verifying Full End-to-End Workflow ===")
    
    # 1. Initialize Agents
    prospector = ProspectorAgent()
    researcher = ResearcherAgent()
    outreach = OutreachAgent()
    
    target_company = "snorkel.ai"
    target_role = "Director of Finance"
    
    print(f"\n[1] Prospecting: Finding '{target_role}' at '{target_company}'...")
    
    # Use the updated url_prospecting_flow with titles
    prospects = await prospector.url_prospecting_flow(target_company, titles=[target_role])
    
    if not prospects:
        print("X No prospects found. Aborting.")
        return

    print(f"-> Found {len(prospects)} prospects.")
    target_prospect = prospects[0]
    print(f"   Target: {target_prospect.first_name} {target_prospect.last_name} ({target_prospect.title})")
    print(f"   LinkedIn: {target_prospect.linkedin_url}")
    
    if not target_prospect.id:
        print("X Prospect ID missing (not saved to DB?). Aborting.")
        return

    # 2. Enrichment
    print(f"\n[2] Enrichment: Enriching prospect {target_prospect.id}...")
    enriched_prospect = await researcher.enrich_prospect(target_prospect.id)
    
    print(f"-> Enrichment Complete.")
    print(f"   Email: {enriched_prospect.email}")
    print(f"   Phone: {enriched_prospect.phone}")
    print(f"   Summary: {enriched_prospect.summary[:100]}...")
    print(f"   Pain Points: {enriched_prospect.pain_points[:100]}...")
    
    # 3. Outreach Generation
    print(f"\n[3] Outreach: Generating email cadence...")
    # Need to fetch company for context
    with Session(engine) as session:
        company = session.get(Company, enriched_prospect.company_id)
        
    # Pass prospect_id and a context string
    email_sequence = await outreach.generate_email_sequence(enriched_prospect.id, "Initial cold outreach campaign for Vayu")
    
    print(f"-> Email Sequence Generated.")
    print(f"   Content Preview:\n{email_sequence.content[:500]}...")
    
    print("\n=== Verification Complete ===")

if __name__ == "__main__":
    asyncio.run(verify_full_flow())
