"""Insights cache table for precomputed product insights."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "insights_cache",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("insight_type", sa.String(length=50), nullable=False),
        sa.Column("cache_key", sa.String(length=100), nullable=False, server_default="default"),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("evidence_review_ids", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("metrics", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("generated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("insight_type", "cache_key", name="uq_insights_cache_type_key"),
    )
    op.create_index("ix_insights_cache_insight_type", "insights_cache", ["insight_type"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_insights_cache_insight_type", table_name="insights_cache")
    op.drop_table("insights_cache")
