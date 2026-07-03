# Load Test Plan (100K Reviews)

**Status:** Documented plan (not executed on free-tier Gemini billing)

## Objective

Validate ingestion throughput, embedding pipeline stability, and search latency at 100K review scale.

## Prerequisites

- Gemini billing enabled (embedding + enrichment at scale)
- Postgres with ≥20 GB disk
- Celery workers (≥2) with Redis
- `ADMIN_API_KEY` configured

## Test matrix

| Stage | Volume | Success criteria |
|-------|--------|------------------|
| Ingest | 100K CSV rows | <2% rejection rate, <4 hours |
| Embed | 100K reviews | Resumable batches, DLQ <1% |
| Search | 100 queries | p95 latency <500ms (excluding embed) |
| Ask | 50 queries | p95 latency <15s |

## Procedure

### 1. Baseline metrics

```powershell
curl http://localhost:8000/api/v1/metrics
curl "http://localhost:8000/health?detailed=true"
```

### 2. Ingest in batches

```powershell
python scripts/run_pipeline.py ingest --source csv --file phases/phase-1/data/spotify_reviews.csv --limit 10000
# Repeat 10x or use full 84K dataset multiple passes with unique source_ids
```

Record: inserts/min, duplicates, rejections.

### 3. Embed in batches

```powershell
python scripts/run_pipeline.py embed --limit 5000 --concurrency 1
# Repeat until unembedded count = 0
```

Monitor: `GET /api/v1/metrics` embed_success / embed_failed.

### 4. Search load

Use `hey` or `k6` against `POST /api/v1/search` with 10 concurrent users, 100 requests.

### 5. Failure recovery

- Stop worker mid-embed
- Verify `embed --all` skips completed chunks (idempotent)
- Inspect DLQ: `redis-cli LRANGE dlq:embed_reviews_task 0 5`

## Current project baseline (local)

- ~1,354 reviews ingested
- ~1,030 embedded
- Free-tier Gemini — **not suitable for full 100K embed test**

## Sign-off

| Role | Criteria met | Date |
|------|--------------|------|
| Engineering | Ingest + embed resumable | |
| Product | Search/ask acceptable latency | |
