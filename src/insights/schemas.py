from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class InsightType(str, Enum):
    PAIN_POINTS = "pain_points"
    FEATURE_REQUESTS = "feature_requests"
    PLATFORM_COMPARISON = "platform_comparison"
    TRENDS = "trends"
    SEGMENTS = "segments"
    THEMES = "themes"


VALID_INSIGHT_TYPES = {item.value for item in InsightType}


class Insight(BaseModel):
    insight_type: str
    title: str
    summary: str
    evidence_review_ids: list[UUID] = Field(default_factory=list)
    metrics: dict[str, Any] = Field(default_factory=dict)
    cache_key: str = "default"


class InsightResponse(BaseModel):
    insight_type: str
    title: str
    summary: str
    evidence_review_ids: list[UUID]
    metrics: dict[str, Any]
    generated_at: str
    cache_key: str = "default"


class InsightListResponse(BaseModel):
    count: int
    insights: list[InsightResponse]
