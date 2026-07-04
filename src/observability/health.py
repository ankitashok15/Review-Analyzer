from typing import Any

import redis
from celery import Celery

from config.settings import get_settings
from src.ai.gemini_client import GeminiClient
from src.embeddings.embedder import embedding_model_version
from src.storage.database import check_db_connection, engine
from sqlalchemy import text

settings = get_settings()


def get_database_stats() -> dict[str, int | str]:
    try:
        with engine.connect() as connection:
            reviews = connection.execute(text("SELECT COUNT(*) FROM reviews")).scalar() or 0
            embeddings = connection.execute(
                text("SELECT COUNT(*) FROM review_embeddings")
            ).scalar() or 0
            versions = connection.execute(
                text(
                    "SELECT model_version, COUNT(*) AS n "
                    "FROM review_embeddings GROUP BY model_version ORDER BY n DESC LIMIT 5"
                )
            ).fetchall()
        return {
            "review_count": int(reviews),
            "embedding_count": int(embeddings),
            "embedding_model_versions": [
                {"model_version": row[0], "count": int(row[1])} for row in versions
            ],
            "search_model_version": embedding_model_version(),
        }
    except Exception as exc:
        return {"error": str(exc)}


def check_redis_connection() -> bool:
    try:
        client = redis.Redis.from_url(
            settings.redis_url,
            decode_responses=True,
            socket_connect_timeout=1,
            socket_timeout=1,
        )
        client.ping()
        return True
    except Exception:
        return False


def check_celery_workers() -> dict[str, Any]:
    try:
        app = Celery(broker=settings.redis_url, backend=settings.redis_url)
        inspector = app.control.inspect(timeout=1.0)
        ping = inspector.ping() if inspector else None
        if not ping:
            return {"status": "unavailable", "workers": 0}
        return {"status": "ok", "workers": len(ping)}
    except Exception as exc:
        return {"status": "error", "detail": str(exc), "workers": 0}


def check_gemini_connectivity() -> dict[str, Any]:
    key = settings.google_api_key.strip()
    if not key or key == "placeholder":
        return {"status": "not_configured"}
    try:
        GeminiClient(api_key=key)
        return {"status": "configured"}
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}


def build_health_report(*, detailed: bool = False) -> dict[str, Any]:
    db_ok = check_db_connection()
    redis_ok = check_redis_connection()

    report: dict[str, Any] = {
        "status": "ok" if db_ok and redis_ok else "degraded",
        "service": "review-discovery-engine",
        "db": "connected" if db_ok else "disconnected",
        "redis": "connected" if redis_ok else "disconnected",
    }

    if detailed:
        report["celery"] = check_celery_workers()
        report["gemini"] = check_gemini_connectivity()
        report["database"] = get_database_stats()

    return report
