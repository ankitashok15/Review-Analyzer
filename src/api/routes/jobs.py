from fastapi import APIRouter, HTTPException

from src.api.schemas_jobs import JobResponse, MetricsResponse
from src.observability.metrics import get_metrics, get_job_store

router = APIRouter(prefix="/api/v1", tags=["jobs"])


@router.get("/jobs/{job_id}", response_model=JobResponse)
def get_job_status(job_id: str) -> JobResponse:
    record = get_job_store().get(job_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")
    return JobResponse(**record)


@router.get("/metrics", response_model=MetricsResponse)
def get_metrics_snapshot() -> MetricsResponse:
    metrics = get_metrics()
    return MetricsResponse(
        counters=metrics.snapshot(),
        enrichment_success_rate=metrics.enrichment_success_rate(),
    )
