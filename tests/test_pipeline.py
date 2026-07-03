from datetime import datetime, timezone
from pathlib import Path

import pytest
from sqlalchemy.orm import Session

from src.ingestion.schemas import ReviewCreate
from src.ingestion.utils import compute_content_hash
from src.pipeline.cleaner import clean_review, strip_html
from src.pipeline.deduplicator import check_duplicates
from src.pipeline.normalizer import normalize_review
from src.pipeline.orchestrator import PipelineOrchestrator
from src.pipeline.schemas import PipelineStatus
from src.pipeline.validator import validate_review
from src.storage.database import SessionLocal
from src.storage.models import IngestionError, Review


def _sample_review(**overrides) -> ReviewCreate:
    data = {
        "source": "google_play",
        "source_id": "test-review-1",
        "body": "Spotify keeps playing the same songs every week.",
        "review_date": datetime(2024, 5, 9, 16, 28, 13, tzinfo=timezone.utc),
        "content_hash": compute_content_hash("Spotify keeps playing the same songs every week."),
        "platform": "android",
    }
    data.update(overrides)
    return ReviewCreate(**data)


def test_empty_body_is_rejected():
    review = _sample_review(body="   ", content_hash=compute_content_hash(""))
    result = validate_review(review)
    assert result.valid is False
    assert result.reason_code == "EMPTY_BODY"


def test_body_too_short_is_rejected():
    review = _sample_review(body="Too short", content_hash=compute_content_hash("Too short"))
    result = validate_review(review)
    assert result.valid is False
    assert result.reason_code == "BODY_TOO_SHORT"


def test_html_is_stripped_without_mutating_original():
    review = _sample_review(body="<p>Great <b>music</b> discovery app!</p>")
    cleaned, is_spam, _ = clean_review(review)
    assert review.body.startswith("<p>")
    assert is_spam is False
    assert cleaned.body == "Great music discovery app!"


def test_duplicate_content_hash_detected(db: Session):
    review = _sample_review(source_id="dup-1")
    db.add(
        Review(
            id=review.to_review_id(),
            source=review.source,
            source_id=review.source_id,
            app_name="Spotify",
            platform=review.platform,
            body=review.body,
            language="en",
            review_date=review.review_date,
            content_hash=review.content_hash,
            source_metadata={},
        )
    )
    db.commit()

    duplicate = _sample_review(source_id="dup-2")
    reason = check_duplicates(db, duplicate)
    assert reason == "DUPLICATE_CONTENT_HASH"

    db.query(Review).filter(Review.source_id.in_(["dup-1", "dup-2"])).delete()
    db.commit()


def test_pipeline_rejects_invalid_rating_and_logs_error():
    db = SessionLocal()
    try:
        review = _sample_review(source_id="pipeline-reject-rating", rating=9)
        orchestrator = PipelineOrchestrator(db)
        outcome = orchestrator.process(review)
        assert outcome.status == PipelineStatus.REJECTED
        assert outcome.reason_code == "INVALID_RATING"
        db.commit()

        logged = db.query(IngestionError).filter(IngestionError.source_id == "pipeline-reject-rating").first()
        assert logged is not None
        db.query(IngestionError).filter(IngestionError.source_id == "pipeline-reject-rating").delete()
        db.commit()
    finally:
        db.close()


def test_pipeline_orchestrator_accepts_valid_review():
    db = SessionLocal()
    try:
        review = _sample_review(source_id="pipeline-accept-1")
        orchestrator = PipelineOrchestrator(db)
        outcome = orchestrator.process(review)
        assert outcome.status == PipelineStatus.ACCEPTED
        assert outcome.review is not None
        assert outcome.review.language
    finally:
        db.close()


@pytest.fixture
def db() -> Session:
    session = SessionLocal()
    yield session
    session.close()
