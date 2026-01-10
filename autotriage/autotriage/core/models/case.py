from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from autotriage.core.models.decisions import Decision
from autotriage.core.models.entities import Edge, Entity


class ScoreContribution(BaseModel):
    name: str
    weight: float
    value: float
    points: float
    reason: str


class ScoreExplanation(BaseModel):
    severity: int = Field(ge=0, le=100)
    confidence: float = Field(ge=0.0, le=1.0)
    contributions: list[ScoreContribution]


class CaseSummary(BaseModel):
    case_id: str
    created_at: datetime
    updated_at: datetime
    severity: int = Field(ge=0, le=100)
    confidence: float = Field(ge=0.0, le=1.0)
    decision: Decision
    queue: str
    summary: str


class CaseDetail(BaseModel):
    case: CaseSummary
    entities: list[Entity]
    edges: list[Edge]
    enrichments: dict[str, Any]
    scoring: ScoreExplanation
    routing_rationale: list[str]
    recommended_actions: list[dict[str, Any]]

