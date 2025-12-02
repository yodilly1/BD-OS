import asyncio
import os
import json
import sys
from dotenv import load_dotenv

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

from app.tools.leadmagic_client import LeadMagicClient

load_dotenv()

async def debug_email_lookup():
    client = LeadMagicClient()
    linkedin_url = "https://www.linkedin.com/in/amymil"
    
    print(f"Debugging email lookup for: {linkedin_url}")
    
    # 1. Call find_person (Profile Search)
    print("\n[1] Calling find_person (Profile Search)...")
    try:
        data = await client.find_person(linkedin_url)
        print("Parsed Data:", json.dumps(data, indent=2))
    except Exception as e:
        print(f"Error in find_person: {e}")

    # 3. Raw Request to see full payload
    print("\n[3] Making RAW request to /v1/people/profile-search...")
    import httpx
    
    headers = {
        "X-API-Key": os.getenv("LEADMAGIC_API_KEY"),
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    payload = {
        "profile_url": linkedin_url,
        "include_contact_info": True
    }
    
    async with httpx.AsyncClient() as http_client:
        try:
            response = await http_client.post(
                "https://api.leadmagic.io/v1/people/profile-search",
                headers=headers,
                json=payload,
                timeout=30.0
            )
            print(f"Status Code: {response.status_code}")
            try:
                raw_data = response.json()
                
                # Save to file to avoid encoding/truncation issues
                with open("raw_response.json", "w", encoding="utf-8") as f:
                    json.dump(raw_data, f, indent=2)
                print("Saved raw response to raw_response.json")
                
                # Safely print email fields
                print("Checking for emails...")
                print(f"work_email: {raw_data.get('work_email')}")
                print(f"personal_email: {raw_data.get('personal_email')}")
                print(f"professional_email: {raw_data.get('professional_email')}")
                print(f"email: {raw_data.get('email')}")
                
            except Exception as e:
                print(f"Could not parse JSON response: {e}")
                print(response.text)
        except Exception as e:
            print(f"Error making raw request: {e}")

if __name__ == "__main__":
    # Add backend to path
    import sys
    sys.path.append(os.path.join(os.getcwd(), "backend"))
    
    asyncio.run(debug_email_lookup())
