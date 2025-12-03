import asyncio
import json
import os

import httpx
from dotenv import load_dotenv

load_dotenv(dotenv_path="backend/.env")

API_KEY = os.getenv("LEADMAGIC_API_KEY")
BASE_URL = "https://api.leadmagic.io"


async def test_profile_search():
    print(f"\n--- Testing Profile Search ---")
    url = f"{BASE_URL}/v1/people/profile-search"
    headers = {"X-API-Key": API_KEY, "Content-Type": "application/json"}
    payload = {
        "profile_url": "https://www.linkedin.com/in/alex-small-37482b98"
    }  # Use the URL found in previous step

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            print(f"Requesting: {url}")
            response = await client.post(url, headers=headers, json=payload)
            print(f"Status Code: {response.status_code}")
            try:
                data = response.json()
                print(f"Response Data: {json.dumps(data, indent=2)}")
            except:
                print(f"Raw Response: {response.text}")
        except Exception as e:
            print(f"Error: {e}")


async def test_mobile_finder():
    print(f"\n--- Testing Mobile Finder ---")
    url = f"{BASE_URL}/v1/people/mobile-finder"
    headers = {"X-API-Key": API_KEY, "Content-Type": "application/json"}
    # Use Alex Small's profile URL from previous test
    payload = {"profile_url": "https://www.linkedin.com/in/alex-small-37482b98"}

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            print(f"Requesting: {url}")
            response = await client.post(url, headers=headers, json=payload)
            print(f"Status Code: {response.status_code}")
            try:
                data = response.json()
                print(f"Response Data: {json.dumps(data, indent=2)}")
            except:
                print(f"Raw Response: {response.text}")
        except Exception as e:
            print(f"Error: {e}")


async def test_email_finder():
    print(f"\n--- Testing Email to Profile ---")
    # Use a known email (e.g., from documentation or a common pattern)
    # Let's try to find Jesse Ouellette as per docs example
    work_email = "jesse@leadmagic.io"

    url = f"{BASE_URL}/v1/people/b2b-profile"
    headers = {"X-API-Key": API_KEY, "Content-Type": "application/json"}
    payload = {"work_email": work_email}

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            print(f"Requesting: {url}")
            response = await client.post(url, headers=headers, json=payload)
            print(f"Status Code: {response.status_code}")
            try:
                data = response.json()
                print(f"Response Data: {json.dumps(data, indent=2)}")
            except:
                print(f"Raw Response: {response.text}")
        except Exception as e:
            print(f"Error: {e}")


async def test_job_change():
    print(f"\n--- Testing Job Change Detector ---")
    url = f"{BASE_URL}/v1/people/job-change-detector"
    headers = {"X-API-Key": API_KEY, "Content-Type": "application/json"}
    # Test Jesse Ouellette (Founder of LeadMagic) checking if he works at "Smartlead" (Expect: NEVER_WORKED_THERE or similar)
    payload = {
        "profile_url": "https://www.linkedin.com/in/jesseoue/",
        "company_domain": "smartlead.ai",
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            print(f"Requesting: {url}")
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

    # await test_employee_finder("stripe.com")
    # await test_profile_search()
    # await test_mobile_finder()
    await test_email_finder()
    await test_job_change()


if __name__ == "__main__":
    asyncio.run(main())
