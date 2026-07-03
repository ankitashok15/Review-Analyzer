import uuid
from datetime import datetime, timezone
from unittest.mock import patch

import pytest
from src.storage.database import SessionLocal
from src.storage.models import Review, ReviewEnrichment


def _sample_review(**overrides) -> Review:
    review_id = overrides.pop("id", uuid.uuid4())
    return Review(
        id=review_id,
        source=overrides.pop("source", "test_api9"),
        source_id=overrides.pop("source_id", f"api9-{review_id.hex[:8]}"),
        app_name="Spotify",
        platform=overrides.pop("platform", "android"),
        body=overrides.pop("body", "Discover Weekly keeps repeating the same songs."),
        language="en",
        rating=overrides.pop("rating", 2),
        review_date=overrides.pop("review_date", datetime(2024, 6, 1, tzinfo=timezone.utc)),
        content_hash=overrides.pop("content_hash", f"hash-{review_id.hex[:8]}"),
        source_metadata={},
        **overrides,
    )


@pytest.fixture
def api9_db():
    db = SessionLocal()
    review_ids: list[uuid.UUID] = []
    yield db, review_ids
    for review_id in review_ids:
        db.query(ReviewEnrichment).filter(ReviewEnrichment.review_id == review_id).delete()
        db.query(Review).filter(Review.id == review_id).delete()
    db.commit()
    db.close()


def test_get_review_detail(api9_db, client):
    db, review_ids = api9_db
    review = _sample_review()
    enrichment = ReviewEnrichment(
        id=uuid.uuid4(),
        review_id=review.id,
        sentiment="negative",
        primary_topic="discovery",
        pain_point="repetitive playlists",
        summary="User finds recommendations repetitive.",
        model_version="enrichment-v1",
    )
    db.add_all([review, enrichment])
    db.commit()
    review_ids.append(review.id)

    response = client.get(f"/api/v1/reviews/{review.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(review.id)
    assert data["enrichment"]["primary_topic"] == "discovery"


def test_get_review_not_found(client):
    response = client.get(f"/api/v1/reviews/{uuid.uuid4()}")
    assert response.status_code == 404


def test_list_topics(api9_db, client):
    db, review_ids = api9_db
    review = _sample_review()
    enrichment = ReviewEnrichment(
        id=uuid.uuid4(),
        review_id=review.id,
        primary_topic="discovery",
        model_version="enrichment-v1",
    )
    db.add_all([review, enrichment])
    db.commit()
    review_ids.append(review.id)

    response = client.get("/api/v1/topics")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] >= 1
    assert any(t["topic"] == "discovery" for t in data["topics"])


def test_list_segments(api9_db, client):
    db, review_ids = api9_db
    review = _sample_review()
    enrichment = ReviewEnrichment(
        id=uuid.uuid4(),
        review_id=review.id,
        user_segment="premium user",
        sentiment="negative",
        model_version="enrichment-v1",
    )
    db.add_all([review, enrichment])
    db.commit()
    review_ids.append(review.id)

    response = client.get("/api/v1/segments")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] >= 1


def test_export_json(api9_db, client, admin_headers):
    db, review_ids = api9_db
    review = _sample_review()
    db.add(review)
    db.commit()
    review_ids.append(review.id)

    response = client.post(
        "/api/v1/export",
        json={"format": "json", "review_ids": [str(review.id)]},
        headers=admin_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 1
    assert data["rows"][0]["review_id"] == str(review.id)


def test_export_csv(api9_db, client, admin_headers):
    db, review_ids = api9_db
    review = _sample_review()
    db.add(review)
    db.commit()
    review_ids.append(review.id)

    response = client.post(
        "/api/v1/export",
        json={"format": "csv", "review_ids": [str(review.id)]},
        headers=admin_headers,
    )
    assert response.status_code == 200
    assert "text/csv" in response.headers.get("content-type", "")
    assert "review_id" in response.text


def test_export_empty_ids_returns_400(client, admin_headers):
    response = client.post(
        "/api/v1/export",
        json={"format": "json", "review_ids": []},
        headers=admin_headers,
    )
    assert response.status_code == 400


@patch("src.api.routes.ingest.IngestionService")
def test_ingest_endpoint(mock_service_cls, client, admin_headers):
    mock_result = type(
        "R",
        (),
        {
            "inserted": 10,
            "skipped": 0,
            "rejected": 0,
            "duplicates": 2,
            "failed": 0,
            "errors": [],
        },
    )()
    mock_service_cls.return_value.run.return_value = mock_result

    response = client.post(
        "/api/v1/ingest",
        json={"source": "csv", "limit": 10},
        headers=admin_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["inserted"] == 10
    assert data["duplicates"] == 2


def test_cors_headers(client):
    response = client.options(
        "/api/v1/search",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers
