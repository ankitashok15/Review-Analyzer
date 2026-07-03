import time
import uuid
from collections import defaultdict
from threading import Lock

from config.settings import get_settings

settings = get_settings()


class InMemoryRateLimiter:
    """Simple per-IP sliding window limiter for local deployments."""

    def __init__(self):
        self._buckets: dict[str, list[float]] = defaultdict(list)
        self._lock = Lock()

    def allow(self, key: str, *, limit: int, window_seconds: int = 60) -> bool:
        now = time.time()
        cutoff = now - window_seconds
        with self._lock:
            hits = [ts for ts in self._buckets[key] if ts >= cutoff]
            if len(hits) >= limit:
                self._buckets[key] = hits
                return False
            hits.append(now)
            self._buckets[key] = hits
            return True


_rate_limiter = InMemoryRateLimiter()


def check_rate_limit(client_key: str, path: str) -> tuple[bool, int]:
    settings = get_settings()
    if path.endswith("/ask"):
        limit = settings.rate_limit_ask_per_minute
    elif path.endswith("/search"):
        limit = settings.rate_limit_search_per_minute
    else:
        return True, 0

    allowed = _rate_limiter.allow(f"{client_key}:{path}", limit=limit)
    return allowed, limit


def reset_rate_limits_for_tests() -> None:
    _rate_limiter._buckets.clear()
