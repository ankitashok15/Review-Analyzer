import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from src.rag.answer_generator import AnswerGenerator, _excerpt_in_body
from src.rag.prompt_builder import build_rag_prompt
from src.rag.schemas import AskRequest, CitationOutput, RagGenerationOutput, RetrievedReview
from src.rag.service import RagService, MIN_RELEVANCE_SCORE
from src.storage.database import SessionLocal
from src.storage.models import InsightCache, Review


def _sample_review(**overrides) -> Review:
    review_id = overrides.pop("id", uuid.uuid4())
    return Review(
        id=review_id,
        source=overrides.pop("source", "test_rag"),
        source_id=overrides.pop("source_id", f"rag-{review_id.hex[:8]}"),
        app_name="Spotify",
        platform=overrides.pop("platform", "android"),
        body=overrides.pop(
            "body",
            "Discover Weekly keeps repeating the same songs every day.",
        ),
        language="en",
        rating=overrides.pop("rating", 2),
        review_date=overrides.pop("review_date", datetime(2024, 6, 1, tzinfo=timezone.utc)),
        content_hash=overrides.pop("content_hash", f"hash-{review_id.hex[:8]}"),
        source_metadata={},
        **overrides,
    )


def _retrieved(review: Review, *, score: float = 0.72) -> RetrievedReview:
    return RetrievedReview(
        review_id=review.id,
        body=review.body,
        excerpt=review.body[:80],
        score=score,
        source=review.source,
        platform=review.platform,
        sentiment="negative",
        primary_topic="discovery",
        summary="User finds recommendations repetitive.",
    )


def test_excerpt_in_body_case_insensitive():
    assert _excerpt_in_body("Same Songs Every Day", "keeps repeating the same songs every day.")


def test_build_rag_prompt_includes_review_ids():
    review = _sample_review()
    retrieved = [_retrieved(review)]
    prompt = build_rag_prompt("Why is discovery hard?", retrieved)
    assert str(review.id) in prompt
    assert review.body in prompt


def test_answer_generator_drops_hallucinated_citations():
    review = _sample_review()
    retrieved = [_retrieved(review)]
    fake_id = uuid.uuid4()

    mock_gemini = MagicMock()
    mock_gemini.generate_json.return_value = RagGenerationOutput(
        answer="Users struggle with repetitive playlists.",
        confidence="high",
        citations=[
            CitationOutput(review_id=str(review.id), excerpt="same songs every day"),
            CitationOutput(review_id=str(fake_id), excerpt="made up quote"),
        ],
    ).model_dump()

    generator = AnswerGenerator(gemini_client=mock_gemini)
    response = generator.generate("Why is discovery hard?", retrieved)

    assert len(response.citations) == 1
    assert response.citations[0].review_id == review.id
    assert "same songs" in response.citations[0].excerpt.lower()


def test_answer_generator_insufficient_evidence_response():
    generator = AnswerGenerator(gemini_client=MagicMock())
    response = generator.insufficient_evidence("Unknown topic?", retrieval_count=0)
    assert response.confidence == "low"
    assert response.citations == []
    assert response.retrieval_count == 0
    assert response.answer_mode == "general"
    assert "Insufficient evidence" in response.answer


def test_answer_generator_fallback_response():
    mock_gemini = MagicMock()
    mock_gemini.generate_json.return_value = {
        "answer": "This is general guidance, not from your review dataset. Users often struggle with discovery.",
    }
    generator = AnswerGenerator(gemini_client=mock_gemini)
    response = generator.generate_fallback("Why is discovery hard?", retrieval_count=2)

    assert response.answer_mode == "general"
    assert response.confidence == "low"
    assert response.citations == []
    assert response.retrieval_count == 2
    assert "general guidance" in response.answer.lower()


@patch("src.rag.service.RagRetriever")
def test_rag_service_no_retrieval_uses_fallback(mock_retriever_cls):
    mock_retriever = MagicMock()
    mock_retriever.retrieve.return_value = ("query", [])
    mock_retriever_cls.return_value = mock_retriever

    mock_generator = MagicMock()
    mock_generator.generate_fallback.return_value = MagicMock(
        question="Why do users struggle to discover new music?",
        answer="General guidance about discovery challenges.",
        confidence="low",
        citations=[],
        related_insights=[],
        retrieval_count=0,
        answer_mode="general",
    )

    db = SessionLocal()
    try:
        service = RagService(db, retriever=mock_retriever, answer_generator=mock_generator)
        response = service.ask(AskRequest(question="Why do users struggle to discover new music?"))
        mock_generator.generate_fallback.assert_called_once()
        assert response.answer_mode == "general"
        assert response.retrieval_count == 0
    finally:
        db.close()


@patch("src.rag.service.RagRetriever")
def test_rag_service_low_score_uses_fallback(mock_retriever_cls):
    review = _sample_review()
    mock_retriever = MagicMock()
    mock_retriever.retrieve.return_value = (
        "query",
        [_retrieved(review, score=0.05)],
    )
    mock_retriever_cls.return_value = mock_retriever

    mock_generator = MagicMock()
    mock_generator.generate_fallback.return_value = MagicMock(
        question="Why is discovery hard?",
        answer="General guidance.",
        confidence="low",
        citations=[],
        related_insights=[],
        retrieval_count=1,
        answer_mode="general",
    )

    db = SessionLocal()
    try:
        service = RagService(db, retriever=mock_retriever, answer_generator=mock_generator, min_relevance_score=MIN_RELEVANCE_SCORE)
        response = service.ask(AskRequest(question="Why is discovery hard?"))
        mock_generator.generate_fallback.assert_called_once()
        assert response.answer_mode == "general"
        assert response.retrieval_count == 1
    finally:
        db.close()


