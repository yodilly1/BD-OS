import asyncio
import os
from dotenv import load_dotenv
import httpx
import json

load_dotenv(dotenv_path="backend/.env")

API_KEY = os.getenv("LEADMAGIC_API_KEY")
BASE_URL = "https://api.leadmagic.io"

async def test_employee_finder(domain):
    print(f"\n--- Testing Employee Finder for {domain} ---")
    url = f"{BASE_URL}/role-finder"
    headers = {
        "X-API-Key": API_KEY,
        "Content-Type": "application/json"
    }
    # Test with job_title parameter
    payload = {
        "company_domain": domain,
        "job_title": "finance" 
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            print(f"Requesting: {url}")
            print(f"Payload: {payload}")
            response = await client.post(url, headers=headers, json=payload)
            print(f"Status Code: {response.status_code}")
            try:
                data = response.json()
                print(f"Response Data: {json.dumps(data, indent=2)}")
            except:
                print(f"Raw Response: {response.text}")
        except Exception as e:
            print(f"Error: {e}")

async def main():
    if not API_KEY:
        print("ERROR: LEADMAGIC_API_KEY not found in backend/.env")
        return
    
    await test_employee_finder("stripe.com")

if __name__ == "__main__":
    asyncio.run(main())
