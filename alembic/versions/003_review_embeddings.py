"""Review embeddings table with pgvector HNSW index."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "review_embeddings",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("review_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("embedding", Vector(768), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("model_version", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["review_id"], ["reviews.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "review_id",
            "chunk_index",
            "model_version",
            name="uq_embedding_review_chunk_model",
        ),
    )
    op.create_index("ix_review_embeddings_review_id", "review_embeddings", ["review_id"], unique=False)
    op.create_index("ix_review_embeddings_content_hash", "review_embeddings", ["content_hash"], unique=False)
    op.execute(
        """
        CREATE INDEX ix_review_embeddings_embedding_hnsw
        ON review_embeddings
        USING hnsw (embedding vector_cosine_ops)
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_review_embeddings_embedding_hnsw")
    op.drop_index("ix_review_embeddings_content_hash", table_name="review_embeddings")
    op.drop_index("ix_review_embeddings_review_id", table_name="review_embeddings")
    op.drop_table("review_embeddings")
