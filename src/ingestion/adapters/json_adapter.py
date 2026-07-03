import json
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from src.ingestion.adapters.csv_adapter import CsvAdapter
from src.ingestion.registry import register_adapter


@register_adapter("json")
class JsonAdapter(CsvAdapter):
    """JSON / NDJSON adapter reusing CSV field mapping from sources.json config."""

    source_name = "json"
    config_key = "json"

    def fetch(self, options: dict[str, Any]) -> Iterable[dict[str, Any]]:
        file_path = options.get("file")
        if not file_path:
            raise ValueError("JSON ingestion requires --file path")

        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"JSON file not found: {path}")

        limit = options.get("limit")
        count = 0

        if path.suffix.lower() == ".ndjson":
            with path.open(encoding="utf-8") as handle:
                for line in handle:
                    line = line.strip()
                    if not line:
                        continue
                    yield json.loads(line)
                    count += 1
                    if limit is not None and count >= limit:
                        break
            return

        with path.open(encoding="utf-8") as handle:
            payload = json.load(handle)

        if isinstance(payload, list):
            records = payload
        elif isinstance(payload, dict) and "reviews" in payload:
            records = payload["reviews"]
        else:
            raise ValueError("JSON file must be an array or contain a top-level 'reviews' key")

        for record in records:
            if not isinstance(record, dict):
                continue
            yield record
            count += 1
            if limit is not None and count >= limit:
                break
