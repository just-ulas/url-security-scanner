from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=(".env", "../.env"), extra="ignore")

    app_env: str = "development"
    database_url: str = "postgresql+psycopg://scanner:scanner@localhost:5432/scanner"
    redis_url: str = "redis://localhost:6379/0"
    virustotal_api_key: str | None = None
    google_safe_browsing_api_key: str | None = None
    urlhaus_auth_key: str | None = None
    scan_rate_limit_per_minute: int = 5
    scan_queue_limit: int = 250
    scan_job_timeout_seconds: int = 90


@lru_cache
def get_settings() -> Settings:
    return Settings()
