# Phase 10 — Production Hardening, Observability & Scale

**Status:** Complete  
**Depends on:** [Phase 9](../phase-9/README.md)  
**GitHub:** [ankitashok15/Review-Analyzer](https://github.com/ankitashok15/Review-Analyzer)

## Your configuration

| Setting | Value |
|---------|-------|
| Environment | local-only |
| Priority | security, CI/CD, observability |
| Adapters | SKIP (CSV only) |
| Load test | document plan only |
| Gemini billing | No |
| Admin API key | `.env` → `ADMIN_API_KEY` |
| Rate limits | 60/min ask, 120/min search |

## Deliverables

### 10.1 Observability

| Item | Location |
|------|----------|
| JSON logging | `src/observability/logging_config.py` |
| Request ID middleware | `src/observability/middleware.py` |
| Metrics store | `src/observability/metrics.py` |
| Extended health | `src/observability/health.py`, `GET /health?detailed=true` |
| Metrics API | `GET /api/v1/metrics` |

### 10.2 Error handling

| Item | Location |
|------|----------|
| Job store (Redis) | `src/observability/metrics.py` → `JobStore` |
| Dead-letter queue | Redis `dlq:{task_name}` |
| Celery retries | `src/workers/celery_app.py`, `src/workers/tasks.py` (max 3, backoff) |
| Job status API | `GET /api/v1/jobs/{id}` |

### 10.3 Security

| Item | Location |
|------|----------|
| Admin API key auth | `src/security/auth.py` on ingest/export/insights refresh |
| Rate limiting | `src/security/rate_limit.py` on search/ask |
| Input sanitization | `src/security/sanitize.py` |
| Secrets rotation doc | `docs/secrets-rotation.md` |

### 10.4 Performance

| Item | Location |
|------|----------|
| DB connection pool | `config/settings.py`, `src/storage/database.py` |
| Redis insight cache | `src/cache/insight_cache.py` (1h TTL) |
| Raw payload archive | `src/ingestion/archiver.py` (opt-in via env) |
| HNSW / batch notes | `docs/runbook.md` |

### 10.5 Adapters

**Skipped per your request.** Adapter pattern documented in `docs/adapter-development-guide.md` (CSV as proof).

### 10.6 CI/CD

| Item | Location |
|------|----------|
| GitHub Actions | `.github/workflows/ci.yml` |
| API Docker image | `Dockerfile` |
| Worker Docker image | `Dockerfile.worker` |
| Ruff lint | `ruff.toml` |

### 10.7 Documentation

| Doc | Path |
|-----|------|
| Runbook | `docs/runbook.md` |
| Load test plan | `docs/load-test-plan.md` |
| pgvector → Qdrant | `docs/scale-migration-qdrant.md` |
| Secrets rotation | `docs/secrets-rotation.md` |
| Adapter guide | `docs/adapter-development-guide.md` |
| OpenAPI | `http://localhost:8000/docs` |

## Environment variables (`.env`)

```env
ADMIN_API_KEY=your-40-char-key
ADMIN_API_KEY_HEADER=X-API-Key
REQUIRE_ADMIN_API_KEY=true
RATE_LIMIT_ASK_PER_MINUTE=60
RATE_LIMIT_SEARCH_PER_MINUTE=120
LOG_FORMAT=json
INSIGHT_CACHE_TTL_SECONDS=3600
ARCHIVE_RAW_PAYLOADS=false
RAW_ARCHIVE_PATH=data/raw_archive
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
```

## Admin API usage

```powershell
curl -X POST http://localhost:8000/api/v1/ingest `
  -H "Content-Type: application/json" `
  -H "X-API-Key: $env:ADMIN_API_KEY" `
  -d "{\"source\": \"csv\", \"limit\": 10}"
```

## Verify

```powershell
pytest tests/test_hardening.py tests/test_dashboard_api.py -v
curl "http://localhost:8000/health?detailed=true"
curl http://localhost:8000/api/v1/metrics
ruff check src tests
```

## Exit criteria

- [x] Structured JSON logging + request IDs
- [x] Metrics + extended health checks
- [x] DLQ + job status + Celery retries
- [x] Admin auth + rate limits + sanitization
- [x] Redis insight cache + DB pool tuning
- [x] Load test **plan** documented (not executed — no Gemini billing)
- [x] Adapter pattern documented (CSV proof; live adapters skipped)
- [x] GitHub Actions CI + Dockerfiles
- [x] Runbook + scale + secrets docs

## Project complete

All phases **0–10** implemented. Optional next steps: push to GitHub, enable billing for full embed/enrich, add Reddit/App Store adapters when credentials are available.
