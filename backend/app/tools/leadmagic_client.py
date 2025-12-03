import os

import httpx
from dotenv import load_dotenv

load_dotenv()


class LeadMagicClient:
    def __init__(self):
        self.api_key = os.getenv("LEADMAGIC_API_KEY")
        if not self.api_key:
            raise ValueError("LEADMAGIC_API_KEY not found in environment variables")
        self.base_url = "https://api.leadmagic.io"
        self.headers = {"X-API-Key": self.api_key, "Content-Type": "application/json"}

    async def find_person(self, linkedin_url: str) -> dict:
        """
        Enriches a person's profile using their LinkedIn URL.
        Returns email, phone, and other profile data.
        """
        url = f"{self.base_url}/v1/people/profile-search"
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
                        raw_data.get("professional_email")
                        or raw_data.get("work_email")
                        or raw_data.get("email")
                    ),
                    "phone": (
                        raw_data.get("mobile_number")
                        or raw_data.get("phone")
                        or raw_data.get("mobile")
                    ),
                    "title": (
                        raw_data.get("job_title")
                        or raw_data.get("title")
                        or raw_data.get("headline")
                    ),
                    "company": (
                        raw_data.get("company_name") or raw_data.get("company")
                    ),
                    "raw": raw_data,  # Keep full response for debugging
                }

                print(
                    f"[LeadMagic] Normalized data - Email: {normalized_data['email']}, Phone: {normalized_data['phone']}"
                )
                return normalized_data

            except httpx.HTTPStatusError as e:
                print(
                    f"[LeadMagic] API error ({e.response.status_code}): {e.response.text}"
                )
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
                {
                    "first_name": "John",
                    "last_name": "Doe",
                    "title": "Software Engineer",
                },
                {
                    "first_name": "Jane",
                    "last_name": "Smith",
                    "title": "Product Manager",
                },
                {
                    "first_name": "Peter",
                    "last_name": "Jones",
                    "title": "Data Scientist",
                },
                {"first_name": "Mary", "last_name": "Williams", "title": "UX Designer"},
                {
                    "first_name": "David",
                    "last_name": "Brown",
                    "title": "DevOps Engineer",
                },
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

                    print(
                        f"[LeadMagic] Extracted {len(employees)} employees from dict response"
                    )
                    return employees
                elif isinstance(data, list):
                    # API returns [...] format directly
                    print(f"[LeadMagic] Found {len(data)} employees")
                    return data
                else:
                    print(f"[LeadMagic] Unexpected response type: {type(data)}")
                    return []
            except httpx.HTTPStatusError as e:
                print(
                    f"[LeadMagic] API error ({e.response.status_code}): {e.response.text}"
                )
                return []
                return []
            except Exception as e:
                print(f"[LeadMagic] Error: {e}")
                return []

    async def find_person_by_role(self, domain: str, role: str) -> dict:
        """
        Finds a specific person at a company matching a role/title.
        Uses the /role-finder endpoint.
        """
        url = f"{self.base_url}/role-finder"
        payload = {"company_domain": domain, "job_title": role}

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                # print(f"[LeadMagic] Searching for {role} at {domain}...")
                response = await client.post(url, headers=self.headers, json=payload)
                response.raise_for_status()
                data = response.json()

                if data.get("message") == "Role Found":
                    # Normalize to match employee-finder format
                    return {
                        "first_name": data.get("first_name"),
                        "last_name": data.get("last_name"),
                        "title": role,  # API doesn't return title, so we use the requested role
                        "linkedin_url": data.get("profile_url"),
                        "company": data.get("company_name"),
                    }
                return {}
            except Exception:
                # print(f"[LeadMagic] Error finding role {role}: {e}")
                return {}

    async def find_mobile_number(
        self, linkedin_url: str, work_email: str = None, personal_email: str = None
    ) -> str:
        """
        Finds the mobile number for a person.
        Uses the /v1/people/mobile-finder endpoint.
        """
        url = f"{self.base_url}/v1/people/mobile-finder"
        payload = {"profile_url": linkedin_url}
        if work_email:
            payload["work_email"] = work_email
        if personal_email:
            payload["personal_email"] = personal_email

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                # print(f"[LeadMagic] Searching mobile for {linkedin_url}...")
                response = await client.post(url, headers=self.headers, json=payload)
                response.raise_for_status()
                data = response.json()

                return data.get("mobile_number")
            except Exception as e:
                print(f"[LeadMagic] Error finding mobile: {e}")
                return None

    async def find_person_by_email(
        self, work_email: str = None, personal_email: str = None
    ) -> dict:
        """
        Finds a person's B2B profile (LinkedIn URL) using their email.
        Uses the /v1/people/b2b-profile endpoint.
        """
        url = f"{self.base_url}/v1/people/b2b-profile"
        payload = {}
        if work_email:
            payload["work_email"] = work_email
        if personal_email:
            payload["personal_email"] = personal_email

        if not payload:
            return {}

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                # print(f"[LeadMagic] Searching profile for email...")
                response = await client.post(url, headers=self.headers, json=payload)
                response.raise_for_status()
                data = response.json()

                if data.get("profile_url"):
                    return {
                        "linkedin_url": data.get("profile_url"),
                        "message": data.get("message"),
                    }
                return {}
            except Exception as e:
                print(f"[LeadMagic] Error finding profile by email: {e}")
                return {}

    async def check_job_change(self, linkedin_url: str, company_domain: str) -> dict:
        """
        Checks if a person has changed jobs.
        Uses the /v1/people/job-change-detector endpoint.
        """
        url = f"{self.base_url}/v1/people/job-change-detector"
        payload = {"profile_url": linkedin_url, "company_domain": company_domain}

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                # print(f"[LeadMagic] Checking job change for {linkedin_url}...")
                response = await client.post(url, headers=self.headers, json=payload)
                response.raise_for_status()
                data = response.json()

                return {
                    "job_change_detected": data.get("job_change_detected"),
                    "status": data.get("status"),
                    "summary": data.get("summary"),
                    "current_company": data.get("current_company"),
                    "current_position": data.get("current_position"),
                }
            except Exception as e:
                print(f"[LeadMagic] Error checking job change: {e}")
                return {}

    async def find_email(self, first_name: str, last_name: str, domain: str) -> dict:
        """
        Finds a professional email address using name and domain.
        Uses the /v1/people/email-finder endpoint.
        """
        url = f"{self.base_url}/v1/people/email-finder"
        payload = {"first_name": first_name, "last_name": last_name, "domain": domain}

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                # print(f"[LeadMagic] Finding email for {first_name} {last_name} at {domain}...")
                response = await client.post(url, headers=self.headers, json=payload)
                response.raise_for_status()
                data = response.json()

                return {
                    "email": data.get("email"),
                    "status": data.get("status"),
                    "verification_status": data.get("verification_status"),
                }
            except Exception as e:
                print(f"[LeadMagic] Error finding email: {e}")
                return {}
