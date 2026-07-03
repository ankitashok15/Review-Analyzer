from sqlalchemy.orm import Session

from src.embeddings.schemas import EmbeddingFilters, ScoredResult
from src.storage.vector_store import VectorStore


class EmbeddingRepository:
    """Repository wrapper over pgvector similarity search."""

    def __init__(self, db: Session):
        self._store = VectorStore(db)

    def find_similar(
        self,
        query_vector: list[float],
        *,
        top_k: int = 10,
        model_version: str | None = None,
        filters: EmbeddingFilters | None = None,
    ) -> list[ScoredResult]:
        return self._store.similarity_search(
            query_vector,
            top_k=top_k,
            model_version=model_version,
            filters=filters,
        )
