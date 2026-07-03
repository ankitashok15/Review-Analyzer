import uuid
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.storage.database import Base


class Review(Base):
    __tablename__ = "reviews"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source: Mapped[str] = mapped_column(String(50), nullable=False)
    source_id: Mapped[str] = mapped_column(String(255), nullable=False)
    source_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    app_name: Mapped[str] = mapped_column(String(100), nullable=False, default="Spotify")
    platform: Mapped[str] = mapped_column(String(50), nullable=False, default="unknown")
    author_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    rating: Mapped[int | None] = mapped_column(Integer, nullable=True)
    title: Mapped[str | None] = mapped_column(String(500), nullable=True)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    body_tsv: Mapped[object | None] = mapped_column(TSVECTOR, nullable=True)
    language: Mapped[str] = mapped_column(String(10), nullable=False, default="en")
    review_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ingested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    source_metadata: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    enrichment: Mapped[list["ReviewEnrichment"]] = relationship(
        "ReviewEnrichment", back_populates="review", uselist=True
    )
    embeddings: Mapped[list["ReviewEmbedding"]] = relationship(
        "ReviewEmbedding", back_populates="review", uselist=True
    )

    __table_args__ = (
        UniqueConstraint("source", "source_id", name="uq_reviews_source_source_id"),
        Index("ix_reviews_source_review_date", "source", "review_date"),
        Index("ix_reviews_content_hash", "content_hash"),
    )


class ReviewEnrichment(Base):
    __tablename__ = "review_enrichments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    review_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("reviews.id", ondelete="CASCADE"), nullable=False
    )
    sentiment: Mapped[str | None] = mapped_column(String(20), nullable=True)
    emotion: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    primary_topic: Mapped[str | None] = mapped_column(String(100), nullable=True)
    user_goal: Mapped[str | None] = mapped_column(String(255), nullable=True)
    pain_point: Mapped[str | None] = mapped_column(String(255), nullable=True)
    feature_request: Mapped[str | None] = mapped_column(String(255), nullable=True)
    discovery_issue: Mapped[str | None] = mapped_column(String(255), nullable=True)
    listening_behavior: Mapped[str | None] = mapped_column(String(255), nullable=True)
    user_segment: Mapped[str | None] = mapped_column(String(100), nullable=True)
    keywords: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    model_version: Mapped[str] = mapped_column(String(50), nullable=False)
    enriched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    review: Mapped["Review"] = relationship("Review", back_populates="enrichment")

    __table_args__ = (
        UniqueConstraint("review_id", "model_version", name="uq_enrichment_review_model_version"),
        Index("ix_review_enrichments_primary_topic", "primary_topic"),
        Index("ix_review_enrichments_pain_point", "pain_point"),
        Index("ix_review_enrichments_user_segment", "user_segment"),
        Index("ix_review_enrichments_sentiment", "sentiment"),
    )


class IngestionError(Base):
    __tablename__ = "ingestion_errors"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source: Mapped[str] = mapped_column(String(50), nullable=False)
    source_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    reason_code: Mapped[str] = mapped_column(String(100), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    raw_payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (Index("ix_ingestion_errors_source_created_at", "source", "created_at"),)


class EnrichmentError(Base):
    __tablename__ = "enrichment_errors"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    review_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("reviews.id", ondelete="CASCADE"), nullable=False
    )
    model_version: Mapped[str] = mapped_column(String(50), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (Index("ix_enrichment_errors_review_id", "review_id"),)


class ReviewEmbedding(Base):
    __tablename__ = "review_embeddings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    review_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("reviews.id", ondelete="CASCADE"), nullable=False
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    embedding: Mapped[list] = mapped_column(Vector(768), nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    model_version: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    review: Mapped["Review"] = relationship("Review", back_populates="embeddings")

    __table_args__ = (
        UniqueConstraint(
            "review_id",
            "chunk_index",
            "model_version",
            name="uq_embedding_review_chunk_model",
        ),
        Index("ix_review_embeddings_review_id", "review_id"),
        Index("ix_review_embeddings_content_hash", "content_hash"),
    )


class InsightCache(Base):
    __tablename__ = "insights_cache"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    insight_type: Mapped[str] = mapped_column(String(50), nullable=False)
    cache_key: Mapped[str] = mapped_column(String(100), nullable=False, default="default")
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_review_ids: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    metrics: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        UniqueConstraint("insight_type", "cache_key", name="uq_insights_cache_type_key"),
        Index("ix_insights_cache_insight_type", "insight_type"),
    )
