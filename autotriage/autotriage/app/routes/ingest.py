from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Header, Request
from fastapi import HTTPException

from autotriage.metrics.prom import INGEST_IDEMPOTENT_HIT_TOTAL, INGEST_TOTAL
from autotriage.storage.repositories.alerts_repo import AlertsRepository
from autotriage.storage.db import with_db

router = APIRouter()


def _compute_idempotency_key(payload: dict[str, Any]) -> str:
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


@router.post("/webhook/alerts", status_code=202)
@with_db
async def webhook_alerts(
    request: Request,
    db,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
) -> dict[str, str]:
    payload = await request.json()
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="alert payload must be an object")
    key = idempotency_key or _compute_idempotency_key(payload)
    repo = AlertsRepository(db)
    ingest_id, hit = repo.insert_or_get_ingest(
        idempotency_key=key, received_at=datetime.now(tz=timezone.utc), raw_payload=payload
    )
    INGEST_TOTAL.inc()
    if hit:
        INGEST_IDEMPOTENT_HIT_TOTAL.inc()
    return {"ingest_id": ingest_id, "status": "accepted"}
