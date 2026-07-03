from src.embeddings.schemas import ScoredResult

VECTOR_WEIGHT = 0.7
KEYWORD_WEIGHT = 0.3
RERANK_POOL_SIZE = 20


def keyword_score(query: str, text: str) -> float:
    query_terms = {term for term in query.lower().split() if term}
    if not query_terms:
        return 0.0
    text_terms = set(text.lower().split())
    return len(query_terms & text_terms) / len(query_terms)


def rerank_hybrid(
    query: str,
    results: list[ScoredResult],
    *,
    top_k: int,
    vector_weight: float = VECTOR_WEIGHT,
    keyword_weight: float = KEYWORD_WEIGHT,
) -> list[ScoredResult]:
    if not results:
        return []

    pool = results[:RERANK_POOL_SIZE]
    reranked: list[ScoredResult] = []
    for item in pool:
        body = item.review.body if item.review else ""
        combined = (vector_weight * item.score) + (keyword_weight * keyword_score(query, body))
        reranked.append(
            ScoredResult(
                review_id=item.review_id,
                chunk_index=item.chunk_index,
                score=combined,
                chunk_text=item.chunk_text,
                review=item.review,
                enrichment=item.enrichment,
            )
        )

    reranked.sort(key=lambda row: row.score, reverse=True)
    return reranked[:top_k]
