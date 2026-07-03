# Phase 5 — Metadata Storage & Repository Layer

**Status:** Complete  
**Depends on:** [Phase 4](../phase-4/README.md) (Phase 3 enrichment optional)

## Objective

Consolidate data access behind repository interfaces so Phase 6+ never touch SQL or vector details directly.

## Deliverables

| Item | Location |
|------|----------|
| Repository schemas | `src/storage/repositories/schemas.py` |
| ReviewRepository | `src/storage/repositories/review_repo.py` |
| EnrichmentRepository | `src/storage/repositories/enrichment_repo.py` |
| EmbeddingRepository | `src/storage/repositories/embedding_repo.py` |
| Composite queries | `src/storage/repositories/composite.py` |
| Full-text migration | `alembic/versions/004_reviews_fulltext_search.py` |
| Tests | `tests/test_repositories.py` |

## Migration

```powershell
alembic upgrade head
```

Adds `reviews.body_tsv` (`tsvector`) with GIN index and trigger to keep it synced on insert/update.

## Repository API

### ReviewRepository

- `get_by_id(review_id)`
- `list(filters, pagination, sort)` → `PaginatedResult`
- `count(filters)`

**Filters:** `source`, `platform`, `language`, `min_rating`, `max_rating`, `review_date_from`, `review_date_to`, `keyword` (full-text), plus optional enrichment filters (`sentiment`, `primary_topic`, `pain_point`, `user_segment`).

### EnrichmentRepository

- `get_by_review_id(review_id)`
- `list_by_topic(topic)`
- `list_by_pain_point(pain_point)`
- `aggregate_sentiment_by_segment()`

Works with empty or partial enrichment data (enrichment optional for MVP).

### EmbeddingRepository

- `find_similar(query_vector, top_k, filters)` — wraps `VectorStore`

### CompositeRepository

- `get_review_with_enrichment(review_id)` → `ReviewDetail`
- `search_reviews_with_enrichment(filters, pagination, sort)` → paginated `ReviewDetail` list

## Usage example

```python
from src.storage.database import SessionLocal
from src.storage.repositories import CompositeRepository, Pagination, ReviewFilters

db = SessionLocal()
repo = CompositeRepository(db)

detail = repo.get_review_with_enrichment(review_id)
results = repo.search_reviews_with_enrichment(
    filters=ReviewFilters(source="google_play", keyword="offline"),
    pagination=Pagination(page=1, page_size=20),
)
db.close()
```

## Verify

```powershell
pytest tests/test_repositories.py -v
```

## Exit criteria

- [x] Review, enrichment, and embedding repository methods
- [x] Composite `ReviewDetail` queries
- [x] Full-text search column + GIN index on `reviews.body`
- [x] Pagination with correct total counts
- [x] Enrichment filters optional (empty enrichment table supported)

## Next phase

→ Phase 6 — Semantic Search & Retrieval (`POST /api/v1/search`)
