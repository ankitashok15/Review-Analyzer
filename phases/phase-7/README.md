# Phase 7 — Insight Generation

**Status:** Complete  
**Depends on:** [Phase 3](../phase-3/README.md) (enrichment data), [Phase 5](../phase-5/README.md), [Phase 6](../phase-6/README.md)

## Objective

Aggregate enriched reviews into evidence-backed product insights: pain points, feature requests, trends, segments, and themes.

## Deliverables

| Item | Location |
|------|----------|
| Insight schemas | `src/insights/schemas.py` |
| Aggregator | `src/insights/aggregator.py` |
| Trend analyzer | `src/insights/trend_analyzer.py` |
| Theme detector | `src/insights/theme_detector.py` |
| Insight service + cache | `src/insights/service.py` |
| Migration | `alembic/versions/005_insights_cache.py` |
| API routes | `src/api/routes/insights.py` |
| Celery task | `src/workers/tasks.py` → `refresh_insights_task` |
| Tests | `tests/test_insights.py` |

## Migration

```powershell
alembic upgrade head
```

Table: `insights_cache` — stores precomputed insights keyed by `(insight_type, cache_key)`.

## Insight types

| Type | Description |
|------|-------------|
| `pain_points` | Top recurring pain points with counts + evidence |
| `feature_requests` | Top requested features |
| `platform_comparison` | Sentiment by source/platform |
| `trends` | Topic frequency period-over-period delta |
| `segments` | Sentiment breakdown by user segment |
| `themes` | Clustered pain points + JTBD statements |

## API

```powershell
uvicorn src.api.main:app --reload --port 8000
```

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/insights` | List all cached insights |
| GET | `/api/v1/insights/{type}` | Get insight by type |
| GET | `/api/v1/insights/{type}?refresh=true` | Regenerate then return |
| POST | `/api/v1/insights/refresh` | Refresh all standard insights |

Example:

```powershell
curl http://localhost:8000/api/v1/insights/pain_points?refresh=true
```

## Prerequisites

Enriched reviews in `review_enrichments`:

```powershell
python scripts/run_pipeline.py enrich --limit 100 --concurrency 1
```

Works with sparse enrichment data; richer insights need more enriched reviews.

## Async refresh (Celery)

```powershell
celery -A src.workers.celery_app worker --loglevel=info -P solo
# Queue: refresh_insights_task.delay()
```

## Verify

```powershell
pytest tests/test_insights.py -v
```

## Exit criteria

- [x] Top pain points / feature requests with evidence review IDs
- [x] Trend insight with period-over-period comparison
- [x] Insights API consumable by frontend
- [x] Cache upsert — regenerate does not duplicate rows
- [x] MVP aggregations (advanced embedding clustering deferred)

## Next phase

→ Phase 8 — RAG-Based Natural Language Q&A (`phases/phase-8/README.md`)
