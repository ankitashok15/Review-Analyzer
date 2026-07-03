import json
import time

import redis

from config.settings import get_settings

settings = get_settings()
CACHE_PREFIX = "insights:list:"


def _client() -> redis.Redis | None:
    try:
        client = redis.Redis.from_url(settings.redis_url, decode_responses=True)
        client.ping()
        return client
    except Exception:
        return None


class InsightListCache:
    """Redis cache for GET /insights list responses."""

    def get(self) -> dict | None:
        client = _client()
        if not client:
            return None
        raw = client.get(f"{CACHE_PREFIX}default")
        if not raw:
            return None
        return json.loads(raw)

    def set(self, payload: dict) -> None:
        client = _client()
        if not client:
            return
        client.setex(
            f"{CACHE_PREFIX}default",
            settings.insight_cache_ttl_seconds,
            json.dumps(payload, default=str),
        )

    def invalidate(self) -> None:
        client = _client()
        if client:
            client.delete(f"{CACHE_PREFIX}default")


insight_list_cache = InsightListCache()
