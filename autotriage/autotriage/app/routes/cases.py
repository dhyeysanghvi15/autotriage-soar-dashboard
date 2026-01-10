from __future__ import annotations

import json
import sqlite3
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query

from autotriage.playbooks.catalog import recommended_actions_for_case
from autotriage.storage.db import db_dependency
from autotriage.storage.repositories.cases_repo import CasesRepository

router = APIRouter()


@router.get("/cases")
def list_cases(
    db: Annotated[sqlite3.Connection, Depends(db_dependency)],
    time_range: str | None = Query(default=None),
    severity_min: int | None = Query(default=None),
    decision: str | None = Query(default=None),
    queue: str | None = Query(default=None),
    q: str | None = Query(default=None),
) -> dict[str, object]:
    repo = CasesRepository(db)
    cases = repo.list_cases(
        time_range=time_range, severity_min=severity_min, decision=decision, queue=queue, q=q
    )
    return {"items": cases}


@router.get("/cases/{case_id}")
def get_case(
    case_id: str, db: Annotated[sqlite3.Connection, Depends(db_dependency)]
) -> dict[str, object]:
    repo = CasesRepository(db)
    detail = repo.get_case_detail(case_id)
    case = detail.get("case") or {}
    scoring = {}
    routing = {}
    try:
        scoring = json.loads(str(case.get("score_json") or "{}"))
    except Exception:  # noqa: BLE001
        scoring = {}
    try:
        routing = json.loads(str(case.get("routing_json") or "{}"))
    except Exception:  # noqa: BLE001
        routing = {}

    timeline: list[dict[str, Any]] = []
    enrichments: dict[str, Any] = {}
    for ev in detail.get("timeline") or []:
        ev = dict(ev)
        try:
            payload = json.loads(str(ev.get("payload_json") or "{}"))
        except Exception:  # noqa: BLE001
            payload = {}
        ev["payload"] = payload
        timeline.append(ev)
        if ev.get("stage") == "enriched":
            enrichments = payload.get("enrichments") or enrichments

    actions = recommended_actions_for_case(case, detail.get("graph"))
    return {
        "case": case,
        "timeline": timeline,
        "graph": detail.get("graph"),
        "ticket": detail.get("ticket"),
        "enrichments": enrichments,
        "scoring": scoring,
        "routing": routing,
        "recommended_actions": actions,
    }
