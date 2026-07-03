# Phase 2 — Validation, Cleaning, Normalization & Deduplication

**Status:** Complete  
**Depends on:** [Phase 1](../phase-1/README.md)

## Objective

Ensure every ingested review passes through a preprocessing pipeline before persistence: validate, clean, normalize, and deduplicate.

## Pipeline flow

```
parse → validate → clean → normalize → deduplicate → persist
                  ↓ rejected
            ingestion_errors
```

## Deliverables

| Module | Location | Responsibility |
|--------|----------|----------------|
| Validator | `src/pipeline/validator.py` | Required fields, min body length, rating bounds |
| Cleaner | `src/pipeline/cleaner.py` | HTML strip, whitespace, spam detection |
| Normalizer | `src/pipeline/normalizer.py` | UTC dates, language detection, canonical fields |
| Deduplicator | `src/pipeline/deduplicator.py` | `source_id` and `content_hash` checks |
| Orchestrator | `src/pipeline/orchestrator.py` | Chains stages, logs rejections |
| Integration | `src/ingestion/service.py` | Pipeline wired into ingest |

## Validation rules (defaults)

| Rule | Behavior |
|------|----------|
| Body min length | 10 characters |
| Rating | 1–5 or null |
| Spam (URL-only, all caps, repeated chars) | Rejected → `ingestion_errors` |
| Duplicate `source + source_id` | Skipped |
| Duplicate `content_hash` | Counted as duplicate |

## Usage

Ingestion automatically runs the pipeline:

```powershell
python scripts/run_pipeline.py ingest --source csv --file phases/phase-1/data/spotify_reviews.csv --limit 1500
```

Debug mode (skip validation):

```powershell
python scripts/run_pipeline.py ingest --source csv --file phases/phase-1/data/spotify_reviews.csv --skip-validation --limit 100
```

## CLI output fields

| Field | Meaning |
|-------|---------|
| Inserted | Accepted and saved |
| Skipped | Same `source + source_id` already exists |
| Rejected | Failed validation or spam |
| Duplicates | Same `content_hash` already exists |
| Failed | Parse / raw record errors |

## Inspect rejections

```sql
SELECT reason_code, COUNT(*) FROM ingestion_errors GROUP BY reason_code;
```

## Tests

```powershell
pytest tests/test_pipeline.py tests/test_ingestion.py -v
```

## Exit criteria

- [x] Pipeline integrated into ingestion
- [x] Rejected records logged to `ingestion_errors`
- [x] Duplicate detection on `content_hash` and `source_id`
- [x] Unit tests for validation, cleaning, dedup, orchestration
- [x] 1,000+ reviews processed in batch ingest

## Next phase

→ Phase 3 — AI Enrichment Layer (Google Gemini)
