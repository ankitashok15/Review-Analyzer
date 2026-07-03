import uuid
from typing import Any, Literal

from pydantic import BaseModel, Field


class EnrichmentResponse(BaseModel):
    sentiment: str | None = None
    emotion: list[str] = Field(default_factory=list)
    primary_topic: str | None = None
    user_goal: str | None = None
    pain_point: str | None = None
    feature_request: str | None = None
    discovery_issue: str | None = None
    listening_behavior: str | None = None
    user_segment: str | None = None
    keywords: list[str] = Field(default_factory=list)
    summary: str | None = None
    confidence_score: float | None = None
    model_version: str | None = None


class ReviewDetailResponse(BaseModel):
    id: uuid.UUID
    source: str
    source_id: str
    source_url: str | None = None
    app_name: str
    platform: str
    rating: int | None = None
    title: str | None = None
    body: str
    language: str
    review_date: str
    ingested_at: str
    enrichment: EnrichmentResponse | None = None


class TopicCluster(BaseModel):
    topic: str
    count: int
    evidence_review_ids: list[uuid.UUID] = Field(default_factory=list)


class TopicsResponse(BaseModel):
    count: int
    topics: list[TopicCluster]


class SegmentRow(BaseModel):
    user_segment: str | None
    sentiment: str | None
    count: int
    evidence_review_ids: list[uuid.UUID] = Field(default_factory=list)


class SegmentsResponse(BaseModel):
    count: int
    segments: list[SegmentRow]


class ExportRequest(BaseModel):
    format: Literal["csv", "json"] = "json"
    review_ids: list[uuid.UUID] = Field(default_factory=list)
    include_enrichment: bool = True


class IngestRequest(BaseModel):
    source: str = "csv"
    file: str | None = None
    limit: int | None = Field(default=None, ge=1)
    skip_validation: bool = False


class IngestResponse(BaseModel):
    source: str
    file: str | None
    inserted: int
    skipped: int
    rejected: int
    duplicates: int
    failed: int
    errors: list[str] = Field(default_factory=list)


class ExportRow(BaseModel):
    review_id: uuid.UUID
    source: str
    platform: str
    rating: int | None
    review_date: str
    body: str
    sentiment: str | None = None
    primary_topic: str | None = None
    pain_point: str | None = None
    feature_request: str | None = None
    summary: str | None = None


class ExportResponse(BaseModel):
    format: str
    count: int
    rows: list[ExportRow]
    csv_content: str | None = None
