"""Enrichment errors table and composite unique on review enrichments."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint("review_enrichments_review_id_key", "review_enrichments", type_="unique")
    op.create_unique_constraint(
        "uq_enrichment_review_model_version",
        "review_enrichments",
        ["review_id", "model_version"],
    )

    op.create_table(
        "enrichment_errors",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("review_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("model_version", sa.String(length=50), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["review_id"], ["reviews.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_enrichment_errors_review_id", "enrichment_errors", ["review_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_enrichment_errors_review_id", table_name="enrichment_errors")
    op.drop_table("enrichment_errors")
    op.drop_constraint("uq_enrichment_review_model_version", "review_enrichments", type_="unique")
    op.create_unique_constraint("review_enrichments_review_id_key", "review_enrichments", ["review_id"])
