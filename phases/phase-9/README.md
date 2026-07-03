# Phase 9 — Research Dashboard & API Surface

**Status:** Complete  
**Depends on:** [Phase 6](../phase-6/README.md), [Phase 7](../phase-7/README.md), [Phase 8](../phase-8/README.md)

## Objective

Deliver a research-oriented UI and complete REST API for search, Q&A, insights, topics, segments, export, and ingestion.

## Deliverables

### Backend API

| Item | Location |
|------|----------|
| API schemas | `src/api/schemas.py` |
| Serializers | `src/api/serializers.py` |
| Review detail | `src/api/routes/reviews.py` |
| Topics | `src/api/routes/topics.py` |
| Segments | `src/api/routes/segments.py` |
| Export | `src/api/routes/export.py` |
| Ingest (admin) | `src/api/routes/ingest.py` |
| CORS | `src/api/main.py` + `CORS_ORIGINS` in settings |
| Tests | `tests/test_dashboard_api.py` |

### Frontend (`frontend/`)

| Item | Location |
|------|----------|
| Vite + React + TypeScript | `frontend/package.json` |
| Tailwind CSS | `frontend/tailwind.config.js` |
| API client | `frontend/src/services/api.ts` |
| Layout + shared components | `frontend/src/components/` |
| Pages | `frontend/src/pages/` |

## API endpoints (complete surface)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/search` | Semantic search |
| POST | `/api/v1/ask` | RAG Q&A |
| GET | `/api/v1/insights` | List cached insights |
| GET | `/api/v1/reviews/{id}` | Review + enrichment |
| GET | `/api/v1/topics` | Topic clusters |
| GET | `/api/v1/segments` | Segment breakdown |
| POST | `/api/v1/export` | CSV/JSON export |
| POST | `/api/v1/ingest` | Trigger CSV ingestion |

## Run locally

### 1. Backend

```powershell
docker compose up -d
uvicorn src.api.main:app --reload --port 8000
```

### 2. Frontend

```powershell
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173** — Vite proxies `/api` and `/health` to port 8000.

Optional `.env`:

```env
VITE_API_URL=
```

Leave empty to use the Vite dev proxy.

### 3. CORS (production)

In root `.env`:

```env
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

## E2E demo flow

1. Start Docker + API + frontend
2. **Search** — query e.g. "repetitive recommendations"
3. Click a result → **Review Detail**
4. **Ask** — sample research question with citations
5. **Insights** → Refresh (needs enriched reviews)
6. **Export** — paste review IDs from search/ask

CLI alternative for ingest:

```powershell
python scripts/run_pipeline.py ingest --source csv --limit 100
# or via API:
curl -X POST http://localhost:8000/api/v1/ingest -H "Content-Type: application/json" -d "{\"limit\": 100}"
```

## Pages

| Page | Route | Features |
|------|-------|----------|
| Search | `/` | NL query, filters, result cards |
| Ask | `/ask` | Chat-style Q&A, markdown answer, citations |
| Insights | `/insights` | Cached insights + evidence links |
| Topics | `/topics` | Topic clusters from enrichments |
| Segments | `/segments` | Segment × sentiment table |
| Export | `/export` | JSON preview or CSV download |
| Review Detail | `/reviews/:id` | Full review + enrichment |

## Verify

```powershell
pytest tests/test_dashboard_api.py -v
cd frontend && npm run build
```

## Exit criteria

- [x] Remaining API routes implemented
- [x] CORS enabled for frontend origin
- [x] MVP pages: Search, Ask, Review Detail
- [x] Full pages: Insights, Topics, Segments, Export
- [x] Shared components: EvidencePanel, CitationCard, FilterBar, Layout
- [x] Typed API client with TanStack Query
- [x] Desktop-friendly layout (1280px+)

## Next phase

→ Phase 10 — Production Hardening (`phases/phase-10/README.md`)
