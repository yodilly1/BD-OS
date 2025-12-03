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
    allow_origins=["*"],
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

from app.models.request import DeepSearchRequest, UrlSearchRequest

from fastapi import BackgroundTasks
from app.models.job import create_job, update_job, get_job, JobStatus

@app.post("/api/prospect/deep-search", response_model=dict)
async def deep_search(request: DeepSearchRequest, background_tasks: BackgroundTasks):
    job = create_job()
    
    async def run_deep_search(job_id: str, req: DeepSearchRequest):
        update_job(job_id, JobStatus.RUNNING)
        try:
            results = await prospector.deep_prospecting_flow(
                req.industry, 
                req.size, 
                req.keywords, 
                req.titles,
                req.limit
            )
            # Convert Prospect objects to dicts for JSON serialization
            result_dicts = [
                {
                    "id": p.id,
                    "first_name": p.first_name,
                    "last_name": p.last_name,
                    "title": p.title,
                    "linkedin_url": p.linkedin_url,
                    "company_id": p.company_id,
                    "status": p.status,
                    "email": p.email,
                    "phone": p.phone
                }
                for p in results
            ]
            update_job(job_id, JobStatus.COMPLETED, result=result_dicts)
        except Exception as e:
            print(f"Job {job_id} failed: {e}")
            update_job(job_id, JobStatus.FAILED, error=str(e))

    background_tasks.add_task(run_deep_search, job.id, request)
    return {"job_id": job.id}

@app.get("/api/jobs/{job_id}")
async def get_job_status(job_id: str):
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@app.post("/api/prospect/url-search", response_model=List[Prospect])
async def url_search(request: UrlSearchRequest):
    try:
        return await prospector.url_prospecting_flow(request.url, request.titles)
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

from app.models.request import ManualAddRequest

@app.post("/api/prospect/manual-add", response_model=Prospect)
async def manual_add(request: ManualAddRequest):
    try:
        prospect = await prospector.manual_prospecting_flow(
            request.first_name, 
            request.last_name, 
            request.domain
        )
        if not prospect:
            raise HTTPException(status_code=404, detail="Could not find prospect with provided details.")
        return prospect
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

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

@app.post("/api/prospect/search-candidates", response_model=dict)
async def search_candidates(request: DeepSearchRequest, background_tasks: BackgroundTasks):
    """
    Phase 1: Search for candidates but do not save.
    """
    job = create_job()
    
    async def run_search(job_id: str, req: DeepSearchRequest):
        update_job(job_id, JobStatus.RUNNING)
        try:
            results = await prospector.search_candidates(
                req.industry, 
                req.size, 
                req.keywords, 
                req.titles,
                req.limit
            )
            update_job(job_id, JobStatus.COMPLETED, result=results)
        except Exception as e:
            print(f"Job {job_id} failed: {e}")
            update_job(job_id, JobStatus.FAILED, error=str(e))

    background_tasks.add_task(run_search, job.id, request)
    return {"job_id": job.id}

@app.post("/api/prospect/save-candidates", response_model=List[Prospect])
async def save_candidates(candidates: List[dict]):
    """
    Phase 2: Save selected candidates to DB.
    """
    try:
        return await prospector.save_candidates(candidates)
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/prospects", response_model=List[Prospect])
async def get_prospects(sort_by: str = "newest", search: str = None):
    with Session(engine) as session:
        query = select(Prospect)
        
        if search:
            search_term = f"%{search}%"
            query = query.where(
                (Prospect.first_name.ilike(search_term)) | 
                (Prospect.last_name.ilike(search_term)) |
                (Prospect.title.ilike(search_term))
            )
            
        if sort_by == "newest":
            query = query.order_by(Prospect.id.desc())
            
        return session.exec(query).all()

@app.post("/api/coach/analyze", response_model=Interaction)
async def analyze_call(transcript: str):
    return await coach.analyze_call_transcript(transcript)

from sqlmodel import delete

@app.post("/api/admin/reset-db")
async def reset_db():
    with Session(engine) as session:
        session.exec(delete(Interaction))
        session.exec(delete(Prospect))
        session.exec(delete(Company))
        session.commit()
    return {"message": "Database reset successfully"}
