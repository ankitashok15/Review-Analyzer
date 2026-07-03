import uuid
from datetime import datetime, timedelta, timezone

import pytest

from src.insights.service import InsightService
from src.storage.database import SessionLocal
from src.storage.models import InsightCache, Review, ReviewEnrichment


def _sample_review(**overrides) -> Review:
    review_id = overrides.pop("id", uuid.uuid4())
    return Review(
        id=review_id,
        source=overrides.pop("source", "test_insights"),
        source_id=overrides.pop("source_id", f"ins-{review_id.hex[:8]}"),
        app_name="Spotify",
        platform=overrides.pop("platform", "android"),
        body=overrides.pop("body", "Offline downloads fail constantly."),
        language="en",
        rating=overrides.pop("rating", 2),
        review_date=overrides.pop(
            "review_date",
            datetime.now(timezone.utc) - timedelta(days=overrides.pop("days_ago", 5)),
        ),
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
        feature_request=overrides.pop("feature_request", "offline mode"),
        user_segment=overrides.pop("user_segment", "premium user"),
        summary=overrides.pop("summary", "User wants reliable offline playback."),
        model_version="enrichment-v1",
        **overrides,
    )


@pytest.fixture
def insight_db():
    db = SessionLocal()
    review_ids: list[uuid.UUID] = []
    yield db, review_ids
    db.query(InsightCache).filter(
        InsightCache.insight_type.in_(InsightService.STANDARD_TYPES)
    ).delete(synchronize_session=False)
    for review_id in review_ids:
        db.query(ReviewEnrichment).filter(ReviewEnrichment.review_id == review_id).delete()
        db.query(Review).filter(Review.id == review_id).delete()
    db.commit()
    db.close()


def _seed_pain_point_cluster(db, review_ids: list[uuid.UUID], *, count: int = 3):
    for _ in range(count):
        review = _sample_review(source="test_insights")
        enrichment = _sample_enrichment(
            review.id,
            pain_point="offline downloads",
            feature_request="download playlists",
            primary_topic="playback",
        )
        db.add_all([review, enrichment])
        review_ids.append(review.id)
    db.commit()


def test_pain_points_insight_has_evidence(insight_db):
    db, review_ids = insight_db
    _seed_pain_point_cluster(db, review_ids, count=4)

    service = InsightService(db)
    insight = service.generate("pain_points")
    assert insight.insight_type == "pain_points"
    assert len(insight.evidence_review_ids) >= 3
    assert insight.metrics["items"][0]["count"] >= 3
    assert len(insight.metrics["items"][0]["evidence_review_ids"]) >= 3


def test_feature_requests_insight_has_evidence(insight_db):
    db, review_ids = insight_db
    _seed_pain_point_cluster(db, review_ids, count=3)

    service = InsightService(db)
    insight = service.generate("feature_requests")
    assert len(insight.evidence_review_ids) >= 3


def test_trends_insight_has_period_comparison(insight_db):
    db, review_ids = insight_db
    for days_ago in (5, 10, 40, 45):
        review = _sample_review(source="test_insights", days_ago=days_ago)
        enrichment = _sample_enrichment(review.id, primary_topic="discovery")
        db.add_all([review, enrichment])
        review_ids.append(review.id)
    db.commit()

    service = InsightService(db)
    insight = service.generate("trends", {"window_days": 30})
    assert insight.insight_type == "trends"
    assert "window_days" in insight.metrics
    assert isinstance(insight.metrics["items"], list)


def test_refresh_cache_does_not_duplicate_entries(insight_db):
    db, review_ids = insight_db
    _seed_pain_point_cluster(db, review_ids, count=3)

    service = InsightService(db)
    service.generate("pain_points")
    service.generate("pain_points")
    rows = db.query(InsightCache).filter(InsightCache.insight_type == "pain_points").all()
    assert len(rows) == 1


def test_insights_api_list_and_get(client, insight_db):
    db, review_ids = insight_db
    _seed_pain_point_cluster(db, review_ids, count=3)

    service = InsightService(db)
    service.refresh_cache()

    list_response = client.get("/api/v1/insights")
    assert list_response.status_code == 200
    assert list_response.json()["count"] >= 1

    detail_response = client.get("/api/v1/insights/pain_points")
    assert detail_response.status_code == 200
    data = detail_response.json()
    assert data["insight_type"] == "pain_points"
    assert len(data["evidence_review_ids"]) >= 3


def test_insights_api_unknown_type_returns_404(client):
    response = client.get("/api/v1/insights/not_a_real_type")
    assert response.status_code == 404
