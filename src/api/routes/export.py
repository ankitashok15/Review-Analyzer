import csv
import io

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session

from src.api.dependencies import AdminRequired, get_db_session
from src.api.schemas import ExportRequest, ExportResponse, ExportRow
from src.storage.repositories.composite import CompositeRepository

router = APIRouter(prefix="/api/v1", tags=["export"])


def _rows_to_csv(rows: list[ExportRow]) -> str:
    buffer = io.StringIO()
    if not rows:
        return ""
    fieldnames = list(ExportRow.model_fields.keys())
    writer = csv.DictWriter(buffer, fieldnames=fieldnames)
    writer.writeheader()
    for row in rows:
        writer.writerow(row.model_dump(mode="json"))
    return buffer.getvalue()


@router.post("/export", dependencies=[AdminRequired])
def export_findings(
    body: ExportRequest,
    db: Session = Depends(get_db_session),
):
    if not body.review_ids:
        raise HTTPException(status_code=400, detail="review_ids cannot be empty")

    composite = CompositeRepository(db)
    rows: list[ExportRow] = []
    for review_id in body.review_ids:
        detail = composite.get_review_with_enrichment(review_id)
        if detail is None:
            continue
        review = detail.review
        enrichment = detail.enrichment
        rows.append(
            ExportRow(
                review_id=review.id,
                source=review.source,
                platform=review.platform,
                rating=review.rating,
                review_date=review.review_date.isoformat(),
                body=review.body,
                sentiment=enrichment.sentiment if enrichment and body.include_enrichment else None,
                primary_topic=enrichment.primary_topic if enrichment and body.include_enrichment else None,
                pain_point=enrichment.pain_point if enrichment and body.include_enrichment else None,
                feature_request=enrichment.feature_request if enrichment and body.include_enrichment else None,
                summary=enrichment.summary if enrichment and body.include_enrichment else None,
            )
        )

    if body.format == "csv":
        csv_content = _rows_to_csv(rows)
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=export.csv"},
        )

    payload = ExportResponse(format="json", count=len(rows), rows=rows)
    return payload
