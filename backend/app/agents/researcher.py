import json
from sqlmodel import Session
from app.db import engine
from app.models.company import Company
from app.models.prospect import Prospect
from app.tools.gemini_client import GeminiClient
from app.tools.leadmagic_client import LeadMagicClient
from app.tools.serper_client import SerperClient
from app.tools.apollo_client import ApolloClient

class ResearcherAgent:
    def __init__(self):
        self.serper = SerperClient()
        self.gemini = GeminiClient()
        self.leadmagic = LeadMagicClient()
        self.apollo_client = ApolloClient()

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
        Enrich a prospect with data from Apollo (Primary) and LeadMagic (Fallback).
        """
        with Session(engine) as session:
            prospect = session.get(Prospect, prospect_id)
            if not prospect:
                return {"error": "Prospect not found"}
            
            company = session.get(Company, prospect.company_id) if prospect.company_id else None
            company_name = company.name if company else ""
            company_domain = company.domain if company else ""

            # 1. Apollo Enrichment (Primary)
            print(f"Researcher: Enriching {prospect.first_name} {prospect.last_name} via Apollo...")
            apollo_data = await self.apollo_client.find_and_enrich(
                name=f"{prospect.first_name} {prospect.last_name}",
                company_name=company_name,
                title=prospect.title
            )
            
            if apollo_data.get("email"):
                print(f"Researcher: Found email via Apollo: {apollo_data.get('email')}")
                print(f"Researcher: Apollo Data Keys: {list(apollo_data.keys())}")
                print(f"Researcher: Apollo Title: {apollo_data.get('title')}")
                print(f"Researcher: Apollo Phone: {apollo_data.get('phone')}")
                print(f"Researcher: Apollo Phone Numbers: {apollo_data.get('phone_numbers')}")

                prospect.email = apollo_data.get("email")
                prospect.linkedin_url = apollo_data.get("linkedin_url") or prospect.linkedin_url
                prospect.title = apollo_data.get("title") or prospect.title
                prospect.phone = apollo_data.get("phone_numbers", [{}])[0].get("sanitized_number") if apollo_data.get("phone_numbers") else None
                
                # Also try direct phone field if phone_numbers list is empty/different structure
                if not prospect.phone:
                    prospect.phone = apollo_data.get("phone") or prospect.phone
                
                # If phone is still missing, try LeadMagic Mobile Finder
                if not prospect.phone and prospect.linkedin_url:
                    print("Researcher: Phone missing from Apollo. Trying LeadMagic Mobile Finder...")
                    try:
                        lm_phone = await self.leadmagic.find_mobile_number(
                            linkedin_url=prospect.linkedin_url,
                            work_email=prospect.email
                        )
                        if lm_phone:
                            print(f"Researcher: Found phone via LeadMagic: {lm_phone}")
                            prospect.phone = lm_phone
                        else:
                            print("Researcher: LeadMagic returned no phone number.")
                    except Exception as e:
                        print(f"Researcher: Error fetching LeadMagic phone: {e}")

                # Save Apollo/LeadMagic data
                print(f"Researcher: Saving Prospect - Title: {prospect.title}, Phone: {prospect.phone}")
                session.add(prospect)
                session.commit()
                session.refresh(prospect)
                session.expunge(prospect)
                return prospect

            # 2. LeadMagic Enrichment (Fallback)
            print("Researcher: Apollo failed. Trying LeadMagic...")
            
            # Try to find email via LeadMagic
            if company_domain:
                 lm_email_data = await self.leadmagic.find_email(
                     prospect.first_name,
                     prospect.last_name,
                     company_domain
                 )
                 if lm_email_data.get("email"):
                     print("Researcher: Found email via LeadMagic!")
                     prospect.email = lm_email_data.get("email")
                     session.add(prospect)
                     session.commit()
                     session.refresh(prospect)
                     # Continue to AI Inference instead of returning
                     # session.expunge(prospect)
                     # return prospect

            # If we still don't have email, try B2B profile search
            if prospect.linkedin_url:
                lm_data = await self.leadmagic.find_person(prospect.linkedin_url)
                if lm_data:
                     prospect.email = lm_data.get("email") or prospect.email
                     prospect.phone = lm_data.get("phone") or prospect.phone
                     session.add(prospect)
                     session.commit()
                     session.refresh(prospect)
            
            # 3. AI Inference (Gemini)
            prompt = f"""
            You are a BDR Researcher. Infer the likely pain points and summary for this prospect.

            Prospect: {prospect.first_name} {prospect.last_name}
            Title: {prospect.title}
            Company: {company_name}
            
            Return a JSON object with keys:
            - summary (professional summary inference based on their title and company)
            - pain_points (likely challenges they face in their role, be specific to their title)
            """

            try:
                response_text = await self.gemini.generate_content(prompt)
                cleaned_response = response_text.replace("```json", "").replace("```", "").strip()
                data = json.loads(cleaned_response)
                
                prospect.summary = data.get("summary")
                pain_points = data.get("pain_points")
                if isinstance(pain_points, list):
                    prospect.pain_points = "\n- ".join(pain_points)
                else:
                    prospect.pain_points = pain_points
                
                session.add(prospect)
                session.commit()
                session.refresh(prospect)
            except Exception as e:
                print(f"Error enriching prospect with AI: {e}")

            session.expunge(prospect)
            return prospect
