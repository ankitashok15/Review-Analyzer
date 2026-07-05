import logging
import uuid

from config.settings import get_settings
from src.ai.gemini_client import GeminiClient
from src.rag.prompt_builder import RAG_SYSTEM_INSTRUCTION, build_rag_prompt
from src.rag.schemas import (
    AskResponse,
    Citation,
    FallbackOutput,
    InsightSnippet,
    RagGenerationOutput,
    RetrievedReview,
)

logger = logging.getLogger(__name__)
settings = get_settings()

INSUFFICIENT_EVIDENCE_ANSWER = (
    "Insufficient evidence in the review corpus to answer this question confidently. "
    "Try broadening your question or ensure more reviews are embedded for semantic search."
)

FALLBACK_SYSTEM_INSTRUCTION = """You are a product research assistant for a music streaming app review analyzer.
The user asked a research question but the system could not produce an evidence-backed answer from the embedded review corpus.
Provide a concise, helpful general answer about typical user behavior and product patterns in music streaming apps
(discovery, recommendations, playlists, shuffle, personalization, ads, premium tiers, etc.).

Rules:
- Start with one sentence noting this is general guidance, NOT derived from the user's review dataset.
- Do not invent specific review quotes, user counts, percentages, or statistics.
- Use markdown bullets when helpful.
- Stay relevant to the question."""


def _normalize_excerpt(excerpt: str) -> str:
    return " ".join(excerpt.split()).lower()


def _excerpt_in_body(excerpt: str, body: str) -> bool:
    if not excerpt.strip():
        return False
    normalized_excerpt = _normalize_excerpt(excerpt)
    normalized_body = _normalize_excerpt(body)
    return normalized_excerpt in normalized_body


def _resolve_excerpt(excerpt: str, review: RetrievedReview) -> str:
    if _excerpt_in_body(excerpt, review.body):
        return excerpt.strip()
    if _excerpt_in_body(review.excerpt, review.body):
        return review.excerpt.strip()
    trimmed = review.body.strip()
    return trimmed[:200] + ("…" if len(trimmed) > 200 else "")


class AnswerGenerator:
    """Generate citation-backed answers with Gemini and validate citations."""

    def __init__(self, gemini_client: GeminiClient | None = None):
        self.gemini = gemini_client or GeminiClient()

    def generate(
        self,
        question: str,
        reviews: list[RetrievedReview],
        insights: list[InsightSnippet] | None = None,
    ) -> AskResponse:
        prompt = build_rag_prompt(question, reviews, insights)
        raw = self.gemini.generate_json(
            prompt,
            RagGenerationOutput,
            model=settings.gemini_rag_model,
            system_instruction=RAG_SYSTEM_INSTRUCTION,
        )
        parsed = RagGenerationOutput.model_validate(raw)
        citations = self._validate_citations(parsed.citations, reviews)

        confidence = parsed.confidence
        if not citations and confidence != "low":
            confidence = "low"

        return AskResponse(
            question=question.strip(),
            answer=parsed.answer.strip(),
            confidence=confidence,
            citations=citations,
            related_insights=[insight.insight_id for insight in (insights or [])],
            retrieval_count=len(reviews),
            answer_mode="grounded",
        )

    def generate_fallback(
        self,
        question: str,
        *,
        retrieval_count: int = 0,
    ) -> AskResponse:
        prompt = (
            f"Research question:\n{question.strip()}\n\n"
            "Provide general product-research context that helps the user understand likely themes, "
            "without claiming they come from a specific review dataset."
        )
        raw = self.gemini.generate_json(
            prompt,
            FallbackOutput,
            model=settings.gemini_rag_model,
            system_instruction=FALLBACK_SYSTEM_INSTRUCTION,
        )
        parsed = FallbackOutput.model_validate(raw)
        return AskResponse(
            question=question.strip(),
            answer=parsed.answer.strip(),
            confidence="low",
            citations=[],
            related_insights=[],
            retrieval_count=retrieval_count,
            answer_mode="general",
        )

    def insufficient_evidence(self, question: str, *, retrieval_count: int) -> AskResponse:
        return AskResponse(
            question=question.strip(),
            answer=INSUFFICIENT_EVIDENCE_ANSWER,
            confidence="low",
            citations=[],
            related_insights=[],
            retrieval_count=retrieval_count,
            answer_mode="general",
        )

    def _validate_citations(
        self,
        raw_citations: list,
        reviews: list[RetrievedReview],
    ) -> list[Citation]:
        by_id = {review.review_id: review for review in reviews}
        validated: list[Citation] = []
        seen: set[uuid.UUID] = set()

        for item in raw_citations:
            try:
                review_id = uuid.UUID(str(item.review_id))
            except (ValueError, AttributeError, TypeError):
                logger.warning("Skipping citation with invalid review_id: %r", item)
                continue

            if review_id not in by_id:
                logger.warning("Dropping hallucinated citation review_id=%s", review_id)
                continue

            review = by_id[review_id]
            excerpt = _resolve_excerpt(getattr(item, "excerpt", "") or "", review)
            if review_id in seen:
                continue

            seen.add(review_id)
            validated.append(
                Citation(
                    review_id=review_id,
                    excerpt=excerpt,
                    source=review.source,
                    relevance_score=round(min(max(review.score, 0.0), 1.0), 6),
                )
            )

        return validated
