import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.api.dependencies import get_db_session
from src.api.schemas import SegmentRow, SegmentsResponse
from src.insights.aggregator import InsightAggregator

router = APIRouter(prefix="/api/v1", tags=["segments"])


@router.get("/segments", response_model=SegmentsResponse)
def list_segments(db: Session = Depends(get_db_session)) -> SegmentsResponse:
    insight = InsightAggregator(db).segment_breakdown()
    items = insight.metrics.get("items", [])
    segments = [
        SegmentRow(
            user_segment=item.get("user_segment"),
            sentiment=item.get("sentiment"),
            count=item.get("count", 0),
            evidence_review_ids=[uuid.UUID(str(rid)) for rid in item.get("evidence_review_ids", [])],
        )
        for item in items
    ]
    return SegmentsResponse(count=len(segments), segments=segments)
