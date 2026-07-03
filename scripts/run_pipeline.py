#!/usr/bin/env python3
"""Pipeline CLI for ingestion, enrichment, and future batch jobs."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import src.ingestion.adapters  # noqa: E402,F401 — register adapters
from src.embeddings.embedder import DEFAULT_CONCURRENCY as EMBED_CONCURRENCY
from src.embeddings.embedder import MODEL_VERSION as EMBED_MODEL_VERSION
from src.embeddings.embedder import EmbeddingService
from src.enrichment.enricher import DEFAULT_CONCURRENCY, EnrichmentService  # noqa: E402
from src.ingestion.registry import list_adapters  # noqa: E402
from src.ingestion.service import IngestionService  # noqa: E402
from src.storage.database import SessionLocal  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

DEFAULT_CSV = ROOT / "phases" / "phase-1" / "data" / "spotify_reviews.csv"


def cmd_ingest(args: argparse.Namespace) -> int:
    file_path = args.file or str(DEFAULT_CSV)
    options = {"file": file_path, "skip_validation": args.skip_validation}
    if args.limit is not None:
        options["limit"] = args.limit

    db = SessionLocal()
    try:
        service = IngestionService(db)
        result = service.run(args.source, options)
    finally:
        db.close()

    print(f"Source:   {args.source}")
    print(f"File:     {file_path}")
    print(f"Inserted:   {result.inserted}")
    print(f"Skipped:    {result.skipped}")
    print(f"Rejected:   {result.rejected}")
    print(f"Duplicates: {result.duplicates}")
    print(f"Failed:     {result.failed}")
    if result.errors:
        print("Sample errors:")
        for error in result.errors[:5]:
            print(f"  - {error}")
    return 0 if result.failed == 0 or result.inserted > 0 else 1


def cmd_enrich(args: argparse.Namespace) -> int:
    if args.async_mode:
        from src.workers.tasks import enrich_reviews_task

        task = enrich_reviews_task.delay(
            limit=None if args.all else args.limit,
            concurrency=args.concurrency,
        )
        print(f"Enrichment job queued: {task.id}")
        print("Start worker: celery -A src.workers.celery_app worker --loglevel=info -P solo")
        return 0

    db = SessionLocal()
    try:
        service = EnrichmentService(db)
        result = service.run(
            limit=args.limit,
            enrich_all=args.all,
            concurrency=args.concurrency,
        )
    finally:
        db.close()

    print(f"Enriched: {result.enriched}")
    print(f"Skipped:  {result.skipped}")
    print(f"Failed:   {result.failed}")
    if result.errors:
        print("Sample errors:")
        for error in result.errors[:5]:
            print(f"  - {error}")
    return 0 if result.failed == 0 or result.enriched > 0 else 1


def cmd_embed(args: argparse.Namespace) -> int:
    if args.async_mode:
        from src.workers.tasks import embed_reviews_task

        task = embed_reviews_task.delay(
            limit=None if args.all else args.limit,
            concurrency=args.concurrency,
        )
        print(f"Embedding job queued: {task.id}")
        print("Start worker: celery -A src.workers.celery_app worker --loglevel=info -P solo")
        return 0

    db = SessionLocal()
    try:
        service = EmbeddingService(db)
        result = service.run(
            limit=args.limit,
            embed_all=args.all,
            concurrency=args.concurrency,
        )
    finally:
        db.close()

    print(f"Embedded: {result.embedded}")
    print(f"Skipped:  {result.skipped}")
    print(f"Cached:   {result.cached}")
    print(f"Failed:   {result.failed}")
    if result.errors:
        print("Sample errors:")
        for error in result.errors[:5]:
            print(f"  - {error}")
    return 0 if result.failed == 0 or result.embedded > 0 else 1


def cmd_search(args: argparse.Namespace) -> int:
    from src.ai.gemini_client import GeminiClient
    from src.storage.vector_store import VectorStore

    db = SessionLocal()
    try:
        client = GeminiClient()
        query_vector = client.embed(args.query)
        store = VectorStore(db)
        results = store.similarity_search(
            query_vector,
            top_k=args.top_k,
            model_version=EMBED_MODEL_VERSION,
        )
    finally:
        db.close()

    if not results:
        print("No results found.")
        return 0

    print(f"Query: {args.query!r}\n")
    for index, item in enumerate(results, start=1):
        review = item.review
        body_preview = (review.body[:200] + "…") if review and len(review.body) > 200 else (review.body if review else "")
        print(f"{index}. score={item.score:.4f} review_id={item.review_id}")
        print(f"   {body_preview}\n")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Review Discovery Engine pipeline")
    subparsers = parser.add_subparsers(dest="command", required=True)

    ingest = subparsers.add_parser("ingest", help="Ingest reviews from a configured source")
    ingest.add_argument("--source", required=True, choices=list_adapters())
    ingest.add_argument("--file", help="Path to CSV or JSON file")
    ingest.add_argument("--limit", type=int, help="Max records to ingest (for testing)")
    ingest.add_argument(
        "--skip-validation",
        action="store_true",
        help="Skip validation pipeline (debug only)",
    )
    ingest.set_defaults(func=cmd_ingest)

    enrich = subparsers.add_parser("enrich", help="Enrich reviews with Google Gemini")
    enrich.add_argument("--limit", type=int, default=200, help="Max reviews to enrich")
    enrich.add_argument("--all", action="store_true", help="Enrich all unenriched reviews")
    enrich.add_argument(
        "--concurrency",
        type=int,
        default=DEFAULT_CONCURRENCY,
        help="Parallel Gemini requests",
    )
    enrich.add_argument(
        "--async",
        dest="async_mode",
        action="store_true",
        help="Queue enrichment via Celery (requires worker)",
    )
    enrich.set_defaults(func=cmd_enrich)

    embed = subparsers.add_parser("embed", help="Generate embeddings for reviews")
    embed.add_argument("--limit", type=int, default=100, help="Max reviews to embed")
    embed.add_argument("--all", action="store_true", help="Embed all unembedded reviews")
    embed.add_argument(
        "--concurrency",
        type=int,
        default=EMBED_CONCURRENCY,
        help="Parallel embedding requests",
    )
    embed.add_argument(
        "--async",
        dest="async_mode",
        action="store_true",
        help="Queue embedding via Celery (requires worker)",
    )
    embed.set_defaults(func=cmd_embed)

    search = subparsers.add_parser("search", help="Semantic similarity search (smoke test)")
    search.add_argument("query", help="Natural-language search query")
    search.add_argument("--top-k", type=int, default=5, help="Number of results")
    search.set_defaults(func=cmd_search)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
