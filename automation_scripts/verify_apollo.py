import asyncio
import sys
import os
import httpx
from dotenv import load_dotenv

# Add backend to sys.path
backend_path = os.path.join(os.getcwd(), "backend")
sys.path.append(backend_path)
load_dotenv(os.path.join(backend_path, ".env"))

from app.tools.apollo_client import ApolloClient

async def main():
    client = ApolloClient()
    
    print("Testing Apollo Search & Enrich...")
    
    try:
        # Test 1: Domain Only (Microsoft)
        test_domain = "microsoft.com"
        print(f"\nTest 1: Searching for anyone at {test_domain}...")
        results = await client.search_people(organization_domain=test_domain, per_page=1)
        print(f"Microsoft Domain Search Results: {len(results.get('people', []))} people found.")
        
        # Test 1b: Domain Only (Accertify)
        test_domain_2 = "accertify.com"
        print(f"\nTest 1b: Searching for anyone at {test_domain_2}...")
        results_2 = await client.search_people(organization_domain=test_domain_2, per_page=1)
        print(f"Accertify Domain Search Results: {len(results_2.get('people', []))} people found.")

        # Test 2: Name + Domain (Andrew Bronstein)
        name = "Andrew Bronstein"
        company = "accertify.com"
        print(f"\nTest 2: Searching for {name} at {company}...")
        result = await client.find_and_enrich(name, company)
            
        print("\n--- Result ---")
        print(f"Name: {result.get('first_name')} {result.get('last_name')}")
        print(f"Title: {result.get('title')}")
        print(f"Email: {result.get('email')}")
        print(f"LinkedIn: {result.get('linkedin_url')}")
        
        if result.get("email"):
            print("\nSUCCESS: Email found!")
        else:
            print("\nWARNING: No email found")
            
    except Exception as e:
        print(f"\nERROR: {e}")
        if hasattr(e, 'response'):
             print(f"Response: {e.response.text}")

if __name__ == "__main__":
    asyncio.run(main())
