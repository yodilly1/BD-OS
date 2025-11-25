from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum

class InteractionType(str, Enum):
    EMAIL_DRAFT = "email_draft"
    LINKEDIN_MESSAGE = "linkedin_message"
    CALL_SCRIPT = "call_script"
    COACHING_FEEDBACK = "coaching_feedback"

class Interaction(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    type: InteractionType
    content: str
    created_at: datetime = Field(default_factory=datetime.now)
    prospect_id: Optional[int] = Field(default=None, foreign_key="prospect.id")
    status: str = "draft" # draft, sent, reviewed
    feedback: Optional[str] = None
