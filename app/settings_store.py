from sqlmodel import Session

from app.config import get_settings
from app.models import AppSettings


def get_location_settings(session: Session) -> AppSettings:
    row = session.get(AppSettings, 1)
    if row is None:
        defaults = get_settings()
        row = AppSettings(id=1, home_location=defaults.home_location, radius_km=defaults.radius_km)
        session.add(row)
        session.commit()
        session.refresh(row)
    return row


def update_location_settings(session: Session, home_location: str, radius_km: float) -> AppSettings:
    row = get_location_settings(session)
    row.home_location = home_location.strip()
    row.radius_km = radius_km
    session.add(row)
    session.commit()
    session.refresh(row)
    return row
