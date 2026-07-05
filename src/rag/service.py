import logging

from sqlalchemy.orm import Session

from config.settings import get_settings
from src.insights.service import InsightService
from src.rag.answer_generator import AnswerGenerator
from src.rag.retriever import RagRetriever
from src.rag.schemas import AskRequest, AskResponse, InsightSnippet, RetrievedReview
from src.retrieval.schemas import SearchFilters
from src.storage.models import InsightCache

logger = logging.getLogger(__name__)
settings = get_settings()

MIN_RELEVANCE_SCORE = 0.15
MAX_RELATED_INSIGHTS = 3


class RagService:
    """End-to-end RAG pipeline: retrieve, assemble context, generate, validate."""

    def __init__(
        self,
        db: Session,
        *,
        retriever: RagRetriever | None = None,
        answer_generator: AnswerGenerator | None = None,
        insight_service: InsightService | None = None,
        min_relevance_score: float = MIN_RELEVANCE_SCORE,
    ):
        self.db = db
        self.retriever = retriever or RagRetriever(db)
        self.answer_generator = answer_generator or AnswerGenerator(
            gemini_client=self.retriever.gemini,
        )
        self.insights = insight_service or InsightService(db, gemini_client=self.retriever.gemini)
        self.min_relevance_score = min_relevance_score

    def ask(self, request: AskRequest) -> AskResponse:
        question = request.question.strip()
        if not question:
            raise ValueError("Question cannot be empty")

        try:
            return self._ask_with_retrieval(request, question)
        except Exception as exc:
            logger.warning("RAG ask failed for question=%r: %s", question, exc)
            return self._fallback_or_insufficient(
                question,
                retrieval_count=0,
                allow_fallback=request.allow_fallback,
            )

    def _ask_with_retrieval(self, request: AskRequest, question: str) -> AskResponse:
        _, retrieved = self.retriever.retrieve(
            question,
            request.filters,
            top_k=request.top_k,
            rewrite_query=request.rewrite_query,
        )

        if not retrieved:
            logger.info("RAG: no retrieval results for question=%r", question)
            return self._fallback_or_insufficient(
                question,
                retrieval_count=0,
                allow_fallback=request.allow_fallback,
            )

        top_score = max(item.score for item in retrieved)
        if top_score < self.min_relevance_score:
            logger.info(
                "RAG: top score %.4f below threshold %.4f",
                top_score,
                self.min_relevance_score,
            )
            return self._fallback_or_insufficient(
                question,
                retrieval_count=len(retrieved),
                allow_fallback=request.allow_fallback,
            )

        insight_snippets = (
            self._related_insights(retrieved) if request.include_insights else []
        )
        try:
            return self.answer_generator.generate(question, retrieved, insight_snippets)
        except Exception as exc:
            logger.warning("RAG generation failed for question=%r: %s", question, exc)
            if request.allow_fallback and settings.rag_fallback_enabled:
                try:
                    return self.answer_generator.generate_fallback(
                        question,
                        retrieval_count=len(retrieved),
                    )
                except Exception as fallback_exc:
                    logger.warning("Fallback generation also failed: %s", fallback_exc)
            return self.answer_generator.insufficient_evidence(
                question,
                retrieval_count=len(retrieved),
            )

    def _fallback_or_insufficient(
        self,
        question: str,
        *,
        retrieval_count: int,
        allow_fallback: bool,
    ) -> AskResponse:
        if allow_fallback and settings.rag_fallback_enabled:
            try:
                return self.answer_generator.generate_fallback(
                    question,
                    retrieval_count=retrieval_count,
                )
            except Exception as exc:
                logger.warning("Fallback generation failed: %s", exc)
        return self.answer_generator.insufficient_evidence(
            question,
            retrieval_count=retrieval_count,
        )

    def _related_insights(self, retrieved: list[RetrievedReview]) -> list[InsightSnippet]:
        retrieved_ids = {str(review.review_id) for review in retrieved}
        rows = (
            self.db.query(InsightCache)
            .order_by(InsightCache.generated_at.desc())
            .all()
        )

        snippets: list[InsightSnippet] = []
        for row in rows:
            evidence = {str(rid) for rid in (row.evidence_review_ids or [])}
            if not evidence & retrieved_ids:
                continue
            snippets.append(
                InsightSnippet(
                    insight_id=str(row.id),
                    insight_type=row.insight_type,
                    title=row.title,
                    summary=row.summary,
                )
            )
            if len(snippets) >= MAX_RELATED_INSIGHTS:
                break

        return snippets
