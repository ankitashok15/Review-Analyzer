import uuid

import pytest

from src.embeddings.chunker import MAX_TOKENS, OVERLAP_TOKENS, chunk_review_text


def test_short_review_single_chunk():
    review_id = uuid.uuid4()
    body = "Spotify keeps playing the same songs every week."
    chunks = chunk_review_text(review_id, body)
    assert len(chunks) == 1
    assert chunks[0].review_id == review_id
    assert chunks[0].chunk_index == 0
    assert "same songs" in chunks[0].text
    assert len(chunks[0].content_hash) == 64


def test_long_review_splits_with_overlap():
    review_id = uuid.uuid4()
    words = [f"word{i}" for i in range(MAX_TOKENS + 100)]
    body = " ".join(words)
    chunks = chunk_review_text(review_id, body)
    assert len(chunks) >= 2
    assert chunks[0].chunk_index == 0
    assert chunks[1].chunk_index == 1
    first_tokens = chunks[0].text.split()
    second_tokens = chunks[1].text.split()
    assert len(first_tokens) == MAX_TOKENS
    overlap = MAX_TOKENS - (MAX_TOKENS - OVERLAP_TOKENS)
    assert first_tokens[-OVERLAP_TOKENS:] == second_tokens[:OVERLAP_TOKENS]


def test_empty_body_still_produces_chunk():
    review_id = uuid.uuid4()
    chunks = chunk_review_text(review_id, "   ")
    assert len(chunks) == 1
    assert chunks[0].chunk_index == 0
