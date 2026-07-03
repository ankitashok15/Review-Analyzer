from dataclasses import dataclass, field
from enum import Enum

from src.ingestion.schemas import ReviewCreate


class PipelineStatus(str, Enum):
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    DUPLICATE = "duplicate"
    SKIPPED = "skipped"


@dataclass
class ValidationResult:
    valid: bool
    errors: list[str] = field(default_factory=list)
    reason_code: str | None = None


@dataclass
class PipelineOutcome:
    status: PipelineStatus
    review: ReviewCreate | None = None
    reason_code: str | None = None
    message: str | None = None


@dataclass
class PipelineStats:
    accepted: int = 0
    rejected: int = 0
    duplicates: int = 0
    skipped: int = 0

    def merge(self, outcome: PipelineOutcome) -> None:
        if outcome.status == PipelineStatus.ACCEPTED:
            self.accepted += 1
        elif outcome.status == PipelineStatus.REJECTED:
            self.rejected += 1
        elif outcome.status == PipelineStatus.DUPLICATE:
            self.duplicates += 1
        elif outcome.status == PipelineStatus.SKIPPED:
            self.skipped += 1
