from __future__ import annotations

import sqlite3
from datetime import datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from autotriage.metrics.experiments import ExperimentsService
from autotriage.storage.db import db_dependency

router = APIRouter()


class ReplayRequest(BaseModel):
    since: datetime
    until: datetime
    config_overrides: dict[str, Any] | None = Field(default=None)


@router.post("/replay")
def start_replay(
    body: ReplayRequest, db: Annotated[sqlite3.Connection, Depends(db_dependency)]
) -> dict[str, str]:
    svc = ExperimentsService(db)
    experiment_id = svc.run_replay(body.since, body.until, body.config_overrides or {})
    return {"experiment_id": experiment_id}


@router.get("/experiments")
def list_experiments(
    db: Annotated[sqlite3.Connection, Depends(db_dependency)],
) -> dict[str, object]:
    svc = ExperimentsService(db)
    return {"items": svc.list_experiments()}


@router.get("/experiments/{experiment_id}")
def get_experiment(
    experiment_id: str, db: Annotated[sqlite3.Connection, Depends(db_dependency)]
) -> dict[str, object]:
    svc = ExperimentsService(db)
    return svc.get_experiment(experiment_id)
