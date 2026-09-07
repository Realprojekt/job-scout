from datetime import datetime

import httpx

from app.sources.base import JobSource, RawJob, clean_html

BASE_URL = "https://api.adzuna.com/v1/api/jobs/{country}/search/{page}"
MAX_PAGES = 3
RESULTS_PER_PAGE = 50

# NOTE: Adzuna's "distance" query param unit is not consistently documented
# (miles vs km depending on locale). If jobs outside your expected radius show
# up, check https://developer.adzuna.com/docs/search and adjust RADIUS_KM.


class AdzunaSource(JobSource):
    name = "adzuna"

    def __init__(
        self,
        app_id: str,
        app_key: str,
        country: str,
        where: str,
        distance_km: float,
        queries: list[str],
        keywords: list[str],
    ):
        self.app_id = app_id
        self.app_key = app_key
        self.country = country
        self.where = where
        self.distance_km = distance_km
        self.queries = queries or ["junior"]
        self.keywords = keywords

    def fetch(self) -> list[RawJob]:
        if not self.app_id or not self.app_key:
            return []

        jobs: list[RawJob] = []
        seen_ids: set[str] = set()
        with httpx.Client(timeout=20) as client:
            for query in self.queries:
                for page in range(1, MAX_PAGES + 1):
                    url = BASE_URL.format(country=self.country, page=page)
                    params = {
                        "app_id": self.app_id,
                        "app_key": self.app_key,
                        "what": query,
                        "where": self.where,
                        "distance": self.distance_km,
                        "results_per_page": RESULTS_PER_PAGE,
                        "content-type": "application/json",
                    }
                    resp = client.get(url, params=params)
                    if resp.status_code != 200:
                        break
                    payload = resp.json()
                    results = payload.get("results", [])
                    if not results:
                        break
                    for item in results:
                        external_id = str(item.get("id"))
                        if external_id in seen_ids:
                            continue
                        title = item.get("title", "")
                        description = clean_html(item.get("description", ""))
                        if not self.matches_keywords(f"{title} {description}", self.keywords):
                            continue
                        seen_ids.add(external_id)
                        posted_at = None
                        if item.get("created"):
                            try:
                                posted_at = datetime.fromisoformat(item["created"].replace("Z", "+00:00"))
                            except ValueError:
                                posted_at = None
                        location = item.get("location", {}).get("display_name", "")
                        jobs.append(
                            RawJob(
                                source=self.name,
                                external_id=external_id,
                                title=title,
                                company=item.get("company", {}).get("display_name", ""),
                                location=location,
                                url=item.get("redirect_url", ""),
                                description=description[:2000],
                                remote="remote" in location.lower() or "remote" in title.lower(),
                                posted_at=posted_at,
                                lat=item.get("latitude"),
                                lon=item.get("longitude"),
                            )
                        )
                    if len(results) < RESULTS_PER_PAGE:
                        break
        return jobs
