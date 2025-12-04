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
    company_name = "Nylas"
    domain = "nylas.com"
    
    print(f"Deep Debugging Apollo Search for {name}...")

    # Test 1: Just Name
    print("\n--- Test 1: Just Name (q_keywords='Brent Geddes') ---")
    res1 = await client.search_people(q_keywords=name, per_page=5)
    for p in res1.get("people", []):
        print(f"  - {p.get('name')} | {p.get('title')} | {p.get('organization', {}).get('name')}")

    # Test 2: Name + Domain in Keywords
    print(f"\n--- Test 2: Name + Domain (q_keywords='{name} {domain}') ---")
    res2 = await client.search_people(q_keywords=f"{name} {domain}", per_page=5)
    for p in res2.get("people", []):
        print(f"  - {p.get('name')} | {p.get('title')} | {p.get('organization', {}).get('name')}")

    # Test 3: Name + Company Name in Keywords
    print(f"\n--- Test 3: Name + Company (q_keywords='{name} {company_name}') ---")
    res3 = await client.search_people(q_keywords=f"{name} {company_name}", per_page=5)
    for p in res3.get("people", []):
        print(f"  - {p.get('name')} | {p.get('title')} | {p.get('organization', {}).get('name')}")

    # Test 4: Name + Organization Filter (Current Implementation)
    print(f"\n--- Test 4: Name + Org Filter (q_keywords='{name}', q_organization_domains='{domain}') ---")
    res4 = await client.search_people(q_keywords=name, organization_domain=domain, per_page=5)
    for p in res4.get("people", []):
        print(f"  - {p.get('name')} | {p.get('title')} | {p.get('organization', {}).get('name')}")

if __name__ == "__main__":
    asyncio.run(main())
