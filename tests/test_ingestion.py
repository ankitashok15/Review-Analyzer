from pathlib import Path

import pytest

import src.ingestion.adapters  # noqa: F401
from src.ingestion.adapters.csv_adapter import CsvAdapter
from src.ingestion.registry import get_adapter, list_adapters
from src.ingestion.service import IngestionService
from src.storage.database import SessionLocal
from src.storage.models import Review


@pytest.fixture
def sample_csv(tmp_path: Path) -> Path:
    content = """reviewId,userName,content,score,at
id-1,Alice,Spotify keeps playing the same songs.,4,2024-05-09 16:28:13
id-2,Bob,Great app for discovering new music!,5,2024-05-10 10:00:00
"""
    path = tmp_path / "reviews.csv"
    path.write_text(content, encoding="utf-8")
    return path


def test_registry_resolves_csv_adapter():
    assert "csv" in list_adapters()
    adapter = get_adapter("csv")
    assert isinstance(adapter, CsvAdapter)


def test_csv_adapter_parses_mapped_fields(sample_csv: Path):
    adapter = CsvAdapter()
    rows = list(adapter.fetch({"file": str(sample_csv)}))
    review = adapter.parse(rows[0])

    assert review.source == "google_play"
    assert review.source_id == "id-1"
    assert review.body == "Spotify keeps playing the same songs."
    assert review.rating == 4
    assert review.platform == "android"
    assert review.author_hash is not None


def test_idempotent_ingestion(sample_csv: Path):
    db = SessionLocal()
    try:
        service = IngestionService(db)
        first = service.run("csv", {"file": str(sample_csv)})
        second = service.run("csv", {"file": str(sample_csv)})

        assert first.inserted == 2
        assert first.skipped == 0
        assert second.inserted == 0
        assert second.skipped == 2

        count = db.query(Review).filter(Review.source_id.in_(["id-1", "id-2"])).count()
        assert count == 2
    finally:
        db.query(Review).filter(Review.source_id.in_(["id-1", "id-2"])).delete()
        db.commit()
        db.close()


def test_invalid_row_is_counted_as_failed(sample_csv: Path, tmp_path: Path):
    bad_csv = tmp_path / "bad.csv"
    bad_csv.write_text("reviewId,userName,content,score,at\n,,\n", encoding="utf-8")

    db = SessionLocal()
    try:
        service = IngestionService(db)
        result = service.run("csv", {"file": str(bad_csv)})
        assert result.inserted == 0
        assert result.failed >= 1
    finally:
        db.close()
