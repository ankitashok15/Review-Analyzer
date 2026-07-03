from datetime import timezone

from src.ingestion.schemas import ReviewCreate
from src.ingestion.utils import compute_author_hash, compute_content_hash

try:
    from langdetect import LangDetectException, detect
except ImportError:  # pragma: no cover
    detect = None
    LangDetectException = Exception


def detect_language(text: str, default: str = "en") -> str:
    if detect is None:
        return default
    try:
        language = detect(text)
        return language[:10] if language else default
    except LangDetectException:
        return default


def normalize_review(review: ReviewCreate, author_plain: str | None = None) -> ReviewCreate:
    review_date = review.review_date
    if review_date.tzinfo is None:
        review_date = review_date.replace(tzinfo=timezone.utc)
    else:
        review_date = review_date.astimezone(timezone.utc)

    language = review.language or detect_language(review.body)
    author_hash = review.author_hash
    if author_plain and not author_hash:
        author_hash = compute_author_hash(author_plain)

    rating = review.rating
    if rating is not None and not (1 <= rating <= 5):
        rating = None

    return review.model_copy(
        update={
            "review_date": review_date,
            "language": language,
            "author_hash": author_hash,
            "rating": rating,
            "platform": (review.platform or "unknown").lower(),
            "source": review.source.strip().lower(),
            "content_hash": compute_content_hash(review.body),
        }
    )
