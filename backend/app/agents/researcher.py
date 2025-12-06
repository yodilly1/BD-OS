import json
import asyncio
from typing import Dict, Any

from sqlmodel import Session, select
from httpx import HTTPStatusError

from app.db import engine
from app.models.company import Company
from app.models.prospect import Prospect
from app.tools.gemini_client import GeminiClient
from app.tools.leadmagic_client import LeadMagicClient
from app.tools.serper_client import SerperClient


class ResearcherAgent:
    """
    The ResearcherAgent is responsible for enriching data for both companies and prospects.
    It uses external tools like Serper for search, LeadMagic for contact info, and Gemini for AI-driven insights.
    """

    def __init__(self):
        self.serper = SerperClient()
        self.gemini = GeminiClient()
        self.leadmagic = LeadMagicClient()

    async def enrich_company(self, company_id: int) -> Company:
        """
        Enriches a company's profile with news, tech stack, and other details using public search.

        This method fetches a company from the database, uses Serper to find the latest news and
        tech stack information, then uses Gemini to generate an improved summary and extract key details.
        The enriched data is then saved back to the database.

        Args:
            company_id: The ID of the company to enrich.

        Returns:
            The enriched Company object, expunged from the session.

        Raises:
            ValueError: If the company with the given ID is not found.
        """
        with Session(engine) as session:
            company = session.get(Company, company_id)
            if not company:
                raise ValueError("Company not found")

            # 1. Search for company news and tech stack in parallel
            search_tasks = [
                self.serper.search(f"latest news about {company.name}", type="news"),
                self.serper.search(f"{company.name} tech stack software engineering"),
            ]
            results = await asyncio.gather(*search_tasks, return_exceptions=True)
            news_results = results[0] if not isinstance(results[0], Exception) else {}
            tech_results = results[1] if not isinstance(results[1], Exception) else {}

            prompt = f"""
            You are a BDR Researcher. Enrich the following company profile based on the search results.

            Company: {company.name}

            News Results:
            {json.dumps(news_results)}

            Tech Stack Search Results:
            {json.dumps(tech_results)}

            Return a JSON object with keys:
            - description (improved summary)
            - industry
            - employees_count (estimate)
            - location
            - tech_stack (comma separated string)
            - news_snippets (comma separated string of headlines)
            """

            try:
                response_text = await self.gemini.generate_content(prompt)
                cleaned_response = (
                    response_text.replace("```json", "").replace("```", "").strip()
                )
                data = json.loads(cleaned_response)

                # Update company with new data
                company.description = data.get("description", company.description)
                company.industry = data.get("industry", company.industry)
                company.employees_count = data.get(
                    "employees_count", company.employees_count
                )
                company.location = data.get("location", company.location)
                company.tech_stack = data.get("tech_stack", "")
                company.news_snippets = data.get("news_snippets", "")

                session.add(company)
                session.commit()
                session.refresh(company)

            except json.JSONDecodeError as e:
                print(f"Error decoding JSON from Gemini: {e}")
            except Exception as e:
                print(f"An unexpected error occurred during company enrichment: {e}")

            session.expunge(company)
            return company

    async def _get_prospect_and_company_data(self, prospect_id: int, session: Session) -> (Dict[str, Any], Dict[str, Any]):
        """Helper to fetch prospect and associated company data."""
        prospect = session.get(Prospect, prospect_id)
        if not prospect:
            raise ValueError("Prospect not found")

        prospect_data = {
            "linkedin_url": prospect.linkedin_url,
            "first_name": prospect.first_name,
            "last_name": prospect.last_name,
            "title": prospect.title,
            "email": prospect.email,
            "company_id": prospect.company_id,
        }

        company_data = {}
        if prospect.company_id:
            company = session.get(Company, prospect.company_id)
            if company:
                company_data = {
                    "name": company.name,
                    "description": company.description,
                    "domain": company.domain,
                }

        return prospect_data, company_data

    async def _enrich_contact_info(self, prospect_data: Dict[str, Any], company_data: Dict[str, Any]) -> Dict[str, Any]:
        """Enriches a prospect's contact information using LeadMagic."""
        updates = {}
        linkedin_url = prospect_data.get("linkedin_url")

        if not linkedin_url:
            return updates

        print(f"Enriching {prospect_data['first_name']} {prospect_data['last_name']} with LeadMagic...")
        
        try:
            leadmagic_data = await self.leadmagic.find_person(linkedin_url)
            
            if leadmagic_data.get("email"):
                updates["email"] = leadmagic_data.get("email")

            if leadmagic_data.get("phone"):
                updates["phone"] = leadmagic_data.get("phone")

            # If email or phone is missing, try fallback methods
            if not updates.get("email"):
                if prospect_data.get("first_name") and prospect_data.get("last_name") and company_data.get("domain"):
                    email_data = await self.leadmagic.find_email(
                        prospect_data["first_name"], prospect_data["last_name"], company_data["domain"]
                    )
                    if email_data.get("email"):
                        updates["email"] = email_data.get("email")

            if not updates.get("phone"):
                work_email = updates.get("email") or prospect_data.get("email")
                mobile = await self.leadmagic.find_mobile_number(linkedin_url, work_email=work_email)
                if mobile:
                    updates["phone"] = mobile

        except HTTPStatusError as e:
            print(f"HTTP error during LeadMagic enrichment: {e.response.status_code} {e.response.text}")
        except Exception as e:
            print(f"An unexpected error occurred during LeadMagic enrichment: {e}")

        return updates

    async def _enrich_ai_insights(self, prospect_data: Dict[str, Any], company_data: Dict[str, Any]) -> Dict[str, Any]:
        """Enriches a prospect with AI-generated summary and pain points."""
        updates = {}
        prompt = f"""
        You are a BDR Researcher. Infer the likely pain points and summary for this prospect.

        Prospect: {prospect_data["first_name"]} {prospect_data["last_name"]}
        Title: {prospect_data["title"]}
        Company: {company_data.get("name", "Unknown")}
        Company Description: {company_data.get("description", "Unknown")}

        Return a JSON object with keys:
        - summary (professional summary inference based on their title and company)
        - pain_points (list of likely challenges they face in their role, be specific to their title)
        """

        try:
            response_text = await self.gemini.generate_content(prompt)
            cleaned_response = response_text.replace("```json", "").replace("```", "").strip()
            data = json.loads(cleaned_response)

            updates["summary"] = data.get("summary")
            
            pain_points = data.get("pain_points")
            if isinstance(pain_points, list):
                updates["pain_points"] = "\n- ".join(pain_points)
            else:
                updates["pain_points"] = pain_points

        except json.JSONDecodeError as e:
            print(f"Error decoding JSON from Gemini for prospect insights: {e}")
        except Exception as e:
            print(f"An unexpected error occurred during AI enrichment: {e}")

        return updates

    async def enrich_prospect(self, prospect_id: int) -> Prospect:
        """
        Enriches a prospect's profile with contact info and AI-driven insights.

        This method orchestrates a multi-step enrichment process:
        1. Fetches the prospect and their company data from the database.
        2. Calls LeadMagic to find the prospect's email and phone number.
        3. Calls Gemini to generate a professional summary and identify likely pain points.
        4. Saves all the collected enrichment data back to the database.

        Args:
            prospect_id: The ID of the prospect to enrich.

        Returns:
            The enriched Prospect object, expunged from the session.

        Raises:
            ValueError: If the prospect with the given ID is not found.
        """
        # 1. Fetch initial data (Read-only DB)
        with Session(engine) as session:
            prospect_data, company_data = self._get_prospect_and_company_data(prospect_id, session)

        # 2. Async IO for enrichment (No DB session)
        enrichment_tasks = [
            self._enrich_contact_info(prospect_data, company_data),
            self._enrich_ai_insights(prospect_data, company_data),
        ]
        results = await asyncio.gather(*enrichment_tasks, return_exceptions=True)

        updates = {}
        for result in results:
            if not isinstance(result, Exception) and result:
                updates.update(result)

        # 3. Save updates (Write DB)
        with Session(engine) as session:
            prospect = session.get(Prospect, prospect_id)
            if not prospect:
                raise ValueError("Prospect not found during save")

            for key, value in updates.items():
                if value:
                    setattr(prospect, key, value)

            session.add(prospect)
            session.commit()
            session.refresh(prospect)
            session.expunge(prospect)

            return prospect
