# Phase 3 — AI Enrichment Layer

**Status:** Complete (code) · **Runtime:** Optional  
**Depends on:** [Phase 2](../phase-2/README.md)

> **Optional for MVP.** Enrichment adds structured metadata (sentiment, topics, pain points) but is **not required** for embeddings, semantic search, or RAG. The MVP path continues at [Phase 4](../phase-4/README.md) using raw review text. Phase 7 (insights) requires enrichment data.

## Objective

Transform unstructured review text into structured metadata using **Google Gemini**, stored in `review_enrichments` without modifying `reviews.body`.

## Deliverables

| Item | Location |
|------|----------|
| Gemini client | `src/ai/gemini_client.py` |
| Enrichment schemas | `src/enrichment/schemas.py` |
| Prompt template | `src/enrichment/prompts/enrichment_v1.txt` |
| Enricher service | `src/enrichment/enricher.py` |
| Celery worker | `src/workers/celery_app.py`, `src/workers/tasks.py` |
| Migration | `alembic/versions/002_enrichment_errors_and_unique.py` |
| Tests | `tests/test_enrichment.py` |

## Configuration (`.env`)

```env
GOOGLE_API_KEY=your-key
GEMINI_ENRICHMENT_MODEL=gemini-2.0-flash
REDIS_URL=redis://localhost:6379/0
```

## Enrichment fields

sentiment, emotion, primary_topic, user_goal, pain_point, feature_request, discovery_issue, listening_behavior, user_segment, keywords, summary, confidence_score

**Model version:** `enrichment-v1`  
**Default concurrency:** 5 parallel Gemini requests

## Usage

### Sync enrichment (CLI)

```powershell
# Enrich 200 reviews
python scripts/run_pipeline.py enrich --limit 200

# Enrich all unenriched reviews
python scripts/run_pipeline.py enrich --all
```

### Async enrichment (Celery)

Terminal 1 — start worker:
```powershell
celery -A src.workers.celery_app worker --loglevel=info -P solo
```

Terminal 2 — queue job:
```powershell
python scripts/run_pipeline.py enrich --limit 200 --async
```

## Verify enrichments

```powershell
pytest tests/test_enrichment.py -v
```

```sql
SELECT COUNT(*) FROM review_enrichments;
SELECT sentiment, COUNT(*) FROM review_enrichments GROUP BY sentiment;
SELECT * FROM enrichment_errors LIMIT 10;
```

## Exit criteria

- [x] Gemini client with JSON mode + retry
- [x] Enrichment stored separately from raw reviews
- [x] Skip if already enriched for `enrichment-v1`
- [x] Failed enrichments logged to `enrichment_errors`
- [x] Celery task for async processing
- [x] CLI `enrich` command

## Next phase

→ Phase 4 — Embedding Generation & Vector Storage
