import logging
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path

from sqlalchemy.orm import Session

from src.ai.gemini_client import GeminiClient
from src.enrichment.schemas import EnrichmentOutput
from src.storage.models import EnrichmentError, Review, ReviewEnrichment

logger = logging.getLogger(__name__)

PROMPT_PATH = Path(__file__).resolve().parent / "prompts" / "enrichment_v1.txt"
MODEL_VERSION = "enrichment-v1"
DEFAULT_CONCURRENCY = 5


@dataclass
class EnrichmentResult:
    enriched: int = 0
    skipped: int = 0
    failed: int = 0
    errors: list[str] = field(default_factory=list)


def _load_system_prompt() -> str:
    return PROMPT_PATH.read_text(encoding="utf-8")


def _build_prompt(review: Review) -> str:
    return (
        f"Source: {review.source}\n"
        f"Platform: {review.platform}\n"
        f"Rating: {review.rating}\n"
        f"Review date: {review.review_date.isoformat()}\n"
        f"Review text:\n{review.body}"
    )


def _call_gemini_for_review(review: Review, system_prompt: str) -> EnrichmentOutput:
    client = GeminiClient()
    raw = client.generate_json(
        _build_prompt(review),
        EnrichmentOutput,
        system_instruction=system_prompt,
    )
    return EnrichmentOutput.model_validate(raw)


class EnrichmentService:
    def __init__(self, db: Session):
        self.db = db
        self.system_prompt = _load_system_prompt()

    def _already_enriched(self, review_id: uuid.UUID, model_version: str) -> bool:
        exists = (
            self.db.query(ReviewEnrichment.id)
            .filter(
                ReviewEnrichment.review_id == review_id,
                ReviewEnrichment.model_version == model_version,
            )
            .first()
        )
        return exists is not None

    def _log_failure(self, review_id: uuid.UUID, message: str, model_version: str) -> None:
        self.db.add(
            EnrichmentError(
                id=uuid.uuid4(),
                review_id=review_id,
                model_version=model_version,
                message=message,
            )
        )

    def _to_enrichment(self, review: Review, output: EnrichmentOutput, model_version: str) -> ReviewEnrichment:
        return ReviewEnrichment(
            id=uuid.uuid4(),
            review_id=review.id,
            sentiment=output.sentiment.value,
            emotion=output.emotion,
            primary_topic=output.primary_topic,
            user_goal=output.user_goal,
            pain_point=output.pain_point,
            feature_request=output.feature_request,
            discovery_issue=output.discovery_issue,
            listening_behavior=output.listening_behavior,
            user_segment=output.user_segment,
            keywords=output.keywords,
            summary=output.summary,
            confidence_score=output.confidence_score,
            model_version=model_version,
        )

    def enrich_one(self, review: Review, model_version: str = MODEL_VERSION) -> ReviewEnrichment | None:
        if self._already_enriched(review.id, model_version):
            return None
        try:
            output = _call_gemini_for_review(review, self.system_prompt)
        except Exception as exc:
            self._log_failure(review.id, str(exc), model_version)
            raise
        return self._to_enrichment(review, output, model_version)

    def enrich_batch(
        self,
        reviews: list[Review],
        *,
        concurrency: int = DEFAULT_CONCURRENCY,
        model_version: str = MODEL_VERSION,
    ) -> EnrichmentResult:
        result = EnrichmentResult()
        to_process: list[Review] = []

        for review in reviews:
            if self._already_enriched(review.id, model_version):
                result.skipped += 1
            else:
                to_process.append(review)

        if not to_process:
            return result

        pending = 0
        with ThreadPoolExecutor(max_workers=concurrency) as executor:
            futures = {
                executor.submit(_call_gemini_for_review, review, self.system_prompt): review
                for review in to_process
            }
            for future in as_completed(futures):
                review = futures[future]
                try:
                    output = future.result()
                    enrichment = self._to_enrichment(review, output, model_version)
                    self.db.add(enrichment)
                    result.enriched += 1
                except Exception as exc:
                    self._log_failure(review.id, str(exc), model_version)
                    result.failed += 1
                    if len(result.errors) < 20:
                        result.errors.append(f"{review.id}: {exc}")

                pending += 1
                if pending >= 50:
                    self.db.commit()
                    pending = 0
                    logger.info(
                        "Enrichment batch commit — enriched=%s failed=%s",
                        result.enriched,
                        result.failed,
                    )

        if pending:
            self.db.commit()

        return result

    def get_unenriched_reviews(
        self,
        *,
        limit: int | None = None,
        model_version: str = MODEL_VERSION,
    ) -> list[Review]:
        query = (
            self.db.query(Review)
            .outerjoin(
                ReviewEnrichment,
                (Review.id == ReviewEnrichment.review_id)
                & (ReviewEnrichment.model_version == model_version),
            )
            .filter(ReviewEnrichment.id.is_(None))
            .order_by(Review.review_date.desc())
        )
        if limit is not None:
            query = query.limit(limit)
        return query.all()

    def run(
        self,
        *,
        limit: int | None = None,
        enrich_all: bool = False,
        concurrency: int = DEFAULT_CONCURRENCY,
        model_version: str = MODEL_VERSION,
    ) -> EnrichmentResult:
        fetch_limit = None if enrich_all else limit
        reviews = self.get_unenriched_reviews(limit=fetch_limit, model_version=model_version)
        logger.info("Enriching %s reviews (model_version=%s)", len(reviews), model_version)
        return self.enrich_batch(reviews, concurrency=concurrency, model_version=model_version)