@patch("src.rag.service.AnswerGenerator")
@patch("src.rag.service.RagRetriever")
def test_rag_service_calls_generator_when_evidence_ok(mock_retriever_cls, mock_generator_cls):
    review = _sample_review()
    retrieved = [_retrieved(review, score=0.8)]
    mock_retriever = MagicMock()
    mock_retriever.retrieve.return_value = ("query", retrieved)
    mock_retriever_cls.return_value = mock_retriever

    from src.rag.schemas import AskResponse

    mock_generator = MagicMock()
    mock_generator.generate.return_value = AskResponse(
        question="Why is discovery hard?",
        answer="Users report repetitive recommendations.",
        confidence="high",
        citations=[
            {
                "review_id": review.id,
                "excerpt": "same songs every day",
                "source": review.source,
                "relevance_score": 0.8,
            }
        ],
        related_insights=[],
        retrieval_count=1,
        answer_mode="grounded",
    )
    mock_generator_cls.return_value = mock_generator

    db = SessionLocal()
    try:
        service = RagService(db, retriever=mock_retriever, answer_generator=mock_generator)
        response = service.ask(AskRequest(question="Why is discovery hard?"))
        mock_generator.generate.assert_called_once()
        assert response.confidence == "high"
        assert response.retrieval_count == 1
    finally:
        db.close()


@patch("src.rag.service.RagRetriever")
def test_rag_service_generation_failure_uses_fallback(mock_retriever_cls):
    review = _sample_review()
    retrieved = [_retrieved(review, score=0.8)]
    mock_retriever = MagicMock()
    mock_retriever.retrieve.return_value = ("query", retrieved)
    mock_retriever_cls.return_value = mock_retriever

    mock_generator = MagicMock()
    mock_generator.generate.side_effect = RuntimeError("quota exceeded")
    mock_generator.generate_fallback.return_value = MagicMock(
        question="Why is discovery hard?",
        answer="General guidance.",
        confidence="low",
        citations=[],
        related_insights=[],
        retrieval_count=1,
        answer_mode="general",
    )

    db = SessionLocal()
    try:
        service = RagService(db, retriever=mock_retriever, answer_generator=mock_generator)
        response = service.ask(AskRequest(question="Why is discovery hard?"))
        mock_generator.generate_fallback.assert_called_once()
        assert response.answer_mode == "general"
    finally:
        db.close()


def test_rag_service_related_insights_overlap():
    review = _sample_review()
    retrieved = [_retrieved(review)]

    db = SessionLocal()
    cache_row = InsightCache(
        id=uuid.uuid4(),
        insight_type="pain_points",
        cache_key="default",
        title="Repetitive playlists",
        summary="Users complain about same songs.",
        evidence_review_ids=[str(review.id)],
        metrics={"count": 1},
    )
    try:
        db.add(cache_row)
        db.commit()

        mock_retriever = MagicMock()
        mock_retriever.retrieve.return_value = ("query", retrieved)
        mock_retriever.gemini = MagicMock()

        mock_generator = MagicMock()
        mock_generator.generate.return_value = MagicMock(
            question="test",
            answer="answer",
            confidence="medium",
            citations=[],
            related_insights=[str(cache_row.id)],
            retrieval_count=1,
        )

        service = RagService(db, retriever=mock_retriever, answer_generator=mock_generator)
        service.ask(AskRequest(question="Why is discovery hard?", include_insights=True))

        _, kwargs = mock_generator.generate.call_args
        insights = mock_generator.generate.call_args[0][2]
        assert len(insights) == 1
        assert insights[0].insight_id == str(cache_row.id)
    finally:
        db.query(InsightCache).filter(InsightCache.id == cache_row.id).delete()
        db.commit()
        db.close()


def test_ask_api_empty_question_returns_400(client):
    response = client.post("/api/v1/ask", json={"question": "   "})
    assert response.status_code == 400


@patch("src.api.routes.ask.RagService")
def test_ask_api_returns_cited_answer(mock_service_cls, client):
    review_id = uuid.uuid4()
    mock_service = MagicMock()
    mock_service.ask.return_value = {
        "question": "Why do users struggle to discover new music?",
        "answer": "Users report repetitive Discover Weekly playlists.",
        "confidence": "high",
        "citations": [
            {
                "review_id": str(review_id),
                "excerpt": "same songs every day",
                "source": "google_play",
                "relevance_score": 0.88,
            }
        ],
        "related_insights": [],
        "retrieval_count": 5,
    }
    mock_service_cls.return_value = mock_service

    response = client.post(
        "/api/v1/ask",
        json={"question": "Why do users struggle to discover new music?", "top_k": 15},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["confidence"] == "high"
    assert len(data["citations"]) == 1
    assert data["citations"][0]["review_id"] == str(review_id)
    assert data["retrieval_count"] == 5


@patch("src.api.routes.ask.RagService")
def test_ask_api_insufficient_evidence(mock_service_cls, client):
    mock_service = MagicMock()
    mock_service.ask.return_value = {
        "question": "What frustrations exist with recommendations?",
        "answer": "Insufficient evidence in the review corpus to answer this question confidently.",
        "confidence": "low",
        "citations": [],
        "related_insights": [],
        "retrieval_count": 0,
    }
    mock_service_cls.return_value = mock_service

    response = client.post(
        "/api/v1/ask",
        json={"question": "What frustrations exist with recommendations?"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["citations"] == []
    assert "Insufficient evidence" in data["answer"]
