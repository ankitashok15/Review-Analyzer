import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class ReviewCreate(BaseModel):
    """Canonical review payload before persistence."""

    source: str
    source_id: str
    body: str
    review_date: datetime
    app_name: str = "Spotify"
    platform: str = "unknown"
    source_url: str | None = None
    author_hash: str | None = None
    rating: int | None = None
    title: str | None = None
    language: str = "en"
    content_hash: str
    source_metadata: dict = Field(default_factory=dict)

    def to_review_id(self) -> uuid.UUID:
        return uuid.uuid4()
