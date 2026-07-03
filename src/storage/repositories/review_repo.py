import uuid

from sqlalchemy import func
from sqlalchemy.orm import Query, Session

from src.storage.models import Review, ReviewEnrichment
from src.storage.repositories.schemas import PaginatedResult, Pagination, ReviewFilters, SortSpec


class ReviewRepository:
    """Data access for reviews with filtering, pagination, and keyword search."""

    _SORT_FIELDS = {
        "review_date": Review.review_date,
        "rating": Review.rating,
        "ingested_at": Review.ingested_at,
    }

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, review_id: uuid.UUID) -> Review | None:
        return self.db.query(Review).filter(Review.id == review_id).first()

    def _apply_filters(self, query: Query, filters: ReviewFilters) -> Query:
        if filters.source:
            query = query.filter(Review.source == filters.source)
        if filters.platform:
            query = query.filter(Review.platform == filters.platform)
        if filters.language:
            query = query.filter(Review.language == filters.language)
        if filters.min_rating is not None:
            query = query.filter(Review.rating >= filters.min_rating)
        if filters.max_rating is not None:
            query = query.filter(Review.rating <= filters.max_rating)
        if filters.review_date_from is not None:
            query = query.filter(Review.review_date >= filters.review_date_from)
        if filters.review_date_to is not None:
            query = query.filter(Review.review_date <= filters.review_date_to)
        if filters.keyword:
            tsquery = func.plainto_tsquery("english", filters.keyword)
            query = query.filter(Review.body_tsv.op("@@")(tsquery))
        return query

    def _needs_enrichment_join(self, filters: ReviewFilters) -> bool:
        return any(
            [
                filters.sentiment,
                filters.primary_topic,
                filters.pain_point,
                filters.user_segment,
            ]
        )

    def _apply_enrichment_filters(self, query: Query, filters: ReviewFilters) -> Query:
        if not self._needs_enrichment_join(filters):
            return query

        query = query.join(ReviewEnrichment, ReviewEnrichment.review_id == Review.id)
        if filters.sentiment:
            query = query.filter(ReviewEnrichment.sentiment == filters.sentiment)
        if filters.primary_topic:
            query = query.filter(ReviewEnrichment.primary_topic == filters.primary_topic)
        if filters.pain_point:
            query = query.filter(ReviewEnrichment.pain_point == filters.pain_point)
        if filters.user_segment:
            query = query.filter(ReviewEnrichment.user_segment == filters.user_segment)
        return query.distinct()

    def _build_query(self, filters: ReviewFilters | None = None) -> Query:
        filters = filters or ReviewFilters()
        query = self.db.query(Review)
        query = self._apply_filters(query, filters)
        query = self._apply_enrichment_filters(query, filters)
        return query

    def count(self, filters: ReviewFilters | None = None) -> int:
        filters = filters or ReviewFilters()
        if self._needs_enrichment_join(filters):
            return (
                self._build_query(filters)
                .with_entities(func.count(func.distinct(Review.id)))
                .scalar()
                or 0
            )
        return self._build_query(filters).count()

    def list(
        self,
        filters: ReviewFilters | None = None,
        pagination: Pagination | None = None,
        sort: SortSpec | None = None,
    ) -> PaginatedResult:
        filters = filters or ReviewFilters()
        pagination = pagination or Pagination()
        sort = sort or SortSpec()

        query = self._build_query(filters)
        total = self.count(filters)

        sort_column = self._SORT_FIELDS.get(sort.field, Review.review_date)
        order = sort_column.desc() if sort.descending else sort_column.asc()
        items = (
            query.order_by(order)
            .offset(pagination.offset)
            .limit(pagination.page_size)
            .all()
        )

        return PaginatedResult(
            items=items,
            total=total,
            page=max(pagination.page, 1),
            page_size=pagination.page_size,
        )
