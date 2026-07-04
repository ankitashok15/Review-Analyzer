# Deploy API on Vercel

Host the FastAPI backend on [Vercel](https://vercel.com) (free Hobby tier) with **Neon** as the database and **GitHub Pages** for the frontend.

```
GitHub Pages  →  React UI
Vercel        →  FastAPI API
Neon          →  PostgreSQL + pgvector
```

---

## Prerequisites

- Neon database populated (you already have 1,354 reviews + 1,034 embeddings)
- GitHub repo: `ankitashok15/Review-Analyzer`
- Vercel account (free): [vercel.com/signup](https://vercel.com/signup)

---

## Step 1 — Import project on Vercel

1. Go to [vercel.com/new](https://vercel.com/new)
2. **Import** `ankitashok15/Review-Analyzer`
3. Configure:

| Setting | Value |
|---------|-------|
| Framework Preset | **Other** |
| Root Directory | `.` (repo root) |
| Build Command | *(leave empty)* |
| Output Directory | *(leave empty — do NOT set `frontend/dist`)* |
| Install Command | `pip install -r api/requirements.txt` *(or leave empty if using `pyproject.toml` deps)* |

4. Do **not** deploy yet — add environment variables first.

---

## Step 2 — Environment variables

In Vercel project → **Settings** → **Environment Variables**, add for **Production**:

| Key | Value |
|-----|-------|
| `DATABASE_URL` | Neon **pooled** connection string (`postgresql://...-pooler...`) |
| `GOOGLE_API_KEY` | Google AI Studio API key |
| `ADMIN_API_KEY` | Random secret (~40 chars) |
| `GEMINI_RAG_MODEL` | `gemini-2.5-pro` |
| `GEMINI_EMBEDDING_MODEL` | `gemini-embedding-001` |
| `VECTOR_DIMENSION` | `768` |
| `CORS_ORIGINS` | `https://ankitashok15.github.io,http://localhost:5173` |
| `REQUIRE_ADMIN_API_KEY` | `true` |
| `LOG_FORMAT` | `text` |

Optional (Redis not required on Vercel):

| Key | Value |
|-----|-------|
| `REDIS_URL` | Leave unset — health shows redis disconnected, API still works |

Click **Deploy**.

Your API URL:

```
https://review-analyzer-XXXX.vercel.app
```

(or the name Vercel assigns)

---

## Step 3 — Verify API

```powershell
curl https://YOUR-PROJECT.vercel.app/health
```

Expected:

```json
{"status":"ok","db":"connected","service":"review-discovery-engine"}
```

Swagger UI: `https://YOUR-PROJECT.vercel.app/docs`

Root URL `https://YOUR-PROJECT.vercel.app/` should return a JSON welcome payload (not 404).

---

## Step 4 — Connect GitHub Pages frontend

1. GitHub → `ankitashok15/Review-Analyzer` → **Settings** → **Secrets and variables** → **Actions** → **Variables**
2. Set **`RENDER_API_URL`** = `https://YOUR-PROJECT.vercel.app` (no trailing slash)
3. **Actions** → **Deploy Frontend to GitHub Pages** → **Run workflow**

Test: https://ankitashok15.github.io/Review-Analyzer/

---

## Repo files for Vercel

| File | Purpose |
|------|---------|
| `api/index.py` | Vercel serverless entrypoint |
| `api/requirements.txt` | Python deps for the function |
| `vercel.json` | Rewrites all routes + bundles `src/`, `config/`, `alembic/` |
| `requirements-vercel.txt` | Production Python deps (no pytest/celery) |
| `pyproject.toml` | `tool.vercel.entrypoint` |
| `.vercelignore` | Excludes frontend, tests, docs from upload |

---

## Limitations

| Limit | Detail |
|-------|--------|
| **Timeout** | `maxDuration: 60` in `vercel.json` — **Ask/RAG** may need Vercel Pro for reliable 60s; Hobby may cap at 10s |
| **No Celery** | Async ingest/enrich jobs unavailable — run pipelines locally |
| **No Redis** | Insight list cache falls back to Postgres |
| **Cold starts** | First request after idle may take 1–3s |
| **Gemini quota** | Same free-tier limits as local |

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| 404 on all routes | Clear **Output Directory** in Vercel Settings; redeploy latest `main` |
| 404 on `/` or `/health` | Ensure `vercel.json` rewrites exist; check deployment **Functions** tab shows `api/index.py` |
| `ModuleNotFoundError: fastapi` | Ensure `pyproject.toml` has `[project].dependencies` and redeploy |
| `db: disconnected` | Use Neon **pooled** URL; prefix `postgresql://` not `postgres://` |
| CORS errors | Add `https://ankitashok15.github.io` to `CORS_ORIGINS` |
| 504 timeout on Ask | Gemini slow + Hobby 10s limit — retry or upgrade Vercel plan |
| Frontend 404 on API | Confirm `RENDER_API_URL` has no trailing slash |

---

## Local Vercel dev (optional)

```powershell
npm i -g vercel
vercel login
vercel link
vercel env pull .env.local
vercel dev
```

---

## Architecture summary

| Layer | Service | URL |
|-------|---------|-----|
| Frontend | GitHub Pages | https://ankitashok15.github.io/Review-Analyzer/ |
| API | Vercel | https://YOUR-PROJECT.vercel.app |
| Database | Neon | External (connection string only) |
