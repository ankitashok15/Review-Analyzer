import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy import text

from src.storage.database import SessionLocal
from src.storage.models import Review, ReviewEnrichment
from src.storage.repositories.composite import CompositeRepository
from src.storage.repositories.enrichment_repo import EnrichmentRepository
from src.storage.repositories.review_repo import ReviewRepository
from src.storage.repositories.schemas import Pagination, ReviewFilters, SortSpec


def _sample_review(**overrides) -> Review:
    review_id = overrides.pop("id", uuid.uuid4())
    body = overrides.pop("body", "Spotify offline mode is broken and downloads fail.")
    return Review(
        id=review_id,
        source=overrides.pop("source", "test_repo"),
        source_id=overrides.pop("source_id", f"repo-{review_id.hex[:8]}"),
        app_name="Spotify",
        platform=overrides.pop("platform", "android"),
        body=body,
        language=overrides.pop("language", "en"),
        rating=overrides.pop("rating", 2),
        review_date=overrides.pop("review_date", datetime(2024, 6, 1, tzinfo=timezone.utc)),
        content_hash=overrides.pop("content_hash", f"hash-{review_id.hex[:8]}"),
        source_metadata={},
        **overrides,
    )


def _sample_enrichment(review_id: uuid.UUID, **overrides) -> ReviewEnrichment:
    return ReviewEnrichment(
        id=uuid.uuid4(),
        review_id=review_id,
        sentiment=overrides.pop("sentiment", "negative"),
        primary_topic=overrides.pop("primary_topic", "playback"),
        pain_point=overrides.pop("pain_point", "offline downloads"),
        user_segment=overrides.pop("user_segment", "premium user"),
        model_version=overrides.pop("model_version", "enrichment-v1"),
        **overrides,
    )


@pytest.fixture
def db_session():
    db = SessionLocal()
    created_review_ids: list[uuid.UUID] = []
    yield db, created_review_ids
    for review_id in created_review_ids:
        db.query(ReviewEnrichment).filter(ReviewEnrichment.review_id == review_id).delete()
        db.query(Review).filter(Review.id == review_id).delete()
    db.commit()
    db.close()


def test_get_by_id(db_session):
    db, created = db_session
    review = _sample_review()
    db.add(review)
    db.commit()
    created.append(review.id)

    repo = ReviewRepository(db)
    found = repo.get_by_id(review.id)
    assert found is not None
    assert found.id == review.id


def test_list_filters_and_pagination(db_session):
    db, created = db_session
    reviews = [
        _sample_review(source="test_repo", platform="android", rating=5),
        _sample_review(source="test_repo", platform="ios", rating=1),
        _sample_review(source="test_repo_other", platform="web", rating=3),
    ]
    db.add_all(reviews)
    db.commit()
    created.extend(review.id for review in reviews)

    repo = ReviewRepository(db)
    result = repo.list(
        filters=ReviewFilters(source="test_repo"),
        pagination=Pagination(page=1, page_size=1),
        sort=SortSpec(field="rating", descending=True),
    )
    assert result.total == 2
    assert len(result.items) == 1
    assert result.items[0].rating == 5


def test_keyword_filter(db_session):
    db, created = db_session
    review = _sample_review(body="Discover Weekly keeps repeating the same songs.", source="test_repo_kw")
    db.add(review)
    db.commit()
    created.append(review.id)
    db.execute(
        text("UPDATE reviews SET body_tsv = to_tsvector('english', body) WHERE id = :id"),
        {"id": review.id},
    )
    db.commit()

    repo = ReviewRepository(db)
    result = repo.list(filters=ReviewFilters(source="test_repo_kw", keyword="repeating songs"))
    assert result.total == 1
    assert result.items[0].id == review.id


def test_enrichment_repository(db_session):
    db, created = db_session
    review = _sample_review()
    enrichment = _sample_enrichment(review.id, primary_topic="discovery", pain_point="repetitive playlist")
    db.add_all([review, enrichment])
    db.commit()
    created.append(review.id)

    repo = EnrichmentRepository(db)
    assert repo.get_by_review_id(review.id) is not None
    assert len(repo.list_by_topic("discovery")) >= 1
    assert len(repo.list_by_pain_point("repetitive playlist")) >= 1
    aggregates = repo.aggregate_sentiment_by_segment()
    assert len(aggregates.aggregates) >= 1


def test_composite_review_detail(db_session):
    db, created = db_session
    review = _sample_review()
    enrichment = _sample_enrichment(review.id)
    db.add_all([review, enrichment])
    db.commit()
    created.append(review.id)

    repo = CompositeRepository(db)
    detail = repo.get_review_with_enrichment(review.id)
    assert detail is not None
    assert detail.review.id == review.id
    assert detail.enrichment is not None

    search = repo.search_reviews_with_enrichment(
        filters=ReviewFilters(sentiment="negative"),
        pagination=Pagination(page=1, page_size=10),
    )
    assert search.total >= 1
    assert all(hasattr(item, "review") for item in search.items)
