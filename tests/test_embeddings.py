import uuid
from datetime import datetime, timezone
from unittest.mock import patch

import pytest

from src.embeddings.chunker import chunk_review_text
from src.embeddings.embedder import MODEL_VERSION, EmbeddingService
from src.storage.database import SessionLocal
from src.storage.models import Review, ReviewEmbedding


def _sample_review(**overrides) -> Review:
    review_id = overrides.pop("id", uuid.uuid4())
    return Review(
        id=review_id,
        source="google_play",
        source_id=f"src-{review_id.hex[:8]}",
        app_name="Spotify",
        platform="android",
        body=overrides.pop("body", "Discover Weekly keeps repeating the same tracks."),
        language="en",
        review_date=overrides.pop("review_date", datetime(2024, 5, 9, tzinfo=timezone.utc)),
        content_hash=overrides.pop("content_hash", f"hash-{review_id.hex[:8]}"),
        source_metadata={},
        **overrides,
    )


MOCK_VECTOR = [0.1] * 768


@patch("src.embeddings.embedder._embed_text")
def test_embedding_persists_vector(mock_embed):
    mock_embed.return_value = MOCK_VECTOR
    db = SessionLocal()
    review = _sample_review()
    db.add(review)
    db.commit()

    try:
        service = EmbeddingService(db)
        result = service.embed_batch([review], concurrency=1)
        assert result.embedded == 1
        assert result.failed == 0

        stored = (
            db.query(ReviewEmbedding)
            .filter(
                ReviewEmbedding.review_id == review.id,
                ReviewEmbedding.model_version == MODEL_VERSION,
            )
            .all()
        )
        assert len(stored) == 1
        assert stored[0].chunk_index == 0
        assert len(list(stored[0].embedding)) == 768
        mock_embed.assert_called_once()
    finally:
        db.query(ReviewEmbedding).filter(ReviewEmbedding.review_id == review.id).delete()
        db.query(Review).filter(Review.id == review.id).delete()
        db.commit()
        db.close()


@patch("src.embeddings.embedder._embed_text")
def test_skip_already_embedded(mock_embed):
    mock_embed.return_value = MOCK_VECTOR
    db = SessionLocal()
    review = _sample_review()
    db.add(review)
    db.commit()

    try:
        service = EmbeddingService(db)
        first = service.embed_batch([review], concurrency=1)
        assert first.embedded == 1

        second = service.embed_batch([review], concurrency=1)
        assert second.skipped == 1
        assert second.embedded == 0
        assert mock_embed.call_count == 1
    finally:
        db.query(ReviewEmbedding).filter(ReviewEmbedding.review_id == review.id).delete()
        db.query(Review).filter(Review.id == review.id).delete()
        db.commit()
        db.close()


@patch("src.embeddings.embedder._embed_text")
def test_content_hash_cache_skips_api(mock_embed):
    mock_embed.return_value = MOCK_VECTOR
    db = SessionLocal()
    shared_body = "Same repetitive playlist every single day."
    review_a = _sample_review(body=shared_body, content_hash="hash-a")
    review_b = _sample_review(body=shared_body, content_hash="hash-b")
    db.add_all([review_a, review_b])
    db.commit()

    try:
        service = EmbeddingService(db)
        result = service.embed_batch([review_a, review_b], concurrency=1)
        assert result.embedded == 2
        assert result.cached == 1
        assert mock_embed.call_count == 1
    finally:
        for review in (review_a, review_b):
            db.query(ReviewEmbedding).filter(ReviewEmbedding.review_id == review.id).delete()
            db.query(Review).filter(Review.id == review.id).delete()
        db.commit()
        db.close()


def test_chunk_count_for_review():
    review_id = uuid.uuid4()
    chunks = chunk_review_text(review_id, "Short review text.")
    assert len(chunks) == 1
