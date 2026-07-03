import uuid
from dataclasses import dataclass, field
from datetime import datetime

from src.storage.models import Review, ReviewEnrichment


@dataclass
class EmbeddingFilters:
    source: str | None = None
    platform: str | None = None
    sentiment: str | None = None
    min_rating: int | None = None
    max_rating: int | None = None
    review_date_from: datetime | None = None
    review_date_to: datetime | None = None


@dataclass
class ScoredResult:
    review_id: uuid.UUID
    chunk_index: int
    score: float
    chunk_text: str | None = None
    review: Review | None = None
    enrichment: ReviewEnrichment | None = None


@dataclass
class EmbeddingRecord:
    review_id: uuid.UUID
    chunk_index: int
    embedding: list[float]
    content_hash: str
    model_version: str


@dataclass
class EmbeddingResult:
    embedded: int = 0
    skipped: int = 0
    cached: int = 0
    failed: int = 0
    errors: list[str] = field(default_factory=list)
