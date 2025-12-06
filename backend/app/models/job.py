import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class Job(BaseModel):
    id: str
    status: JobStatus
    result: Optional[Any] = None
    error: Optional[str] = None
    created_at: datetime = datetime.now()


# Simple in-memory job store
jobs: Dict[str, Job] = {}


def create_job() -> Job:
    job_id = str(uuid.uuid4())
    job = Job(id=job_id, status=JobStatus.PENDING)
    jobs[job_id] = job
    return job


def get_job(job_id: str) -> Optional[Job]:
    return jobs.get(job_id)


def update_job(job_id: str, status: JobStatus, result: Any = None, error: str = None):
    if job_id in jobs:
        jobs[job_id].status = status
        if result is not None:
            jobs[job_id].result = result
        if error is not None:
            jobs[job_id].error = error
