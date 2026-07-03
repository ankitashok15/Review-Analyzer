from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.api.dependencies import AdminRequired, get_db_session
from src.retrieval.schemas import SearchQuery, SearchResponse, SearchResultResponse
from src.retrieval.semantic_search import SemanticSearchService
from src.security.sanitize import sanitize_query

router = APIRouter(prefix="/api/v1", tags=["search"])


@router.post("/search", response_model=SearchResponse)
def search_reviews(
    body: SearchQuery,
    db: Session = Depends(get_db_session),
) -> SearchResponse:
    query = sanitize_query(body.query)
    if not query:
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    service = SemanticSearchService(db)
    try:
        results = service.search(
            query,
            body.filters,
            top_k=body.top_k,
            hybrid=body.hybrid,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return SearchResponse(
        query=query,
        count=len(results),
        results=[SearchResultResponse.model_validate(result.__dict__) for result in results],
    )
