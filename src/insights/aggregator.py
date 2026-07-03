import logging
import uuid
from collections import defaultdict

from sqlalchemy import func
from sqlalchemy.orm import Session

from src.insights.schemas import Insight
from src.storage.models import Review, ReviewEnrichment

logger = logging.getLogger(__name__)

DEFAULT_TOP_N = 10
MIN_EVIDENCE = 3


def _sample_review_ids(
    db: Session,
    *,
    field_name: str,
    field_value: str,
    limit: int = MIN_EVIDENCE,
) -> list[uuid.UUID]:
    column = getattr(ReviewEnrichment, field_name)
    rows = (
        db.query(ReviewEnrichment.review_id)
        .filter(column == field_value)
        .order_by(ReviewEnrichment.enriched_at.desc())
        .limit(limit)
        .all()
    )
    return [row[0] for row in rows]


class InsightAggregator:
    """SQL aggregations over enrichment metadata."""

    def __init__(self, db: Session):
        self.db = db

    def top_pain_points(self, *, limit: int = DEFAULT_TOP_N) -> Insight:
        rows = (
            self.db.query(
                ReviewEnrichment.pain_point,
                func.count(ReviewEnrichment.id).label("count"),
            )
            .filter(ReviewEnrichment.pain_point.isnot(None))
            .filter(ReviewEnrichment.pain_point != "")
            .group_by(ReviewEnrichment.pain_point)
            .order_by(func.count(ReviewEnrichment.id).desc())
            .limit(limit)
            .all()
        )

        items = []
        all_evidence: list[uuid.UUID] = []
        for pain_point, count in rows:
            evidence = _sample_review_ids(self.db, field_name="pain_point", field_value=pain_point)
            items.append(
                {
                    "pain_point": pain_point,
                    "count": count,
                    "evidence_review_ids": [str(rid) for rid in evidence],
                }
            )
            all_evidence.extend(evidence)

        summary = (
            f"Identified {len(items)} recurring pain themes from enriched reviews."
            if items
            else "No pain points found in enriched reviews."
        )
        return Insight(
            insight_type="pain_points",
            title="Top Pain Points",
            summary=summary,
            evidence_review_ids=list(dict.fromkeys(all_evidence)),
            metrics={"items": items, "total_themes": len(items)},
        )

    def top_feature_requests(self, *, limit: int = DEFAULT_TOP_N) -> Insight:
        rows = (
            self.db.query(
                ReviewEnrichment.feature_request,
                func.count(ReviewEnrichment.id).label("count"),
            )
            .filter(ReviewEnrichment.feature_request.isnot(None))
            .filter(ReviewEnrichment.feature_request != "")
            .group_by(ReviewEnrichment.feature_request)
            .order_by(func.count(ReviewEnrichment.id).desc())
            .limit(limit)
            .all()
        )

        items = []
        all_evidence: list[uuid.UUID] = []
        for feature_request, count in rows:
            evidence = _sample_review_ids(
                self.db,
                field_name="feature_request",
                field_value=feature_request,
            )
            items.append(
                {
                    "feature_request": feature_request,
                    "count": count,
                    "evidence_review_ids": [str(rid) for rid in evidence],
                }
            )
            all_evidence.extend(evidence)

        summary = (
            f"Identified {len(items)} requested features from enriched reviews."
            if items
            else "No feature requests found in enriched reviews."
        )
        return Insight(
            insight_type="feature_requests",
            title="Top Feature Requests",
            summary=summary,
            evidence_review_ids=list(dict.fromkeys(all_evidence)),
            metrics={"items": items, "total_requests": len(items)},
        )

    def platform_comparison(self) -> Insight:
        rows = (
            self.db.query(
                Review.source,
                Review.platform,
                ReviewEnrichment.sentiment,
                func.count(ReviewEnrichment.id).label("count"),
            )
            .join(Review, Review.id == ReviewEnrichment.review_id)
            .group_by(Review.source, Review.platform, ReviewEnrichment.sentiment)
            .order_by(func.count(ReviewEnrichment.id).desc())
            .all()
        )

        items = []
        evidence: list[uuid.UUID] = []
        for source, platform, sentiment, count in rows:
            sample = (
                self.db.query(ReviewEnrichment.review_id)
                .join(Review, Review.id == ReviewEnrichment.review_id)
                .filter(Review.source == source, Review.platform == platform)
                .filter(ReviewEnrichment.sentiment == sentiment)
                .limit(MIN_EVIDENCE)
                .all()
            )
            sample_ids = [row[0] for row in sample]
            items.append(
                {
                    "source": source,
                    "platform": platform,
                    "sentiment": sentiment,
                    "count": count,
                    "evidence_review_ids": [str(rid) for rid in sample_ids],
                }
            )
            evidence.extend(sample_ids)

        pairs = {(item["source"], item["platform"]) for item in items}
        summary = (
            f"Compared sentiment distribution across {len(pairs)} source/platform pairs."
            if items
            else "No platform comparison data available."
        )
        return Insight(
            insight_type="platform_comparison",
            title="Platform & Sentiment Comparison",
            summary=summary,
            evidence_review_ids=list(dict.fromkeys(evidence)),
            metrics={"items": items},
        )

    def segment_breakdown(self) -> Insight:
        rows = (
            self.db.query(
                ReviewEnrichment.user_segment,
                ReviewEnrichment.sentiment,
                func.count(ReviewEnrichment.id).label("count"),
            )
            .group_by(ReviewEnrichment.user_segment, ReviewEnrichment.sentiment)
            .order_by(func.count(ReviewEnrichment.id).desc())
            .all()
        )

        items = []
        evidence: list[uuid.UUID] = []
        for segment, sentiment, count in rows:
            sample = (
                self.db.query(ReviewEnrichment.review_id)
                .filter(
                    ReviewEnrichment.user_segment == segment,
                    ReviewEnrichment.sentiment == sentiment,
                )
                .limit(MIN_EVIDENCE)
                .all()
            )
            sample_ids = [row[0] for row in sample]
            items.append(
                {
                    "user_segment": segment,
                    "sentiment": sentiment,
                    "count": count,
                    "evidence_review_ids": [str(rid) for rid in sample_ids],
                }
            )
            evidence.extend(sample_ids)

        return Insight(
            insight_type="segments",
            title="User Segment Sentiment Analysis",
            summary=f"Sentiment breakdown across {len({i['user_segment'] for i in items})} user segments.",
            evidence_review_ids=list(dict.fromkeys(evidence)),
            metrics={"items": items},
        )
