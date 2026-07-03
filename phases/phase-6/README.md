# Phase 6 — Semantic Search & Retrieval

**Status:** Complete  
**Depends on:** [Phase 5](../phase-5/README.md)

## Objective

Enable natural-language search that returns ranked reviews with relevance scores and excerpts via a REST API.

## Deliverables

| Item | Location |
|------|----------|
| Search schemas | `src/retrieval/schemas.py` |
| Semantic search service | `src/retrieval/semantic_search.py` |
| Hybrid ranker | `src/retrieval/ranker.py` |
| Search API route | `src/api/routes/search.py` |
| Router registration | `src/api/main.py` |
| Tests | `tests/test_search.py` |

## API

### `POST /api/v1/search`

**Request:**

```json
{
  "query": "repetitive recommendations",
  "filters": {
    "source": "google_play",
    "platform": "android",
    "min_rating": 1,
    "max_rating": 3,
    "sentiment": "negative"
  },
  "top_k": 10,
  "hybrid": true
}
```

**Response:**

```json
{
  "query": "repetitive recommendations",
  "count": 2,
  "results": [
    {
      "review_id": "uuid",
      "score": 0.82,
      "excerpt": "Discover Weekly keeps repeating…",
      "highlight_offsets": [42, 98],
      "source": "google_play",
      "platform": "android",
      "rating": 2,
      "review_date": "2024-05-09T00:00:00+00:00",
      "source_url": null,
      "sentiment": null,
      "primary_topic": null,
      "summary": null
    }
  ]
}
```

- Empty / whitespace query → **400**
- No matches → **200** with `"count": 0`, `"results": []`

## How it works

1. Embed query text via `GeminiClient` (`text-embedding-004`)
2. Vector similarity search via `EmbeddingRepository`
3. Optional metadata pre-filters (source, platform, rating, sentiment)
4. Hybrid re-rank (default): `0.7 × vector score + 0.3 × keyword overlap`
5. Extract best-matching excerpt from review body

## Prerequisites

Embedded reviews in `review_embeddings` (Phase 4):

```powershell
python scripts/run_pipeline.py embed --limit 100 --concurrency 1
```

## Try it

```powershell
uvicorn src.api.main:app --reload --port 8000
```

```powershell
curl -X POST http://localhost:8000/api/v1/search `
  -H "Content-Type: application/json" `
  -d '{"query":"offline downloads","top_k":5}'
```

CLI smoke test (Phase 4):

```powershell
python scripts/run_pipeline.py search "repetitive recommendations" --top-k 5
```

## Verify

```powershell
pytest tests/test_search.py -v
```

## Exit criteria

- [x] `POST /api/v1/search` returns review_id, excerpt, score, source
- [x] Hybrid ranker boosts paraphrase/keyword overlap
- [x] Filters narrow results (source, platform, rating, sentiment)
- [x] Empty query → 400; no results → empty array with 200
- [x] Enrichment fields included when present (optional)

## Next phase

→ Phase 8 — RAG Q&A (Phase 7 insights optional without enrichment)
