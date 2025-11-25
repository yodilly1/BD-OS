import anthropic
import os
from dotenv import load_dotenv

load_dotenv()

class ClaudeClient:
    def __init__(self):
        api_key = os.getenv("CLAUDE_API_KEY")
        if not api_key:
            raise ValueError("CLAUDE_API_KEY not found in environment variables")
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = "claude-opus-4-5-20251101" # Or claude-3-sonnet-20240229 for speed

    async def generate_text(self, system_prompt: str, user_prompt: str) -> str:
        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_prompt}
                ]
            )
            return message.content[0].text
        except Exception as e:
            print(f"Error generating text with Claude: {e}")
            return ""
