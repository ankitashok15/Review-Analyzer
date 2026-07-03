from abc import ABC, abstractmethod
from collections.abc import Iterable
from typing import Any

from src.ingestion.schemas import ReviewCreate


class SourceAdapter(ABC):
    """Pluggable adapter for ingesting reviews from a single source type."""

    source_name: str

    @abstractmethod
    def fetch(self, options: dict[str, Any]) -> Iterable[dict[str, Any]]:
        """Yield raw records from the source."""

    @abstractmethod
    def parse(self, raw: dict[str, Any]) -> ReviewCreate:
        """Map a raw record to the unified review schema."""

    def validate_raw(self, raw: dict[str, Any]) -> bool:
        return raw is not None and isinstance(raw, dict)
