import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.api.dependencies import get_db_session
from src.rag.answer_generator import AnswerGenerator
from src.rag.schemas import AskRequest, AskResponse
from src.rag.service import RagService
from src.security.sanitize import sanitize_query

router = APIRouter(prefix="/api/v1", tags=["ask"])
logger = logging.getLogger(__name__)


@router.post("/ask", response_model=AskResponse)
def ask_question(
    body: AskRequest,
    db: Session = Depends(get_db_session),
) -> AskResponse:
    question = sanitize_query(body.question)
    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    try:
        service = RagService(db)
        sanitized = body.model_copy(update={"question": question})
        return service.ask(sanitized)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Ask route failed for question=%r", question)
        return AnswerGenerator().insufficient_evidence(question, retrieval_count=0)
