from sqlmodel import Session

from app.config import VAYU_CONTEXT
from app.db import engine
from app.models.company import Company
from app.models.interaction import Interaction, InteractionType
from app.models.prospect import Prospect
from app.tools.claude_client import ClaudeClient
from app.tools.gemini_client import GeminiClient


class OutreachAgent:
    """
    The OutreachAgent is responsible for generating personalized outreach content.
    It uses LLMs like Claude and Gemini to draft and refine emails and LinkedIn messages,
    leveraging enriched prospect and company data.
    """

    def __init__(self):
        self.claude = ClaudeClient()
        self.gemini = GeminiClient()

    async def generate_email_sequence(self, prospect_id: int, context: str) -> Interaction:
        """
        Generates a personalized 3-step email sequence for a prospect.

        This method fetches prospect and company data, then uses a two-step LLM process:
        1. Claude drafts an email sequence based on a detailed prompt including company context.
        2. Gemini critiques and refines the draft to be more concise and effective.
        The final sequence is saved as an Interaction in the database.

        Args:
            prospect_id: The ID of the prospect for whom to generate the email.
            context: A string providing the context for the outreach campaign.

        Returns:
            An Interaction object containing the generated email sequence.

        Raises:
            ValueError: If the prospect with the given ID is not found.
        """
        with Session(engine) as session:
            prospect = session.get(Prospect, prospect_id)
            if not prospect:
                raise ValueError("Prospect not found")

            company = session.get(Company, prospect.company_id) if prospect.company_id else None

            # Build a rich context string from available company data
            company_context = self._build_company_context(company)

            # 1. Draft the email sequence with Claude
            system_prompt = self._get_email_system_prompt()
            user_prompt = self._get_email_user_prompt(prospect, company_context, context)
            
            draft = await self.claude.generate_text(system_prompt, user_prompt)

            # 2. Critique and refine the draft with Gemini
            critique_prompt = f"""
            Critique this email sequence. Is it too long? Too salesy?
            Does it effectively use the company context to make it personalized?

            Rewrite it to be punchier and more specific.
            IMPORTANT: Return ONLY the final email sequence. Do NOT include your critique or analysis.

            Draft:
            {draft}
            """
            final_version = await self.gemini.generate_content(critique_prompt)

            # 3. Save the result as an Interaction
            interaction = Interaction(
                type=InteractionType.EMAIL_DRAFT,
                content=final_version,
                prospect_id=prospect.id,
                status="draft",
            )
            session.add(interaction)
            session.commit()
            session.refresh(interaction)
            session.expunge(interaction)

            return interaction

    async def generate_linkedin_message(self, prospect_id: int, context: str) -> Interaction:
        """
        Generates a personalized LinkedIn connection request and a follow-up message.

        This method uses Claude to draft a short, casual, and value-driven message
        based on the prospect's role and company. The result is saved as an Interaction.

        Args:
            prospect_id: The ID of the prospect.
            context: The goal or context of the LinkedIn outreach.

        Returns:
            An Interaction object containing the generated LinkedIn message.

        Raises:
            ValueError: If the prospect with the given ID is not found.
        """
        with Session(engine) as session:
            prospect = session.get(Prospect, prospect_id)
            if not prospect:
                raise ValueError("Prospect not found")

            company = session.get(Company, prospect.company_id) if prospect.company_id else None

            company_info = f"{company.name}" if company else "their company"
            if company and company.industry:
                company_info += f" in the {company.industry} space"

            system_prompt = f"""
            You are a LinkedIn networking expert for {VAYU_CONTEXT["name"]}.
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
                status="draft",
            )
            session.add(interaction)
            session.commit()
            session.refresh(interaction)
            session.expunge(interaction)

            return interaction

    def _build_company_context(self, company: Company | None) -> str:
        """Helper to create a detailed context string from a Company object."""
        if not company:
            return "No company information available."

        return f"""
        Company: {company.name}
        Industry: {company.industry or "Unknown"}
        Size: {company.employees_count or "Unknown"}
        Location: {company.location or "Unknown"}
        Description: {company.description or "No description available"}
        Tech Stack: {company.tech_stack or "Unknown"}
        Recent News: {company.news_snippets or "No recent news"}
        """

    def _get_email_system_prompt(self) -> str:
        """Helper to generate the system prompt for email generation."""
        return f"""
        You are a world-class BDR copywriter for {VAYU_CONTEXT["name"]}.
        {VAYU_CONTEXT["description"]}

        Your Value Prop: {VAYU_CONTEXT["value_proposition"]}
        Key Differentiators: {", ".join(VAYU_CONTEXT["differentiators"])}
        Target Audience: {VAYU_CONTEXT["target_audience"]}
        Tone: {VAYU_CONTEXT["tone"]}

        Write concise, personalized, and effective cold emails that reference specific company details.
        """

    def _get_email_user_prompt(self, prospect: Prospect, company_context: str, context: str) -> str:
        """Helper to generate the user prompt for email generation."""
        return f"""
        Write a 3-step email sequence for this prospect. Use the company information to identify
        specific pain points related to billing/revenue operations that Vayu can solve.

        PROSPECT INFORMATION:
        Name: {prospect.first_name} {prospect.last_name}
        Title: {prospect.title}
        Pain Points: {prospect.pain_points or "Unknown"}

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
