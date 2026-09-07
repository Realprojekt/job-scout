from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select

from app.database import get_session
from app.fetcher import fetch_all_jobs
from app.models import Job, JobStatus

router = APIRouter()
templates = Jinja2Templates(directory="templates")


def _query_jobs(session: Session, status: str = "", q: str = "", source: str = "") -> list[Job]:
    statement = select(Job)
    if status:
        statement = statement.where(Job.status == status)
    if source:
        statement = statement.where(Job.source == source)
    if q:
        like = f"%{q.lower()}%"
        statement = statement.where(
            (Job.title.ilike(like)) | (Job.company.ilike(like)) | (Job.location.ilike(like))
        )
    statement = statement.order_by(Job.distance_km.is_(None), Job.distance_km, Job.posted_at.desc())
    return list(session.exec(statement))


@router.get("/", response_class=HTMLResponse)
def index(request: Request, session: Session = Depends(get_session)):
    jobs = _query_jobs(session)
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "jobs": jobs, "statuses": list(JobStatus), "status": "", "q": "", "source": ""},
    )


@router.get("/partials/jobs", response_class=HTMLResponse)
def partial_jobs(request: Request, status: str = "", q: str = "", source: str = "", session: Session = Depends(get_session)):
    jobs = _query_jobs(session, status=status, q=q, source=source)
    return templates.TemplateResponse("partials/job_list.html", {"request": request, "jobs": jobs})


@router.post("/jobs/{job_id}/status", response_class=HTMLResponse)
def update_status(request: Request, job_id: int, status: str = Form(...), session: Session = Depends(get_session)):
    job = session.get(Job, job_id)
    if job:
        job.status = JobStatus(status)
        session.add(job)
        session.commit()
        session.refresh(job)
    return templates.TemplateResponse("partials/job_card.html", {"request": request, "job": job})


@router.post("/fetch", response_class=HTMLResponse)
def trigger_fetch(request: Request, session: Session = Depends(get_session)):
    fetch_all_jobs()
    jobs = _query_jobs(session)
    return templates.TemplateResponse("partials/job_list.html", {"request": request, "jobs": jobs})
