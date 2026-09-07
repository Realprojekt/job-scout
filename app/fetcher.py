import logging

from sqlmodel import Session, select

from app.config import get_settings
from app.database import engine
from app.geocode import geocode, haversine_km
from app.models import Job
from app.settings_store import get_location_settings
from app.sources.adzuna import AdzunaSource
from app.sources.arbeitnow import ArbeitnowSource
from app.sources.base import RawJob

logger = logging.getLogger("job-scout.fetcher")


def _build_sources(settings, keywords: list[str], home_location: str, radius_km: float):
    return [
        ArbeitnowSource(keywords=keywords),
        AdzunaSource(
            app_id=settings.adzuna_app_id,
            app_key=settings.adzuna_app_key,
            country=settings.adzuna_country,
            where=home_location,
            distance_km=radius_km,
            queries=settings.adzuna_query_list,
            keywords=keywords,
        ),
    ]


def _resolve_distance(raw: RawJob, home_coords: tuple[float, float] | None, session: Session, settings) -> float | None:
    if home_coords is None:
        return None
    if raw.lat is not None and raw.lon is not None:
        return haversine_km(*home_coords, raw.lat, raw.lon)
    if raw.location:
        coords = geocode(raw.location, session, settings.nominatim_user_agent, settings.adzuna_country)
        if coords:
            return haversine_km(*home_coords, *coords)
    return None


def fetch_all_jobs() -> int:
    settings = get_settings()
    keywords = settings.keyword_list
    new_count = 0

    with Session(engine) as session:
        location = get_location_settings(session)
        home_coords = geocode(location.home_location, session, settings.nominatim_user_agent, settings.adzuna_country)
        if home_coords is None:
            logger.warning("Could not geocode HOME_LOCATION=%r; radius filtering disabled, only remote jobs will be kept", location.home_location)

        for source in _build_sources(settings, keywords, location.home_location, location.radius_km):
            try:
                raw_jobs = source.fetch()
            except Exception:
                logger.exception("Fetching from source %s failed", source.name)
                continue

            for raw in raw_jobs:
                distance = _resolve_distance(raw, home_coords, session, settings)
                within_radius = distance is not None and distance <= location.radius_km
                is_remote_ok = settings.include_remote and raw.remote
                if not (within_radius or is_remote_ok):
                    continue

                exists = session.exec(
                    select(Job).where(Job.source == raw.source, Job.external_id == raw.external_id)
                ).first()
                if exists:
                    continue

                session.add(
                    Job(
                        source=raw.source,
                        external_id=raw.external_id,
                        title=raw.title,
                        company=raw.company,
                        location=raw.location,
                        url=raw.url,
                        description=raw.description,
                        remote=raw.remote,
                        posted_at=raw.posted_at,
                        distance_km=round(distance, 1) if distance is not None else None,
                    )
                )
                new_count += 1
            session.commit()

    logger.info("Fetch complete: %d new job(s)", new_count)
    return new_count
