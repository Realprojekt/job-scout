from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    home_location: str = "45657"
    radius_km: float = 40.0
    include_remote: bool = True
    keywords: str = (
        "junior developer,junior software,junior softwareentwickler,junior programmierer,"
        "junior fullstack,junior full-stack,junior backend,junior frontend,junior web developer,"
        "junior it,fachinformatiker anwendungsentwicklung,trainee software,trainee developer,"
        "werkstudent softwareentwickl,werkstudent developer"
    )
    fetch_interval_minutes: int = 60
    database_url: str = "sqlite:///./data/jobs.db"

    adzuna_app_id: str = ""
    adzuna_app_key: str = ""
    adzuna_country: str = "de"
    adzuna_queries: str = "junior"

    nominatim_user_agent: str = "job-scout/1.0 (self-hosted personal project)"

    @property
    def keyword_list(self) -> list[str]:
        return [k.strip().lower() for k in self.keywords.split(",") if k.strip()]

    @property
    def adzuna_query_list(self) -> list[str]:
        return [q.strip() for q in self.adzuna_queries.split(",") if q.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
