import uuid
from datetime import datetime, timezone

from src.embeddings.embedder import MODEL_VERSION
from src.storage.database import SessionLocal
from src.storage.models import Review, ReviewEmbedding
from src.storage.vector_store import VectorStore


def _unit_vector(index: int) -> list[float]:
    vector = [0.0] * 768
    vector[index % 768] = 1.0
    return vector


def test_similarity_search_returns_ordered_results():
    db = SessionLocal()
    reviews = []
    try:
        for idx in range(3):
            review = Review(
                id=uuid.uuid4(),
                source="google_play",
                source_id=f"search-{idx}",
                app_name="Spotify",
                platform="android",
                body=f"Review body {idx}",
                language="en",
                review_date=datetime(2024, 1, idx + 1, tzinfo=timezone.utc),
                content_hash=f"search-hash-{idx}",
                source_metadata={},
            )
            reviews.append(review)
            db.add(review)
        db.commit()

        for idx, review in enumerate(reviews):
            db.add(
                ReviewEmbedding(
                    id=uuid.uuid4(),
                    review_id=review.id,
                    chunk_index=0,
                    embedding=_unit_vector(idx),
                    content_hash=f"chunk-{idx}",
                    model_version=MODEL_VERSION,
                )
            )
        db.commit()

        store = VectorStore(db)
        results = store.similarity_search(
            _unit_vector(1),
            top_k=2,
            model_version=MODEL_VERSION,
        )
        assert len(results) == 2
        assert results[0].review_id == reviews[1].id
        assert results[0].score >= results[1].score
    finally:
        for review in reviews:
            db.query(ReviewEmbedding).filter(ReviewEmbedding.review_id == review.id).delete()
            db.query(Review).filter(Review.id == review.id).delete()
        db.commit()
        db.close()
