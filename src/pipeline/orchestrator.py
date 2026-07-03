import logging
import uuid

from sqlalchemy.orm import Session

from src.ingestion.schemas import ReviewCreate
from src.pipeline.cleaner import clean_review
from src.pipeline.deduplicator import check_duplicates
from src.pipeline.normalizer import normalize_review
from src.pipeline.schemas import PipelineOutcome, PipelineStatus, PipelineStats
from src.pipeline.validator import validate_review
from src.storage.models import IngestionError

logger = logging.getLogger(__name__)


class PipelineOrchestrator:
    def __init__(self, db: Session):
        self.db = db

    def _log_rejection(
        self,
        review: ReviewCreate | None,
        reason_code: str,
        message: str,
        raw_payload: dict | None = None,
    ) -> None:
        self.db.add(
            IngestionError(
                id=uuid.uuid4(),
                source=review.source if review else "unknown",
                source_id=review.source_id if review else None,
                reason_code=reason_code,
                message=message,
                raw_payload=raw_payload,
            )
        )

    def process(
        self,
        review: ReviewCreate,
        *,
        skip_validation: bool = False,
        raw_payload: dict | None = None,
    ) -> PipelineOutcome:
        if not skip_validation:
            validation = validate_review(review)
            if not validation.valid:
                message = "; ".join(validation.errors)
                self._log_rejection(review, validation.reason_code or "VALIDATION_FAILED", message, raw_payload)
                return PipelineOutcome(
                    status=PipelineStatus.REJECTED,
                    reason_code=validation.reason_code,
                    message=message,
                )

        cleaned, is_spam, spam_reason = clean_review(review)
        if is_spam:
            message = f"Spam detected: {spam_reason}"
            self._log_rejection(review, spam_reason or "SPAM_DETECTED", message, raw_payload)
            return PipelineOutcome(status=PipelineStatus.REJECTED, reason_code=spam_reason, message=message)

        if not skip_validation:
            post_clean_validation = validate_review(cleaned)
            if not post_clean_validation.valid:
                message = "; ".join(post_clean_validation.errors)
                self._log_rejection(
                    cleaned,
                    post_clean_validation.reason_code or "VALIDATION_FAILED",
                    message,
                    raw_payload,
                )
                return PipelineOutcome(
                    status=PipelineStatus.REJECTED,
                    reason_code=post_clean_validation.reason_code,
                    message=message,
                )

        normalized = normalize_review(cleaned)

        duplicate_reason = check_duplicates(self.db, normalized)
        if duplicate_reason == "DUPLICATE_SOURCE_ID":
            return PipelineOutcome(
                status=PipelineStatus.SKIPPED,
                reason_code=duplicate_reason,
                message="Review with same source and source_id already exists",
            )
        if duplicate_reason == "DUPLICATE_CONTENT_HASH":
            return PipelineOutcome(
                status=PipelineStatus.DUPLICATE,
                reason_code=duplicate_reason,
                message="Review with same content hash already exists",
            )

        return PipelineOutcome(status=PipelineStatus.ACCEPTED, review=normalized)

    def process_batch(
        self,
        reviews: list[ReviewCreate],
        *,
        skip_validation: bool = False,
    ) -> tuple[list[ReviewCreate], PipelineStats]:
        stats = PipelineStats()
        accepted: list[ReviewCreate] = []

        for review in reviews:
            outcome = self.process(review, skip_validation=skip_validation)
            stats.merge(outcome)
            if outcome.status == PipelineStatus.ACCEPTED and outcome.review:
                accepted.append(outcome.review)

        return accepted, stats
