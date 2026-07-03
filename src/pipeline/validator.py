import re

from src.ingestion.schemas import ReviewCreate
from src.pipeline.schemas import ValidationResult

MIN_BODY_LENGTH = 10
URL_ONLY_PATTERN = re.compile(r"^https?://\S+$", re.IGNORECASE)
REPEATED_CHAR_PATTERN = re.compile(r"(.)\1{4,}")


def validate_review(review: ReviewCreate) -> ValidationResult:
    errors: list[str] = []

    if not review.source or not review.source.strip():
        errors.append("Source is required")

    if not review.source_id or not review.source_id.strip():
        errors.append("Source ID is required")

    body = (review.body or "").strip()
    if not body:
        return ValidationResult(valid=False, errors=["Review body is empty"], reason_code="EMPTY_BODY")
    if len(body) < MIN_BODY_LENGTH:
        return ValidationResult(
            valid=False,
            errors=[f"Review body must be at least {MIN_BODY_LENGTH} characters"],
            reason_code="BODY_TOO_SHORT",
        )

    if review.review_date is None:
        errors.append("Review date is required")

    if review.rating is not None and not (1 <= review.rating <= 5):
        errors.append("Rating must be between 1 and 5")

    if errors:
        reason = "INVALID_RATING" if any("Rating" in e for e in errors) else "VALIDATION_FAILED"
        if any("date" in e.lower() for e in errors):
            reason = "INVALID_DATE"
        if any("Source" in e for e in errors):
            reason = "INVALID_SOURCE"
        return ValidationResult(valid=False, errors=errors, reason_code=reason)

    return ValidationResult(valid=True)
