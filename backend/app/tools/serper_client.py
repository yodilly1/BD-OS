import httpx
import os
import json
from dotenv import load_dotenv

load_dotenv()

class SerperClient:
    def __init__(self):
        self.api_key = os.getenv("SERPER_API_KEY")
        if not self.api_key:
            raise ValueError("SERPER_API_KEY not found in environment variables")
        self.base_url = "https://google.serper.dev/search"
        self.headers = {
            "X-API-KEY": self.api_key,
            "Content-Type": "application/json"
        }

    async def search(self, query: str, type: str = "search") -> dict:
        """
        type can be 'search', 'news', 'places', etc.
        """
        url = f"https://google.serper.dev/{type}" if type != "search" else self.base_url
        payload = json.dumps({"q": query})
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, headers=self.headers, data=payload)
                response.raise_for_status()
                return response.json()
            except Exception as e:
                print(f"Error searching with Serper: {e}")
                return {}
