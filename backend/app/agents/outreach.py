from app.tools.claude_client import ClaudeClient
from app.tools.gemini_client import GeminiClient
from app.models.prospect import Prospect
from app.models.company import Company
from app.models.interaction import Interaction, InteractionType
from app.db import engine
from sqlmodel import Session
from app.config import VAYU_CONTEXT

class OutreachAgent:
    def __init__(self):
        self.claude = ClaudeClient()
        self.gemini = GeminiClient()

    async def generate_email_sequence(self, prospect_id: int, context: str) -> Interaction:
        """
        Generates a personalized email sequence for a prospect using company enrichment data.
        """
        with Session(engine) as session:
            prospect = session.get(Prospect, prospect_id)
            if not prospect:
                raise ValueError("Prospect not found")
            
            company = session.get(Company, prospect.company_id) if prospect.company_id else None

            # Build company context from enrichment data
            company_context = ""
            if company:
                company_context = f"""
                Company: {company.name}
                Industry: {company.industry or 'Unknown'}
                Size: {company.employees_count or 'Unknown'}
                Location: {company.location or 'Unknown'}
                Description: {company.description or 'No description available'}
                Tech Stack: {company.tech_stack or 'Unknown'}
                Recent News: {company.news_snippets or 'No recent news'}
                """

            # 1. Draft with Claude
            system_prompt = f"""
            You are a world-class BDR copywriter for {VAYU_CONTEXT['name']}. 
            {VAYU_CONTEXT['description']}
            
            Your Value Prop: {VAYU_CONTEXT['value_proposition']}
            Key Differentiators: {', '.join(VAYU_CONTEXT['differentiators'])}
            Target Audience: {VAYU_CONTEXT['target_audience']}
            Tone: {VAYU_CONTEXT['tone']}
            
            Write concise, personalized, and effective cold emails that reference specific company details.
            """
            
            user_prompt = f"""
            Write a 3-step email sequence for this prospect. Use the company information to identify 
            specific pain points related to billing/revenue operations that Vayu can solve.
            
            PROSPECT INFORMATION:
            Name: {prospect.first_name} {prospect.last_name}
            Title: {prospect.title}
            Pain Points: {prospect.pain_points or 'Unknown'}
            
            COMPANY INFORMATION:
            {company_context}
            
            CAMPAIGN CONTEXT:
            {context}
            
            INSTRUCTIONS:
            - Reference their tech stack, industry, or recent news where relevant
            - Connect their company's needs to Vayu's solutions
            - Be specific about how Vayu can help based on their industry/size
            - Keep each email under 150 words
            
            Format the output clearly with Subject lines and Body text for each step.
            """
            
            draft = await self.claude.generate_text(system_prompt, user_prompt)
            
            # 2. Critique/Refine with Gemini
            critique_prompt = f"""
            Critique this email sequence. Is it too long? Too salesy? 
            Does it effectively use the company context to make it personalized?
            If it's good, just return the original text. 
            If it needs improvement, rewrite it to be punchier and more specific.
            
            Draft:
            {draft}
            """
            final_version = await self.gemini.generate_content(critique_prompt)
            
            interaction = Interaction(
                type=InteractionType.EMAIL_DRAFT,
                content=final_version,
                prospect_id=prospect.id,
                status="draft"
            )
            session.add(interaction)
            session.commit()
            session.refresh(interaction)
            
            return interaction

    async def generate_linkedin_message(self, prospect_id: int, context: str) -> Interaction:
        """
        Generates a personalized LinkedIn connection request and follow-up using company data.
        """
        with Session(engine) as session:
            prospect = session.get(Prospect, prospect_id)
            if not prospect:
                raise ValueError("Prospect not found")
            
            company = session.get(Company, prospect.company_id) if prospect.company_id else None

            # Build concise company context
            company_info = f"{company.name}" if company else "their company"
            if company and company.industry:
                company_info += f" in {company.industry}"
            if company and company.news_snippets:
                company_info += f". Recent: {company.news_snippets[:100]}"

            system_prompt = f"""
            You are a LinkedIn networking expert for {VAYU_CONTEXT['name']}. 
            Write short, casual, and value-add messages that reference specific company details.
            """
            
            user_prompt = f"""
            Write a LinkedIn Connection Request (max 300 chars) and a Follow-up Message for this prospect.
            
            Prospect: {prospect.first_name} {prospect.last_name}
            Title: {prospect.title}
            Company Info: {company_info}
            Context/Goal: {context}
            
            Make it personal by referencing their company or industry. Keep it conversational.
            """
            
            draft = await self.claude.generate_text(system_prompt, user_prompt)
            
            interaction = Interaction(
                type=InteractionType.LINKEDIN_MESSAGE,
                content=draft,
                prospect_id=prospect.id,
                status="draft"
            )
            session.add(interaction)
            session.commit()
            session.refresh(interaction)
            
            return interaction
