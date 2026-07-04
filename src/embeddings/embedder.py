import logging
import uuid

from sqlalchemy.orm import Session

from config.settings import get_settings
from src.ai.gemini_client import GeminiClient
from src.embeddings.chunker import TextChunk, chunk_review_text
from src.embeddings.schemas import EmbeddingRecord, EmbeddingResult
from src.storage.models import Review, ReviewEmbedding
from src.storage.vector_store import VectorStore

logger = logging.getLogger(__name__)

DEFAULT_CONCURRENCY = 1


def embedding_model_version() -> str:
    """Runtime model version tag stored with vectors (avoids import-time env drift)."""
    raw = get_settings().gemini_embedding_model.strip()
    if raw.endswith("-v1"):
        return raw
    return f"{raw}-v1"


MODEL_VERSION = embedding_model_version()
COMMIT_BATCH_SIZE = 25


def _embed_text(text: str) -> list[float]:
    return GeminiClient().embed(text)


class EmbeddingService:
    def __init__(self, db: Session):
        self.db = db
        self.vector_store = VectorStore(db)

    def _chunk_exists(
        self,
        review_id: uuid.UUID,
        chunk_index: int,
        model_version: str = MODEL_VERSION,
    ) -> bool:
        exists = (
            self.db.query(ReviewEmbedding.id)
            .filter(
                ReviewEmbedding.review_id == review_id,
                ReviewEmbedding.chunk_index == chunk_index,
                ReviewEmbedding.model_version == model_version,
            )
            .first()
        )
        return exists is not None

    def _lookup_cached_vector(self, content_hash: str, model_version: str = MODEL_VERSION) -> list[float] | None:
        row = (
            self.db.query(ReviewEmbedding)
            .filter(
                ReviewEmbedding.content_hash == content_hash,
                ReviewEmbedding.model_version == model_version,
            )
            .first()
        )
        if row is None:
            return None
        return list(row.embedding)

    def _flush_records(self, records: list[EmbeddingRecord], result: EmbeddingResult) -> None:
        if not records:
            return
        self.vector_store.upsert_embeddings(records)
        self.db.commit()
        logger.info(
            "Embedding batch commit — embedded=%s skipped=%s cached=%s failed=%s",
            result.embedded,
            result.skipped,
            result.cached,
            result.failed,
        )

    def embed_chunks(
        self,
        chunks: list[TextChunk],
        *,
        concurrency: int = DEFAULT_CONCURRENCY,
        model_version: str = MODEL_VERSION,
    ) -> EmbeddingResult:
        result = EmbeddingResult()
        to_process: list[TextChunk] = []

        for chunk in chunks:
            if self._chunk_exists(chunk.review_id, chunk.chunk_index, model_version):
                result.skipped += 1
            else:
                to_process.append(chunk)

        if not to_process:
            return result

        pending: list[EmbeddingRecord] = []
        session_cache: dict[str, list[float]] = {}

        for chunk in to_process:
            try:
                if chunk.content_hash in session_cache:
                    vector = session_cache[chunk.content_hash]
                    was_cached = True
                else:
                    cached_vector = self._lookup_cached_vector(chunk.content_hash, model_version)
                    if cached_vector is not None:
                        vector = cached_vector
                        session_cache[chunk.content_hash] = vector
                        was_cached = True
                    else:
                        vector = _embed_text(chunk.text)
                        session_cache[chunk.content_hash] = vector
                        was_cached = False

                pending.append(
                    EmbeddingRecord(
                        review_id=chunk.review_id,
                        chunk_index=chunk.chunk_index,
                        embedding=vector,
                        content_hash=chunk.content_hash,
                        model_version=model_version,
                    )
                )
                result.embedded += 1
                if was_cached:
                    result.cached += 1

                if len(pending) >= COMMIT_BATCH_SIZE:
                    self._flush_records(pending, result)
                    pending.clear()
            except Exception as exc:
                result.failed += 1
                if len(result.errors) < 20:
                    result.errors.append(f"{chunk.review_id}[{chunk.chunk_index}]: {exc}")

        self._flush_records(pending, result)
        return result

    def get_unembedded_reviews(
        self,
        *,
        limit: int | None = None,
        model_version: str = MODEL_VERSION,
    ) -> list[Review]:
        query = (
            self.db.query(Review)
            .outerjoin(
                ReviewEmbedding,
                (Review.id == ReviewEmbedding.review_id)
                & (ReviewEmbedding.model_version == model_version),
            )
            .filter(ReviewEmbedding.id.is_(None))
            .order_by(Review.review_date.desc())
        )
        if limit is not None:
            query = query.limit(limit)
        return query.all()

    def embed_batch(
        self,
        reviews: list[Review],
        *,
        concurrency: int = DEFAULT_CONCURRENCY,
        model_version: str = MODEL_VERSION,
    ) -> EmbeddingResult:
        all_chunks: list[TextChunk] = []
        for review in reviews:
            all_chunks.extend(chunk_review_text(review.id, review.body))
        logger.info(
            "Embedding %s reviews (%s chunks, model_version=%s)",
            len(reviews),
            len(all_chunks),
            model_version,
        )
        return self.embed_chunks(all_chunks, concurrency=concurrency, model_version=model_version)

    def run(
        self,
        *,
        limit: int | None = None,
        embed_all: bool = False,
        concurrency: int = DEFAULT_CONCURRENCY,
        model_version: str = MODEL_VERSION,
    ) -> EmbeddingResult:
        fetch_limit = None if embed_all else limit
        reviews = self.get_unembedded_reviews(limit=fetch_limit, model_version=model_version)
        return self.embed_batch(reviews, concurrency=concurrency, model_version=model_version)
