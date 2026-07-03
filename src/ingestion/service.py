import logging
from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from src.ingestion.archiver import archive_raw_payload
from src.ingestion.registry import get_adapter
from src.pipeline.orchestrator import PipelineOrchestrator
from src.pipeline.schemas import PipelineStatus
from src.storage.models import Review

logger = logging.getLogger(__name__)

BATCH_SIZE = 500


@dataclass
class IngestionResult:
    inserted: int = 0
    skipped: int = 0
    rejected: int = 0
    duplicates: int = 0
    failed: int = 0
    errors: list[str] = field(default_factory=list)


class IngestionService:
    def __init__(self, db: Session):
        self.db = db
        self.pipeline = PipelineOrchestrator(db)

    def run(self, source_name: str, options: dict | None = None) -> IngestionResult:
        options = options or {}
        skip_validation = bool(options.get("skip_validation", False))
        adapter = get_adapter(source_name)
        result = IngestionResult()
        pending = 0

        for raw in adapter.fetch(options):
            if not adapter.validate_raw(raw):
                result.failed += 1
                if len(result.errors) < 20:
                    result.errors.append("Invalid raw record")
                continue

            try:
                review_data = adapter.parse(raw)
            except Exception as exc:
                result.failed += 1
                if len(result.errors) < 20:
                    result.errors.append(str(exc))
                continue

            outcome = self.pipeline.process(
                review_data,
                skip_validation=skip_validation,
                raw_payload=raw,
            )

            if outcome.status == PipelineStatus.REJECTED:
                result.rejected += 1
                if outcome.message and len(result.errors) < 20:
                    result.errors.append(outcome.message)
                pending += 1
            elif outcome.status == PipelineStatus.SKIPPED:
                result.skipped += 1
            elif outcome.status == PipelineStatus.DUPLICATE:
                result.duplicates += 1
            elif outcome.status == PipelineStatus.ACCEPTED and outcome.review:
                review_data = outcome.review
                archive_raw_payload(
                    review_data.source,
                    review_data.source_id,
                    raw if isinstance(raw, dict) else {"raw": raw},
                )
                review = Review(
                    id=review_data.to_review_id(),
                    source=review_data.source,
                    source_id=review_data.source_id,
                    source_url=review_data.source_url,
                    app_name=review_data.app_name,
                    platform=review_data.platform,
                    author_hash=review_data.author_hash,
                    rating=review_data.rating,
                    title=review_data.title,
                    body=review_data.body,
                    language=review_data.language,
                    review_date=review_data.review_date,
                    content_hash=review_data.content_hash,
                    source_metadata=review_data.source_metadata,
                )
                self.db.add(review)
                result.inserted += 1
                pending += 1

            if pending >= BATCH_SIZE:
                self.db.commit()
                pending = 0
                logger.info(
                    "Committed batch — inserted=%s rejected=%s",
                    result.inserted,
                    result.rejected,
                )

        if pending:
            self.db.commit()

        logger.info(
            "Ingestion complete — inserted=%s skipped=%s rejected=%s duplicates=%s failed=%s",
            result.inserted,
            result.skipped,
            result.rejected,
            result.duplicates,
            result.failed,
        )
        return result
