import asyncio
import os
from dotenv import load_dotenv
# Set PYTHONPATH to include backend directory
import sys
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app.agents.prospector import ProspectorAgent
from app.db import create_db_and_tables

# Force load env vars from backend/.env
load_dotenv("backend/.env")

async def debug_prospector():
    print("Initializing DB...")
    create_db_and_tables()
    
    print("Initializing Prospector Agent...")
    try:
        agent = ProspectorAgent()
        print("Agent initialized.")
        
        icp = "Identity Verification SaaS companies"
        print(f"Searching for: {icp}")
        
        # This will trigger the print statements we added to the agent
        companies = await agent.find_companies(icp)
        
        print(f"\nFinal Result: Found {len(companies)} companies.")
        for c in companies:
            print(f" - ID: {c.id} | Name: {c.name} | Domain: {c.domain}")
            
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_prospector())
