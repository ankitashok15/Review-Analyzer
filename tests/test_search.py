import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from src.embeddings.embedder import MODEL_VERSION
from src.retrieval.ranker import keyword_score, rerank_hybrid
from src.retrieval.schemas import SearchFilters
from src.retrieval.semantic_search import SemanticSearchService, extract_excerpt
from src.storage.database import SessionLocal
from src.storage.models import Review, ReviewEmbedding


def _unit_vector(index: int) -> list[float]:
    vector = [0.0] * 768
    vector[index % 768] = 1.0
    return vector


def _sample_review(**overrides) -> Review:
    review_id = overrides.pop("id", uuid.uuid4())
    return Review(
        id=review_id,
        source=overrides.pop("source", "test_search"),
        source_id=overrides.pop("source_id", f"search-{review_id.hex[:8]}"),
        app_name="Spotify",
        platform=overrides.pop("platform", "android"),
        body=overrides.pop("body", "The playlist feels repetitive with the same songs every day."),
        language="en",
        rating=overrides.pop("rating", 2),
        review_date=overrides.pop("review_date", datetime(2024, 6, 1, tzinfo=timezone.utc)),
        content_hash=overrides.pop("content_hash", f"hash-{review_id.hex[:8]}"),
        source_metadata={},
        **overrides,
    )


def test_extract_excerpt_prefers_overlapping_sentence():
    body = "Great app overall. Discover Weekly keeps repeating the same songs every day. Love the UI."
    excerpt, offsets = extract_excerpt(body, "same songs every day")
    assert "same songs" in excerpt.lower()
    assert offsets[0] >= 0
    assert offsets[1] > offsets[0]


def test_keyword_score_paraphrase_overlap():
    score = keyword_score("same songs every day", "repetitive playlist with the same songs every day")
    assert score > 0.5


@patch("src.retrieval.semantic_search.GeminiClient")
def test_semantic_search_paraphrase_match(mock_client_cls):
    mock_client = MagicMock()
    mock_client.embed.return_value = _unit_vector(0)
    mock_client_cls.return_value = mock_client

    db = SessionLocal()
    reviews = [
        _sample_review(body="Discover Weekly keeps repeating the same songs every day."),
        _sample_review(body="Excellent sound quality and easy navigation."),
    ]
    try:
        db.add_all(reviews)
        db.commit()
        for review in reviews:
            db.add(
                ReviewEmbedding(
                    id=uuid.uuid4(),
                    review_id=review.id,
                    chunk_index=0,
                    embedding=_unit_vector(0),
                    content_hash=f"chunk-{review.id.hex[:8]}",
                    model_version=MODEL_VERSION,
                )
            )
        db.commit()

        service = SemanticSearchService(db, gemini_client=mock_client)
        results = service.search("same songs every day", top_k=2, hybrid=True)
        assert len(results) >= 1
        assert results[0].review_id == reviews[0].id
        assert results[0].score > 0
        assert results[0].excerpt
    finally:
        for review in reviews:
            db.query(ReviewEmbedding).filter(ReviewEmbedding.review_id == review.id).delete()
            db.query(Review).filter(Review.id == review.id).delete()
        db.commit()
        db.close()


@patch("src.retrieval.semantic_search.GeminiClient")
def test_semantic_search_source_filter(mock_client_cls):
    mock_client = MagicMock()
    mock_client.embed.return_value = _unit_vector(0)
    mock_client_cls.return_value = mock_client

    db = SessionLocal()
    reviews = [
        _sample_review(source="test_search_a", body="Offline downloads fail constantly."),
        _sample_review(source="test_search_b", body="Offline downloads fail constantly."),
    ]
    try:
        db.add_all(reviews)
        db.commit()
        for review in reviews:
            db.add(
                ReviewEmbedding(
                    id=uuid.uuid4(),
                    review_id=review.id,
                    chunk_index=0,
                    embedding=_unit_vector(0),
                    content_hash=f"chunk-{review.id.hex[:8]}",
                    model_version=MODEL_VERSION,
                )
            )
        db.commit()

        service = SemanticSearchService(db, gemini_client=mock_client)
        results = service.search(
            "offline downloads",
            SearchFilters(source="test_search_b"),
            top_k=5,
        )
        assert len(results) == 1
        assert results[0].source == "test_search_b"
    finally:
        for review in reviews:
            db.query(ReviewEmbedding).filter(ReviewEmbedding.review_id == review.id).delete()
            db.query(Review).filter(Review.id == review.id).delete()
        db.commit()
        db.close()


@patch("src.retrieval.semantic_search.EmbeddingRepository")
@patch("src.retrieval.semantic_search.GeminiClient")
def test_semantic_search_no_results(mock_client_cls, mock_repo_cls):
    mock_client = MagicMock()
    mock_client.embed.return_value = _unit_vector(99)
    mock_client_cls.return_value = mock_client
    mock_repo = MagicMock()
    mock_repo.find_similar.return_value = []
    mock_repo_cls.return_value = mock_repo

    db = SessionLocal()
    try:
        service = SemanticSearchService(db, gemini_client=mock_client)
        results = service.search("nonexistent topic xyz", top_k=5)
        assert results == []
    finally:
        db.close()


def test_search_api_empty_query_returns_400(client):
    response = client.post("/api/v1/search", json={"query": "   ", "top_k": 5})
    assert response.status_code == 400


@patch("src.api.routes.search.SemanticSearchService")
def test_search_api_no_results_returns_empty_array(mock_service_cls, client):
    mock_service = MagicMock()
    mock_service.search.return_value = []
    mock_service_cls.return_value = mock_service

    response = client.post(
        "/api/v1/search",
        json={"query": "offline mode", "top_k": 5},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 0
    assert data["results"] == []


def test_rerank_hybrid_boosts_keyword_match():
    review_match = _sample_review(body="Same songs every day on repeat.")
    review_miss = _sample_review(body="Great audio quality.")
    from src.embeddings.schemas import ScoredResult

    results = [
        ScoredResult(review_match.id, 0, 0.6, review=review_match),
        ScoredResult(review_miss.id, 0, 0.9, review=review_miss),
    ]
    reranked = rerank_hybrid("same songs every day", results, top_k=2)
    assert reranked[0].review_id == review_match.id
