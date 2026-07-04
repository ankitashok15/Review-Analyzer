import logging
import re

from sqlalchemy.orm import Session

from config.settings import get_settings
from src.ai.gemini_client import GeminiClient
from src.embeddings.embedder import embedding_model_version
from src.embeddings.schemas import EmbeddingFilters, ScoredResult
from src.retrieval.ranker import RERANK_POOL_SIZE, rerank_hybrid
from src.retrieval.schemas import SearchFilters, SearchResult
from src.storage.repositories.embedding_repo import EmbeddingRepository

logger = logging.getLogger(__name__)
settings = get_settings()
EXCERPT_MAX_LENGTH = 200
_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")


def _to_embedding_filters(filters: SearchFilters | None) -> EmbeddingFilters:
    filters = filters or SearchFilters()
    return EmbeddingFilters(
        source=filters.source,
        platform=filters.platform,
        sentiment=filters.sentiment,
        min_rating=filters.min_rating,
        max_rating=filters.max_rating,
    )


def extract_excerpt(body: str, query: str, *, max_length: int = EXCERPT_MAX_LENGTH) -> tuple[str, list[int]]:
    text = body.strip()
    if not text:
        return "", [0, 0]

    query_terms = {term for term in query.lower().split() if term}
    best_sentence = ""
    best_overlap = -1
    best_start = 0

    for sentence in _SENTENCE_SPLIT.split(text):
        sentence = sentence.strip()
        if not sentence:
            continue
        overlap = len(query_terms & set(sentence.lower().split())) if query_terms else 0
        if overlap > best_overlap:
            best_overlap = overlap
            best_sentence = sentence
            best_start = text.lower().find(sentence.lower())
            if best_start < 0:
                best_start = 0

    if best_overlap <= 0 or not best_sentence:
        excerpt = text[:max_length]
        if len(text) > max_length:
            excerpt += "…"
        return excerpt, [0, len(excerpt)]

    if len(best_sentence) > max_length:
        best_sentence = best_sentence[:max_length] + "…"
    end = min(best_start + len(best_sentence), len(text))
    return best_sentence, [best_start, end]


def _to_search_result(item: ScoredResult, query: str) -> SearchResult:
    review = item.review
    if review is None:
        raise ValueError(f"Review missing for search hit {item.review_id}")

    excerpt, highlight_offsets = extract_excerpt(review.body, query)
    enrichment = item.enrichment
    return SearchResult(
        review_id=review.id,
        score=round(item.score, 6),
        excerpt=excerpt,
        highlight_offsets=highlight_offsets,
        source=review.source,
        platform=review.platform,
        rating=review.rating,
        review_date=review.review_date.isoformat(),
        source_url=review.source_url,
        sentiment=enrichment.sentiment if enrichment else None,
        primary_topic=enrichment.primary_topic if enrichment else None,
        summary=enrichment.summary if enrichment else None,
    )


class SemanticSearchService:
    """Natural-language semantic search over embedded reviews."""

    def __init__(self, db: Session, gemini_client: GeminiClient | None = None):
        self.db = db
        self.gemini = gemini_client or GeminiClient()
        self.embeddings = EmbeddingRepository(db)

    def search(
        self,
        query: str,
        filters: SearchFilters | None = None,
        *,
        top_k: int = 10,
        hybrid: bool = True,
    ) -> list[SearchResult]:
        normalized = query.strip()
        if not normalized:
            raise ValueError("Query cannot be empty")

        query_vector = self.gemini.embed(normalized)
        embedding_filters = _to_embedding_filters(filters)
        model_version = embedding_model_version()

        fetch_k = min(max(top_k, RERANK_POOL_SIZE), 100) if hybrid else top_k
        candidates = self.embeddings.find_similar(
            query_vector,
            top_k=fetch_k,
            model_version=model_version,
            filters=embedding_filters,
        )
        if not candidates:
            logger.warning(
                "No vector hits for model_version=%r; retrying without model filter",
                model_version,
            )
            candidates = self.embeddings.find_similar(
                query_vector,
                top_k=fetch_k,
                model_version=None,
                filters=embedding_filters,
            )

        if hybrid and candidates:
            candidates = rerank_hybrid(normalized, candidates, top_k=top_k)
        else:
            candidates = candidates[:top_k]

        return [_to_search_result(item, normalized) for item in candidates]
