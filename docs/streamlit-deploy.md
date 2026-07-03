# Deploy on Streamlit Community Cloud

Streamlit Cloud runs **Python apps**, not a standalone FastAPI server. This repo includes `streamlit_app.py`, which calls the same search, RAG, and insight services as the FastAPI API.

## Architecture

| Component | Where it runs |
|-----------|----------------|
| Streamlit UI + Python services | [share.streamlit.io](https://share.streamlit.io) |
| PostgreSQL + pgvector | Hosted DB (Neon, Supabase, Railway, etc.) |
| React dashboard (optional) | GitHub Pages — needs a separate API URL |

The GitHub Pages frontend (`https://ankitashok15.github.io/Review-Analyzer/`) will **not** talk to Streamlit automatically. Use the Streamlit app URL as your live demo, or deploy FastAPI separately (Render/Railway) and set `VITE_API_URL` for the React app.

## Prerequisites

1. **Hosted PostgreSQL with pgvector** — Streamlit Cloud cannot run Docker Postgres.
2. **Data migrated** — reviews and embeddings must exist in that database.
3. **Gemini API key** — for Ask and semantic search (embeddings).

### Recommended: Neon (free tier)

1. Create a project at [neon.tech](https://neon.tech).
2. Enable pgvector:

   ```sql
   CREATE EXTENSION IF NOT EXISTS vector;
   ```

3. Run migrations from your machine against the Neon connection string:

   ```powershell
   $env:DATABASE_URL = "postgresql://...@...neon.tech/neondb?sslmode=require"
   alembic upgrade head
   ```

4. Re-ingest / re-embed if the cloud DB is empty (point `.env` `DATABASE_URL` at Neon temporarily).

## Deploy steps

### 1. Push code to GitHub

Ensure `streamlit_app.py`, `.streamlit/config.toml`, and `requirements.txt` (with `streamlit`) are on `main`.

### 2. Create the Streamlit app

1. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub.
2. **New app** → Repository: `ankitashok15/Review-Analyzer`.
3. **Main file path:** `streamlit_app.py`
4. **Branch:** `main`

### 3. Add secrets

In **App settings → Secrets**, paste (with your real values):

```toml
DATABASE_URL = "postgresql://USER:PASSWORD@HOST/DB?sslmode=require"
GOOGLE_API_KEY = "your-google-ai-studio-api-key"
GEMINI_RAG_MODEL = "gemini-2.5-pro"
GEMINI_EMBEDDING_MODEL = "gemini-embedding-001"
REQUIRE_ADMIN_API_KEY = "false"
```

See `.streamlit/secrets.toml.example` for all supported keys.

### 4. Deploy

Click **Deploy**. First build installs `requirements.txt` and may take a few minutes.

Your app URL will look like:

`https://review-analyzer-xxxxx.streamlit.app`

(Add that link to your GitHub README.)

## Local test (before cloud deploy)

```powershell
pip install streamlit
$env:DATABASE_URL = "postgresql://postgres:postgres@localhost:5434/review_engine"
$env:GOOGLE_API_KEY = "your-key"
streamlit run streamlit_app.py
```

Open http://localhost:8501

## Limitations on Streamlit Cloud

- No Celery workers — use local/CI pipelines for bulk ingest, embed, enrich.
- Redis is optional — insight list cache falls back to Postgres.
- Cold starts on free tier — first request may be slow.
- Gemini free-tier quotas still apply.

## If you need a real REST API

Deploy the existing `Dockerfile` to **Render**, **Railway**, or **Fly.io**, then point the React app at that URL via `VITE_API_URL` in the GitHub Pages build.
