"""Add tsvector full-text search column on reviews.body."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("reviews", sa.Column("body_tsv", postgresql.TSVECTOR(), nullable=True))
    op.execute("UPDATE reviews SET body_tsv = to_tsvector('english', coalesce(body, ''))")
    op.create_index("ix_reviews_body_tsv", "reviews", ["body_tsv"], unique=False, postgresql_using="gin")
    op.execute(
        """
        CREATE OR REPLACE FUNCTION reviews_body_tsv_update() RETURNS trigger AS $$
        BEGIN
            NEW.body_tsv := to_tsvector('english', coalesce(NEW.body, ''));
            RETURN NEW;
        END
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_reviews_body_tsv_update
        BEFORE INSERT OR UPDATE OF body ON reviews
        FOR EACH ROW EXECUTE FUNCTION reviews_body_tsv_update();
        """
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_reviews_body_tsv_update ON reviews")
    op.execute("DROP FUNCTION IF EXISTS reviews_body_tsv_update()")
    op.drop_index("ix_reviews_body_tsv", table_name="reviews")
    op.drop_column("reviews", "body_tsv")
