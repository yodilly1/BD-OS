import os
import json
from typing import Dict, Any, List, Optional

import httpx
from dotenv import load_dotenv

load_dotenv()


class LeadMagicClient:
    """
    A client for interacting with the LeadMagic API.

    This client provides methods for finding people, enriching profiles, finding contact
    information, and other B2B data-related tasks.
    """

    def __init__(self):
        self.api_key = os.getenv("LEADMAGIC_API_KEY")
        if not self.api_key:
            raise ValueError("LEADMAGIC_API_KEY not found in environment variables")
        self.base_url = "https://api.leadmagic.io"
        self.headers = {"X-API-Key": self.api_key, "Content-Type": "application/json"}

    async def _make_request(self, method: str, url: str, **kwargs) -> Dict[str, Any]:
        """Helper method to make async HTTP requests."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.request(method, url, headers=self.headers, **kwargs)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                print(f"[LeadMagic] API error ({e.response.status_code}): {e.response.text}")
            except json.JSONDecodeError as e:
                print(f"[LeadMagic] JSON Decode Error: {e}")
            except Exception as e:
                print(f"[LeadMagic] An unexpected error occurred: {e}")
        return {}

    async def find_person(self, linkedin_url: str) -> Dict[str, Any]:
        """
        Enriches a person's profile using their LinkedIn URL.

        Args:
            linkedin_url: The URL of the person's LinkedIn profile.

        Returns:
            A dictionary containing the person's enriched data, including email, phone, and title.
        """
        url = f"{self.base_url}/v1/people/profile-search"
        payload = {"profile_url": linkedin_url}
        raw_data = await self._make_request("POST", url, json=payload)

        if not raw_data:
            return {}

        return {
            "email": raw_data.get("professional_email") or raw_data.get("work_email") or raw_data.get("email"),
            "phone": raw_data.get("mobile_number") or raw_data.get("phone") or raw_data.get("mobile"),
            "title": raw_data.get("job_title") or raw_data.get("title") or raw_data.get("headline"),
            "company": raw_data.get("company_name") or raw_data.get("company"),
            "raw": raw_data,
        }

    async def find_employees(self, domain: str) -> List[Dict[str, Any]]:
        """
        Finds employees for a given company domain.

        Args:
            domain: The domain of the company.

        Returns:
            A list of dictionaries, where each dictionary represents an employee profile.
        """
        url = f"{self.base_url}/employee-finder"
        payload = {"company_domain": domain}
        data = await self._make_request("POST", url, json=payload)

        if isinstance(data, dict):
            return data.get("data", data.get("employees", []))
        elif isinstance(data, list):
            return data
        
        return []

    async def find_person_by_role(self, domain: str, role: str) -> Dict[str, Any]:
        """
        Finds a specific person at a company matching a role/title.

        Args:
            domain: The company's domain.
            role: The job title or role to search for.

        Returns:
            A dictionary representing the person found, or an empty dictionary if not found.
        """
        url = f"{self.base_url}/role-finder"
        payload = {"company_domain": domain, "job_title": role}
        data = await self._make_request("POST", url, json=payload)

        if data.get("message") == "Role Found":
            return {
                "first_name": data.get("first_name"),
                "last_name": data.get("last_name"),
                "title": role,
                "linkedin_url": data.get("profile_url"),
                "company": data.get("company_name"),
            }
        return {}

    async def find_mobile_number(self, linkedin_url: str, work_email: Optional[str] = None, personal_email: Optional[str] = None) -> Optional[str]:
        """
        Finds the mobile number for a person.

        Args:
            linkedin_url: The person's LinkedIn profile URL.
            work_email: The person's work email (optional).
            personal_email: The person's personal email (optional).

        Returns:
            The mobile number as a string, or None if not found.
        """
        url = f"{self.base_url}/v1/people/mobile-finder"
        payload = {"profile_url": linkedin_url}
        if work_email:
            payload["work_email"] = work_email
        if personal_email:
            payload["personal_email"] = personal_email
            
        data = await self._make_request("POST", url, json=payload)
        return data.get("mobile_number")

    async def find_person_by_email(self, work_email: Optional[str] = None, personal_email: Optional[str] = None) -> Dict[str, Any]:
        """
        Finds a person's B2B profile (LinkedIn URL) using their email.

        Args:
            work_email: The person's work email (optional).
            personal_email: The person's personal email (optional).

        Returns:
            A dictionary with the LinkedIn URL, or an empty dictionary if not found.
        """
        url = f"{self.base_url}/v1/people/b2b-profile"
        payload = {}
        if work_email:
            payload["work_email"] = work_email
        if personal_email:
            payload["personal_email"] = personal_email

        if not payload:
            return {}
            
        data = await self._make_request("POST", url, json=payload)
        if data.get("profile_url"):
            return {
                "linkedin_url": data.get("profile_url"),
                "message": data.get("message"),
            }
        return {}

    async def find_email(self, first_name: str, last_name: str, domain: str) -> Dict[str, Any]:
        """
        Finds a professional email address using a person's name and company domain.

        Args:
            first_name: The person's first name.
            last_name: The person's last name.
            domain: The company's domain.

        Returns:
            A dictionary containing the email and its verification status.
        """
        url = f"{self.base_url}/v1/people/email-finder"
        payload = {"first_name": first_name, "last_name": last_name, "domain": domain}
        data = await self._make_request("POST", url, json=payload)
        return {
            "email": data.get("email"),
            "status": data.get("status"),
            "verification_status": data.get("verification_status"),
        }
