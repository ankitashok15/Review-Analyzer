import uuid

from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from src.embeddings.schemas import EmbeddingFilters, EmbeddingRecord, ScoredResult
from src.storage.models import Review, ReviewEmbedding, ReviewEnrichment


class VectorStore:
    """pgvector-backed storage and similarity search."""

    def __init__(self, db: Session):
        self.db = db

    def upsert_embeddings(self, records: list[EmbeddingRecord]) -> int:
        if not records:
            return 0

        inserted = 0
        for record in records:
            existing = (
                self.db.query(ReviewEmbedding)
                .filter(
                    ReviewEmbedding.review_id == record.review_id,
                    ReviewEmbedding.chunk_index == record.chunk_index,
                    ReviewEmbedding.model_version == record.model_version,
                )
                .first()
            )
            if existing:
                continue

            self.db.add(
                ReviewEmbedding(
                    id=uuid.uuid4(),
                    review_id=record.review_id,
                    chunk_index=record.chunk_index,
                    embedding=record.embedding,
                    content_hash=record.content_hash,
                    model_version=record.model_version,
                )
            )
            inserted += 1
        return inserted

    def similarity_search(
        self,
        query_vector: list[float],
        *,
        top_k: int = 10,
        model_version: str | None = None,
        filters: EmbeddingFilters | None = None,
    ) -> list[ScoredResult]:
        distance = ReviewEmbedding.embedding.cosine_distance(query_vector)
        score = (1 - distance).label("score")

        stmt = (
            select(ReviewEmbedding, Review, score)
            .join(Review, Review.id == ReviewEmbedding.review_id)
            .order_by(distance)
            .limit(top_k)
        )

        if model_version:
            stmt = stmt.where(ReviewEmbedding.model_version == model_version)

        filters = filters or EmbeddingFilters()
        if filters.source:
            stmt = stmt.where(Review.source == filters.source)
        if filters.platform:
            stmt = stmt.where(Review.platform == filters.platform)
        if filters.min_rating is not None:
            stmt = stmt.where(Review.rating >= filters.min_rating)
        if filters.max_rating is not None:
            stmt = stmt.where(Review.rating <= filters.max_rating)
        if filters.review_date_from is not None:
            stmt = stmt.where(Review.review_date >= filters.review_date_from)
        if filters.review_date_to is not None:
            stmt = stmt.where(Review.review_date <= filters.review_date_to)

        if filters.sentiment:
            stmt = stmt.join(
                ReviewEnrichment,
                and_(
                    ReviewEnrichment.review_id == Review.id,
                    ReviewEnrichment.sentiment == filters.sentiment,
                ),
            )

        rows = self.db.execute(stmt).all()
        results: list[ScoredResult] = []

        for embedding_row, review, similarity_score in rows:
            enrichment = (
                self.db.query(ReviewEnrichment)
                .filter(ReviewEnrichment.review_id == review.id)
                .order_by(ReviewEnrichment.enriched_at.desc())
                .first()
            )
            results.append(
                ScoredResult(
                    review_id=review.id,
                    chunk_index=embedding_row.chunk_index,
                    score=float(similarity_score),
                    chunk_text=None,
                    review=review,
                    enrichment=enrichment,
                )
            )

        return results
