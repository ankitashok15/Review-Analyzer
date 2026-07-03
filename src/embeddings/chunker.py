import uuid
from dataclasses import dataclass

from src.ingestion.utils import compute_content_hash, normalize_body

MAX_TOKENS = 512
OVERLAP_TOKENS = 50


@dataclass(frozen=True)
class TextChunk:
    review_id: uuid.UUID
    chunk_index: int
    text: str
    content_hash: str


def _tokenize(text: str) -> list[str]:
    """Word-based token proxy for chunking (MVP; ~1 word ≈ 1 token for English)."""
    return normalize_body(text).split()


def chunk_review_text(review_id: uuid.UUID, body: str) -> list[TextChunk]:
    """Split long reviews into overlapping chunks for embedding."""
    tokens = _tokenize(body)
    if not tokens:
        normalized = normalize_body(body)
        return [
            TextChunk(
                review_id=review_id,
                chunk_index=0,
                text=normalized,
                content_hash=compute_content_hash(normalized),
            )
        ]

    if len(tokens) <= MAX_TOKENS:
        text = " ".join(tokens)
        return [
            TextChunk(
                review_id=review_id,
                chunk_index=0,
                text=text,
                content_hash=compute_content_hash(text),
            )
        ]

    step = MAX_TOKENS - OVERLAP_TOKENS
    chunks: list[TextChunk] = []
    start = 0
    chunk_index = 0

    while start < len(tokens):
        window = tokens[start : start + MAX_TOKENS]
        text = " ".join(window)
        chunks.append(
            TextChunk(
                review_id=review_id,
                chunk_index=chunk_index,
                text=text,
                content_hash=compute_content_hash(text),
            )
        )
        chunk_index += 1
        if start + MAX_TOKENS >= len(tokens):
            break
        start += step

    return chunks
