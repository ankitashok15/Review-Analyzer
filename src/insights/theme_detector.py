import json
import logging
from collections import defaultdict

from sqlalchemy.orm import Session

from config.settings import get_settings
from src.ai.gemini_client import GeminiClient
from src.insights.schemas import Insight
from src.storage.models import ReviewEnrichment

logger = logging.getLogger(__name__)
settings = get_settings()


def _normalize_pain_point(value: str) -> str:
    return " ".join(value.lower().split())


def _cluster_key(pain_point: str) -> str:
    """MVP clustering: normalize whitespace/case; group exact normalized forms."""
    return _normalize_pain_point(pain_point)


class ThemeDetector:
    """Cluster pain points and optionally synthesize JTBD statements via Gemini."""

    def __init__(self, db: Session, gemini_client: GeminiClient | None = None):
        self.db = db
        self.gemini = gemini_client

    def detect_themes(self, *, use_gemini: bool = True) -> Insight:
        enrichments = (
            self.db.query(ReviewEnrichment)
            .filter(ReviewEnrichment.pain_point.isnot(None))
            .filter(ReviewEnrichment.pain_point != "")
            .all()
        )

        clusters: dict[str, list[ReviewEnrichment]] = defaultdict(list)
        for row in enrichments:
            clusters[_cluster_key(row.pain_point)].append(row)

        cluster_items = []
        all_evidence: list = []
        for key, members in sorted(clusters.items(), key=lambda item: len(item[1]), reverse=True):
            if len(members) < 2:
                continue
            evidence_ids = [member.review_id for member in members[:3]]
            representative = members[0].pain_point or key
            summaries = [member.summary for member in members if member.summary]
            jtbd = self._synthesize_jtbd(representative, summaries, use_gemini=use_gemini)
            cluster_items.append(
                {
                    "cluster_key": key,
                    "representative_pain_point": representative,
                    "count": len(members),
                    "jtbd_statement": jtbd,
                    "evidence_review_ids": [str(rid) for rid in evidence_ids],
                }
            )
            all_evidence.extend(evidence_ids)

        summary = (
            f"Detected {len(cluster_items)} recurring pain-point theme clusters."
            if cluster_items
            else "Not enough repeated pain points to detect themes."
        )
        return Insight(
            insight_type="themes",
            title="Pain Point Themes & JTBD Patterns",
            summary=summary,
            evidence_review_ids=list(dict.fromkeys(all_evidence)),
            metrics={"clusters": cluster_items[:10]},
        )

    def _synthesize_jtbd(
        self,
        pain_point: str,
        summaries: list[str],
        *,
        use_gemini: bool,
    ) -> str:
        fallback = f"When using Spotify, users struggle with {pain_point.lower()}."
        if not use_gemini or self.gemini is None:
            return fallback

        prompt = (
            "Write one Jobs-to-be-Done (JTBD) statement for product researchers based on these review summaries.\n"
            f"Pain point: {pain_point}\n"
            f"Summaries: {json.dumps(summaries[:5])}\n"
            "Return a single sentence starting with 'When'."
        )
        try:
            from pydantic import BaseModel

            class JtbdOutput(BaseModel):
                statement: str

            result = self.gemini.generate_json(
                prompt,
                JtbdOutput,
                model=settings.gemini_enrichment_model,
            )
            return result.get("statement") or fallback
        except Exception as exc:
            logger.warning("JTBD synthesis failed: %s", exc)
            return fallback
