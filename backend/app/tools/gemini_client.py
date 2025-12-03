import os

import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()


class GeminiClient:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("gemini-2.5-flash")

    async def generate_content(self, prompt: str) -> str:
        # --- MOCK IMPLEMENTATION ---
        if os.getenv("GEMINI_API_KEY") == "mock-key":
            print(
                f"[Gemini] MOCK: Simulating content generation for prompt: {prompt[:50]}..."
            )
            if "List of companies" in prompt:
                return """
                ```json
                [
                    {"name": "Stripe", "domain": "stripe.com", "description": "Online payment processing for internet businesses."},
                    {"name": "Square", "domain": "squareup.com", "description": "Payments and point-of-sale solutions."},
                    {"name": "Adyen", "domain": "adyen.com", "description": "A single payments platform globally."}
                ]
                ```
                """
            return ""
        # --- END MOCK ---
        try:
            import asyncio

            response = await asyncio.to_thread(self.model.generate_content, prompt)
            return response.text
        except Exception as e:
            print(f"Error generating content with Gemini: {e}")
            return ""

    async def analyze_image(self, prompt: str, image_path: str) -> str:
        # Placeholder for multimodal capabilities
        pass
