import httpx
import os
from dotenv import load_dotenv

load_dotenv()

class LeadMagicClient:
    def __init__(self):
        self.api_key = os.getenv("LEADMAGIC_API_KEY")
        if not self.api_key:
            raise ValueError("LEADMAGIC_API_KEY not found in environment variables")
        self.base_url = "https://api.leadmagic.io"
        self.headers = {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json"
        }

    async def find_person(self, linkedin_url: str) -> dict:
        """
        Enriches a person's profile using their LinkedIn URL.
        Returns email, phone, and other profile data.
        """
        url = f"{self.base_url}/profile-search"
        payload = {"profile_url": linkedin_url}
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                print(f"[LeadMagic] Calling API for {linkedin_url}...")
                response = await client.post(url, headers=self.headers, json=payload)
                response.raise_for_status()
                raw_data = response.json()
                print(f"[LeadMagic] Raw response: {raw_data}")
                
                # Parse LeadMagic's actual response format
                # They may return fields like "professional_email", "work_email", "mobile_number", etc.
                normalized_data = {
                    "email": (
                        raw_data.get("professional_email") or 
                        raw_data.get("work_email") or 
                        raw_data.get("email")
                    ),
                    "phone": (
                        raw_data.get("mobile_number") or 
                        raw_data.get("phone") or 
                        raw_data.get("mobile")
                    ),
                    "raw": raw_data  # Keep full response for debugging
                }
                
                print(f"[LeadMagic] Normalized data - Email: {normalized_data['email']}, Phone: {normalized_data['phone']}")
                return normalized_data
                
            except httpx.HTTPStatusError as e:
                print(f"[LeadMagic] API error ({e.response.status_code}): {e.response.text}")
                return {}
            except Exception as e:
                print(f"[LeadMagic] Error: {e}")
                return {}

    async def find_employees(self, domain: str) -> list:
        """
        Finds employees for a given company domain.
        Returns a list of employee profiles.
        """
        # --- MOCK IMPLEMENTATION ---
        if self.api_key == "mock-key":
            print(f"[LeadMagic] MOCK: Simulating employee search for {domain}")
            mock_data = [
                {"first_name": "John", "last_name": "Doe", "title": "Software Engineer"},
                {"first_name": "Jane", "last_name": "Smith", "title": "Product Manager"},
                {"first_name": "Peter", "last_name": "Jones", "title": "Data Scientist"},
                {"first_name": "Mary", "last_name": "Williams", "title": "UX Designer"},
                {"first_name": "David", "last_name": "Brown", "title": "DevOps Engineer"},
            ]
            print(f"[LeadMagic] MOCK: Found {len(mock_data)} employees")
            return mock_data
        # --- END MOCK ---

        url = f"{self.base_url}/employee-finder"
        payload = {"company_domain": domain}
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                print(f"[LeadMagic] Searching employees for domain: {domain}...")
                response = await client.post(url, headers=self.headers, json=payload)
                response.raise_for_status()
                data = response.json()
                print(f"[LeadMagic] Response type: {type(data)}")
                
                # Handle both list and dict responses
                if isinstance(data, dict):
                    # API returns {"data": [...]} format
                    employees = data.get("data", [])
                    if not employees:
                        # Fallback to 'employees' just in case
                        employees = data.get("employees", [])
                    
                    print(f"[LeadMagic] Extracted {len(employees)} employees from dict response")
                    return employees
                elif isinstance(data, list):
                    # API returns [...] format directly
                    print(f"[LeadMagic] Found {len(data)} employees")
                    return data
                else:
                    print(f"[LeadMagic] Unexpected response type: {type(data)}")
                    return []
            except httpx.HTTPStatusError as e:
                print(f"[LeadMagic] API error ({e.response.status_code}): {e.response.text}")
                return []
            except Exception as e:
                print(f"[LeadMagic] Error: {e}")
                return []
