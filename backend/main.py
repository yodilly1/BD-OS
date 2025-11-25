from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
from contextlib import asynccontextmanager
from app.db import create_db_and_tables
from app.agents.prospector import ProspectorAgent
from app.agents.researcher import ResearcherAgent
from app.agents.outreach import OutreachAgent
from app.agents.coach import CoachAgent
from app.models.company import Company
from app.models.prospect import Prospect
from app.models.interaction import Interaction
from app.db import engine
from sqlmodel import Session, select
from typing import List

load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield

app = FastAPI(title="BD-OS Backend", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Agents
prospector = ProspectorAgent()
researcher = ResearcherAgent()
outreach = OutreachAgent()
coach = CoachAgent()

@app.get("/")
async def root():
    return {"message": "BD-OS Backend is running"}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "gemini_key_present": bool(os.getenv("GEMINI_API_KEY")),
        "claude_key_present": bool(os.getenv("CLAUDE_API_KEY")),
        "serper_key_present": bool(os.getenv("SERPER_API_KEY")),
        "leadmagic_key_present": bool(os.getenv("LEADMAGIC_API_KEY")),
    }

@app.post("/api/prospect/find-companies", response_model=List[Company])
async def find_companies(icp_description: str):
    return await prospector.find_companies(icp_description)

@app.post("/api/prospect/find-people", response_model=List[Prospect])
async def find_people(company_id: int, role_description: str):
    return await prospector.find_prospects(company_id, role_description)

@app.post("/api/enrich/company", response_model=Company)
async def enrich_company(company_id: int):
    return await researcher.enrich_company(company_id)

@app.post("/api/enrich/prospect", response_model=Prospect)
async def enrich_prospect(prospect_id: int):
    return await researcher.enrich_prospect(prospect_id)

@app.post("/api/outreach/generate-email", response_model=Interaction)
async def generate_email(prospect_id: int, context: str):
    return await outreach.generate_email_sequence(prospect_id, context)

@app.post("/api/outreach/generate-linkedin", response_model=Interaction)
async def generate_linkedin(prospect_id: int, context: str):
    return await outreach.generate_linkedin_message(prospect_id, context)

@app.get("/api/companies", response_model=List[Company])
async def get_companies():
    with Session(engine) as session:
        return session.exec(select(Company)).all()

@app.get("/api/prospects", response_model=List[Prospect])
async def get_prospects():
    with Session(engine) as session:
        return session.exec(select(Prospect)).all()

@app.post("/api/coach/analyze", response_model=Interaction)
async def analyze_call(transcript: str):
    return await coach.analyze_call_transcript(transcript)
