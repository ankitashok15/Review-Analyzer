import uuid
from dataclasses import dataclass, field
from datetime import datetime

from src.storage.models import Review, ReviewEnrichment


@dataclass
class ReviewFilters:
    source: str | None = None
    platform: str | None = None
    language: str | None = None
    min_rating: int | None = None
    max_rating: int | None = None
    review_date_from: datetime | None = None
    review_date_to: datetime | None = None
    keyword: str | None = None
    sentiment: str | None = None
    primary_topic: str | None = None
    pain_point: str | None = None
    user_segment: str | None = None


@dataclass
class Pagination:
    page: int = 1
    page_size: int = 20

    @property
    def offset(self) -> int:
        page = max(self.page, 1)
        return (page - 1) * self.page_size


@dataclass
class SortSpec:
    field: str = "review_date"
    descending: bool = True


@dataclass
class PaginatedResult:
    items: list
    total: int
    page: int
    page_size: int


@dataclass
class ReviewDetail:
    review: Review
    enrichment: ReviewEnrichment | None = None


@dataclass
class SentimentSegmentAggregate:
    user_segment: str | None
    sentiment: str | None
    count: int


@dataclass
class SentimentBySegmentResult:
    aggregates: list[SentimentSegmentAggregate] = field(default_factory=list)
