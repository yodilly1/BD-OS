from app.models.interaction import Interaction, InteractionType
from app.tools.gemini_client import GeminiClient


class CoachAgent:
    def __init__(self):
        self.gemini = GeminiClient()

    async def analyze_call_transcript(self, transcript: str) -> Interaction:
        """
        Analyzes a call transcript and provides coaching feedback.
        """
        prompt = f"""
        You are a Sales Coach. Analyze this call transcript between a BDR and a Prospect.
        Identify:
        1. What went well?
        2. Missed opportunities.
        3. Objection handling quality.
        4. Actionable advice for next time.

        Transcript:
        {transcript}
        """

        feedback = await self.gemini.generate_content(prompt)

        return Interaction(
            type=InteractionType.COACHING_FEEDBACK, content=feedback, status="reviewed"
        )
