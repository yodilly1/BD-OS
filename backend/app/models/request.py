from pydantic import BaseModel
from typing import List

class DeepSearchRequest(BaseModel):
    industry: str
    size: str
    keywords: str
    titles: List[str]
    limit: int = 20

class UrlSearchRequest(BaseModel):
    url: str
