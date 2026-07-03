from enum import Enum

from pydantic import BaseModel, Field, field_validator


class Sentiment(str, Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    MIXED = "mixed"


class EnrichmentOutput(BaseModel):
    sentiment: Sentiment
    emotion: list[str] = Field(default_factory=list)
    primary_topic: str
    user_goal: str | None = None
    pain_point: str | None = None
    feature_request: str | None = None
    discovery_issue: str | None = None
    listening_behavior: str | None = None
    user_segment: str | None = None
    keywords: list[str] = Field(default_factory=list)
    summary: str
    confidence_score: float = Field(ge=0.0, le=1.0)

    @field_validator("emotion", "keywords", mode="before")
    @classmethod
    def empty_list_if_none(cls, value):
        return value or []

    @field_validator("confidence_score", mode="before")
    @classmethod
    def clamp_confidence(cls, value):
        if value is None:
            return 0.5
        return max(0.0, min(1.0, float(value)))
