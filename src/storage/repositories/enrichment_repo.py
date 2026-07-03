import uuid

from sqlalchemy import func
from sqlalchemy.orm import Session

from src.storage.models import ReviewEnrichment
from src.storage.repositories.schemas import SentimentBySegmentResult, SentimentSegmentAggregate


class EnrichmentRepository:
    """Data access for review enrichment metadata."""

    def __init__(self, db: Session):
        self.db = db

    def get_by_review_id(
        self,
        review_id: uuid.UUID,
        *,
        model_version: str | None = None,
    ) -> ReviewEnrichment | None:
        query = self.db.query(ReviewEnrichment).filter(ReviewEnrichment.review_id == review_id)
        if model_version:
            query = query.filter(ReviewEnrichment.model_version == model_version)
        return query.order_by(ReviewEnrichment.enriched_at.desc()).first()

    def list_by_topic(self, topic: str, *, limit: int = 100) -> list[ReviewEnrichment]:
        return (
            self.db.query(ReviewEnrichment)
            .filter(ReviewEnrichment.primary_topic == topic)
            .order_by(ReviewEnrichment.enriched_at.desc())
            .limit(limit)
            .all()
        )

    def list_by_pain_point(self, pain_point: str, *, limit: int = 100) -> list[ReviewEnrichment]:
        return (
            self.db.query(ReviewEnrichment)
            .filter(ReviewEnrichment.pain_point == pain_point)
            .order_by(ReviewEnrichment.enriched_at.desc())
            .limit(limit)
            .all()
        )

    def aggregate_sentiment_by_segment(self) -> SentimentBySegmentResult:
        rows = (
            self.db.query(
                ReviewEnrichment.user_segment,
                ReviewEnrichment.sentiment,
                func.count(ReviewEnrichment.id),
            )
            .group_by(ReviewEnrichment.user_segment, ReviewEnrichment.sentiment)
            .order_by(func.count(ReviewEnrichment.id).desc())
            .all()
        )
        aggregates = [
            SentimentSegmentAggregate(
                user_segment=segment,
                sentiment=sentiment,
                count=count,
            )
            for segment, sentiment, count in rows
        ]
        return SentimentBySegmentResult(aggregates=aggregates)
