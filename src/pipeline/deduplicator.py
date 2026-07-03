from sqlalchemy.orm import Session

from src.ingestion.schemas import ReviewCreate
from src.storage.models import Review


def is_duplicate_source(db: Session, review: ReviewCreate) -> bool:
    exists = (
        db.query(Review.id)
        .filter(Review.source == review.source, Review.source_id == review.source_id)
        .first()
    )
    return exists is not None


def is_duplicate_content(db: Session, content_hash: str) -> bool:
    exists = db.query(Review.id).filter(Review.content_hash == content_hash).first()
    return exists is not None


def check_duplicates(db: Session, review: ReviewCreate) -> str | None:
    """Return duplicate reason code or None if unique."""
    if is_duplicate_source(db, review):
        return "DUPLICATE_SOURCE_ID"
    if is_duplicate_content(db, review.content_hash):
        return "DUPLICATE_CONTENT_HASH"
    return None
