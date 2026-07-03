# Operations Runbook

## Services

```powershell
docker compose up -d
uvicorn src.api.main:app --reload --port 8000
celery -A src.workers.celery_app worker --loglevel=info -P solo
cd frontend && npm run dev
```

## Health & metrics

| Endpoint | Purpose |
|----------|---------|
| `GET /health` | DB + Redis status |
| `GET /health?detailed=true` | + Celery workers + Gemini config |
| `GET /api/v1/metrics` | API/pipeline counters |
| `GET /api/v1/jobs/{id}` | Celery job status |

## Ingest reviews (CSV)

```powershell
python scripts/run_pipeline.py ingest --source csv --file phases/phase-1/data/spotify_reviews.csv --limit 1000
```

API (requires `X-API-Key`):

```powershell
curl -X POST http://localhost:8000/api/v1/ingest `
  -H "Content-Type: application/json" `
  -H "X-API-Key: $env:ADMIN_API_KEY" `
  -d "{\"source\": \"csv\", \"limit\": 500}"
```

## Re-enrich

```powershell
python scripts/run_pipeline.py enrich --limit 200 --concurrency 1
# Async:
python scripts/run_pipeline.py enrich --limit 200 --async
```

Check job: `GET /api/v1/jobs/{celery-task-id}`

## Re-embed

```powershell
python scripts/run_pipeline.py embed --all --concurrency 1
```

On Gemini free tier, run in daily batches to avoid 429 quota errors.

## Refresh insights

```powershell
curl -X POST http://localhost:8000/api/v1/insights/refresh -H "X-API-Key: $env:ADMIN_API_KEY"
```

## Rebuild vector index (HNSW)

```sql
REINDEX INDEX CONCURRENTLY ix_review_embeddings_embedding_hnsw;
```

Tune HNSW at migration time (`m=16`, `ef_construction=64` defaults in PostgreSQL/pgvector).

## Dead-letter queue (Redis)

Failed Celery tasks are recorded under `dlq:{task_name}` lists and `job:{task_id}` keys.

Inspect with `redis-cli LRANGE dlq:enrich_reviews_task 0 10`

## Raw payload archive

Set `ARCHIVE_RAW_PAYLOADS=true` and `RAW_ARCHIVE_PATH=data/raw_archive` in `.env`.

## Troubleshooting

| Symptom | Action |
|---------|--------|
| 401 on ingest/export | Pass `X-API-Key` header |
| 429 on search/ask | Rate limit — wait 1 minute |
| 429 on embed | Gemini daily quota — wait or enable billing |
| Degraded health | Check `docker compose ps`, restart Postgres/Redis |
