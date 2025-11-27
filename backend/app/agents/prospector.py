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
import asyncio

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
        
        prompt = f"""
        You are a BDR Prospecting Agent. 
        Analyze the following search results and extract a list of companies that match the ICP: "{icp_description}".
        
        Search Results:
        {json.dumps(search_results)}
        
        Return a JSON array of objects with keys: name, domain, description.
        Only return valid JSON, no markdown.
        """
        
        response_text = await self.gemini.generate_content(prompt)
        cleaned_response = response_text.replace("```json", "").replace("```", "").strip()
        
        def save_companies_to_db(json_response):
            companies = []
            with Session(engine) as session:
                try:
                    data = json.loads(json_response)
                    if not isinstance(data, list):
                        print(f"ERROR: Gemini response is not a list: {type(data)}")
                    
                    for i, item in enumerate(data):
                        name = item.get("name")
                        if not name:
                            continue

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
                
                for company in companies:
                    session.refresh(company)
                    session.expunge(company)
            return companies

        return await asyncio.to_thread(save_companies_to_db, cleaned_response)

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
        Executes a deep prospecting workflow.
        Refactored to use a single session and handle detached instances correctly.
        """
        # SAFEGUARDS
        MAX_COMPANIES = 10
        MAX_PROSPECTS_PER_COMPANY = 5
        MAX_TOTAL_PROSPECTS = limit
        
        size_str = f"{size}" if size.lower() != "any size" else ""
        queries = [
            f"List of {size_str} {industry} companies {keywords}",
            f"Top {industry} startups {keywords} 2024",
            f"Competitors of {keywords} {industry} companies"
        ]
        
        all_prospects = []

        with Session(engine) as session:
            all_companies = []
            seen_domains = set()
            
            for q in queries:
                if len(all_companies) >= MAX_COMPANIES: break
                companies_from_query = await self.find_companies(q)
                for c in companies_from_query:
                    if len(all_companies) >= MAX_COMPANIES: break
                    if c.domain and c.domain not in seen_domains:
                        attached_company = session.merge(c)
                        all_companies.append(attached_company)
                        seen_domains.add(attached_company.domain)

            # 1. Gather all data concurrently (No DB access here)
            async def gather_company_data(company):
                if not company.domain: return []
                try:
                    employees = await self.leadmagic.find_employees(company.domain)
                except Exception as e:
                    print(f"Error finding employees for {company.name}: {e}")
                    return []

                candidates = [emp for emp in employees if any(t.lower() in emp.get("title", "").lower() for t in titles)]
                candidates = candidates[:MAX_PROSPECTS_PER_COMPANY]

                async def process_candidate(emp):
                    first_name, last_name = emp.get("first_name", ""), emp.get("last_name", "")
                    linkedin_url = await self._find_linkedin_url(first_name, last_name, company.name)
                    return {**emp, "linkedin_url": linkedin_url, "company_id": company.id}

                return await asyncio.gather(*[process_candidate(c) for c in candidates])

            # Execute gathering
            tasks = [gather_company_data(c) for c in all_companies]
            results_nested = await asyncio.gather(*tasks)
            
            # Flatten results
            all_prospect_data = [p for sublist in results_nested for p in sublist if p and p.get("linkedin_url")]

            # 2. Save to DB sequentially (in a separate thread to avoid blocking event loop)
            def save_to_db(prospect_data_list):
                saved_prospects = []
                with Session(engine) as session:
                    for p_data in prospect_data_list:
                        if len(saved_prospects) >= MAX_TOTAL_PROSPECTS: break
                        
                        existing = session.exec(select(Prospect).where(Prospect.linkedin_url == p_data["linkedin_url"])).first()
                        if existing:
                            saved_prospects.append(existing)
                        else:
                            prospect = Prospect(
                                first_name=p_data.get("first_name"), 
                                last_name=p_data.get("last_name"),
                                title=p_data.get("title"), 
                                linkedin_url=p_data.get("linkedin_url"),
                                company_id=p_data.get("company_id"), 
                                status="New"
                            )
                            session.add(prospect)
                            saved_prospects.append(prospect)
                    
                    session.commit()
                    
                    for p in saved_prospects:
                        session.refresh(p)
                        session.expunge(p)
                return saved_prospects

            final_prospects = await asyncio.to_thread(save_to_db, all_prospect_data)
                
            return final_prospects

    async def url_prospecting_flow(self, url: str) -> List[Prospect]:
        """
        Executes a prospecting workflow based on a company URL.
        Refactored to use a single session and handle detached instances correctly.
        """
        # SAFEGUARDS
        MAX_PROSPECTS = 10

        domain = url.replace("https://", "").replace("http://", "").replace("www.", "").split("/")[0]

        with Session(engine) as session:
            company = session.exec(select(Company).where(Company.domain.contains(domain))).first()
            if not company:
                name = domain.split(".")[0].capitalize()
                company = Company(name=name, domain=domain, description=f"Company at {domain}")
                session.add(company)
                session.commit()
                session.refresh(company)

            try:
                employees = await self.leadmagic.find_employees(domain)
            except Exception as e:
                print(f"Error searching employees for {domain}: {e}")
                return []
            
            employees = employees[:MAX_PROSPECTS]
            if not employees:
                return []

            company_name_for_search = company.name
            async def process_candidate(emp):
                first_name = emp.get("first_name", "")
                last_name = emp.get("last_name", "")
                if not first_name or not last_name:
                    return None
                linkedin_url = await self._find_linkedin_url(first_name, last_name, company_name_for_search)
                return {**emp, "linkedin_url": linkedin_url}
            
            enriched_candidates = await asyncio.gather(*[process_candidate(e) for e in employees])

            new_prospects = []
            for emp in enriched_candidates:
                if not emp: continue

                linkedin_url = emp.get("linkedin_url", "")
                if not linkedin_url: continue

                existing = session.exec(select(Prospect).where(Prospect.linkedin_url == linkedin_url)).first()
                if existing:
                    new_prospects.append(existing)
                    continue

                prospect = Prospect(
                    first_name=emp.get("first_name", ""),
                    last_name=emp.get("last_name", ""),
                    title=emp.get("title", ""),
                    linkedin_url=linkedin_url,
                    company_id=company.id,
                    status="New"
                )
                session.add(prospect)
                new_prospects.append(prospect)

            session.commit()

            for p in new_prospects:
                session.refresh(p)
                session.expunge(p)

            return new_prospects
