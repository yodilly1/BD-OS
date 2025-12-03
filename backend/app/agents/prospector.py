import asyncio
import json
from typing import List

from sqlmodel import Session, select

from app.db import engine
from app.models.company import Company
from app.models.prospect import Prospect
from app.tools.gemini_client import GeminiClient
from app.tools.leadmagic_client import LeadMagicClient
from app.tools.serper_client import SerperClient


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
        search_query = (
            f"List of companies that match this description: {icp_description}"
        )
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
        cleaned_response = (
            response_text.replace("```json", "").replace("```", "").strip()
        )

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

                        existing = session.exec(
                            select(Company).where(Company.name == name)
                        ).first()
                        if existing:
                            companies.append(existing)
                            continue

                        domain = item.get("domain", "")
                        if not domain:
                            continue

                        company = Company(
                            name=item.get("name"),
                            domain=domain,
                            description=item.get("description"),
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

    async def find_prospects(
        self, company_id: int, role_description: str
    ) -> List[Prospect]:
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
            cleaned_response = (
                response_text.replace("```json", "").replace("```", "").strip()
            )

            prospects = []
            try:
                data = json.loads(cleaned_response)
                for item in data:
                    existing = session.exec(
                        select(Prospect).where(
                            Prospect.linkedin_url == item.get("linkedin_url")
                        )
                    ).first()
                    if existing:
                        prospects.append(existing)
                        continue

                    prospect = Prospect(
                        first_name=item.get("first_name", ""),
                        last_name=item.get("last_name", ""),
                        title=item.get("title", ""),
                        linkedin_url=item.get("linkedin_url"),
                        company_id=company.id,
                        status="New",
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

    async def _find_linkedin_url(
        self, first_name: str, last_name: str, company_name: str
    ) -> dict:
        """
        Finds the LinkedIn URL for a specific person using Serper.
        Returns a dict with url, title, and snippet.
        """
        query = f"site:linkedin.com/in/ {first_name} {last_name} {company_name}"
        try:
            results = await self.serper.search(query)
            if "organic" in results and len(results["organic"]) > 0:
                item = results["organic"][0]
                return {
                    "url": item.get("link", ""),
                    "title": item.get("title", ""),
                    "snippet": item.get("snippet", ""),
                }
        except Exception as e:
            print(f"Error finding LinkedIn URL for {first_name} {last_name}: {e}")
        return {"url": "", "title": "", "snippet": ""}

    async def search_candidates(
        self,
        industry: str,
        size: str,
        keywords: str,
        titles: List[str],
        limit: int = 20,
    ) -> List[dict]:
        """
        Phase 1: Search for candidates but DO NOT save to DB.
        Returns a list of candidate dictionaries.
        """
        # SAFEGUARDS
        MAX_COMPANIES = 10
        MAX_PROSPECTS_PER_COMPANY = 5

        size_str = f"{size}" if size.lower() != "any size" else ""
        queries = [
            f"List of {size_str} {industry} companies {keywords}",
            f"Top {industry} startups {keywords} 2024",
            f"Competitors of {keywords} {industry} companies",
        ]

        with Session(engine) as session:
            all_companies = []
            seen_domains = set()

            for q in queries:
                if len(all_companies) >= MAX_COMPANIES:
                    break
                companies_from_query = await self.find_companies(q)
                for c in companies_from_query:
                    if len(all_companies) >= MAX_COMPANIES:
                        break
                    if c.domain and c.domain not in seen_domains:
                        attached_company = session.merge(c)
                        all_companies.append(attached_company)
                        seen_domains.add(attached_company.domain)

            # Gather data concurrently
            async def gather_company_data(company):
                if not company.domain:
                    return []

                candidates = []
                if titles:
                    # Search for EACH title
                    tasks = [
                        self.leadmagic.find_person_by_role(company.domain, title)
                        for title in titles
                    ]
                    results = await asyncio.gather(*tasks)

                    seen_urls = set()
                    for res in results:
                        if (
                            res
                            and res.get("linkedin_url")
                            and res.get("linkedin_url") not in seen_urls
                        ):
                            candidates.append(res)
                            seen_urls.add(res.get("linkedin_url"))
                else:
                    try:
                        employees = await self.leadmagic.find_employees(company.domain)
                        candidates = employees[:MAX_PROSPECTS_PER_COMPANY]
                    except Exception as e:
                        print(f"Error finding employees for {company.name}: {e}")
                        return []

                candidates = candidates[:MAX_PROSPECTS_PER_COMPANY]

                async def process_candidate(emp):
                    # If we already have linkedin_url (from role-finder), use it
                    if emp.get("linkedin_url"):
                        return {
                            **emp,
                            "company_id": company.id,
                            "company_name": company.name,
                        }

                    # Otherwise find it (for generic search)
                    first_name, last_name = (
                        emp.get("first_name", ""),
                        emp.get("last_name", ""),
                    )
                    serper_data = await self._find_linkedin_url(
                        first_name, last_name, company.name
                    )
                    linkedin_url = serper_data.get("url")
                    return {
                        **emp,
                        "linkedin_url": linkedin_url,
                        "company_id": company.id,
                        "company_name": company.name,
                    }

                return await asyncio.gather(*[process_candidate(c) for c in candidates])

            tasks = [gather_company_data(c) for c in all_companies]
            results_nested = await asyncio.gather(*tasks)

            # Flatten results
            all_candidates = [
                p
                for sublist in results_nested
                for p in sublist
                if p and p.get("linkedin_url")
            ]
            return all_candidates[:limit]

    async def save_candidates(self, candidates: List[dict], campaign_id: int = None) -> List[Prospect]:
        """
        Phase 2: Save selected candidates to DB.
        """
        saved_prospects = []

        # De-duplicate candidates by linkedin_url
        unique_candidates = {}
        for c in candidates:
            if c.get("linkedin_url"):
                unique_candidates[c["linkedin_url"]] = c

        candidates_to_process = list(unique_candidates.values())

        with Session(engine) as session:
            for p_data in candidates_to_process:
                existing = session.exec(
                    select(Prospect).where(
                        Prospect.linkedin_url == p_data["linkedin_url"]
                    )
                ).first()
                if existing:
                    # If prospect exists but isn't in a campaign, and we have one, add them?
                    # For now, let's just return existing.
                    # Optional: Update campaign_id if not set?
                    if campaign_id and not existing.campaign_id:
                        existing.campaign_id = campaign_id
                        session.add(existing)
                    saved_prospects.append(existing)
                else:
                    prospect = Prospect(
                        first_name=p_data.get("first_name"),
                        last_name=p_data.get("last_name"),
                        title=p_data.get("title"),
                        linkedin_url=p_data.get("linkedin_url"),
                        company_id=p_data.get("company_id"),
                        campaign_id=campaign_id,
                        status="New",
                    )
                    session.add(prospect)
                    saved_prospects.append(prospect)

            session.commit()

            for p in saved_prospects:
                session.refresh(p)
                session.expunge(p)
        return saved_prospects

    async def deep_prospecting_flow(
        self,
        industry: str,
        size: str,
        keywords: str,
        titles: List[str],
        limit: int = 20,
        campaign_id: int = None,
    ) -> List[Prospect]:
        """
        Legacy wrapper: Search + Save immediately.
        """
        candidates = await self.search_candidates(
            industry, size, keywords, titles, limit
        )
        return await self.save_candidates(candidates, campaign_id=campaign_id)

    async def url_prospecting_flow(
        self, url: str, titles: List[str] = None
    ) -> List[Prospect]:
        """
        Executes a prospecting workflow based on a company URL.
        Fixed to handle multiple titles correctly.
        """
        # SAFEGUARDS
        MAX_PROSPECTS = 10

        domain = (
            url.replace("https://", "")
            .replace("http://", "")
            .replace("www.", "")
            .split("/")[0]
        )

        with Session(engine) as session:
            company = session.exec(
                select(Company).where(Company.domain.contains(domain))
            ).first()
            if not company:
                name = domain.split(".")[0].capitalize()
                company = Company(
                    name=name, domain=domain, description=f"Company at {domain}"
                )
                session.add(company)
                session.commit()
                session.refresh(company)

            candidates = []
            if titles:
                # Use role-finder for EACH title
                print(f"Searching for roles {titles} at {domain}")
                tasks = [
                    self.leadmagic.find_person_by_role(domain, title)
                    for title in titles
                ]
                results = await asyncio.gather(*tasks)

                seen_urls = set()
                for res in results:
                    if (
                        res
                        and res.get("linkedin_url")
                        and res.get("linkedin_url") not in seen_urls
                    ):
                        candidates.append(res)
                        seen_urls.add(res.get("linkedin_url"))
            else:
                # Fallback to general employee search
                try:
                    employees = await self.leadmagic.find_employees(domain)
                    candidates = employees[:MAX_PROSPECTS]
                except Exception as e:
                    print(f"Error searching employees for {domain}: {e}")
                    return []

            if not candidates:
                return []

            company_name_for_search = company.name

            async def process_candidate(emp):
                if emp.get("linkedin_url"):
                    return {**emp, "company_id": company.id}

                first_name = emp.get("first_name", "")
                last_name = emp.get("last_name", "")
                if not first_name or not last_name:
                    return None
                linkedin_data = await self._find_linkedin_url(
                    first_name, last_name, company_name_for_search
                )
                return {
                    **emp,
                    "linkedin_url": linkedin_data.get("url"),
                    "company_id": company.id,
                }

            enriched_candidates = await asyncio.gather(
                *[process_candidate(e) for e in candidates]
            )

            # Filter valid candidates
            valid_candidates = [
                c for c in enriched_candidates if c and c.get("linkedin_url")
            ]

            # Reuse save_candidates logic (but we need to pass dicts)
            # Since save_candidates expects dicts, we can just pass valid_candidates
            # But we need to ensure they have company_id

            # Actually, let's just use save_candidates directly to avoid code duplication
            # But we need to be careful about the session.
            # save_candidates opens its own session.
            pass

        # Call save_candidates outside the session block
        return await self.save_candidates(valid_candidates)

    async def manual_prospecting_flow(
        self, first_name: str, last_name: str, domain: str
    ) -> Prospect:
        """
        Manually adds a prospect using Name + Domain.
        Uses Email Finder -> B2B Profile -> Profile Search chain.
        """
        with Session(engine) as session:
            # 1. Ensure Company Exists
            company = session.exec(
                select(Company).where(Company.domain.contains(domain))
            ).first()
            if not company:
                name = domain.split(".")[0].capitalize()
                company = Company(
                    name=name, domain=domain, description=f"Company at {domain}"
                )
                session.add(company)
                session.commit()
                session.refresh(company)

            # 2. Try to find Email first
            print(
                f"Manual Add: Finding email for {first_name} {last_name} @ {domain}..."
            )
            email_data = await self.leadmagic.find_email(first_name, last_name, domain)
            email = email_data.get("email")

            linkedin_url = ""

            if email:
                print(f"Manual Add: Found email {email}. Finding LinkedIn profile...")
                # 3. Use Email to find LinkedIn URL
                profile_data = await self.leadmagic.find_person_by_email(
                    work_email=email
                )
                linkedin_url = profile_data.get("linkedin_url", "")

            serper_title_fallback = ""

            if not linkedin_url:
                print("Manual Add: No LinkedIn URL found via Email. Trying Serper...")
                # Fallback: Serper Search
                serper_data = await self._find_linkedin_url(
                    first_name, last_name, company.name
                )
                linkedin_url = serper_data.get("url")

                # Try to extract title from Serper result title (e.g. "Name - Title - Company")
                raw_title = serper_data.get("title", "")
                if " - " in raw_title:
                    parts = raw_title.split(" - ")
                    if len(parts) >= 2:
                        # Take the second part as potential title
                        candidate_title = parts[1].strip()
                        # Clean up common suffixes
                        candidate_title = (
                            candidate_title.replace("| LinkedIn", "")
                            .replace("...", "")
                            .strip()
                        )
                        serper_title_fallback = candidate_title

            if not linkedin_url:
                print("Manual Add: Could not find LinkedIn URL. Aborting.")
                return None

            # 4. Enrich Profile (Title, Company, Mobile)
            print(f"Manual Add: Enriching profile for {linkedin_url}...")

            # Use profile-search to get full details (Title, Company, Mobile)
            # This is better than just mobile-finder
            profile_data = await self.leadmagic.find_person(linkedin_url)

            phone = profile_data.get("phone")
            title = profile_data.get("title")

            # Fallback: If phone is missing, try Mobile Finder explicitly
            if not phone:
                print("Manual Add: Phone missing from Profile Search. Trying Mobile Finder...")
                try:
                    phone = await self.leadmagic.find_mobile_number(
                        linkedin_url=linkedin_url,
                        work_email=email
                    )
                    if phone:
                        print(f"Manual Add: Found phone via Mobile Finder: {phone}")
                except Exception as e:
                    print(f"Manual Add: Error fetching mobile number: {e}")

            if not title or title == "Unknown":
                if serper_title_fallback:
                    title = serper_title_fallback
                else:
                    title = "Unknown"

            company_name_found = profile_data.get("company")

            # If we found a company name and our current company is just a placeholder, update it
            if company_name_found and company.name == domain.split(".")[0].capitalize():
                company.name = company_name_found
                session.add(company)
                session.commit()
                session.refresh(company)

            # 5. Check if exists
            existing = session.exec(
                select(Prospect).where(Prospect.linkedin_url == linkedin_url)
            ).first()
            if existing:
                # Update existing with new info if missing
                if not existing.email and email:
                    existing.email = email
                if not existing.phone and phone:
                    existing.phone = phone
                if existing.title == "Unknown" and title != "Unknown":
                    existing.title = title

                session.add(existing)
                session.commit()
                session.refresh(existing)
                session.expunge(existing)
                return existing

            # 6. Create Prospect
            prospect = Prospect(
                first_name=first_name,
                last_name=last_name,
                title=title,
                email=email,
                phone=phone,
                linkedin_url=linkedin_url,
                company_id=company.id,
                status="New",
            )
            session.add(prospect)
            session.commit()
            session.refresh(prospect)
            session.expunge(prospect)
            return prospect
