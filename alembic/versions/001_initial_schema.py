"""Initial schema: reviews, enrichments, ingestion_errors, pgvector extension."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "reviews",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source", sa.String(length=50), nullable=False),
        sa.Column("source_id", sa.String(length=255), nullable=False),
        sa.Column("source_url", sa.String(length=2048), nullable=True),
        sa.Column("app_name", sa.String(length=100), nullable=False),
        sa.Column("platform", sa.String(length=50), nullable=False),
        sa.Column("author_hash", sa.String(length=64), nullable=True),
        sa.Column("rating", sa.Integer(), nullable=True),
        sa.Column("title", sa.String(length=500), nullable=True),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("language", sa.String(length=10), nullable=False),
        sa.Column("review_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ingested_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("source_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("source", "source_id", name="uq_reviews_source_source_id"),
    )
    op.create_index("ix_reviews_content_hash", "reviews", ["content_hash"], unique=False)
    op.create_index("ix_reviews_source_review_date", "reviews", ["source", "review_date"], unique=False)

    op.create_table(
        "review_enrichments",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("review_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("sentiment", sa.String(length=20), nullable=True),
        sa.Column("emotion", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("primary_topic", sa.String(length=100), nullable=True),
        sa.Column("user_goal", sa.String(length=255), nullable=True),
        sa.Column("pain_point", sa.String(length=255), nullable=True),
        sa.Column("feature_request", sa.String(length=255), nullable=True),
        sa.Column("discovery_issue", sa.String(length=255), nullable=True),
        sa.Column("listening_behavior", sa.String(length=255), nullable=True),
        sa.Column("user_segment", sa.String(length=100), nullable=True),
        sa.Column("keywords", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("confidence_score", sa.Float(), nullable=True),
        sa.Column("model_version", sa.String(length=50), nullable=False),
        sa.Column("enriched_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["review_id"], ["reviews.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("review_id"),
    )
    op.create_index("ix_review_enrichments_pain_point", "review_enrichments", ["pain_point"], unique=False)
    op.create_index("ix_review_enrichments_primary_topic", "review_enrichments", ["primary_topic"], unique=False)
    op.create_index("ix_review_enrichments_sentiment", "review_enrichments", ["sentiment"], unique=False)
    op.create_index("ix_review_enrichments_user_segment", "review_enrichments", ["user_segment"], unique=False)

    op.create_table(
        "ingestion_errors",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source", sa.String(length=50), nullable=False),
        sa.Column("source_id", sa.String(length=255), nullable=True),
        sa.Column("reason_code", sa.String(length=100), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("raw_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_ingestion_errors_source_created_at",
        "ingestion_errors",
        ["source", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_ingestion_errors_source_created_at", table_name="ingestion_errors")
    op.drop_table("ingestion_errors")
    op.drop_index("ix_review_enrichments_user_segment", table_name="review_enrichments")
    op.drop_index("ix_review_enrichments_sentiment", table_name="review_enrichments")
    op.drop_index("ix_review_enrichments_primary_topic", table_name="review_enrichments")
    op.drop_index("ix_review_enrichments_pain_point", table_name="review_enrichments")
    op.drop_table("review_enrichments")
    op.drop_index("ix_reviews_source_review_date", table_name="reviews")
    op.drop_index("ix_reviews_content_hash", table_name="reviews")
    op.drop_table("reviews")
