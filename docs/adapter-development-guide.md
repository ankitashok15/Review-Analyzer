# Adapter Development Guide

Prove the ingestion framework supports new sources in &lt;1 day using the existing **CSV adapter** as reference.

## Adapter contract

1. Register with `@register_adapter("source_name")`
2. Implement `SourceAdapter`: `fetch`, `validate_raw`, `parse`
3. Return unified `ReviewData` schema from `parse()`

## Reference: CSV adapter

See `src/ingestion/adapters/csv_adapter.py`.

Flow:

```
fetch(options) → raw dict rows
validate_raw(raw) → bool
parse(raw) → ReviewData
```

## Add a new source in 4 steps

### 1. Create adapter file

`src/ingestion/adapters/my_source_adapter.py`

### 2. Register in `src/ingestion/adapters/__init__.py`

```python
from src.ingestion.adapters import my_source_adapter  # noqa: F401
```

### 3. Add source config in `config/sources.yaml` (optional)

### 4. Test

```powershell
python scripts/run_pipeline.py ingest --source my_source --limit 10
```

## Deferred adapters (Phase 10 scope: SKIP)

| Source | Package | Credentials |
|--------|---------|-------------|
| Reddit | PRAW | `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET` |
| App Store | app-store-scraper / Apple API | Apple credentials |
| Google Play | google-play-scraper | Service account JSON |

## Raw payload archival

Enable `ARCHIVE_RAW_PAYLOADS=true` to save raw records under `data/raw_archive/{source}/{date}/`.

## Time estimate

| Task | Hours |
|------|-------|
| Scaffold adapter | 1–2 |
| Field mapping + tests | 2–4 |
| Ingest smoke test | 1 |
| **Total** | **&lt;1 day** |

The CSV adapter demonstrates the full pattern — new sources follow the same `IngestionService.run()` pipeline.
