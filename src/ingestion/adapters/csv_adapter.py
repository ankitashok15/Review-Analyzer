import csv
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from src.ingestion.base import SourceAdapter
from src.ingestion.config_loader import get_source_config
from src.ingestion.registry import register_adapter
from src.ingestion.schemas import ReviewCreate
from src.ingestion.utils import (
    compute_author_hash,
    compute_content_hash,
    parse_rating,
    parse_review_date,
)


@register_adapter("csv")
class CsvAdapter(SourceAdapter):
    source_name = "csv"
    config_key = "csv"

    def fetch(self, options: dict[str, Any]) -> Iterable[dict[str, Any]]:
        file_path = options.get("file")
        if not file_path:
            raise ValueError("CSV ingestion requires --file path")

        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"CSV file not found: {path}")

        limit = options.get("limit")
        count = 0

        with path.open(encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                yield row
                count += 1
                if limit is not None and count >= limit:
                    break

    def parse(self, raw: dict[str, Any]) -> ReviewCreate:
        config = get_source_config(self.config_key)
        column_map: dict[str, str] = config.get("column_map", {})
        metadata_columns: list[str] = config.get("metadata_columns", [])

        def get_field(canonical: str) -> str | None:
            source_column = column_map.get(canonical, canonical)
            value = raw.get(source_column)
            if value is None or str(value).strip() == "":
                return None
            return str(value).strip()

        body = get_field("body")
        if not body:
            raise ValueError("Review body is required")

        review_date = parse_review_date(get_field("review_date"))
        if review_date is None:
            raise ValueError("Review date is required")

        source_id = get_field("source_id")
        if not source_id:
            source_id = compute_content_hash(body)[:32]

        author_value = get_field("author")
        source_metadata = {
            column: raw.get(column)
            for column in metadata_columns
            if column in raw and raw.get(column) not in (None, "")
        }

        rating_column = column_map.get("rating", "rating")
        rating_raw = raw.get(rating_column)

        return ReviewCreate(
            source=get_field("source") or config.get("default_source", self.config_key),
            source_id=source_id,
            body=body,
            review_date=review_date,
            app_name=config.get("app_name", "Spotify"),
            platform=get_field("platform") or config.get("default_platform", "unknown"),
            source_url=get_field("source_url"),
            author_hash=compute_author_hash(author_value),
            rating=parse_rating(rating_raw),
            title=get_field("title"),
            language=get_field("language") or "en",
            content_hash=compute_content_hash(body),
            source_metadata=source_metadata,
        )

    def validate_raw(self, raw: dict[str, Any]) -> bool:
        if not super().validate_raw(raw):
            return False
        config = get_source_config(self.config_key)
        column_map: dict[str, str] = config.get("column_map", {})
        body_column = column_map.get("body", "body")
        body = raw.get(body_column)
        return body is not None and str(body).strip() != ""
