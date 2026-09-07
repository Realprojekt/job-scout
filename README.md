# job-scout

A self-hosted tool that collects junior developer job listings from multiple
sources, filters them by radius and keyword, and shows them in a simple
dashboard with per-listing status tracking (new / interested / applied /
rejected). You still apply directly on the source site — this tool only
bundles the overview, it doesn't replace an application platform.

## Data sources

- [Arbeitnow](https://www.arbeitnow.com/api/job-board-api) — free, no API key needed
- [Adzuna](https://developer.adzuna.com/) — free API key required (sign up), aggregates data from sources including Indeed

Other sources (e.g. scraping Indeed/Instaffo directly) are intentionally not
included, since both prohibit automated scraping in their terms of service.
`app/sources/` is structured so that adding a new source only requires a new
class with a `fetch()` method (see `app/sources/base.py`).

## How it works

- A scheduler fetches new jobs on startup and then every
  `FETCH_INTERVAL_MINUTES` (default: 60).
- Jobs without coordinates (Arbeitnow) are geocoded via
  [Nominatim](https://nominatim.org/) (OpenStreetMap) to compute the
  distance to `HOME_LOCATION`; Adzuna provides coordinates directly.
- Listings are shown if they're within `RADIUS_KM` **or** marked as remote
  (see `INCLUDE_REMOTE`).
- Jobs already seen (`source` + `external_id`) are not inserted again.

## Setup (local)

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Edit `.env` (at minimum `HOME_LOCATION`, `RADIUS_KM`; for Adzuna results
also set `ADZUNA_APP_ID` / `ADZUNA_APP_KEY` from https://developer.adzuna.com/).

```bash
uvicorn app.main:app --reload
```

Dashboard: http://localhost:8000

## Setup (Docker)

```bash
copy .env.example .env
docker compose up -d --build
```

The SQLite database persists in `./data/jobs.db`.

## Notes

- Without Adzuna keys, only Arbeitnow results show up (that source doesn't
  error, it just returns no Adzuna matches).
- Nominatim allows at most 1 request/second — with many new, distinct
  Arbeitnow locations, a manual "Refresh now" can take a bit longer.
- Adzuna's `distance` parameter unit isn't clearly documented (miles vs.
  km). If the radius feels noticeably off, adjust `RADIUS_KM` or check the
  [Adzuna API docs](https://developer.adzuna.com/docs/search).

## Tech stack

Python · FastAPI · SQLModel (SQLite) · APScheduler · HTMX · Jinja2
