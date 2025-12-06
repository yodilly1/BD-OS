import asyncio
import json
from typing import List, Dict, Any

from sqlmodel import Session, select
from httpx import HTTPStatusError

from app.db import engine
from app.models.company import Company
from app.models.prospect import Prospect
from app.tools.gemini_client import GeminiClient
from app.tools.leadmagic_client import LeadMagicClient
from app.tools.serper_client import SerperClient


class ProspectorAgent:
    """
    The ProspectorAgent is responsible for finding and qualifying companies and prospects.
    It uses external tools like Serper for search, LeadMagic for person/company data,
    and Gemini for AI-driven analysis and extraction.
    """

    def __init__(self):
        self.serper = SerperClient()
        self.gemini = GeminiClient()
        self.leadmagic = LeadMagicClient()

    async def find_companies(self, icp_description: str) -> List[Company]:
        """
        Finds companies that match an Ideal Customer Profile (ICP) description.

        This method uses a search engine to find potential companies, then uses an LLM
        to analyze the results and extract a clean list of companies that match the ICP.
        It handles saving these companies to the database, avoiding duplicates based on company name.

        Args:
            icp_description: A string describing the ideal customer profile.

        Returns:
            A list of Company objects that have been saved to the database.
        """
        search_query = f"List of companies that match this description: {icp_description}"
        try:
            search_results = await self.serper.search(search_query)
        except HTTPStatusError as e:
            print(f"Error during Serper search for companies: {e.response.status_code}")
            return []

        prompt = f"""
        You are a BDR Prospecting Agent.
        Analyze the following search results and extract a list of companies that match the ICP: "{icp_description}".

        Search Results:
        {json.dumps(search_results)}

        Return a JSON array of objects with keys: name, domain, description.
        Only return valid JSON, no markdown.
        """

        try:
            response_text = await self.gemini.generate_content(prompt)
            cleaned_response = response_text.replace("```json", "").replace("```", "").strip()
            company_data = json.loads(cleaned_response)
        except (json.JSONDecodeError, TypeError) as e:
            print(f"Error parsing Gemini response for companies: {e}")
            return []

        if not isinstance(company_data, list):
            print(f"ERROR: Gemini response for companies is not a list: {type(company_data)}")
            return []

        saved_companies = []
        with Session(engine) as session:
            for item in company_data:
                name = item.get("name")
                if not name:
                    continue

                # Check for existing company to avoid duplicates
                existing_company = session.exec(select(Company).where(Company.name == name)).first()
                if existing_company:
                    saved_companies.append(existing_company)
                else:
                    new_company = Company(
                        name=name,
                        domain=item.get("domain", ""),
                        description=item.get("description", ""),
                    )
                    session.add(new_company)
                    session.commit()
                    session.refresh(new_company)
                    saved_companies.append(new_company)

            for company in saved_companies:
                session.expunge(company)

        return saved_companies

    async def find_prospects(self, company_id: int, role_description: str) -> List[Prospect]:
        """
        Finds prospects at a specific company who match a given role description.

        This method uses LinkedIn search results via Serper and then leverages an LLM to
        extract structured prospect data. It saves new prospects to the database,
        avoiding duplicates based on LinkedIn URL.

        Args:
            company_id: The ID of the company to search within.
            role_description: A string describing the target role (e.g., "Director of Engineering").

        Returns:
            A list of Prospect objects saved to the database.
        """
        with Session(engine) as session:
            company = session.get(Company, company_id)
            if not company:
                raise ValueError("Company not found")

            query = f"site:linkedin.com/in/ {role_description} at {company.name}"
            try:
                search_results = await self.serper.search(query)
            except HTTPStatusError as e:
                print(f"Error during Serper search for prospects: {e.response.status_code}")
                return []

            prompt = f"""
            Extract prospect details from these LinkedIn search results for company: {company.name}.
            Target Role: {role_description}

            Search Results:
            {json.dumps(search_results)}

            Return a JSON array of objects with keys: first_name, last_name, title, linkedin_url.
            Only return valid JSON.
            """

            try:
                response_text = await self.gemini.generate_content(prompt)
                cleaned_response = response_text.replace("```json", "").replace("```", "").strip()
                prospect_data = json.loads(cleaned_response)
            except (json.JSONDecodeError, TypeError) as e:
                print(f"Error parsing Gemini response for prospects: {e}")
                return []

            # Bulk check for existing prospects to avoid N+1 queries
            linkedin_urls = [p.get("linkedin_url") for p in prospect_data if p.get("linkedin_url")]
            existing_prospects_query = session.exec(select(Prospect).where(Prospect.linkedin_url.in_(linkedin_urls)))
            existing_urls = {p.linkedin_url for p in existing_prospects_query}

            new_prospects = []
            for item in prospect_data:
                url = item.get("linkedin_url")
                if url and url not in existing_urls:
                    prospect = Prospect(
                        first_name=item.get("first_name", ""),
                        last_name=item.get("last_name", ""),
                        title=item.get("title", ""),
                        linkedin_url=url,
                        company_id=company.id,
                        status="New",
                    )
                    session.add(prospect)
                    new_prospects.append(prospect)

            if new_prospects:
                session.commit()
                for p in new_prospects:
                    session.refresh(p)
                    session.expunge(p)

            # Re-query all relevant prospects to return a complete list
            final_prospects_query = session.exec(select(Prospect).where(Prospect.linkedin_url.in_(linkedin_urls)))
            final_prospects = final_prospects_query.all()
            for p in final_prospects:
                session.expunge(p)

            return final_prospects

    async def _find_linkedin_url(self, first_name: str, last_name: str, company_name: str) -> Dict[str, str]:
        """Helper to find a person's LinkedIn URL using Serper."""
        query = f"site:linkedin.com/in/ {first_name} {last_name} {company_name}"
        try:
            results = await self.serper.search(query)
            if results.get("organic"):
                item = results["organic"][0]
                return {
                    "url": item.get("link", ""),
                    "title": item.get("title", ""),
                    "snippet": item.get("snippet", ""),
                }
        except HTTPStatusError as e:
            print(f"HTTP Error finding LinkedIn URL for {first_name} {last_name}: {e.response.status_code}")
        except Exception as e:
            print(f"Error finding LinkedIn URL for {first_name} {last_name}: {e}")
        return {"url": "", "title": "", "snippet": ""}

    async def search_candidates(self, industry: str, size: str, keywords: str, titles: List[str], limit: int = 20) -> List[Dict[str, Any]]:
        """
        Searches for potential candidates without saving them to the database.

        This is the first phase of a two-phase prospecting flow. It finds companies,
        then searches for people at those companies matching specific titles.

        Args:
            industry: The industry of the target companies.
            size: The size of the target companies (e.g., "1-10 employees").
            keywords: Keywords related to the companies' business.
            titles: A list of job titles to search for.
            limit: The maximum number of candidates to return.

        Returns:
            A list of dictionaries, where each dictionary represents a potential candidate.
        """
        MAX_COMPANIES = 10
        MAX_PROSPECTS_PER_COMPANY = 5

        # Find companies first
        icp = f"{size} {industry} companies {keywords}"
        companies = await self.find_companies(icp)
        
        # Take a limited number of companies to search for people
        target_companies = companies[:MAX_COMPANIES]

        async def get_candidates_for_company(company: Company) -> List[Dict[str, Any]]:
            if not company.domain:
                return []
            
            try:
                tasks = [self.leadmagic.find_person_by_role(company.domain, title) for title in titles]
                results = await asyncio.gather(*tasks, return_exceptions=True)

                candidates = []
                seen_urls = set()
                for res in results:
                    if not isinstance(res, Exception) and res and res.get("linkedin_url") not in seen_urls:
                        res["company_id"] = company.id
                        res["company_name"] = company.name
                        candidates.append(res)
                        seen_urls.add(res["linkedin_url"])

                return candidates[:MAX_PROSPECTS_PER_COMPANY]
            except Exception as e:
                print(f"Error getting candidates for {company.name}: {e}")
                return []

        company_tasks = [get_candidates_for_company(c) for c in target_companies]
        nested_candidates = await asyncio.gather(*company_tasks)

        # Flatten the list of lists
        all_candidates = [candidate for sublist in nested_candidates for candidate in sublist]

        return all_candidates[:limit]

    async def save_candidates(self, candidates: List[Dict[str, Any]]) -> List[Prospect]:
        """
        Saves a list of candidate dictionaries to the database as Prospect objects.

        This is the second phase of a two-phase prospecting flow. It efficiently handles
        duplicates by checking for existing LinkedIn URLs in a single database query.

        Args:
            candidates: A list of candidate dictionaries.

        Returns:
            A list of the saved Prospect objects, expunged from the session.
        """
        if not candidates:
            return []

        # De-duplicate candidates by linkedin_url from the input list
        unique_candidates = {c["linkedin_url"]: c for c in candidates if c.get("linkedin_url")}
        
        urls_to_check = list(unique_candidates.keys())

        with Session(engine) as session:
            # Single query to find all existing prospects
            existing_prospects_query = session.exec(select(Prospect).where(Prospect.linkedin_url.in_(urls_to_check)))
            existing_urls = {p.linkedin_url for p in existing_prospects_query}

            new_prospects = []
            for url, p_data in unique_candidates.items():
                if url not in existing_urls:
                    prospect = Prospect(
                        first_name=p_data.get("first_name"),
                        last_name=p_data.get("last_name"),
                        title=p_data.get("title"),
                        linkedin_url=p_data.get("linkedin_url"),
                        company_id=p_data.get("company_id"),
                        status="New",
                    )
                    session.add(prospect)
                    new_prospects.append(prospect)
            
            if new_prospects:
                session.commit()

            # Return a list of all prospects (new and existing)
            final_prospects_query = session.exec(select(Prospect).where(Prospect.linkedin_url.in_(urls_to_check)))
            all_prospects = final_prospects_query.all()
            for p in all_prospects:
                session.expunge(p)

        return all_prospects

    async def deep_prospecting_flow(
        self,
        industry: str,
        size: str,
        keywords: str,
        titles: List[str],
        limit: int = 20,
    ) -> List[Prospect]:
        """
        An end-to-end prospecting flow that first searches for candidates and then saves them.
        This method is a convenience wrapper around search_candidates and save_candidates.
        """
        candidates = await self.search_candidates(
            industry, size, keywords, titles, limit
        )
        return await self.save_candidates(candidates)

    async def manual_prospecting_flow(
        self, first_name: str, last_name: str, domain: str
    ) -> Prospect | None:
        """
        Manually adds a single prospect by finding their information and saving them to the database.
        This flow attempts to find an email, then a LinkedIn URL, enriches the profile, and saves it.
        """
        with Session(engine) as session:
            company = session.exec(select(Company).where(Company.domain == domain)).first()
            if not company:
                name = domain.split(".")[0].capitalize()
                company = Company(name=name, domain=domain)
                session.add(company)
                session.commit()
                session.refresh(company)

            # Chain of logic: Find email -> find LI -> enrich -> save
            email_data = await self.leadmagic.find_email(first_name, last_name, domain)
            email = email_data.get("email")

            linkedin_url = ""
            if email:
                li_data = await self.leadmagic.find_person_by_email(work_email=email)
                linkedin_url = li_data.get("linkedin_url", "")

            if not linkedin_url:
                li_data = await self._find_linkedin_url(first_name, last_name, company.name)
                linkedin_url = li_data.get("url", "")

            if not linkedin_url:
                return None  # Could not find the prospect

            # Check if prospect already exists before further enrichment
            existing_prospect = session.exec(select(Prospect).where(Prospect.linkedin_url == linkedin_url)).first()
            if existing_prospect:
                session.expunge(existing_prospect)
                return existing_prospect

            # New prospect, enrich and save
            enriched_data = await self.leadmagic.find_person(linkedin_url)

            prospect = Prospect(
                first_name=first_name,
                last_name=last_name,
                title=enriched_data.get("title", "Unknown"),
                email=email,
                phone=enriched_data.get("phone"),
                linkedin_url=linkedin_url,
                company_id=company.id,
                status="New",
            )
            session.add(prospect)
            session.commit()
            session.refresh(prospect)
            session.expunge(prospect)

            return prospect

    async def url_prospecting_flow(self, url: str, titles: List[str] = None) -> List[Prospect]:
        """
        Finds and saves prospects from a single company URL, searching for specific titles.

        Args:
            url: The URL of the company (e.g., "stripe.com").
            titles: A list of job titles to search for.

        Returns:
            A list of saved Prospect objects.
        """
        domain = url.replace("https://", "").replace("http://", "").replace("www.", "").split("/")[0]

        with Session(engine) as session:
            company = session.exec(select(Company).where(Company.domain.contains(domain))).first()
            if not company:
                name = domain.split(".")[0].capitalize()
                company = Company(name=name, domain=domain, description=f"Company at {domain}")
                session.add(company)
                session.commit()
                session.refresh(company)

        if not titles:
            return []

        tasks = [self.leadmagic.find_person_by_role(domain, title) for title in titles]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        valid_candidates = []
        seen_urls = set()
        for res in results:
            if not isinstance(res, Exception) and res and res.get("linkedin_url") not in seen_urls:
                res["company_id"] = company.id
                valid_candidates.append(res)
                seen_urls.add(res["linkedin_url"])

        return await self.save_candidates(valid_candidates)
