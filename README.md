# Review Discovery Engine

AI-powered platform that transforms unstructured user feedback into structured, searchable, evidence-backed product intelligence.

## Links

| Resource | URL |
|----------|-----|
| **Repository** | https://github.com/ankitashok15/Review-Analyzer |
| **Live Dashboard (Frontend)** | https://ankitashok15.github.io/Review-Analyzer/ |
| **Deploy backend (free — recommended)** | [docs/free-deploy.md](docs/free-deploy.md) |
| **Deploy backend (Render — paid/long-term)** | [docs/render-deploy.md](docs/render-deploy.md) |
| **API docs (local)** | http://localhost:8000/docs |

> **Free hosting:** Deploy the API on [Koyeb](https://koyeb.com) + database on [Neon](https://neon.tech) — see [free deploy guide](docs/free-deploy.md). Set GitHub variable `RENDER_API_URL` to your API URL, then redeploy the frontend.

## Stack

- **API:** FastAPI 0.139+
- **Database:** PostgreSQL 16 + pgvector
- **Queue:** Redis (Celery in later phases)
- **AI:** Google Gemini (`google-genai`)

## Prerequisites

- Python 3.11+
- Docker Desktop

## Setup

### 1. Environment

```powershell
cd "c:\Users\Hp\OneDrive\Desktop\Spotify Review Analyser"
copy .env.example .env
```

Edit `.env` if needed. Default Postgres host port is **5434** (5433 was already in use on this machine).

### 2. Virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 3. Start services

```powershell
docker compose up -d postgres redis
```

> **Note:** Host port **5434** is used because **5433** is already taken by another Postgres container. Change ports in `docker-compose.yml` and `DATABASE_URL` if needed.

### 4. Run migrations

```powershell
alembic upgrade head
```

### 5. Start API

```powershell
uvicorn src.api.main:app --reload --port 8000
```

### 6. Verify

```powershell
curl http://localhost:8000/health
pytest tests/ -v
```

Expected health response:

```json
{
  "status": "ok",
  "db": "connected",
  "service": "review-discovery-engine"
}
```

## Project structure

```
config/          Settings and source configuration
phases/          Phase deliverables, docs, and datasets
  phase-0/       Foundation (see README)
  phase-1/       Ingestion + spotify_reviews.csv
  phase-2/       Validation pipeline docs
src/api/         FastAPI application
src/ingestion/   Data ingestion framework (Phase 1)
src/pipeline/    Validation, cleaning, dedup (Phase 2)
src/ai/          Google Gemini client (Phase 3)
src/enrichment/  AI enrichment layer (Phase 3, optional)
src/embeddings/  Chunking and embedding pipeline (Phase 4)
src/retrieval/   Semantic search service (Phase 6)
src/insights/    Insight generation (Phase 7)
src/workers/     Celery background jobs (Phase 3)
src/storage/     Database models, vector store, repositories (Phase 5)
alembic/         Database migrations
tests/           Unit tests
scripts/         CLI tools
```

## Ingest reviews (Phase 1)

```powershell
python scripts/run_pipeline.py ingest --source csv --file phases/phase-1/data/spotify_reviews.csv --limit 100
```

See `phases/phase-1/README.md` for full ingestion commands.

## Phase status

- [x] Phase 0 — Foundation & Infrastructure
- [x] Phase 1 — Data Ingestion
- [x] Phase 2 — Validation & Cleaning
- [x] Phase 3 — AI Enrichment *(optional at runtime — code complete, not required for MVP)*
- [x] Phase 4 — Embeddings
- [x] Phase 5 — Repository layer
- [x] Phase 6 — Semantic search API
- [x] Phase 7 — Insight generation API
- [x] Phase 8 — RAG Q&A API
- [x] Phase 9 — React dashboard
- [x] Phase 10 — Production hardening & CI/CD

**MVP path without bulk enrichment:** ingest → embed → search/RAG (Phases 4–6). Phase 7 needs enriched reviews. Enrichment can be run later via `python scripts/run_pipeline.py enrich` when API quota allows.

See `Architecture.md`, `ImplementationPlan.md`, and `phases/README.md` for full roadmap.
