from datetime import datetime, timedelta, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from src.insights.schemas import Insight
from src.storage.models import Review, ReviewEnrichment


class TrendAnalyzer:
    """Time-windowed rollups with period-over-period deltas."""

    def __init__(self, db: Session):
        self.db = db

    def analyze(self, *, window_days: int = 30) -> Insight:
        now = datetime.now(timezone.utc)
        current_start = now - timedelta(days=window_days)
        previous_start = now - timedelta(days=window_days * 2)

        current_rows = self._topic_counts(since=current_start, until=now)
        previous_rows = self._topic_counts(since=previous_start, until=current_start)

        previous_map = {topic: count for topic, count in previous_rows}
        items = []
        all_evidence: list = []

        for topic, current_count in current_rows:
            previous_count = previous_map.get(topic, 0)
            if previous_count == 0:
                delta_pct = 100.0 if current_count > 0 else 0.0
            else:
                delta_pct = round(((current_count - previous_count) / previous_count) * 100, 2)

            evidence = self._sample_topic_evidence(topic, limit=3)
            items.append(
                {
                    "primary_topic": topic,
                    "current_count": current_count,
                    "previous_count": previous_count,
                    "delta_percent": delta_pct,
                    "evidence_review_ids": [str(rid) for rid in evidence],
                }
            )
            all_evidence.extend(evidence)

        rising = sorted(items, key=lambda row: row["delta_percent"], reverse=True)[:10]
        summary = (
            f"Compared topic frequency over the last {window_days} days vs the prior {window_days} days."
            if rising
            else "Insufficient enriched review history for trend analysis."
        )

        return Insight(
            insight_type="trends",
            title="Emerging Topic Trends",
            summary=summary,
            evidence_review_ids=list(dict.fromkeys(all_evidence)),
            metrics={
                "window_days": window_days,
                "items": rising,
            },
        )

    def _topic_counts(
        self,
        *,
        since: datetime,
        until: datetime,
    ) -> list[tuple[str, int]]:
        rows = (
            self.db.query(
                ReviewEnrichment.primary_topic,
                func.count(ReviewEnrichment.id),
            )
            .join(Review, Review.id == ReviewEnrichment.review_id)
            .filter(Review.review_date >= since, Review.review_date < until)
            .filter(ReviewEnrichment.primary_topic.isnot(None))
            .group_by(ReviewEnrichment.primary_topic)
            .order_by(func.count(ReviewEnrichment.id).desc())
            .all()
        )
        return [(topic, count) for topic, count in rows if topic]

    def _sample_topic_evidence(self, topic: str, *, limit: int = 3) -> list:
        rows = (
            self.db.query(ReviewEnrichment.review_id)
            .filter(ReviewEnrichment.primary_topic == topic)
            .order_by(ReviewEnrichment.enriched_at.desc())
            .limit(limit)
            .all()
        )
        return [row[0] for row in rows]
