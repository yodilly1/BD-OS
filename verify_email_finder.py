import asyncio
import os
import sys
from dotenv import load_dotenv

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

from app.tools.leadmagic_client import LeadMagicClient

load_dotenv()

async def verify_email_finder():
    client = LeadMagicClient()
    
    test_cases = [
        {"first": "Stephen", "last": "Alexander", "domain": "snorkel.ai"},
        {"first": "Derric", "last": "Lee", "domain": "snorkel.ai"},
        {"first": "Amy", "last": "Miller", "domain": "amazon.com"},
        {"first": "Sarah", "last": "L.", "domain": "hubspot.com"}, # Trying with initial
        {"first": "Andrea", "last": "Giannotti", "domain": "ramp.com"}
    ]
    
    print("=== Verifying LeadMagic Email Finder Endpoint ===")
    
    for person in test_cases:
        print(f"\nTesting: {person['first']} {person['last']} @ {person['domain']}")
        try:
            result = await client.find_email(person['first'], person['last'], person['domain'])
            print(f"Result: {result}")
            
            if result.get("email"):
                print(f"✅ FOUND EMAIL: {result['email']}")
            else:
                print("❌ No email found.")
                
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(verify_email_finder())
