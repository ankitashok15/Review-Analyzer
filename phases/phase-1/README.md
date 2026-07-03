# Phase 1 — Data Ingestion Framework

**Status:** Complete  
**Depends on:** [Phase 0](../phase-0/README.md)

## Objective

Ingest reviews from CSV/JSON files into the unified `reviews` table via a pluggable adapter framework.

## Deliverables

| Item | Location |
|------|----------|
| SourceAdapter interface | `src/ingestion/base.py` |
| ReviewCreate schema | `src/ingestion/schemas.py` |
| Adapter registry | `src/ingestion/registry.py` |
| CSV adapter | `src/ingestion/adapters/csv_adapter.py` |
| JSON adapter | `src/ingestion/adapters/json_adapter.py` |
| Ingestion service | `src/ingestion/service.py` |
| Source configuration | `config/sources.yaml` |
| CLI | `scripts/run_pipeline.py` |
| Seed helper | `scripts/seed_sample_data.py` |
| Dataset | `phases/phase-1/data/spotify_reviews.csv` |
| Tests | `tests/test_ingestion.py` |

## Dataset

| Field | CSV column |
|-------|------------|
| Review text | `content` |
| Rating | `score` |
| Date | `at` |
| Source ID | `reviewId` |
| Author (hashed) | `userName` |
| Platform | `android` (default) |
| Source | `google_play` (default) |

**File:** `phases/phase-1/data/spotify_reviews.csv` (~84,000 Google Play reviews)

## Usage

### Ingest full dataset

```powershell
.\.venv\Scripts\Activate.ps1
python scripts/run_pipeline.py ingest --source csv --file phases/phase-1/data/spotify_reviews.csv
```

### Ingest sample (testing)

```powershell
python scripts/run_pipeline.py ingest --source csv --file phases/phase-1/data/spotify_reviews.csv --limit 100
```

### Convenience script

```powershell
python scripts/seed_sample_data.py --limit 500
```

### JSON ingest

```powershell
python scripts/run_pipeline.py ingest --source json --file path/to/reviews.json
```

## Exit criteria

- [x] CSV adapter with configurable column mapping
- [x] JSON adapter (array / NDJSON)
- [x] Idempotent ingest on `(source, source_id)`
- [x] CLI entry point
- [x] Unit tests for parse, registry, idempotency

## Adding a new source

1. Create `src/ingestion/adapters/my_adapter.py`
2. Implement `SourceAdapter` and decorate with `@register_adapter("my_source")`
3. Import the module in `src/ingestion/adapters/__init__.py`
4. Add config to `config/sources.yaml`

## Next phase

→ Phase 2 — Validation, Cleaning, Normalization & Deduplication
