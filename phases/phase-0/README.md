# Phase 0 — Foundation & Infrastructure

**Status:** Complete  
**Depends on:** Nothing  
**Verified:** July 2026

## Objective

Establish project skeleton, configuration, database, Docker services, and a health-check API.

## Deliverables

| Item | Location |
|------|----------|
| Settings & env config | `config/settings.py`, `.env.example` |
| Docker Compose (Postgres + Redis) | `docker-compose.yml` |
| Database models | `src/storage/models/__init__.py` |
| Alembic migrations | `alembic/`, `alembic/versions/001_initial_schema.py` |
| FastAPI app + `/health` | `src/api/main.py` |
| Tests | `tests/test_health.py`, `tests/test_settings.py` |
| Project docs | `README.md` |

## Infrastructure

| Service | Container | Host port |
|---------|-----------|-----------|
| PostgreSQL + pgvector | `review_engine_postgres` | **5434** |
| Redis | `review_engine_redis` | **6379** |

> Port **5434** is used because **5432** and **5433** were already taken on the dev machine.

## Verification commands

```powershell
docker compose up -d postgres redis
alembic upgrade head
uvicorn src.api.main:app --reload --port 8000
curl http://localhost:8000/health
pytest tests/test_health.py tests/test_settings.py -v
```

## Exit criteria

- [x] Docker services start without errors
- [x] `/health` returns 200 with `"db": "connected"`
- [x] Migrations apply on empty database
- [x] Settings load from `.env`

## Next phase

→ [Phase 1 — Data Ingestion](../phase-1/README.md)
