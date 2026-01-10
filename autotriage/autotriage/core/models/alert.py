from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from autotriage.core.models.entities import Entity


class CanonicalAlert(BaseModel):
    ingest_id: str | None = None
    vendor: str = Field(min_length=1)
    alert_type: str = Field(min_length=1)
    ts: datetime
    title: str = Field(min_length=1)
    rule_id: str | None = None
    technique_id: str | None = None
    severity: int = Field(ge=0, le=100)
    entities: list[Entity] = Field(default_factory=list)
    raw: dict[str, Any] = Field(default_factory=dict)


class NormalizationResult(BaseModel):
    alert: CanonicalAlert
    warnings: list[str] = Field(default_factory=list)
