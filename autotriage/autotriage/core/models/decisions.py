from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel


class Decision(StrEnum):
    auto_close = "AUTO_CLOSE"
    create_ticket = "CREATE_TICKET"
    escalate = "ESCALATE"


class RoutingDecision(BaseModel):
    decision: Decision
    queue: str
    rationale: list[str]

