from typing import Optional

from sqlmodel import Field, SQLModel


class Company(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    domain: str
    industry: Optional[str] = None
    description: Optional[str] = None
    linkedin_url: Optional[str] = None
    location: Optional[str] = None
    employees_count: Optional[str] = None
    # Note: Lists are not natively supported in SQLite/SQLModel without JSON serialization or relationship tables.
    # For simplicity in this MVP, we will store them as JSON strings or ignore them for DB persistence if not critical.
    # To keep it simple, we'll make them optional strings for now (e.g. comma separated).
    tech_stack: Optional[str] = None
    news_snippets: Optional[str] = None
