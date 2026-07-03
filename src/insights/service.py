import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from src.insights.aggregator import InsightAggregator
from src.insights.schemas import VALID_INSIGHT_TYPES, Insight
from src.insights.theme_detector import ThemeDetector
from src.insights.trend_analyzer import TrendAnalyzer
from src.storage.models import InsightCache


class InsightService:
    """Generate and cache evidence-backed product insights."""

    STANDARD_TYPES = (
        "pain_points",
        "feature_requests",
        "platform_comparison",
        "trends",
        "segments",
        "themes",
    )

    def __init__(self, db: Session, *, gemini_client=None):
        self.db = db
        self.aggregator = InsightAggregator(db)
        self.trends = TrendAnalyzer(db)
        self.themes = ThemeDetector(db, gemini_client=gemini_client)

    def generate(self, insight_type: str, params: dict | None = None) -> Insight:
        params = params or {}
        if insight_type not in VALID_INSIGHT_TYPES:
            raise ValueError(f"Unknown insight type: {insight_type}")

        if insight_type == "pain_points":
            insight = self.aggregator.top_pain_points(limit=params.get("limit", 10))
        elif insight_type == "feature_requests":
            insight = self.aggregator.top_feature_requests(limit=params.get("limit", 10))
        elif insight_type == "platform_comparison":
            insight = self.aggregator.platform_comparison()
        elif insight_type == "trends":
            insight = self.trends.analyze(window_days=params.get("window_days", 30))
        elif insight_type == "segments":
            insight = self.aggregator.segment_breakdown()
        elif insight_type == "themes":
            insight = self.themes.detect_themes(use_gemini=params.get("use_gemini", True))
        else:
            raise ValueError(f"Unsupported insight type: {insight_type}")

        cache_key = params.get("cache_key", "default")
        insight.cache_key = cache_key
        self._upsert_cache(insight)
        return insight

    def refresh_cache(self, params: dict | None = None) -> list[Insight]:
        params = params or {}
        insights: list[Insight] = []
        for insight_type in self.STANDARD_TYPES:
            type_params = dict(params)
            if insight_type == "themes":
                type_params.setdefault("use_gemini", False)
            insights.append(self.generate(insight_type, type_params))
        return insights

    def list_cached(self) -> list[Insight]:
        rows = (
            self.db.query(InsightCache)
            .order_by(InsightCache.insight_type.asc(), InsightCache.generated_at.desc())
            .all()
        )
        return [self._to_insight(row) for row in rows]

    def get_cached(self, insight_type: str, *, cache_key: str = "default") -> Insight | None:
        row = (
            self.db.query(InsightCache)
            .filter(
                InsightCache.insight_type == insight_type,
                InsightCache.cache_key == cache_key,
            )
            .first()
        )
        if row is None:
            return None
        return self._to_insight(row)

    def _upsert_cache(self, insight: Insight) -> InsightCache:
        row = (
            self.db.query(InsightCache)
            .filter(
                InsightCache.insight_type == insight.insight_type,
                InsightCache.cache_key == insight.cache_key,
            )
            .first()
        )
        payload = {
            "title": insight.title,
            "summary": insight.summary,
            "evidence_review_ids": [str(rid) for rid in insight.evidence_review_ids],
            "metrics": insight.metrics,
            "generated_at": datetime.now(timezone.utc),
        }
        if row is None:
            row = InsightCache(
                id=uuid.uuid4(),
                insight_type=insight.insight_type,
                cache_key=insight.cache_key,
                **payload,
            )
            self.db.add(row)
        else:
            row.title = payload["title"]
            row.summary = payload["summary"]
            row.evidence_review_ids = payload["evidence_review_ids"]
            row.metrics = payload["metrics"]
            row.generated_at = payload["generated_at"]

        self.db.commit()
        self.db.refresh(row)
        return row

    @staticmethod
    def _to_insight(row: InsightCache) -> Insight:
        evidence = [uuid.UUID(str(rid)) for rid in (row.evidence_review_ids or [])]
        return Insight(
            insight_type=row.insight_type,
            title=row.title,
            summary=row.summary,
            evidence_review_ids=evidence,
            metrics=row.metrics or {},
            cache_key=row.cache_key,
        )

    @staticmethod
    def to_response(insight: Insight, generated_at: datetime | None = None) -> dict:
        return {
            "insight_type": insight.insight_type,
            "title": insight.title,
            "summary": insight.summary,
            "evidence_review_ids": insight.evidence_review_ids,
            "metrics": insight.metrics,
            "generated_at": (generated_at or datetime.now(timezone.utc)).isoformat(),
            "cache_key": insight.cache_key,
        }
