# Phase 4 — Embedding Generation & Vector Storage

**Status:** Complete  
**Depends on:** [Phase 2](../phase-2/README.md) (Phase 3 enrichment optional)

## Objective

Generate vector embeddings for review text using **Google Gemini `text-embedding-004`**, store them in **pgvector**, and enable similarity search for Phase 6.

## Deliverables

| Item | Location |
|------|----------|
| Alembic migration | `alembic/versions/003_review_embeddings.py` |
| SQLAlchemy model | `src/storage/models/__init__.py` → `ReviewEmbedding` |
| Chunker | `src/embeddings/chunker.py` |
| Embedder service | `src/embeddings/embedder.py` |
| Vector store | `src/storage/vector_store.py` |
| Celery task | `src/workers/tasks.py` → `embed_reviews_task` |
| CLI commands | `scripts/run_pipeline.py` → `embed`, `search` |
| Tests | `tests/test_chunker.py`, `tests/test_embeddings.py`, `tests/test_vector_store.py` |

## Configuration (`.env`)

```env
GOOGLE_API_KEY=AIzaSy...
GEMINI_EMBEDDING_MODEL=gemini-embedding-001
VECTOR_DIMENSION=768
DATABASE_URL=postgresql://postgres:postgres@localhost:5434/review_engine
REDIS_URL=redis://localhost:6379/0
```

**Model version stored in DB:** `gemini-embedding-001-v1` (768-dim via `output_dimensionality`)

> **Note:** Google deprecated `text-embedding-004` on the current API. This project uses `gemini-embedding-001` with `VECTOR_DIMENSION=768` to match the pgvector schema.

## Database

Run migration:

```powershell
alembic upgrade head
```

Table: `review_embeddings`

| Column | Type | Notes |
|--------|------|-------|
| `review_id` | UUID FK | Parent review |
| `chunk_index` | int | 0 for short reviews; >0 for long split chunks |
| `embedding` | vector(768) | pgvector HNSW index |
| `content_hash` | SHA-256 | Cache key — skip re-embed if hash exists |
| `model_version` | string | e.g. `text-embedding-004-v1` |

## Chunking

- Reviews ≤512 tokens (word proxy): **1 chunk**
- Longer reviews: sliding window, **512 tokens** with **50-token overlap**

## Usage

### Sync embedding (CLI)

```powershell
# Embed 100 reviews (default)
python scripts/run_pipeline.py embed --limit 100

# Embed all unembedded reviews
python scripts/run_pipeline.py embed --all

# Lower concurrency for free-tier rate limits
python scripts/run_pipeline.py embed --limit 50 --concurrency 1
```

### Async embedding (Celery)

Terminal 1 — worker:

```powershell
celery -A src.workers.celery_app worker --loglevel=info -P solo
```

Terminal 2 — queue job:

```powershell
python scripts/run_pipeline.py embed --limit 500 --async
```

### Semantic search smoke test

Requires embedded reviews in DB:

```powershell
python scripts/run_pipeline.py search "repetitive recommendations" --top-k 5
```

## Verify

```powershell
pytest tests/test_chunker.py tests/test_embeddings.py tests/test_vector_store.py -v
```

```sql
SELECT COUNT(*) FROM review_embeddings;
SELECT model_version, COUNT(*) FROM review_embeddings GROUP BY model_version;
SELECT review_id, chunk_index, content_hash FROM review_embeddings LIMIT 5;
```

## Exit criteria

- [x] `review_embeddings` table with HNSW index on `embedding`
- [x] Embeddings stored at 768 dimensions with `model_version` tracked
- [x] Job resumable — skips existing `(review_id, chunk_index, model_version)`
- [x] Content-hash cache — skips Gemini API call when hash already embedded
- [x] `VectorStore.similarity_search()` with metadata filters
- [x] CLI `embed` and Celery `embed_reviews_task`
- [x] Unit tests for chunker, embedder, vector store

## Next phase

→ Phase 5 — Metadata Storage & Repository Layer
