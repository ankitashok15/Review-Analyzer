import re
import uuid
from dataclasses import dataclass

from pydantic import BaseModel, Field


class SearchFilters(BaseModel):
    source: str | None = None
    platform: str | None = None
    language: str | None = None
    min_rating: int | None = Field(default=None, ge=1, le=5)
    max_rating: int | None = Field(default=None, ge=1, le=5)
    sentiment: str | None = None
    primary_topic: str | None = None
    pain_point: str | None = None
    user_segment: str | None = None


class SearchQuery(BaseModel):
    query: str
    filters: SearchFilters = Field(default_factory=SearchFilters)
    top_k: int = Field(default=10, ge=1, le=100)
    hybrid: bool = True


@dataclass
class SearchResult:
    review_id: uuid.UUID
    score: float
    excerpt: str
    highlight_offsets: list[int]
    source: str
    platform: str
    rating: int | None
    review_date: str
    source_url: str | None
    sentiment: str | None = None
    primary_topic: str | None = None
    summary: str | None = None


class SearchResultResponse(BaseModel):
    review_id: uuid.UUID
    score: float
    excerpt: str
    highlight_offsets: list[int]
    source: str
    platform: str
    rating: int | None
    review_date: str
    source_url: str | None = None
    sentiment: str | None = None
    primary_topic: str | None = None
    summary: str | None = None


class SearchResponse(BaseModel):
    query: str
    count: int
    results: list[SearchResultResponse]
