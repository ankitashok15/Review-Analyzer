# Deploy for Free (Neon + Hugging Face Spaces)

**Recommended $0 path** — no credit card for Neon or Hugging Face CPU Basic.

| Component | Service | Cost |
|-----------|---------|------|
| PostgreSQL + pgvector | [Neon](https://neon.tech) | Free — you already have this |
| FastAPI API | [Hugging Face Spaces](https://huggingface.co/spaces) (Docker) | Free CPU Basic (2 vCPU, 16 GB RAM) |
| Redis (optional) | Skip or [Upstash](https://upstash.com) free | Optional |
| React dashboard | GitHub Pages | Free (already live) |

> **Why not Koyeb / Render?** Both often prompt for a credit card or move you to paid tiers quickly. HF Spaces **CPU Basic** is free without a card.

---

## What you already have

Your Neon database is ready:

- **1,354** reviews
- **1,034** embeddings (~76%)
- Schema + `pgvector` migrated

That is enough to deploy the API now. Search/Ask need Gemini quota (resets daily).

---

## Phase 1 — Create Hugging Face Space

### 1a. Account

1. Sign up at [huggingface.co](https://huggingface.co) (no credit card).
2. Create an **Access Token** (Settings → Access Tokens → Read) if you need private secrets — optional for public Space.

### 1b. New Docker Space

1. Go to [huggingface.co/new-space](https://huggingface.co/new-space)
2. Settings:

| Field | Value |
|-------|-------|
| Space name | `review-analyzer-api` (or your choice) |
| License | MIT |
| SDK | **Docker** |
| Hardware | **CPU basic** (free) |
| Visibility | Public |

3. **Create Space**.

### 1c. Connect GitHub repo

1. In the Space → **Files** → **Add file** → **Add from GitHub**  
   — or clone the Space repo and copy files.

**Easier approach:** duplicate deploy files into the Space:

1. Space → **Settings** → link repository, **or** push these files to the Space repo:
   - Copy `deploy/huggingface/Dockerfile` → Space root as `Dockerfile`
   - Copy `deploy/huggingface/README.md` → Space root as `README.md`
   - Copy `requirements.txt`, `src/`, `config/`, `alembic/`, `scripts/start_api.sh`, etc.

**GitHub sync (recommended):** In Space Settings, connect to `ankitashok15/Review-Analyzer` if HF supports monorepo import; otherwise create a **second repo** `review-analyzer-api` with only API files, or use HF's "duplicate this Space" from a template.

For a **monorepo**, the simplest path:

1. Space → **Files** → upload / sync from your GitHub branch `main`
2. Ensure root `Dockerfile` exists (project already has one)
3. Edit Space `README.md` YAML (top of file) — use template in `deploy/huggingface/README.md`

### 1d. Space README YAML (required)

The Space `README.md` must start with:

```yaml
---
title: Review Analyzer API
emoji: 🎧
colorFrom: green
colorTo: black
sdk: docker
app_port: 8000
---
```

`app_port: 8000` matches our uvicorn port.

### 1e. Environment secrets

Space → **Settings** → **Repository secrets** (or Variables):

| Key | Value |
|-----|-------|
| `DATABASE_URL` | Your Neon pooled connection string |
| `GOOGLE_API_KEY` | Google AI Studio key |
| `ADMIN_API_KEY` | Random secret |
| `GEMINI_RAG_MODEL` | `gemini-2.5-pro` |
| `GEMINI_EMBEDDING_MODEL` | `gemini-embedding-001` |
| `VECTOR_DIMENSION` | `768` |
| `CORS_ORIGINS` | `https://ankitashok15.github.io,https://YOUR-USERNAME-review-analyzer-api.hf.space` |
| `REQUIRE_ADMIN_API_KEY` | `true` |
| `LOG_FORMAT` | `text` |

Replace `YOUR-USERNAME` with your HF username.

### 1f. Build

Space rebuilds automatically on file push. Wait ~5–10 min.

Your API URL:

```
https://YOUR-USERNAME-review-analyzer-api.hf.space
```

Verify:

```powershell
curl https://YOUR-USERNAME-review-analyzer-api.hf.space/health
```

---

## Phase 2 — Connect GitHub Pages frontend

1. GitHub → `ankitashok15/Review-Analyzer` → **Settings** → **Secrets and variables** → **Actions** → **Variables**
2. Set `RENDER_API_URL` = `https://YOUR-USERNAME-review-analyzer-api.hf.space` (no trailing slash)
3. **Actions** → **Deploy Frontend to GitHub Pages** → **Run workflow**

---

## Phase 3 — Test

| URL | Check |
|-----|-------|
| `https://YOUR-SPACE.hf.space/health` | `db: connected` |
| `https://YOUR-SPACE.hf.space/docs` | Swagger UI |
| https://ankitashok15.github.io/Review-Analyzer/ | Search / Ask |

---

## HF Spaces limitations (free tier)

| Limit | Impact |
|-------|--------|
| **Sleeps after ~48h inactive** | First request wakes it (~30–60s) |
| **Non-persistent disk** | Migrations run on each cold start (`start_api.sh`) — fine with external Neon DB |
| **Only `/tmp` writable** | Our app writes to Neon, not local disk — OK |
| **Public Space** | API is visible; protect write routes with `ADMIN_API_KEY` |

---

## Alternatives if HF doesn't work

| Option | Cost | Card? | Notes |
|--------|------|-------|-------|
| **Cloudflare Tunnel** | $0 | No | Run API on your PC; tunnel to public URL. PC must stay on. |
| **Oracle Cloud Always Free** | $0 | Yes (verify only) | ARM VM, run Docker yourself. Never expires. |
| **Koyeb / Render** | Paid | Often yes | Fine for production if you accept ~$7+/mo |

### Cloudflare Tunnel (quick)

```powershell
# Install cloudflared, then:
cloudflared tunnel --url http://localhost:8000
```

Run API locally (`uvicorn src.api.main:app --port 8000`), use the tunnel URL as `RENDER_API_URL`.

---

## Local development (unchanged)

```powershell
docker compose up -d
uvicorn src.api.main:app --reload --port 8000
cd frontend && npm run dev
```
