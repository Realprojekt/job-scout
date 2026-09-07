from datetime import datetime, UTC
from enum import Enum

from sqlmodel import Field, SQLModel, UniqueConstraint


class JobStatus(str, Enum):
    new = "new"
    interested = "interested"
    applied = "applied"
    rejected = "rejected"


class Job(SQLModel, table=True):
    __table_args__ = (UniqueConstraint("source", "external_id", name="uq_source_external_id"),)

    id: int | None = Field(default=None, primary_key=True)
    source: str
    external_id: str
    title: str
    company: str = ""
    location: str = ""
    url: str
    description: str = ""
    remote: bool = False
    posted_at: datetime | None = None
    fetched_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    distance_km: float | None = None
    status: JobStatus = Field(default=JobStatus.new)


class GeoCache(SQLModel, table=True):
    query: str = Field(primary_key=True)
    lat: float
    lon: float
