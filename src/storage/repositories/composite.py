import uuid

from sqlalchemy.orm import Session

from src.storage.repositories.enrichment_repo import EnrichmentRepository
from src.storage.repositories.review_repo import ReviewRepository
from src.storage.repositories.schemas import PaginatedResult, Pagination, ReviewDetail, ReviewFilters, SortSpec


class CompositeRepository:
    """Join queries across reviews and enrichments for API-ready responses."""

    def __init__(self, db: Session):
        self.db = db
        self.reviews = ReviewRepository(db)
        self.enrichments = EnrichmentRepository(db)

    def get_review_with_enrichment(
        self,
        review_id: uuid.UUID,
        *,
        model_version: str | None = None,
    ) -> ReviewDetail | None:
        review = self.reviews.get_by_id(review_id)
        if review is None:
            return None
        enrichment = self.enrichments.get_by_review_id(review_id, model_version=model_version)
        return ReviewDetail(review=review, enrichment=enrichment)

    def search_reviews_with_enrichment(
        self,
        filters: ReviewFilters | None = None,
        pagination: Pagination | None = None,
        sort: SortSpec | None = None,
        *,
        model_version: str | None = None,
    ) -> PaginatedResult:
        filters = filters or ReviewFilters()
        pagination = pagination or Pagination()
        sort = sort or SortSpec()

        result = self.reviews.list(filters=filters, pagination=pagination, sort=sort)
        details = []
        for review in result.items:
            enrichment = self.enrichments.get_by_review_id(review.id, model_version=model_version)
            details.append(ReviewDetail(review=review, enrichment=enrichment))

        return PaginatedResult(
            items=details,
            total=result.total,
            page=result.page,
            page_size=result.page_size,
        )
