import uuid
from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel, Field

from src.retrieval.schemas import SearchFilters


ConfidenceLevel = Literal["high", "medium", "low"]


class AskRequest(BaseModel):
    question: str
    filters: SearchFilters = Field(default_factory=SearchFilters)
    top_k: int = Field(default=15, ge=1, le=50)
    rewrite_query: bool = False
    include_insights: bool = True


class Citation(BaseModel):
    review_id: uuid.UUID
    excerpt: str
    source: str
    relevance_score: float = Field(ge=0.0, le=1.0)


class AskResponse(BaseModel):
    question: str
    answer: str
    confidence: ConfidenceLevel
    citations: list[Citation]
    related_insights: list[str]
    retrieval_count: int


@dataclass
class RetrievedReview:
    review_id: uuid.UUID
    body: str
    excerpt: str
    score: float
    source: str
    platform: str
    sentiment: str | None = None
    primary_topic: str | None = None
    summary: str | None = None


@dataclass
class InsightSnippet:
    insight_id: str
    insight_type: str
    title: str
    summary: str


class CitationOutput(BaseModel):
    review_id: str
    excerpt: str


class RagGenerationOutput(BaseModel):
    answer: str
    confidence: ConfidenceLevel
    citations: list[CitationOutput] = Field(default_factory=list)


class QueryRewriteOutput(BaseModel):
    rewritten_query: str
