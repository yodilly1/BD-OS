from typing import Optional

from sqlmodel import Field, SQLModel


class Prospect(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    first_name: str
    last_name: str
    title: str
    email: Optional[str] = None
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    company_id: Optional[int] = Field(default=None, foreign_key="company.id")
    location: Optional[str] = None
    summary: Optional[str] = None
    pain_points: Optional[str] = None
    status: str = "New"  # New, Contacted, Replied, Meeting Booked
