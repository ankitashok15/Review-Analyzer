import re

from config.settings import get_settings

settings = get_settings()

_CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_MULTISPACE = re.compile(r"\s+")


def sanitize_query(text: str, *, max_length: int | None = None) -> str:
    """Normalize user queries for search/ask endpoints."""
    limit = max_length or settings.max_query_length
    cleaned = _CONTROL_CHARS.sub("", text or "")
    cleaned = _MULTISPACE.sub(" ", cleaned).strip()
    if len(cleaned) > limit:
        cleaned = cleaned[:limit].rstrip()
    return cleaned
