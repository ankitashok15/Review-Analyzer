import json
import time
from typing import Any

import redis

from config.settings import get_settings

settings = get_settings()

METRICS_PREFIX = "metrics:"
JOB_PREFIX = "job:"
DLQ_PREFIX = "dlq:"


def _redis_client() -> redis.Redis | None:
    try:
        client = redis.Redis.from_url(settings.redis_url, decode_responses=True)
        client.ping()
        return client
    except Exception:
        return None


class MetricsStore:
    """Track pipeline and API counters in Redis with in-memory fallback."""

    def __init__(self):
        self._redis = _redis_client()
        self._memory: dict[str, float] = {}

    def increment(self, name: str, amount: float = 1.0) -> None:
        if self._redis:
            self._redis.incrbyfloat(f"{METRICS_PREFIX}{name}", amount)
            return
        self._memory[name] = self._memory.get(name, 0.0) + amount

    def observe_latency(self, name: str, duration_ms: float) -> None:
        self.increment(f"{name}_count", 1.0)
        self.increment(f"{name}_total_ms", duration_ms)

    def snapshot(self) -> dict[str, Any]:
        if self._redis:
            keys = self._redis.keys(f"{METRICS_PREFIX}*")
            return {key.removeprefix(METRICS_PREFIX): float(self._redis.get(key) or 0) for key in keys}
        return dict(self._memory)

    def enrichment_success_rate(self) -> float | None:
        snap = self.snapshot()
        enriched = snap.get("enrichment_success", 0.0)
        failed = snap.get("enrichment_failed", 0.0)
        total = enriched + failed
        if total <= 0:
            return None
        return round(enriched / total, 4)


_metrics = MetricsStore()


def get_metrics() -> MetricsStore:
    return _metrics


class JobStore:
    """Persist async job metadata and dead-letter records in Redis."""

    def __init__(self):
        self._redis = _redis_client()

    def _ttl(self) -> int:
        return settings.job_result_ttl_seconds

    def create(self, job_id: str, *, task_name: str, payload: dict | None = None) -> dict:
        record = {
            "job_id": job_id,
            "task_name": task_name,
            "status": "pending",
            "payload": payload or {},
            "result": None,
            "error": None,
            "created_at": time.time(),
            "updated_at": time.time(),
        }
        self._save(job_id, record)
        return record

    def update(self, job_id: str, **fields: Any) -> dict | None:
        record = self.get(job_id)
        if record is None:
            record = self.create(job_id, task_name=fields.get("task_name", "unknown"))
        record.update(fields)
        record["updated_at"] = time.time()
        self._save(job_id, record)
        return record

    def get(self, job_id: str) -> dict | None:
        if not self._redis:
            return None
        raw = self._redis.get(f"{JOB_PREFIX}{job_id}")
        if not raw:
            return None
        return json.loads(raw)

    def _save(self, job_id: str, record: dict) -> None:
        if not self._redis:
            return
        self._redis.setex(f"{JOB_PREFIX}{job_id}", self._ttl(), json.dumps(record, default=str))

    def push_dlq(self, job_id: str, *, task_name: str, error: str, payload: dict | None = None) -> None:
        if not self._redis:
            return
        entry = {
            "job_id": job_id,
            "task_name": task_name,
            "error": error,
            "payload": payload or {},
            "failed_at": time.time(),
        }
        self._redis.lpush(f"{DLQ_PREFIX}{task_name}", json.dumps(entry, default=str))
        self._redis.ltrim(f"{DLQ_PREFIX}{task_name}", 0, 499)
        self.update(job_id, status="failed", error=error)


_job_store = JobStore()


def get_job_store() -> JobStore:
    return _job_store
