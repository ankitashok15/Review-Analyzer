import hashlib
import re
from datetime import datetime, timezone

from dateutil import parser as date_parser


def normalize_body(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip())


def compute_content_hash(body: str) -> str:
    normalized = normalize_body(body)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def compute_author_hash(author: str | None) -> str | None:
    if not author or not str(author).strip():
        return None
    return hashlib.sha256(str(author).strip().lower().encode("utf-8")).hexdigest()


def parse_review_date(value: str | None) -> datetime | None:
    if value is None or str(value).strip() == "":
        return None
    parsed = date_parser.parse(str(value))
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def parse_rating(value: str | int | float | None) -> int | None:
    if value is None or str(value).strip() == "":
        return None
    rating = int(float(value))
    if 1 <= rating <= 5:
        return rating
    return None
