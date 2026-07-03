from src.rag.schemas import InsightSnippet, RetrievedReview

RAG_SYSTEM_INSTRUCTION = """You are a product research assistant analyzing user reviews.
Answer the research question using ONLY the provided review evidence and insight snippets.
Rules:
- Every factual claim must be supported by at least one citation.
- Cite reviews using their exact review_id UUID and a verbatim excerpt from the review body.
- If the evidence is weak or contradictory, say so and lower confidence.
- Do not invent review IDs or quotes not present in the context.
- Use markdown for readability when helpful.
- If evidence is insufficient, set answer to explain what is missing and use confidence "low"."""


def build_rag_prompt(
    question: str,
    reviews: list[RetrievedReview],
    insights: list[InsightSnippet] | None = None,
) -> str:
    insights = insights or []
    review_blocks: list[str] = []

    for index, review in enumerate(reviews, start=1):
        enrichment_lines: list[str] = []
        if review.sentiment:
            enrichment_lines.append(f"sentiment: {review.sentiment}")
        if review.primary_topic:
            enrichment_lines.append(f"topic: {review.primary_topic}")
        if review.summary:
            enrichment_lines.append(f"summary: {review.summary}")

        enrichment_block = ""
        if enrichment_lines:
            enrichment_block = "\n  enrichment: " + "; ".join(enrichment_lines)

        review_blocks.append(
            f"[Review {index}]\n"
            f"  review_id: {review.review_id}\n"
            f"  source: {review.source} ({review.platform})\n"
            f"  relevance_score: {review.score:.4f}\n"
            f"  body: {review.body.strip()}"
            f"{enrichment_block}"
        )

    insight_blocks: list[str] = []
    for insight in insights:
        insight_blocks.append(
            f"[Insight {insight.insight_id}]\n"
            f"  type: {insight.insight_type}\n"
            f"  title: {insight.title}\n"
            f"  summary: {insight.summary}"
        )

    context_parts = ["## Retrieved reviews", *review_blocks]
    if insight_blocks:
        context_parts.extend(["## Related insights", *insight_blocks])

    context = "\n\n".join(context_parts)
    return (
        f"{context}\n\n"
        f"## Research question\n{question.strip()}\n\n"
        "Produce a JSON object with: answer (markdown string), confidence (high|medium|low), "
        "and citations (list of {review_id, excerpt} drawn from the review bodies above)."
    )
