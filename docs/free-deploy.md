# Deploy for Free (Neon + Koyeb)

**Recommended path.** Host the FastAPI backend and PostgreSQL at **$0/month** with no credit card required (in most regions).

| Component | Service | Cost |
|-----------|---------|------|
| PostgreSQL + pgvector | [Neon](https://neon.tech) | Free (0.5 GB, 100 compute-hrs/mo) |
| FastAPI API | [Koyeb](https://koyeb.com) | Free (1 web service, 512 MB RAM) |
| Redis (optional) | [Upstash](https://upstash.com) | Free tier — or skip (app works without it) |
| React dashboard | GitHub Pages | Free (already set up) |

> **Why not Render?** Render’s free Postgres expires after 30 days and often requires a credit card for Docker. See [render-deploy.md](render-deploy.md) only if you prefer Render paid hosting.

---

## Overview

1. Create Neon database and load review data
2. Deploy API on Koyeb from GitHub
3. Connect GitHub Pages frontend to the live API
4. Verify Search, Ask, and Insights

---

## Phase 1 — Neon database (free)

### 1a. Create project

1. Sign up at [neon.tech](https://neon.tech) (no credit card).
2. **New project** → name e.g. `review-engine` → region closest to you.
3. Copy the **connection string** (use the **pooled** URL for serverless — host contains `-pooler`).

Example format:

```
postgresql://user:password@ep-xxx-pooler.region.aws.neon.tech/neondb?sslmode=require
```

### 1b. Enable pgvector

In Neon **SQL Editor**, run:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

> Alembic migration `001` also runs this on deploy, but running it once upfront avoids surprises.

### 1c. Migrate schema from your PC

Temporarily point your local environment at Neon:

```powershell
cd "c:\Users\Hp\OneDrive\Desktop\Spotify Review Analyser"
.\.venv\Scripts\Activate.ps1

$env:DATABASE_URL = "postgresql://USER:PASS@ep-xxx-pooler.region.aws.neon.tech/neondb?sslmode=require"
alembic upgrade head
```

### 1d. Load reviews and embeddings

```powershell
$env:GOOGLE_API_KEY = "your-google-ai-studio-key"

# Ingest Spotify reviews
python scripts/run_pipeline.py ingest --source csv --file phases/phase-1/data/spotify_reviews.csv

# Embeddings (Gemini free tier ~1000/day — run in batches if needed)
python scripts/run_pipeline.py embed --all --concurrency 1

# Optional enrichment
python scripts/run_pipeline.py enrich --limit 200 --concurrency 1
```

Confirm in Neon SQL Editor:

```sql
SELECT COUNT(*) FROM reviews;
SELECT COUNT(*) FROM review_embeddings;
```

---

## Phase 2 — Koyeb API (free)

### 2a. Connect GitHub

1. Sign up at [koyeb.com](https://koyeb.com).
2. **Create Web Service** → **GitHub** as deploy source.
3. If `Review-Analyzer` is missing, authorize Koyeb for `ankitashok15/Review-Analyzer` (same flow as Render — GitHub → Settings → Applications → Koyeb → configure repo access).

### 2b. Service settings

| Setting | Value |
|---------|-------|
| Repository | `ankitashok15/Review-Analyzer` |
| Branch | `main` |
| Builder | **Dockerfile** |
| Dockerfile path | `./Dockerfile` |
| Exposed port | `8000` |
| Instance type | **Free** (Frankfurt or Washington only) |
| Health check path | `/health` |

### 2c. Environment variables

In Koyeb → your service → **Variables**:

| Key | Value | Required |
|-----|-------|----------|
| `DATABASE_URL` | Neon **pooled** connection string | Yes |
| `GOOGLE_API_KEY` | Google AI Studio API key | Yes |
| `ADMIN_API_KEY` | Long random secret (~40 chars) | Yes |
| `GEMINI_RAG_MODEL` | `gemini-2.5-pro` | Yes |
| `GEMINI_EMBEDDING_MODEL` | `gemini-embedding-001` | Yes |
| `VECTOR_DIMENSION` | `768` | Yes |
| `CORS_ORIGINS` | `https://ankitashok15.github.io,http://localhost:5173` | Yes |
| `REQUIRE_ADMIN_API_KEY` | `true` | Yes |
| `LOG_FORMAT` | `text` | Recommended |
| `REDIS_URL` | Upstash URL (see Phase 2e) | Optional |

**Note:** If Neon gives `postgres://`, change the prefix to `postgresql://` if you see SQLAlchemy connection errors.

### 2d. Deploy

Click **Deploy**. First build takes ~5–10 minutes.

Your API URL will look like:

```
https://review-analyzer-YOUR-ORG.koyeb.app
```

Verify:

```powershell
curl https://YOUR-APP.koyeb.app/health
```

Expected: `"db":"connected"` (Redis may show disconnected — that is OK without Upstash).

API docs: `https://YOUR-APP.koyeb.app/docs`

### 2e. Optional — Upstash Redis (free)

Only needed for insight list caching and Celery. The API works without it.

1. [console.upstash.com](https://console.upstash.com) → **Create database** → Redis.
2. Copy **Redis URL** → set `REDIS_URL` on Koyeb → redeploy.

---

## Phase 3 — Connect GitHub Pages frontend

The React app bakes the API URL in at build time.

### 3a. Set GitHub Actions variable

1. GitHub → `ankitashok15/Review-Analyzer` → **Settings**
2. **Secrets and variables** → **Actions** → **Variables**
3. **New repository variable**
   - **Name:** `RENDER_API_URL` (legacy name — works for any API host)
   - **Value:** `https://YOUR-APP.koyeb.app` (no trailing slash)

### 3b. Redeploy frontend

**Actions** → **Deploy Frontend to GitHub Pages** → **Run workflow**

Or push any change under `frontend/`.

### 3c. Test end-to-end

1. Open https://ankitashok15.github.io/Review-Analyzer/
2. **Search** — e.g. "shuffle playlist"
3. **Ask** — e.g. "What do users complain about ads?"
4. **Insights** — lists cached insights if you generated them in Phase 1d

If API calls fail, open browser DevTools → **Network** and check for CORS errors. Ensure `CORS_ORIGINS` includes exactly `https://ankitashok15.github.io`.

---

## Phase 4 — Update README live links (optional)

After deploy, add your URLs to the repo README:

| Resource | Example |
|----------|---------|
| Live API | `https://your-app.koyeb.app` |
| API docs | `https://your-app.koyeb.app/docs` |
| Frontend | `https://ankitashok15.github.io/Review-Analyzer/` |

---

## Free tier limits

| Service | Limit | Impact |
|---------|-------|--------|
| **Neon** | 0.5 GB storage, 100 compute-hrs/mo | Enough for ~1k reviews + embeddings; DB sleeps after ~5 min idle (wakes on query) |
| **Koyeb Free** | 1 service, 512 MB RAM, scales to zero after 1 hr idle | First request after idle may take a few seconds |
| **Gemini** | ~1000 embeds/day on free tier | Embed in daily batches |
| **GitHub Pages** | 100 GB bandwidth/mo | Fine for portfolio demo |

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `db: disconnected` on `/health` | Wrong `DATABASE_URL`; use Neon **pooled** string; check `sslmode=require` |
| CORS error in browser | Add `https://ankitashok15.github.io` to `CORS_ORIGINS` on Koyeb |
| Search returns empty | Neon DB empty — rerun Phase 1d ingest + embed |
| Koyeb build fails | Check **Logs**; often missing `GOOGLE_API_KEY` or bad `DATABASE_URL` |
| Neon "compute limit" | Free 100 hrs/mo exhausted — wait for reset or upgrade |
| Koyeb asks for credit card | Try a different region (Frankfurt/Washington) or contact Koyeb support |

---

## Local development (unchanged)

```powershell
docker compose up -d
uvicorn src.api.main:app --reload --port 8000
cd frontend && npm run dev
```

---

## Quick reference

```powershell
# Health check
curl https://YOUR-APP.koyeb.app/health

# Search (no admin key needed)
curl -X POST https://YOUR-APP.koyeb.app/api/v1/search `
  -H "Content-Type: application/json" `
  -d '{"query": "billing issues", "top_k": 5}'

# Ask
curl -X POST https://YOUR-APP.koyeb.app/api/v1/ask `
  -H "Content-Type: application/json" `
  -d '{"question": "What do users dislike about ads?"}'
```
