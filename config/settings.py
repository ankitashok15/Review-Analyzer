from functools import lru_cache
from urllib.parse import urlparse

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def normalize_database_url(url: str) -> str:
    """Normalize common Railway/Neon paste mistakes before SQLAlchemy parses the URL."""
    cleaned = url.strip()
    if not cleaned:
        return cleaned

    if (cleaned.startswith('"') and cleaned.endswith('"')) or (
        cleaned.startswith("'") and cleaned.endswith("'")
    ):
        cleaned = cleaned[1:-1].strip()

    if cleaned.startswith("${") or cleaned.startswith("$("):
        raise ValueError(
            "DATABASE_URL looks like an unexpanded Railway reference "
            "(e.g. ${{Postgres.DATABASE_URL}}). Paste the full Neon URL instead."
        )

    if cleaned.startswith("postgres://"):
        cleaned = "postgresql://" + cleaned[len("postgres://") :]

    return cleaned


def validate_database_url(url: str) -> str:
    cleaned = normalize_database_url(url)
    if not cleaned:
        raise ValueError(
            "DATABASE_URL is empty. Set DATABASE_URL or NEON_DATABASE_URL to your Neon "
            "postgresql:// connection string (pooled URL with ?sslmode=require)."
        )

    parsed = urlparse(cleaned)
    if parsed.scheme not in {"postgresql", "postgres"}:
        raise ValueError(
            f"DATABASE_URL must start with postgresql:// (got scheme {parsed.scheme!r})."
        )
    if not parsed.hostname:
        raise ValueError("DATABASE_URL is missing a hostname.")

    return cleaned


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    database_url: str = "postgresql://postgres:postgres@localhost:5434/review_engine"
    # Optional override for Railway when a linked Postgres service injects DATABASE_URL.
    neon_database_url: str = ""
    redis_url: str = "redis://localhost:6379/0"
    google_api_key: str = "placeholder"
    gemini_enrichment_model: str = "gemini-2.0-flash"
    gemini_rag_model: str = "gemini-2.5-pro"
    gemini_embedding_model: str = "gemini-embedding-001"
    vector_dimension: int = 768
    log_level: str = "INFO"
    log_format: str = "json"
    cors_origins: str = (
        "http://localhost:5173,http://127.0.0.1:5173,"
        "https://ankitashok15.github.io"
    )

    admin_api_key: str = ""
    admin_api_key_header: str = "X-API-Key"
    require_admin_api_key: bool = True

    rate_limit_ask_per_minute: int = 60
    rate_limit_search_per_minute: int = 120

    db_pool_size: int = 10
    db_max_overflow: int = 20
    db_pool_recycle: int = 1800

    insight_cache_ttl_seconds: int = 3600
    archive_raw_payloads: bool = False
    raw_archive_path: str = "data/raw_archive"

    max_query_length: int = 2000
    job_result_ttl_seconds: int = 86400
    rag_fallback_enabled: bool = True

    @model_validator(mode="after")
    def apply_neon_database_url(self) -> "Settings":
        raw_url = self.neon_database_url.strip() or self.database_url
        self.database_url = validate_database_url(raw_url)
        return self

    @property
    def database_host(self) -> str:
        return urlparse(self.database_url).hostname or "unknown"


@lru_cache
def get_settings() -> Settings:
    return Settings()
