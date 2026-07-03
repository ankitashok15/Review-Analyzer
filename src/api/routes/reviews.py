import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.api.dependencies import get_db_session
from src.api.schemas import ReviewDetailResponse
from src.api.serializers import review_detail_to_response
from src.storage.repositories.composite import CompositeRepository

router = APIRouter(prefix="/api/v1", tags=["reviews"])


@router.get("/reviews/{review_id}", response_model=ReviewDetailResponse)
def get_review(
    review_id: uuid.UUID,
    db: Session = Depends(get_db_session),
) -> ReviewDetailResponse:
    detail = CompositeRepository(db).get_review_with_enrichment(review_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="Review not found")
    return review_detail_to_response(detail)
