# Deploy API on Railway

Host the FastAPI backend on [Railway](https://railway.app) with **Neon** as the database and **GitHub Pages** for the frontend.

```
GitHub Pages  →  React UI   (already live)
Railway       →  FastAPI API
Neon          →  PostgreSQL (already set up)
```

---

## What you already have

| Item | Status |
|------|--------|
| Neon database | 1,354 reviews, 1,034 embeddings |
| Dockerfile | Ready at repo root |
| GitHub repo | `ankitashok15/Review-Analyzer` |

---

## Step 1 — Create Railway account

1. Go to [railway.app](https://railway.app)
2. Click **Login** → **GitHub**
3. Authorize Railway for your GitHub account
4. Grant access to **`Review-Analyzer`** repo

---

## Step 2 — Create project & deploy

1. Railway dashboard → **New Project**
2. Choose **Deploy from GitHub repo**
3. Select **`ankitashok15/Review-Analyzer`**
4. Railway detects the **`Dockerfile`** and starts building

Wait ~5–10 minutes for the first build.

---

## Step 3 — Add environment variables

Click your service → **Variables** tab → **Raw Editor** and paste (replace values where noted):

```env
DATABASE_URL=postgresql://neondb_owner:YOUR_PASSWORD@ep-damp-hat-at9v5j9d-pooler.c-9.us-east-1.aws.neon.tech/neondb?sslmode=require
GOOGLE_API_KEY=your-google-ai-studio-key
ADMIN_API_KEY=your-random-40-char-secret
GEMINI_RAG_MODEL=gemini-2.5-flash-lite
GEMINI_EMBEDDING_MODEL=gemini-embedding-001
GEMINI_ENRICHMENT_MODEL=gemini-2.5-flash-lite
VECTOR_DIMENSION=768
CORS_ORIGINS=https://ankitashok15.github.io,http://localhost:5173
REQUIRE_ADMIN_API_KEY=true
LOG_FORMAT=text
LOG_LEVEL=INFO
REDIS_URL=redis://127.0.0.1:6379/0
```

| Variable | Notes |
|----------|-------|
| `DATABASE_URL` | Neon **pooled** URL from [console.neon.tech](https://console.neon.tech) |
| `GEMINI_RAG_MODEL` | Use `gemini-2.5-flash-lite` on free tier (not `gemini-2.5-pro`) |
| `REDIS_URL` | Placeholder is fine — API works without Redis |
| `PORT` | **Do not set** — Railway injects this automatically |

Click **Save**. Railway redeploys automatically.

---

## Step 4 — Generate public URL

1. Service → **Settings** → **Networking**
2. Click **Generate Domain**
3. Copy your URL, e.g.:

```
https://review-analyzer-production.up.railway.app
```

---

## Step 5 — Verify API

```powershell
curl https://YOUR-APP.up.railway.app/health
```

Expected:

```json
{"status":"ok","db":"connected","service":"review-discovery-engine"}
```

Also test:

| URL | Purpose |
|-----|---------|
| `/` | Welcome JSON |
| `/docs` | Swagger UI |
| `/health?detailed=true` | Full health report |

---

## Step 6 — Connect GitHub Pages frontend

1. GitHub → `ankitashok15/Review-Analyzer` → **Settings**
2. **Secrets and variables** → **Actions** → **Variables**
3. Set **`RENDER_API_URL`** = `https://YOUR-APP.up.railway.app` (no trailing slash)
4. **Actions** → **Deploy Frontend to GitHub Pages** → **Run workflow**

Test: https://ankitashok15.github.io/Review-Analyzer/

---

## Step 7 — Optional Redis on Railway

Only needed for insight caching / Celery. Skip for demo.

1. In the same Railway project → **New** → **Database** → **Redis**
2. Copy the **`REDIS_URL`** from the Redis service variables
3. Paste into your API service variables
4. Redeploy

---

## How deployment works

On each deploy, Railway runs your `Dockerfile`, which executes `scripts/start_api.sh`:

1. `alembic upgrade head` — applies DB migrations to Neon
2. `uvicorn src.api.main:app` — starts API on Railway's `$PORT`

Config file: `railway.toml` (health check on `/health`).

---

## Costs

| Plan | Details |
|------|---------|
| **Trial** | ~$5 free credit for new accounts |
| **Hobby** | ~$5/month after trial — enough for a portfolio demo |
| **Neon** | Separate free tier (already using) |

Railway charges for **uptime + RAM/CPU**. A small API service is typically **$3–8/month**.

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Build fails | Check **Deployments** → **View logs**; often missing env var |
| `db: disconnected` | Wrong `DATABASE_URL`; use Neon **pooled** URL with `sslmode=require` |
| CORS error in browser | Add `https://ankitashok15.github.io` to `CORS_ORIGINS` |
| Ask returns 500 | Gemini quota — use `gemini-2.5-flash-lite` for RAG |
| App sleeps / slow start | Railway free tier may scale to zero on Hobby — first request slower |
| Migration error on deploy | Check Neon connection; ensure pgvector extension exists |

---

## Local vs Railway

| | Local | Railway |
|--|-------|---------|
| Start | `uvicorn src.api.main:app --reload --port 8000` | Auto via Docker |
| Database | Neon (same `.env`) | Neon (same URL in Variables) |
| URL | `http://localhost:8000` | `https://xxx.up.railway.app` |

---

## Quick reference

```powershell
# Health
curl https://YOUR-APP.up.railway.app/health

# Search
curl -X POST https://YOUR-APP.up.railway.app/api/v1/search `
  -H "Content-Type: application/json" `
  -d '{"query": "billing issues", "top_k": 5}'

# Ask
curl -X POST https://YOUR-APP.up.railway.app/api/v1/ask `
  -H "Content-Type: application/json" `
  -d '{"question": "What do users dislike about ads?"}'
```

After Railway is live, update your README Live API link and share the Railway URL in your portfolio.
