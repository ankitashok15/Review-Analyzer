import logging
import uuid

from celery.exceptions import MaxRetriesExceededError

from src.embeddings.embedder import DEFAULT_CONCURRENCY as EMBED_CONCURRENCY
from src.embeddings.embedder import MODEL_VERSION as EMBED_MODEL_VERSION
from src.embeddings.embedder import EmbeddingService
from src.enrichment.enricher import DEFAULT_CONCURRENCY as ENRICH_CONCURRENCY
from src.enrichment.enricher import MODEL_VERSION as ENRICH_MODEL_VERSION
from src.enrichment.enricher import EnrichmentService
from src.observability.logging_config import log_duration
from src.observability.metrics import get_metrics
from src.storage.database import SessionLocal
from src.storage.models import Review
from src.workers.celery_app import celery_app

logger = logging.getLogger(__name__)
MAX_RETRIES = 3


def _run_with_metrics(operation: str, func):
    import time

    started = time.perf_counter()
    try:
        result = func()
        get_metrics().increment(f"{operation}_success")
        log_duration(logger, operation, started)
        return result
    except Exception:
        get_metrics().increment(f"{operation}_failed")
        raise


@celery_app.task(
    name="enrich_reviews_task",
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=60,
    retry_kwargs={"max_retries": MAX_RETRIES},
)
def enrich_reviews_task(
    self,
    review_ids: list[str] | None = None,
    limit: int | None = None,
    model_version: str = ENRICH_MODEL_VERSION,
    concurrency: int = ENRICH_CONCURRENCY,
) -> dict:
    db = SessionLocal()
    try:
        service = EnrichmentService(db)
        if review_ids:
            ids = [uuid.UUID(rid) for rid in review_ids]
            reviews = db.query(Review).filter(Review.id.in_(ids)).all()
        else:
            reviews = service.get_unenriched_reviews(limit=limit, model_version=model_version)

        result = _run_with_metrics(
            "enrichment",
            lambda: service.enrich_batch(reviews, concurrency=concurrency, model_version=model_version),
        )
        return {
            "enriched": result.enriched,
            "skipped": result.skipped,
            "failed": result.failed,
            "errors": result.errors[:5],
        }
    except MaxRetriesExceededError:
        raise
    except Exception as exc:
        logger.warning("enrich_reviews_task retry %s/%s: %s", self.request.retries, MAX_RETRIES, exc)
        raise
    finally:
        db.close()


@celery_app.task(name="enrich_pending_task")
def enrich_pending_task(limit: int = 100, concurrency: int = ENRICH_CONCURRENCY) -> dict:
    return enrich_reviews_task(limit=limit, concurrency=concurrency)


@celery_app.task(
    name="embed_reviews_task",
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=60,
    retry_kwargs={"max_retries": MAX_RETRIES},
)
def embed_reviews_task(
    self,
    review_ids: list[str] | None = None,
    limit: int | None = None,
    model_version: str = EMBED_MODEL_VERSION,
    concurrency: int = EMBED_CONCURRENCY,
) -> dict:
    db = SessionLocal()
    try:
        service = EmbeddingService(db)
        if review_ids:
            ids = [uuid.UUID(rid) for rid in review_ids]
            reviews = db.query(Review).filter(Review.id.in_(ids)).all()
            result = _run_with_metrics(
                "embed",
                lambda: service.embed_batch(reviews, concurrency=concurrency, model_version=model_version),
            )
        else:
            result = _run_with_metrics(
                "embed",
                lambda: service.run(
                    limit=limit,
                    embed_all=limit is None,
                    concurrency=concurrency,
                    model_version=model_version,
                ),
            )

        logger.info(
            "embed_reviews_task complete — embedded=%s skipped=%s cached=%s failed=%s",
            result.embedded,
            result.skipped,
            result.cached,
            result.failed,
        )
        return {
            "embedded": result.embedded,
            "skipped": result.skipped,
            "cached": result.cached,
            "failed": result.failed,
            "errors": result.errors[:5],
        }
    except MaxRetriesExceededError:
        raise
    except Exception as exc:
        logger.warning("embed_reviews_task retry %s/%s: %s", self.request.retries, MAX_RETRIES, exc)
        raise
    finally:
        db.close()


@celery_app.task(name="embed_pending_task")
def embed_pending_task(limit: int = 100, concurrency: int = EMBED_CONCURRENCY) -> dict:
    return embed_reviews_task(limit=limit, concurrency=concurrency)


@celery_app.task(name="refresh_insights_task")
def refresh_insights_task() -> dict:
    db = SessionLocal()
    try:
        from src.cache.insight_cache import insight_list_cache
        from src.insights.service import InsightService

        service = InsightService(db, gemini_client=None)
        insights = service.refresh_cache()
        insight_list_cache.invalidate()
        return {"refreshed": len(insights), "types": [item.insight_type for item in insights]}
    finally:
        db.close()
