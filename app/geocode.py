import math
import time

import httpx
from sqlmodel import Session

from app.models import GeoCache

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
_last_request_time = 0.0
_MIN_INTERVAL = 1.0  # Nominatim usage policy: max 1 request/sec


def _respect_rate_limit() -> None:
    global _last_request_time
    elapsed = time.monotonic() - _last_request_time
    if elapsed < _MIN_INTERVAL:
        time.sleep(_MIN_INTERVAL - elapsed)
    _last_request_time = time.monotonic()


def geocode(query: str, session: Session, user_agent: str, country_code: str = "de") -> tuple[float, float] | None:
    """Resolve a free-text location to (lat, lon), using a persistent DB cache."""
    key = query.strip().lower()
    if not key:
        return None

    cached = session.get(GeoCache, key)
    if cached:
        return cached.lat, cached.lon

    _respect_rate_limit()
    try:
        resp = httpx.get(
            NOMINATIM_URL,
            params={"q": query, "format": "json", "limit": 1, "countrycodes": country_code},
            headers={"User-Agent": user_agent},
            timeout=10,
        )
        resp.raise_for_status()
        results = resp.json()
    except httpx.HTTPError:
        return None

    if not results:
        return None

    lat, lon = float(results[0]["lat"]), float(results[0]["lon"])
    session.add(GeoCache(query=key, lat=lat, lon=lon))
    session.commit()
    return lat, lon


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))
