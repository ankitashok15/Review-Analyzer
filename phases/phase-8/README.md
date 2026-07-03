# Phase 8 — RAG-Based Natural Language Q&A

**Status:** Complete  
**Depends on:** [Phase 6](../phase-6/README.md) (semantic search), [Phase 7](../phase-7/README.md) (optional — insight context)

## Objective

Answer research questions in plain English with Gemini-generated, citation-backed responses grounded in retrieved review evidence.

## Deliverables

| Item | Location |
|------|----------|
| RAG schemas | `src/rag/schemas.py` |
| Retriever | `src/rag/retriever.py` |
| Prompt builder | `src/rag/prompt_builder.py` |
| Answer generator | `src/rag/answer_generator.py` |
| RAG orchestrator | `src/rag/service.py` |
| API route | `src/api/routes/ask.py` |
| Tests | `tests/test_rag.py` |

## Pipeline

1. **Retrieve** — top-K reviews via `SemanticSearchService` (optional query rewrite)
2. **Guardrails** — skip LLM if `retrieval_count == 0` or top score &lt; 0.15
3. **Context assembly** — review bodies, enrichment summaries, related insight snippets
4. **Generate** — `gemini-2.5-pro` (configurable via `GEMINI_RAG_MODEL`)
5. **Validate** — drop hallucinated review IDs; ensure excerpts ⊆ review body

## API

```powershell
uvicorn src.api.main:app --reload --port 8000
```

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/ask` | RAG Q&A with citations |

### Request

```json
{
  "question": "Why do users struggle to discover new music?",
  "top_k": 15,
  "rewrite_query": false,
  "include_insights": true,
  "filters": {}
}
```

### Response

```json
{
  "question": "Why do users struggle to discover new music?",
  "answer": "markdown answer text",
  "confidence": "high",
  "citations": [
    {
      "review_id": "uuid",
      "excerpt": "verbatim quote from review",
      "source": "google_play",
      "relevance_score": 0.88
    }
  ],
  "related_insights": ["insight-cache-uuid"],
  "retrieval_count": 15
}
```

### Example

```powershell
curl -X POST http://localhost:8000/api/v1/ask `
  -H "Content-Type: application/json" `
  -d "{\"question\": \"Why do users struggle to discover new music?\", \"top_k\": 15}"
```

## Prerequisites

Embeddings must exist for semantic retrieval:

```powershell
python scripts/run_pipeline.py embed --limit 500 --concurrency 1
```

Valid `GOOGLE_API_KEY` with quota for:

- `text-embedding-004` (query embedding at retrieval time)
- `GEMINI_RAG_MODEL` (default `gemini-2.5-pro` for answer generation)

Optional enrichment and cached insights improve answer quality but are not required for MVP RAG.

## Sample validation questions

From `ProblemStatement.md`:

- "Why do users struggle to discover new music?"
- "What frustrations exist with recommendations?"
- "Which product features are most frequently requested?"

Each should return cited answers or explicit **"Insufficient evidence"** (not hallucinated IDs).

## Performance

Target latency: **&lt;15s** for `top_k=15` (embedding + retrieval + one `gemini-2.5-pro` call). Actual latency depends on Gemini API response time and DB size.

## Verify

```powershell
pytest tests/test_rag.py -v
```

## Exit criteria

- [x] `AskRequest` / `AskResponse` schemas
- [x] Retrieval via semantic search with optional query rewrite
- [x] Prompt assembly with reviews + optional insights
- [x] Citation validation (no hallucinated review IDs)
- [x] Guardrails for empty/low-confidence retrieval
- [x] `POST /api/v1/ask` endpoint
- [x] Unit and API tests

## Next phase

→ Phase 9 — Research Dashboard & API Surface (`phases/phase-9/README.md`)
