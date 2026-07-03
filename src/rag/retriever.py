import logging

from sqlalchemy.orm import Session

from config.settings import get_settings
from src.ai.gemini_client import GeminiClient
from src.rag.schemas import QueryRewriteOutput, RetrievedReview
from src.retrieval.schemas import SearchFilters
from src.retrieval.semantic_search import SemanticSearchService
from src.storage.repositories.review_repo import ReviewRepository

logger = logging.getLogger(__name__)
settings = get_settings()

REWRITE_SYSTEM = (
    "You rewrite user research questions into concise semantic search queries "
    "for finding relevant app store reviews. Return only the rewritten query."
)


class RagRetriever:
    """Retrieve review evidence for RAG via semantic search."""

    def __init__(
        self,
        db: Session,
        gemini_client: GeminiClient | None = None,
        search_service: SemanticSearchService | None = None,
    ):
        self.db = db
        self.gemini = gemini_client or GeminiClient()
        self.search = search_service or SemanticSearchService(db, gemini_client=self.gemini)
        self.reviews = ReviewRepository(db)

    def rewrite_query(self, question: str) -> str:
        prompt = f"Research question:\n{question.strip()}\n\nRewritten search query:"
        result = self.gemini.generate_json(
            prompt,
            QueryRewriteOutput,
            model=settings.gemini_enrichment_model,
            system_instruction=REWRITE_SYSTEM,
        )
        rewritten = result.get("rewritten_query", "").strip()
        return rewritten or question.strip()

    def retrieve(
        self,
        question: str,
        filters: SearchFilters | None = None,
        *,
        top_k: int = 15,
        rewrite_query: bool = False,
    ) -> tuple[str, list[RetrievedReview]]:
        normalized = question.strip()
        if not normalized:
            raise ValueError("Question cannot be empty")

        query_used = self.rewrite_query(normalized) if rewrite_query else normalized
        if rewrite_query and query_used != normalized:
            logger.info("RAG query rewrite: %r -> %r", normalized, query_used)

        search_results = self.search.search(
            query_used,
            filters,
            top_k=top_k,
            hybrid=True,
        )

        retrieved: list[RetrievedReview] = []
        for hit in search_results:
            review = self.reviews.get_by_id(hit.review_id)
            body = review.body if review else hit.excerpt
            retrieved.append(
                RetrievedReview(
                    review_id=hit.review_id,
                    body=body,
                    excerpt=hit.excerpt,
                    score=hit.score,
                    source=hit.source,
                    platform=hit.platform,
                    sentiment=hit.sentiment,
                    primary_topic=hit.primary_topic,
                    summary=hit.summary,
                )
            )

        return query_used, retrieved
