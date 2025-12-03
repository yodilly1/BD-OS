from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import datetime
import json

class Campaign(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    status: str = "Active" # Active, Paused, Completed
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Target Criteria
    target_industry: Optional[str] = None
    target_size: Optional[str] = None
    target_keywords: Optional[str] = None
    target_titles_json: Optional[str] = None # Stored as JSON string
    
    # Auto-Pilot Config
    auto_pilot_enabled: bool = False
    auto_pilot_schedule: str = "daily" # daily, weekly
    last_run_at: Optional[datetime] = None

    @property
    def target_titles(self) -> List[str]:
        if not self.target_titles_json:
            return []
        return json.loads(self.target_titles_json)

    @target_titles.setter
    def target_titles(self, value: List[str]):
        self.target_titles_json = json.dumps(value)
