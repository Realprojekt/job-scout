from datetime import datetime, UTC

import httpx

from app.sources.base import JobSource, RawJob, clean_html

API_URL = "https://www.arbeitnow.com/api/job-board-api"
MAX_PAGES = 5


class ArbeitnowSource(JobSource):
    name = "arbeitnow"

    def __init__(self, keywords: list[str]):
        self.keywords = keywords

    def fetch(self) -> list[RawJob]:
        jobs: list[RawJob] = []
        with httpx.Client(timeout=20) as client:
            page = 1
            while page <= MAX_PAGES:
                resp = client.get(API_URL, params={"page": page})
                resp.raise_for_status()
                payload = resp.json()
                data = payload.get("data", [])
                if not data:
                    break
                for item in data:
                    title = item.get("title", "")
                    if not self.matches_keywords(title, self.keywords):
                        continue
                    posted_at = None
                    if item.get("created_at"):
                        posted_at = datetime.fromtimestamp(item["created_at"], tz=UTC)
                    jobs.append(
                        RawJob(
                            source=self.name,
                            external_id=item.get("slug", item.get("url", title)),
                            title=title,
                            company=item.get("company_name", ""),
                            location=item.get("location", ""),
                            url=item.get("url", ""),
                            description=clean_html(item.get("description", ""))[:2000],
                            remote=bool(item.get("remote", False)),
                            posted_at=posted_at,
                        )
                    )
                if not payload.get("links", {}).get("next"):
                    break
                page += 1
        return jobs
