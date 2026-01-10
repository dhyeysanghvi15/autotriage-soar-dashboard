from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from autotriage.metrics.experiments import ExperimentsService
from autotriage.storage.db import with_db

router = APIRouter()


class ReplayRequest(BaseModel):
    since: datetime
    until: datetime
    config_overrides: dict[str, Any] | None = Field(default=None)


@router.post("/replay")
@with_db
def start_replay(db, body: ReplayRequest) -> dict[str, str]:
    svc = ExperimentsService(db)
    experiment_id = svc.run_replay(body.since, body.until, body.config_overrides or {})
    return {"experiment_id": experiment_id}


@router.get("/experiments")
@with_db
def list_experiments(db) -> dict[str, object]:
    svc = ExperimentsService(db)
    return {"items": svc.list_experiments()}


@router.get("/experiments/{experiment_id}")
@with_db
def get_experiment(db, experiment_id: str) -> dict[str, object]:
    svc = ExperimentsService(db)
    return svc.get_experiment(experiment_id)

