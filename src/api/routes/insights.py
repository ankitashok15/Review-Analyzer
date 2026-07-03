import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from src.api.dependencies import AdminRequired, get_db_session
from src.cache.insight_cache import insight_list_cache
from src.insights.schemas import VALID_INSIGHT_TYPES, InsightListResponse, InsightResponse
from src.insights.service import InsightService
from src.storage.models import InsightCache

router = APIRouter(prefix="/api/v1", tags=["insights"])


def _to_response(row: InsightCache) -> InsightResponse:
    evidence = [uuid.UUID(str(rid)) for rid in (row.evidence_review_ids or [])]
    return InsightResponse(
        insight_type=row.insight_type,
        title=row.title,
        summary=row.summary,
        evidence_review_ids=evidence,
        metrics=row.metrics or {},
        generated_at=row.generated_at.isoformat(),
        cache_key=row.cache_key,
    )


@router.get("/insights", response_model=InsightListResponse)
def list_insights(db: Session = Depends(get_db_session)) -> InsightListResponse:
    cached = insight_list_cache.get()
    if cached:
        return InsightListResponse(**cached)

    rows = (
        db.query(InsightCache)
        .order_by(InsightCache.insight_type.asc(), InsightCache.generated_at.desc())
        .all()
    )
    response = InsightListResponse(
        count=len(rows),
        insights=[_to_response(row) for row in rows],
    )
    insight_list_cache.set(response.model_dump())
    return response


@router.get("/insights/{insight_type}", response_model=InsightResponse)
def get_insight(
    insight_type: str,
    db: Session = Depends(get_db_session),
    refresh: bool = Query(default=False, description="Regenerate insight before returning"),
) -> InsightResponse:
    if insight_type not in VALID_INSIGHT_TYPES:
        raise HTTPException(status_code=404, detail=f"Unknown insight type: {insight_type}")

    service = InsightService(db)
    if refresh:
        insight = service.generate(insight_type)
        row = (
            db.query(InsightCache)
            .filter(
                InsightCache.insight_type == insight.insight_type,
                InsightCache.cache_key == insight.cache_key,
            )
            .first()
        )
        if row is None:
            raise HTTPException(status_code=500, detail="Failed to cache insight")
        return _to_response(row)

    row = (
        db.query(InsightCache)
        .filter(InsightCache.insight_type == insight_type, InsightCache.cache_key == "default")
        .first()
    )
    if row is None:
        raise HTTPException(
            status_code=404,
            detail=f"No cached insight for type '{insight_type}'. Call with ?refresh=true to generate.",
        )
    return _to_response(row)


@router.post("/insights/refresh", response_model=InsightListResponse, dependencies=[AdminRequired])
def refresh_insights(db: Session = Depends(get_db_session)) -> InsightListResponse:
    service = InsightService(db, gemini_client=None)
    service.refresh_cache()
    insight_list_cache.invalidate()
    rows = (
        db.query(InsightCache)
        .order_by(InsightCache.insight_type.asc())
        .all()
    )
    return InsightListResponse(
        count=len(rows),
        insights=[_to_response(row) for row in rows],
    )
