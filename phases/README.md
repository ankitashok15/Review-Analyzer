# Phased Implementation

This folder tracks deliverables for each build phase defined in `Architecture.md` and `ImplementationPlan.md`.

## Project decision: enrichment is optional

**Phase 3 (AI enrichment) is implemented** but **not required** to continue the MVP path. Semantic search, RAG, and repositories work from raw `reviews.body` plus embeddings (Phases 4–6). Run enrichment later when Gemini quota allows, or skip entirely for a search-only demo. **Phase 7** requires enrichment data.

| Phase | Folder | Status |
|-------|--------|--------|
| 0 — Foundation & Infrastructure | [phase-0/](phase-0/README.md) | Complete |
| 1 — Data Ingestion | [phase-1/](phase-1/README.md) | Complete |
| 2 — Validation & Cleaning | [phase-2/](phase-2/README.md) | Complete |
| 3 — AI Enrichment | [phase-3/](phase-3/README.md) | Complete (optional at runtime) |
| 4 — Embeddings | [phase-4/](phase-4/README.md) | Complete |
| 5 — Repositories | [phase-5/](phase-5/README.md) | Complete |
| 6 — Semantic Search | [phase-6/](phase-6/README.md) | Complete |
| 7 — Insight Generation | [phase-7/](phase-7/README.md) | Complete |
| 8 — RAG Q&A | [phase-8/](phase-8/README.md) | Complete |
| 9 — Dashboard & API | [phase-9/](phase-9/README.md) | Complete |
| 10 — Production Hardening | [phase-10/](phase-10/README.md) | Complete |

**MVP path:** 0 → 2 → **4** → **5** → **6** → **8** → **9** (Phase 7 optional — requires enrichment data)  
**Full product:** MVP + Phase 7 + Phase 10
