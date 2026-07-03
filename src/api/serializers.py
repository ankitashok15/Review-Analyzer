import uuid

from src.api.schemas import EnrichmentResponse, ReviewDetailResponse
from src.storage.repositories.schemas import ReviewDetail


def enrichment_to_response(enrichment) -> EnrichmentResponse | None:
    if enrichment is None:
        return None
    return EnrichmentResponse(
        sentiment=enrichment.sentiment,
        emotion=enrichment.emotion or [],
        primary_topic=enrichment.primary_topic,
        user_goal=enrichment.user_goal,
        pain_point=enrichment.pain_point,
        feature_request=enrichment.feature_request,
        discovery_issue=enrichment.discovery_issue,
        listening_behavior=enrichment.listening_behavior,
        user_segment=enrichment.user_segment,
        keywords=enrichment.keywords or [],
        summary=enrichment.summary,
        confidence_score=enrichment.confidence_score,
        model_version=enrichment.model_version,
    )


def review_detail_to_response(detail: ReviewDetail) -> ReviewDetailResponse:
    review = detail.review
    return ReviewDetailResponse(
        id=review.id,
        source=review.source,
        source_id=review.source_id,
        source_url=review.source_url,
        app_name=review.app_name,
        platform=review.platform,
        rating=review.rating,
        title=review.title,
        body=review.body,
        language=review.language,
        review_date=review.review_date.isoformat(),
        ingested_at=review.ingested_at.isoformat(),
        enrichment=enrichment_to_response(detail.enrichment),
    )
