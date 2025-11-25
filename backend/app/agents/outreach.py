from app.tools.claude_client import ClaudeClient
from app.tools.gemini_client import GeminiClient
from app.models.prospect import Prospect
from app.models.company import Company
from app.models.interaction import Interaction, InteractionType
from app.db import engine
from sqlmodel import Session

class OutreachAgent:
    def __init__(self):
        self.claude = ClaudeClient()
        self.gemini = GeminiClient()

    async def generate_email_sequence(self, prospect_id: int, context: str) -> Interaction:
        """
        Generates a personalized email sequence for a prospect.
        """
        with Session(engine) as session:
            prospect = session.get(Prospect, prospect_id)
            if not prospect:
                raise ValueError("Prospect not found")
            
            company = session.get(Company, prospect.company_id) if prospect.company_id else None

            # 1. Draft with Claude
            system_prompt = "You are a world-class BDR copywriter. Write concise, personalized, and effective cold emails."
            user_prompt = f"""
            Write a 3-step email sequence for this prospect.
            
            Prospect: {prospect.first_name} {prospect.last_name}
            Title: {prospect.title}
            Company: {company.name if company else 'Unknown'}
            Pain Points: {prospect.pain_points}
            Context/Goal: {context}
            
            Format the output clearly with Subject lines and Body text for each step.
            """
            
            draft = await self.claude.generate_text(system_prompt, user_prompt)
            
            # 2. Critique/Refine with Gemini
            critique_prompt = f"""
            Critique this email sequence. Is it too long? Too salesy? 
            If it's good, just return the original text. 
            If it needs improvement, rewrite it to be punchier.
            
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
        Generates a personalized LinkedIn connection request and follow-up.
        """
        with Session(engine) as session:
            prospect = session.get(Prospect, prospect_id)
            if not prospect:
                raise ValueError("Prospect not found")
            
            company = session.get(Company, prospect.company_id) if prospect.company_id else None

            system_prompt = "You are a LinkedIn networking expert. Write short, casual, and value-add messages."
            user_prompt = f"""
            Write a LinkedIn Connection Request (max 300 chars) and a Follow-up Message for this prospect.
            
            Prospect: {prospect.first_name} {prospect.last_name}
            Title: {prospect.title}
            Company: {company.name if company else 'Unknown'}
            Context/Goal: {context}
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
