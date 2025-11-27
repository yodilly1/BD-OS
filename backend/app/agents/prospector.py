from app.tools.serper_client import SerperClient
from app.tools.gemini_client import GeminiClient
from app.tools.leadmagic_client import LeadMagicClient
from app.models.company import Company
from app.models.prospect import Prospect
from app.db import engine
from sqlmodel import Session, select
from typing import List
import json
import re

class ProspectorAgent:
    def __init__(self):
        self.serper = SerperClient()
        self.gemini = GeminiClient()
        self.leadmagic = LeadMagicClient()

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
        print(f"DEBUG: Cleaned Gemini Response: {cleaned_response}")
        
        companies = []
        with Session(engine) as session:
            try:
                data = json.loads(cleaned_response)
                if not isinstance(data, list):
                    print(f"ERROR: Gemini response is not a list: {type(data)}")
                
                for i, item in enumerate(data):
                    print(f"DEBUG: Processing item {i}: {item}")
                    name = item.get("name")
                    if not name:
                        print(f"WARNING: Item {i} missing 'name'. Skipping.")
                        continue

                    # Check if company already exists
                    existing = session.exec(select(Company).where(Company.name == name)).first()
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
            
            # Refresh and expunge all companies to ensure they are available outside session
            for company in companies:
                session.refresh(company)
                session.expunge(company)
            
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
                
            # Refresh and expunge all prospects
            for prospect in prospects:
                session.refresh(prospect)
                session.expunge(prospect)
                
            return prospects

    async def _find_linkedin_url(self, first_name: str, last_name: str, company_name: str) -> str:
        """
        Finds the LinkedIn URL for a specific person using Serper.
        """
        query = f"site:linkedin.com/in/ {first_name} {last_name} {company_name}"
        try:
            results = await self.serper.search(query)
            if "organic" in results and len(results["organic"]) > 0:
                return results["organic"][0].get("link", "")
        except Exception as e:
            print(f"Error finding LinkedIn URL for {first_name} {last_name}: {e}")
        return ""

    async def deep_prospecting_flow(self, industry: str, size: str, keywords: str, titles: List[str], limit: int = 20) -> List[Prospect]:
        """
        Executes a deep prospecting workflow:
        1. Find companies matching criteria (Serper + Gemini).
        2. For each company, find employees via LeadMagic.
        3. Filter by title.
        4. Find LinkedIn URL (Serper).
        5. Save to DB.
        """
        # SAFEGUARDS
        MAX_COMPANIES = 10 # Increased slightly to allow for more filtering if needed
        MAX_PROSPECTS_PER_COMPANY = 5
        MAX_TOTAL_PROSPECTS = limit
        
        # 1. Construct Company Search Query
        size_str = f"{size}" if size.lower() != "any size" else ""
        
        queries = [
            f"List of {size_str} {industry} companies {keywords}",
            f"Top {industry} startups {keywords} 2024",
            f"Competitors of {keywords} {industry} companies"
        ]
        
        all_companies = []
        seen_domains = set()
        
        print(f"DEBUG: Starting Multi-Source Company Search...")
        for q in queries:
            if len(all_companies) >= MAX_COMPANIES:
                break
            print(f"DEBUG: Running query: {q}")
            companies = await self.find_companies(q)
            for c in companies:
                if len(all_companies) >= MAX_COMPANIES:
                    break
                if c.domain and c.domain not in seen_domains:
                    all_companies.append(c)
                    seen_domains.add(c.domain)
        
        print(f"DEBUG: Found {len(all_companies)} unique companies.")
        
        all_prospects = []
        import asyncio

        # 2. Find People for each company via LeadMagic (PARALLEL)
        async def process_company(company):
            if not company.domain:
                return []
            
            print(f"DEBUG: Searching employees at {company.name} ({company.domain}) via LeadMagic...")
            try:
                employees = await self.leadmagic.find_employees(company.domain)
            except Exception as e:
                print(f"Error searching employees for {company.name}: {e}")
                return []
            
            # Filter employees first
            candidates = []
            for emp in employees:
                emp_title = emp.get("title", "").lower()
                if any(t.lower() in emp_title for t in titles):
                    candidates.append(emp)
            
            # Limit candidates per company
            candidates = candidates[:MAX_PROSPECTS_PER_COMPANY]
            
            # Parallel LinkedIn Lookup
            async def process_candidate(emp):
                first_name = emp.get("first_name", "")
                last_name = emp.get("last_name", "")
                linkedin_url = await self._find_linkedin_url(first_name, last_name, company.name)
                return {**emp, "linkedin_url": linkedin_url}

            if not candidates:
                return []

            enriched_candidates = await asyncio.gather(*[process_candidate(c) for c in candidates])
            
            company_prospects = []
            for emp in enriched_candidates:
                first_name = emp.get("first_name", "")
                last_name = emp.get("last_name", "")
                linkedin_url = emp.get("linkedin_url", "")
                
                with Session(engine) as session:
                    # Check existing
                    existing = session.exec(select(Prospect).where(Prospect.linkedin_url == linkedin_url)).first() if linkedin_url else None
                    if existing:
                        company_prospects.append(existing)
                        continue
                        
                    prospect = Prospect(
                        first_name=first_name,
                        last_name=last_name,
                        title=emp.get("title", ""),
                        linkedin_url=linkedin_url,
                        company_id=company.id,
                        status="New"
                    )
                    session.add(prospect)
                    session.commit()
                    session.refresh(prospect)
                    company_prospects.append(prospect)
            return company_prospects

        # Run company processing in parallel
        results_list = await asyncio.gather(*[process_company(c) for c in all_companies])
        
        # Flatten results
        for prospects in results_list:
            all_prospects.extend(prospects)
            if len(all_prospects) >= MAX_TOTAL_PROSPECTS:
                break
        
        return all_prospects[:MAX_TOTAL_PROSPECTS]

    async def url_prospecting_flow(self, url: str) -> List[Prospect]:
        try:
            """
            Executes a prospecting workflow based on a company URL.
            1. Identify/Create company from URL.
            2. Use LeadMagic to find employees.
            3. Find LinkedIn URLs.
            4. Save prospects to DB.
            """
            # SAFEGUARDS
            MAX_PROSPECTS = 10
            
            # Clean URL to get domain
            domain = url.replace("https://", "").replace("http://", "").replace("www.", "").split("/")[0]
            
            with Session(engine) as session:
                # 1. Find or Create Company
                company = session.exec(select(Company).where(Company.domain.contains(domain))).first()
                if not company:
                    # Try to infer name from domain
                    name = domain.split(".")[0].capitalize()
                    company = Company(name=name, domain=domain, description=f"Company at {domain}")
                    session.add(company)
                    session.commit()
                    session.refresh(company)
                
                # Expunge company so we can use it outside session if needed (though we have ID)
                session.refresh(company)
                session.expunge(company)

            # 2. Find Employees via LeadMagic
            try:
                employees = await self.leadmagic.find_employees(domain)
            except Exception as e:
                print(f"Error searching employees for {domain}: {e}")
                return []
            
            # Limit employees
            employees = employees[:MAX_PROSPECTS]
            
            new_prospects = []
            import asyncio
            
            # Parallel LinkedIn Lookup
            async def process_candidate(emp):
                first_name = emp.get("first_name", "")
                last_name = emp.get("last_name", "")
                if not first_name or not last_name:
                    return None
                linkedin_url = await self._find_linkedin_url(first_name, last_name, company.name)
                return {**emp, "linkedin_url": linkedin_url}

            if not employees:
                return []

            enriched_candidates = await asyncio.gather(*[process_candidate(e) for e in employees])
            
            for emp in enriched_candidates:
                if not emp: continue
                
                first_name = emp.get("first_name", "")
                last_name = emp.get("last_name", "")
                title = emp.get("title", "")
                linkedin_url = emp.get("linkedin_url", "")

                with Session(engine) as session:
                    # Check if prospect exists
                    existing = session.exec(select(Prospect).where(Prospect.linkedin_url == linkedin_url)).first() if linkedin_url else None
                    
                    if existing:
                        session.refresh(existing)
                        session.expunge(existing)
                        new_prospects.append(existing)
                        continue

                    prospect = Prospect(
                        first_name=first_name,
                        last_name=last_name,
                        title=title,
                        linkedin_url=linkedin_url,
                        company_id=company.id,
                        status="New"
                    )
                    session.add(prospect)
                    session.commit()
                    session.refresh(prospect)
                    session.expunge(prospect)
                    new_prospects.append(prospect)
                    
            return new_prospects
        except Exception as e:
            import traceback
            traceback.print_exc()
            raise e

