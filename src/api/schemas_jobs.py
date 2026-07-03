from pydantic import BaseModel, Field


class JobResponse(BaseModel):
    job_id: str
    task_name: str
    status: str
    payload: dict = Field(default_factory=dict)
    result: dict | None = None
    error: str | None = None
    created_at: float | None = None
    updated_at: float | None = None


class MetricsResponse(BaseModel):
    counters: dict[str, float]
    enrichment_success_rate: float | None = None
