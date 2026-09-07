from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select

from app.database import get_session
from app.fetcher import fetch_all_jobs
from app.models import Job, JobStatus
from app.settings_store import get_location_settings, update_location_settings

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


def _render_job_list(request: Request, session: Session, status: str = "", q: str = "", source: str = ""):
    jobs = _query_jobs(session, status=status, q=q, source=source)
    location = get_location_settings(session)
    return templates.TemplateResponse(
        "partials/job_list.html",
        {"request": request, "jobs": jobs, "home_location": location.home_location, "radius_km": location.radius_km},
    )


@router.get("/", response_class=HTMLResponse)
def index(request: Request, session: Session = Depends(get_session)):
    jobs = _query_jobs(session)
    location = get_location_settings(session)
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "jobs": jobs,
            "statuses": list(JobStatus),
            "status": "",
            "q": "",
            "source": "",
            "home_location": location.home_location,
            "radius_km": location.radius_km,
        },
    )


@router.get("/partials/jobs", response_class=HTMLResponse)
def partial_jobs(request: Request, status: str = "", q: str = "", source: str = "", session: Session = Depends(get_session)):
    return _render_job_list(request, session, status=status, q=q, source=source)


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
    return _render_job_list(request, session)


@router.post("/settings/location", response_class=HTMLResponse)
def update_location(request: Request, home_location: str = Form(...), radius_km: float = Form(...), session: Session = Depends(get_session)):
    update_location_settings(session, home_location=home_location, radius_km=radius_km)
    fetch_all_jobs()
    return _render_job_list(request, session)
