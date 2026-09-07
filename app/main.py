import logging

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.database import init_db
from app.routers.jobs import router
from app.scheduler import start_scheduler

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

app = FastAPI(title="job-scout")
app.mount("/static", StaticFiles(directory="static"), name="static")
app.include_router(router)


@app.on_event("startup")
def on_startup() -> None:
    init_db()
    start_scheduler()
