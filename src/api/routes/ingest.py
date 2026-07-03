from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import src.ingestion.adapters  # noqa: F401 — register adapters
from src.api.dependencies import AdminRequired, get_db_session
from src.api.schemas import IngestRequest, IngestResponse
from src.ingestion.service import IngestionService

router = APIRouter(prefix="/api/v1", tags=["ingest"])

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CSV = ROOT / "phases" / "phase-1" / "data" / "spotify_reviews.csv"


@router.post("/ingest", response_model=IngestResponse, dependencies=[AdminRequired])
def trigger_ingest(
    body: IngestRequest,
    db: Session = Depends(get_db_session),
) -> IngestResponse:
    file_path = body.file or str(DEFAULT_CSV)
    options: dict = {"file": file_path, "skip_validation": body.skip_validation}
    if body.limit is not None:
        options["limit"] = body.limit

    try:
        result = IngestionService(db).run(body.source, options)
    except KeyError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return IngestResponse(
        source=body.source,
        file=file_path,
        inserted=result.inserted,
        skipped=result.skipped,
        rejected=result.rejected,
        duplicates=result.duplicates,
        failed=result.failed,
        errors=result.errors,
    )
