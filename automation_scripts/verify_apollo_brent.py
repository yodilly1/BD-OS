import asyncio
import sys
import os
from dotenv import load_dotenv
import json

# Add backend to sys.path
backend_path = os.path.join(os.getcwd(), "backend")
sys.path.append(backend_path)
load_dotenv(os.path.join(backend_path, ".env"))

from app.tools.apollo_client import ApolloClient

async def main():
    client = ApolloClient()
    name = "Brent Geddes"
    company = "Nylas"
    
    print(f"Searching Apollo for {name} at {company}...")
    
    # Strategy A: Domain Search
    print("\n--- Strategy A: Domain Search (nylas.com) ---")
    results_a = await client.search_people(q_keywords=name, organization_domain="nylas.com", per_page=5)
    people_a = results_a.get("people", [])
    for p in people_a:
        print(f"FOUND: {p.get('first_name')} {p.get('last_name')} - {p.get('title')}")

    # Strategy B: Broad Keyword Search
    print("\n--- Strategy B: Broad Keyword Search ('Brent Geddes Nylas') ---")
    results_b = await client.search_people(q_keywords=f"{name} {company}", per_page=5)
    people_b = results_b.get("people", [])
    for p in people_b:
        print(f"FOUND: {p.get('first_name')} {p.get('last_name')} - {p.get('title')}")

if __name__ == "__main__":
    asyncio.run(main())
