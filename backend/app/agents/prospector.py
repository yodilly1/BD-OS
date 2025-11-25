from app.tools.serper_client import SerperClient
from app.tools.gemini_client import GeminiClient
from app.models.company import Company
from app.models.prospect import Prospect
from app.db import engine
from sqlmodel import Session, select
from typing import List
import json

class ProspectorAgent:
    def __init__(self):
        self.serper = SerperClient()
        self.gemini = GeminiClient()

    async def find_companies(self, icp_description: str) -> List[Company]:
        """
        Finds companies matching the ICP description using Search + LLM filtering.
        Saves them to the DB.
        """
        search_query = f"List of companies that match this description: {icp_description}"
        search_results = await self.serper.search(search_query)
        print(f"DEBUG: Serper Results: {search_results}")
        
        prompt = f"""
        You are a BDR Prospecting Agent. 
        Analyze the following search results and extract a list of companies that match the ICP: "{icp_description}".
        
        Search Results:
        {json.dumps(search_results)}
        
        Return a JSON array of objects with keys: name, domain, description.
        Only return valid JSON, no markdown.
        """
        
        response_text = await self.gemini.generate_content(prompt)
        print(f"DEBUG: Gemini Response: {response_text}")
        
        cleaned_response = response_text.replace("```json", "").replace("```", "").strip()
        
        companies = []
        with Session(engine) as session:
            try:
                data = json.loads(cleaned_response)
                for item in data:
                    # Check if company already exists
                    existing = session.exec(select(Company).where(Company.name == item.get("name"))).first()
                    if existing:
                        companies.append(existing)
                        continue

                    company = Company(
                        name=item.get("name"),
                        domain=item.get("domain", ""),
                        description=item.get("description")
                    )
                    session.add(company)
                    session.commit()
                    session.refresh(company)
                    companies.append(company)
            except Exception as e:
                print(f"Error parsing Gemini response or saving to DB: {e}")
            
        return companies

    async def find_prospects(self, company_id: int, role_description: str) -> List[Prospect]:
        """
        Finds prospects at a specific company matching the role description.
        Saves them to the DB.
        """
        with Session(engine) as session:
            company = session.get(Company, company_id)
            if not company:
                return []

            query = f"site:linkedin.com/in/ {role_description} at {company.name}"
            search_results = await self.serper.search(query)
            
            prompt = f"""
            Extract prospect details from these LinkedIn search results for company: {company.name}.
            Target Role: {role_description}
            
            Search Results:
            {json.dumps(search_results)}
            
            Return a JSON array of objects with keys: first_name, last_name, title, linkedin_url.
            Only return valid JSON.
            """
            
            response_text = await self.gemini.generate_content(prompt)
            cleaned_response = response_text.replace("```json", "").replace("```", "").strip()
            
            prospects = []
            try:
                data = json.loads(cleaned_response)
                for item in data:
                    # Check if prospect exists
                    existing = session.exec(select(Prospect).where(Prospect.linkedin_url == item.get("linkedin_url"))).first()
                    if existing:
                        prospects.append(existing)
                        continue

                    prospect = Prospect(
                        first_name=item.get("first_name", ""),
                        last_name=item.get("last_name", ""),
                        title=item.get("title", ""),
                        linkedin_url=item.get("linkedin_url"),
                        company_id=company.id,
                        status="New"
                    )
                    session.add(prospect)
                    session.commit()
                    session.refresh(prospect)
                    prospects.append(prospect)
            except Exception as e:
                print(f"Error parsing prospects: {e}")
                
            return prospects
