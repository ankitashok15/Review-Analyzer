import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from src.api.dependencies import get_db_session
from src.api.schemas import TopicCluster, TopicsResponse
from src.storage.models import ReviewEnrichment

router = APIRouter(prefix="/api/v1", tags=["topics"])

SAMPLE_EVIDENCE = 5


@router.get("/topics", response_model=TopicsResponse)
def list_topics(
    db: Session = Depends(get_db_session),
    limit: int = Query(default=20, ge=1, le=100),
) -> TopicsResponse:
    rows = (
        db.query(
            ReviewEnrichment.primary_topic,
            func.count(ReviewEnrichment.id).label("count"),
        )
        .filter(ReviewEnrichment.primary_topic.isnot(None))
        .filter(ReviewEnrichment.primary_topic != "")
        .group_by(ReviewEnrichment.primary_topic)
        .order_by(func.count(ReviewEnrichment.id).desc())
        .limit(limit)
        .all()
    )

    topics: list[TopicCluster] = []
    for topic, count in rows:
        evidence_rows = (
            db.query(ReviewEnrichment.review_id)
            .filter(ReviewEnrichment.primary_topic == topic)
            .order_by(ReviewEnrichment.enriched_at.desc())
            .limit(SAMPLE_EVIDENCE)
            .all()
        )
        topics.append(
            TopicCluster(
                topic=topic,
                count=count,
                evidence_review_ids=[row[0] for row in evidence_rows],
            )
        )

    return TopicsResponse(count=len(topics), topics=topics)
