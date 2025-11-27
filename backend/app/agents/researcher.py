from app.tools.serper_client import SerperClient
from app.tools.gemini_client import GeminiClient
from app.tools.leadmagic_client import LeadMagicClient
from app.models.company import Company
from app.models.prospect import Prospect
from app.db import engine
from sqlmodel import Session
import json

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
            news_results = await self.serper.search(f"latest news about {company.name}", type="news")
            
            # 2. Search for tech stack
            tech_results = await self.serper.search(f"{company.name} tech stack software engineering")
            
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
            cleaned_response = response_text.replace("```json", "").replace("```", "").strip()
            
            try:
                data = json.loads(cleaned_response)
                company.description = data.get("description", company.description)
                company.industry = data.get("industry", company.industry)
                company.employees_count = data.get("employees_count", company.employees_count)
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
        with Session(engine) as session:
            prospect = session.get(Prospect, prospect_id)
            if not prospect:
                raise ValueError("Prospect not found")
            
            # Fetch company for context
            company = session.get(Company, prospect.company_id) if prospect.company_id else None

            # 1. Use LeadMagic to get email, phone, and signals
            if prospect.linkedin_url:
                print(f"Enriching {prospect.first_name} {prospect.last_name} with LeadMagic...")
                leadmagic_data = await self.leadmagic.find_person(prospect.linkedin_url)
                
                # Update contact info from LeadMagic
                if leadmagic_data.get("email"):
                    prospect.email = leadmagic_data.get("email")
                if leadmagic_data.get("phone"):
                    prospect.phone = leadmagic_data.get("phone")
                
                print(f"LeadMagic data: {leadmagic_data}")
            
            # 2. Use public search + AI to infer pain points and summary
            prompt = f"""
            You are a BDR Researcher. Infer the likely pain points and summary for this prospect.
            
            Prospect: {prospect.first_name} {prospect.last_name}
            Title: {prospect.title}
            Company: {company.name if company else 'Unknown'}
            Company Description: {company.description if company else 'Unknown'}
            
            Return a JSON object with keys:
            - summary (professional summary inference based on their title and company)
            - pain_points (likely challenges they face in their role, be specific to their title)
            """
            
            response_text = await self.gemini.generate_content(prompt)
            cleaned_response = response_text.replace("```json", "").replace("```", "").strip()
            
            try:
                data = json.loads(cleaned_response)
                prospect.summary = data.get("summary")
                prospect.pain_points = data.get("pain_points")
                
                session.add(prospect)
                session.commit()
                session.refresh(prospect)
            except Exception as e:
                print(f"Error enriching prospect with AI: {e}")
            
            # Expunge to avoid DetachedInstanceError when returning
            session.expunge(prospect)
            return prospect
