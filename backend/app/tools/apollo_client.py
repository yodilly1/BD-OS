import httpx
import json
from typing import List, Dict, Optional
from app.config import settings

class ApolloClient:
    def __init__(self):
        self.api_key = settings.APOLLO_API_KEY
        self.base_url = "https://api.apollo.io/v1"
        self.headers = {
            "Content-Type": "application/json",
            "Cache-Control": "no-cache",
            "X-Api-Key": self.api_key
        }

    async def search_people(self, q_keywords: str = None, organization_name: str = None, organization_domain: str = None, page: int = 1, per_page: int = 10) -> Dict:
        """
        Search for people using Apollo's /v1/people/search endpoint.
        """
        url = f"{self.base_url}/people/search"
        payload = {
            "q_keywords": q_keywords,
            "page": page,
            "per_page": per_page
        }
        
        if organization_name:
            payload["q_organization_name"] = organization_name
        if organization_domain:
            # Apollo API expects newline separated string for domains in some versions, or array.
            # Trying string as per some docs.
            payload["q_organization_domains"] = organization_domain
            
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, headers=self.headers, json=payload)
                response.raise_for_status()
                data = response.json()
                
                # Log full response to file for debugging
                with open("apollo_debug.log", "w") as f:
                    json.dump(data, f, indent=2)
                    
                return data
            except Exception as e:
                print(f"Error searching Apollo: {e}")
                if hasattr(e, 'response'):
                    print(f"Response: {e.response.text}")
                return {}

    async def enrich_person(self, person_id: str = None, email: str = None) -> Dict:
        """
        Enrich a person record to get email/phone.
        Uses POST /people/match.
        """
        url = f"{self.base_url}/people/match"
        payload = {
            "reveal_personal_emails": True,
            "reveal_phone_number": False
        }
        
        if person_id:
            payload["id"] = person_id
        if email:
            payload["email"] = email
            
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, headers=self.headers, json=payload)
                response.raise_for_status()
                return response.json()
            except Exception as e:
                print(f"Error enriching with Apollo: {e}")
                if hasattr(e, 'response'):
                    print(f"Response: {e.response.text}")
                return {}

    async def find_and_enrich(self, name: str, company_name: str, title: str = None) -> Dict:
        """
        Waterfall helper: Search -> Enrich.
        """
        # 1. Search
        # Use name as keyword, and company name as filter
        search_q = name
        if title:
            search_q += f" {title}"
        
        # Check if company_name looks like a domain
        domain = None
        if company_name and "." in company_name and " " not in company_name:
            domain = company_name
            company_name = None
            
        results = await self.search_people(q_keywords=search_q, organization_name=company_name, organization_domain=domain, per_page=50)
        # print(f"DEBUG: Apollo Search Results: {json.dumps(results)}")
        people = results.get("people", [])
        
        if not people:
            return {}
            
        # Find the best match by name
        person = None
        name_lower = name.lower()
        for p in people:
            p_name = f"{p.get('first_name', '')} {p.get('last_name', '')}".strip().lower()
            if name_lower in p_name or p_name in name_lower:
                person = p
                break
        
        # If no exact match, take the first one (fallback) or return None?
        # Let's take the first one if no match, but log warning
        if not person:
            print(f"WARNING: No exact name match for {name} in top results. Using first result: {people[0].get('name')}")
            person = people[0]
        
        # 2. Check if we already have email
        email = person.get("email")
        if email and "email_not_unlocked" not in email:
            return person
            
        # 3. If not, enrich (reveal)
        enriched = await self.enrich_person(person_id=person.get("id"))
        enriched_person = enriched.get("person", {}) or person
        
        # Final check for placeholder
        if enriched_person.get("email") and "email_not_unlocked" in enriched_person.get("email"):
            enriched_person["email"] = None
            
        return enriched_person
