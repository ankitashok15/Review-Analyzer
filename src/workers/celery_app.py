from celery import Celery
from celery.signals import task_failure, task_postrun, task_prerun

from config.settings import get_settings
from src.observability.metrics import get_job_store, get_metrics

settings = get_settings()

celery_app = Celery(
    "review_engine",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["src.workers.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_default_retry_delay=2,
)


@task_prerun.connect
def on_task_prerun(sender=None, task_id=None, task=None, **kwargs):
    store = get_job_store()
    store.create(
        task_id,
        task_name=sender.name if sender else "unknown",
        payload=kwargs.get("kwargs"),
    )
    store.update(task_id, status="running")


@task_postrun.connect
def on_task_postrun(sender=None, task_id=None, retval=None, state=None, **kwargs):
    store = get_job_store()
    if state == "SUCCESS":
        store.update(task_id, status="completed", result=retval if isinstance(retval, dict) else {"value": retval})
    elif state == "FAILURE":
        store.update(task_id, status="failed", error=str(retval))


@task_failure.connect
def on_task_failure(sender=None, task_id=None, exception=None, kwargs=None, **other):
    task_name = sender.name if sender else "unknown"
    get_metrics().increment("enrichment_failed" if "enrich" in task_name else "embed_failed")
    get_job_store().push_dlq(
        task_id,
        task_name=task_name,
        error=str(exception),
        payload=kwargs or {},
    )
