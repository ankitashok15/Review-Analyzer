from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    database_url: str = "postgresql://postgres:postgres@localhost:5434/review_engine"
    redis_url: str = "redis://localhost:6379/0"
    google_api_key: str = "placeholder"
    gemini_enrichment_model: str = "gemini-2.0-flash"
    gemini_rag_model: str = "gemini-2.5-pro"
    gemini_embedding_model: str = "gemini-embedding-001"
    vector_dimension: int = 768
    log_level: str = "INFO"
    log_format: str = "json"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

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


@lru_cache
def get_settings() -> Settings:
    return Settings()
