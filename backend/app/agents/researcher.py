import json

from sqlmodel import Session

from app.db import engine
from app.models.company import Company
from app.models.prospect import Prospect
from app.tools.gemini_client import GeminiClient
from app.tools.leadmagic_client import LeadMagicClient
from app.tools.serper_client import SerperClient


class ResearcherAgent:
    def __init__(self):
        self.serper = SerperClient()
        self.gemini = GeminiClient()
        self.leadmagic = LeadMagicClient()

    async def enrich_company(self, company_id: int) -> Company:
        """
        Enriches company data with news, tech stack, and more details using public search.
        Saves updates to DB.
        """
        with Session(engine) as session:
            company = session.get(Company, company_id)
            if not company:
                raise ValueError("Company not found")

            # 1. Search for company news
            news_results = await self.serper.search(
                f"latest news about {company.name}", type="news"
            )

            # 2. Search for tech stack
            tech_results = await self.serper.search(
                f"{company.name} tech stack software engineering"
            )

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

            response_text = await self.gemini.generate_content(prompt)
            cleaned_response = (
                response_text.replace("```json", "").replace("```", "").strip()
            )

            try:
                data = json.loads(cleaned_response)
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
            except Exception as e:
                print(f"Error enriching company: {e}")

            # Expunge to avoid DetachedInstanceError when returning
            session.expunge(company)
            return company

    async def enrich_prospect(self, prospect_id: int) -> Prospect:
        """
        Enriches prospect data using LeadMagic for contact info and signals,
        and public search for company context to infer pain points.
        Saves updates to DB.
        """
        # 1. Fetch initial data (Read-only DB)
        prospect_data = {}
        company_data = {}
        with Session(engine) as session:
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

            if prospect.company_id:
                company = session.get(Company, prospect.company_id)
                if company:
                    company_data = {
                        "name": company.name,
                        "description": company.description,
                        "domain": company.domain,
                    }

        # 2. Async IO (No DB session)
        updates = {}

        # LeadMagic
        if prospect_data.get("linkedin_url"):
            print(
                f"Enriching {prospect_data['first_name']} {prospect_data['last_name']} with LeadMagic..."
            )
            leadmagic_data = await self.leadmagic.find_person(
                prospect_data["linkedin_url"]
            )

            if leadmagic_data.get("email"):
                updates["email"] = leadmagic_data.get("email")
            else:
                # Fallback: Try Email Finder endpoint
                if (
                    prospect_data.get("first_name")
                    and prospect_data.get("last_name")
                    and company_data.get("domain")
                ):
                    print(
                        f"No email in profile, trying Email Finder for {prospect_data['first_name']} {prospect_data['last_name']} @ {company_data['domain']}..."
                    )
                    email_data = await self.leadmagic.find_email(
                        prospect_data["first_name"],
                        prospect_data["last_name"],
                        company_data["domain"],
                    )
                    if email_data.get("email"):
                        updates["email"] = email_data.get("email")
                        print(f"Email found via Finder: {email_data.get('email')}")

            if leadmagic_data.get("phone"):
                updates["phone"] = leadmagic_data.get("phone")
            else:
                # Try mobile finder
                print(
                    f"No phone found, trying Mobile Finder for {prospect_data['linkedin_url']}..."
                )
                # Use email from LeadMagic or Finder if found, else existing email
                work_email = updates.get("email") or prospect_data.get("email")
                mobile = await self.leadmagic.find_mobile_number(
                    prospect_data["linkedin_url"], work_email=work_email
                )
                if mobile:
                    updates["phone"] = mobile
                    print(f"Mobile found: {mobile}")

            print(f"LeadMagic data: {leadmagic_data}")

        # Gemini / Serper
        prompt = f"""
        You are a BDR Researcher. Infer the likely pain points and summary for this prospect.

        Prospect: {prospect_data["first_name"]} {prospect_data["last_name"]}
        Title: {prospect_data["title"]}
        Company: {company_data.get("name", "Unknown")}
        Company Description: {company_data.get("description", "Unknown")}

        Return a JSON object with keys:
        - summary (professional summary inference based on their title and company)
        - pain_points (likely challenges they face in their role, be specific to their title)
        """

        try:
            response_text = await self.gemini.generate_content(prompt)
            cleaned_response = (
                response_text.replace("```json", "").replace("```", "").strip()
            )
            data = json.loads(cleaned_response)
            updates["summary"] = data.get("summary")

            pain_points = data.get("pain_points")
            if isinstance(pain_points, list):
                updates["pain_points"] = "\n- ".join(pain_points)
            else:
                updates["pain_points"] = pain_points
        except Exception as e:
            print(f"Error enriching prospect with AI: {e}")

        # 3. Save updates (Write DB)
        with Session(engine) as session:
            prospect = session.get(Prospect, prospect_id)
            if prospect:
                for key, value in updates.items():
                    if value:
                        setattr(prospect, key, value)

                session.add(prospect)
                session.commit()
                session.refresh(prospect)
                session.expunge(prospect)
                return prospect
            else:
                raise ValueError("Prospect not found during save")
