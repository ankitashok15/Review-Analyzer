import json
import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from src.enrichment.enricher import MODEL_VERSION, EnrichmentService
from src.enrichment.schemas import EnrichmentOutput, Sentiment
from src.storage.database import SessionLocal
from src.storage.models import Review, ReviewEnrichment


def _sample_review(**overrides) -> Review:
    review_id = overrides.pop("id", uuid.uuid4())
    return Review(
        id=review_id,
        source="google_play",
        source_id=f"src-{review_id.hex[:8]}",
        app_name="Spotify",
        platform="android",
        body=overrides.pop("body", "Spotify keeps playing the same songs every week."),
        language="en",
        review_date=overrides.pop("review_date", datetime(2024, 5, 9, tzinfo=timezone.utc)),
        content_hash=overrides.pop("content_hash", "abc123"),
        source_metadata={},
        **overrides,
    )


MOCK_ENRICHMENT = EnrichmentOutput(
    sentiment=Sentiment.NEGATIVE,
    emotion=["frustration"],
    primary_topic="discovery",
    user_goal="find new music",
    pain_point="repetitive recommendations",
    feature_request=None,
    discovery_issue="Discover Weekly feels stale",
    listening_behavior="repeat listening",
    user_segment="casual listener",
    keywords=["repetitive", "discover weekly"],
    summary="User frustrated with repetitive recommendations.",
    confidence_score=0.88,
)


@patch("src.enrichment.enricher._call_gemini_for_review")
def test_enrichment_parses_and_persists(mock_gemini):
    mock_gemini.return_value = MOCK_ENRICHMENT
    db = SessionLocal()
    review = _sample_review()
    db.add(review)
    db.commit()

    try:
        service = EnrichmentService(db)
        enrichment = service.enrich_one(review)
        assert enrichment is not None
        db.add(enrichment)
        db.commit()

        stored = db.query(ReviewEnrichment).filter(ReviewEnrichment.review_id == review.id).first()
        assert stored is not None
        assert stored.sentiment == "negative"
        assert stored.primary_topic == "discovery"
        assert stored.model_version == MODEL_VERSION

        original_body = db.query(Review.body).filter(Review.id == review.id).scalar()
        assert original_body == review.body
    finally:
        db.query(ReviewEnrichment).filter(ReviewEnrichment.review_id == review.id).delete()
        db.query(Review).filter(Review.id == review.id).delete()
        db.commit()
        db.close()


@patch("src.enrichment.enricher._call_gemini_for_review")
def test_skip_already_enriched(mock_gemini):
    mock_gemini.return_value = MOCK_ENRICHMENT
    db = SessionLocal()
    review = _sample_review()
    db.add(review)
    db.commit()

    try:
        service = EnrichmentService(db)
        first = service.enrich_one(review)
        db.add(first)
        db.commit()

        second = service.enrich_one(review)
        assert second is None
        assert mock_gemini.call_count == 1
    finally:
        db.query(ReviewEnrichment).filter(ReviewEnrichment.review_id == review.id).delete()
        db.query(Review).filter(Review.id == review.id).delete()
        db.commit()
        db.close()


def test_enrichment_output_schema_validation():
    payload = {
        "sentiment": "positive",
        "emotion": ["delight"],
        "primary_topic": "playback",
        "user_goal": "listen offline",
        "pain_point": None,
        "feature_request": "offline mode",
        "discovery_issue": None,
        "listening_behavior": None,
        "user_segment": "premium user",
        "keywords": ["offline", "download"],
        "summary": "User wants offline playback.",
        "confidence_score": 0.9,
    }
    output = EnrichmentOutput.model_validate(payload)
    assert output.sentiment == Sentiment.POSITIVE
    assert output.feature_request == "offline mode"


@patch("src.ai.gemini_client.genai.Client")
def test_gemini_client_generate_json(mock_genai_client):
    from src.ai.gemini_client import GeminiClient
    from src.enrichment.schemas import EnrichmentOutput

    mock_client = MagicMock()
    mock_genai_client.return_value = mock_client
    mock_response = MagicMock()
    mock_response.text = json.dumps(MOCK_ENRICHMENT.model_dump())
    mock_client.models.generate_content.return_value = mock_response

    client = GeminiClient(api_key="test-key")
    result = client.generate_json("test prompt", EnrichmentOutput, system_instruction="sys")
    assert result["sentiment"] == "negative"
