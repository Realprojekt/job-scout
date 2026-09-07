import html
import re
from dataclasses import dataclass
from datetime import datetime

_TAG_RE = re.compile(r"<[^>]+>")
_WHITESPACE_RE = re.compile(r"\s+")


def clean_html(text: str) -> str:
    without_tags = _TAG_RE.sub(" ", text)
    unescaped = html.unescape(without_tags)
    return _WHITESPACE_RE.sub(" ", unescaped).strip()


@dataclass
class RawJob:
    source: str
    external_id: str
    title: str
    company: str
    location: str
    url: str
    description: str
    remote: bool
    posted_at: datetime | None
    lat: float | None = None
    lon: float | None = None


class JobSource:
    name: str = "base"

    def fetch(self) -> list[RawJob]:
        raise NotImplementedError

    def matches_keywords(self, text: str, keywords: list[str]) -> bool:
        text_lower = text.lower()
        return any(kw in text_lower for kw in keywords)
