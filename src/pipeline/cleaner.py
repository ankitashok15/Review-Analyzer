import re
import unicodedata

from src.ingestion.schemas import ReviewCreate
from src.ingestion.utils import compute_content_hash, normalize_body

HTML_TAG_PATTERN = re.compile(r"<[^>]+>")
URL_ONLY_PATTERN = re.compile(r"^https?://\S+$", re.IGNORECASE)
REPEATED_CHAR_PATTERN = re.compile(r"(.)\1{4,}")


def strip_html(text: str) -> str:
    return HTML_TAG_PATTERN.sub("", text)


def normalize_unicode(text: str) -> str:
    return unicodedata.normalize("NFKC", text)


def is_spam(text: str) -> tuple[bool, str | None]:
    stripped = text.strip()
    if not stripped:
        return True, "EMPTY_BODY"

    if URL_ONLY_PATTERN.match(stripped):
        return True, "SPAM_URL_ONLY"

    if REPEATED_CHAR_PATTERN.search(stripped):
        return True, "SPAM_REPEATED_CHARS"

    letters = [c for c in stripped if c.isalpha()]
    if len(letters) >= 20:
        upper_ratio = sum(1 for c in letters if c.isupper()) / len(letters)
        if upper_ratio > 0.8:
            return True, "SPAM_ALL_CAPS"

    return False, None


def clean_review(review: ReviewCreate) -> tuple[ReviewCreate, bool, str | None]:
    """Return cleaned review copy, spam flag, and spam reason code."""
    cleaned_body = normalize_unicode(strip_html(review.body))
    cleaned_body = normalize_body(cleaned_body)

    spam, spam_reason = is_spam(cleaned_body)
    if spam:
        return review.model_copy(), True, spam_reason

    cleaned = review.model_copy(
        update={
            "body": cleaned_body,
            "content_hash": compute_content_hash(cleaned_body),
            "title": normalize_body(strip_html(review.title)) if review.title else None,
        }
    )
    return cleaned, False, None
