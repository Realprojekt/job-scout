from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler

from app.config import get_settings
from app.fetcher import fetch_all_jobs

scheduler = BackgroundScheduler()


def start_scheduler() -> None:
    settings = get_settings()
    scheduler.add_job(
        fetch_all_jobs,
        "interval",
        minutes=settings.fetch_interval_minutes,
        next_run_time=datetime.now(),
        id="fetch_all_jobs",
        max_instances=1,
        coalesce=True,
    )
    scheduler.start()
