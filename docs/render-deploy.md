# Deploy on Render

Step-by-step guide to deploy the **Review Discovery Engine** backend (FastAPI) on [Render](https://render.com), connect the **GitHub Pages** frontend, and load your review data.

## What gets deployed

| Component | Render service | Notes |
|-----------|----------------|-------|
| FastAPI API | **Web Service** (Docker) | Search, Ask, Insights, health |
| PostgreSQL + pgvector | **PostgreSQL** | Embeddings + reviews |
| Redis | **Key Value** | Cache, Celery broker (optional worker) |
| React dashboard | **GitHub Pages** (existing) | Points to Render API via `VITE_API_URL` |

Streamlit is **not** used for this deployment path.

---

## Overview (5 phases)

1. Create Render account and connect GitHub
2. Create PostgreSQL + Redis + Web Service
3. Set environment variables and deploy API
4. Migrate schema and load review data
5. Wire GitHub Pages frontend to the live API

---

## Phase 1 — Prepare GitHub

Your repo is already on GitHub: `ankitashok15/Review-Analyzer`.

Confirm these files exist on `main`:

- `Dockerfile` — API container (runs migrations on start)
- `render.yaml` — optional Blueprint for one-click setup
- `scripts/start_api.sh` — migrate + start uvicorn

---

## Phase 2 — Create Render services

### Option A: Blueprint (faster)

1. Go to [dashboard.render.com](https://dashboard.render.com) → **New** → **Blueprint**.
2. Connect GitHub → select `ankitashok15/Review-Analyzer`.
3. Render reads `render.yaml` and proposes:
   - `review-engine-db` (PostgreSQL 16)
   - `review-engine-redis` (Key Value)
   - `review-analyzer-api` (Web Service)
4. Click **Apply**.

### Option B: Manual (dashboard)

#### 2a. PostgreSQL

1. **New** → **PostgreSQL**
2. Name: `review-engine-db`
3. Database: `review_engine`
4. PostgreSQL version: **16**
5. Plan: **Free** (fine for demo; expires after 90 days on free tier)
6. Create → copy **Internal Database URL** (for Render services) and **External Database URL** (for your PC)

pgvector is enabled automatically by Alembic migration `001` (`CREATE EXTENSION vector`).

#### 2b. Redis (Key Value)

1. **New** → **Key Value**
2. Name: `review-engine-redis`
3. Plan: **Free**
4. Create

#### 2c. Web Service (API)

1. **New** → **Web Service**
2. Connect `ankitashok15/Review-Analyzer`
3. Settings:

| Setting | Value |
|---------|-------|
| Name | `review-analyzer-api` |
| Region | Closest to you |
| Branch | `main` |
| Runtime | **Docker** |
| Dockerfile path | `./Dockerfile` |
| Plan | **Free** |
| Health check path | `/health` |

4. Do **not** deploy yet — add env vars first (Phase 3).

---

## Phase 3 — Environment variables

On the **review-analyzer-api** Web Service → **Environment**:

| Key | Value | Required |
|-----|-------|----------|
| `DATABASE_URL` | From Postgres → **Internal Database URL** | Yes |
| `REDIS_URL` | From Key Value → **Internal Redis URL** | Yes |
| `GOOGLE_API_KEY` | Your [Google AI Studio](https://aistudio.google.com/apikey) key | Yes |
| `ADMIN_API_KEY` | Long random secret (e.g. 40 chars) | Yes |
| `GEMINI_RAG_MODEL` | `gemini-2.5-pro` | Yes |
| `GEMINI_EMBEDDING_MODEL` | `gemini-embedding-001` | Yes |
| `VECTOR_DIMENSION` | `768` | Yes |
| `REQUIRE_ADMIN_API_KEY` | `true` | Yes |
| `CORS_ORIGINS` | `https://ankitashok15.github.io,http://localhost:5173` | Yes |
| `LOG_FORMAT` | `text` | Recommended |

**Important:** Render Postgres URLs may start with `postgres://`. SQLAlchemy accepts them; if you see connection errors, change the prefix to `postgresql://`.

Click **Save Changes** → **Manual Deploy** → **Deploy latest commit**.

Wait for build (~5–10 min first time). When live, note your API URL:

`https://review-analyzer-api.onrender.com` (your name may differ)

### Verify API

```powershell
curl https://YOUR-SERVICE.onrender.com/health
```

Expected: `{"status":"ok","db":"connected","redis":"connected",...}`

API docs: `https://YOUR-SERVICE.onrender.com/docs`

> Free Web Services **spin down after ~15 min idle**. First request after sleep takes 30–60 seconds.

---

## Phase 4 — Database schema and data

The API runs `alembic upgrade head` on every container start. After first deploy, tables exist but are **empty**.

### Option 1: Re-ingest from your machine (recommended)

Point your local `.env` at Render **External Database URL**:

```powershell
# In .env (temporary — do not commit)
DATABASE_URL=postgresql://...@...oregon-postgres.render.com/review_engine
GOOGLE_API_KEY=your-key
```

Ensure Docker Postgres is **not** required for this step — you're writing directly to Render.

```powershell
.\.venv\Scripts\Activate.ps1

# Schema (if you want to run manually once)
alembic upgrade head

# Ingest reviews
python scripts/run_pipeline.py ingest --source csv --file phases/phase-1/data/spotify_reviews.csv

# Embeddings (respect Gemini free-tier ~1000/day)
python scripts/run_pipeline.py embed --all --concurrency 1

# Optional enrichment
python scripts/run_pipeline.py enrich --limit 200 --concurrency 1
```

### Option 2: pg_dump from local Docker

```powershell
docker exec review_engine_postgres pg_dump -U postgres -d review_engine -Fc -f /tmp/review_engine.dump
docker cp review_engine_postgres:/tmp/review_engine.dump ./review_engine.dump
```

Restore to Render (requires `pg_restore` and External URL):

```powershell
pg_restore --clean --no-owner --dbname="postgresql://USER:PASS@HOST/review_engine" review_engine.dump
```

---

## Phase 5 — Connect GitHub Pages frontend

The React app needs the Render API URL at **build time**.

### 5a. Add GitHub repository variable

1. GitHub → `ankitashok15/Review-Analyzer` → **Settings** → **Secrets and variables** → **Actions** → **Variables**
2. **New repository variable**
   - Name: `RENDER_API_URL`
   - Value: `https://YOUR-SERVICE.onrender.com` (no trailing slash)

### 5b. Re-deploy frontend

Push any change to `frontend/`, or run the workflow manually:

**Actions** → **Deploy Frontend to GitHub Pages** → **Run workflow**

### 5c. Test end-to-end

1. Open https://ankitashok15.github.io/Review-Analyzer/
2. **Search** — try "shuffle playlist problems"
3. **Ask** — try "What do users dislike about ads?"
4. **Insights** — should list cached insights if generated

If the UI loads but API calls fail, check browser DevTools → Network for CORS errors and confirm `CORS_ORIGINS` includes `https://ankitashok15.github.io` exactly.

---

## Optional — Celery background worker

For async ingest/enrich via API:

1. **New** → **Background Worker**
2. Docker → `Dockerfile.worker`
3. Same `DATABASE_URL`, `REDIS_URL`, `GOOGLE_API_KEY` as the API
4. Uncomment the worker block in `render.yaml` if using Blueprint

---

## Optional — Deploy frontend on Render instead of GitHub Pages

1. **New** → **Static Site**
2. Build command: `cd frontend && npm ci && npm run build`
3. Publish directory: `frontend/dist`
4. Environment variable: `VITE_API_URL=https://YOUR-SERVICE.onrender.com`
5. Add the Static Site URL to API `CORS_ORIGINS`

---

## Costs (Render free tier)

| Service | Free tier caveat |
|---------|------------------|
| Web Service | Spins down when idle; 750 hrs/month |
| PostgreSQL | **Expires after 90 days** — upgrade or export before then |
| Key Value | 25 MB, fine for cache/DLQ |

For a permanent demo, upgrade Postgres to a paid plan (~$7/mo).

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Build fails on Render | Check **Logs** tab; often missing env var |
| `db: disconnected` | Wrong `DATABASE_URL`; use **Internal** URL on Web Service |
| CORS error in browser | Add exact frontend origin to `CORS_ORIGINS` |
| Search returns nothing | DB empty or embeddings not generated — run Phase 4 |
| 429 from Gemini | Free quota; embed in daily batches |
| Slow first request | Free tier cold start — normal |

---

## Quick reference

| URL | Purpose |
|-----|---------|
| `https://YOUR-SERVICE.onrender.com` | Live API |
| `https://YOUR-SERVICE.onrender.com/docs` | Swagger UI |
| `https://YOUR-SERVICE.onrender.com/health` | Health check |
| `https://ankitashok15.github.io/Review-Analyzer/` | Live frontend |

---

## Local development (unchanged)

```powershell
docker compose up -d
uvicorn src.api.main:app --reload --port 8000
cd frontend && npm run dev
```
