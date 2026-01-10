from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from typing import Any

import structlog

from autotriage.config import load_effective_config
from autotriage.core.pipeline.stages import (
    PipelineState,
    stage_correlate,
    stage_dedup,
    stage_enrich,
    stage_finalize,
    stage_fingerprint,
    stage_normalize,
    stage_score_decide_route,
)
from autotriage.storage.repositories.deadletter_repo import DeadletterRepository
from autotriage.storage.repositories.events_repo import EventsRepository

log = structlog.get_logger(__name__)


def process_ingest(
    db: sqlite3.Connection, ingest_id: str, raw_payload: dict[str, Any]
) -> PipelineState:
    cfg = load_effective_config()
    events = EventsRepository(db)
    st = PipelineState(ingest_id=ingest_id, raw=raw_payload)
    try:
        st = stage_normalize(db, cfg, events, st)
        st = stage_fingerprint(db, cfg, events, st)
        st = stage_dedup(db, events, st)
        st = stage_correlate(db, cfg, events, st)
        st = stage_enrich(db, cfg, events, st)
        st = stage_score_decide_route(db, cfg, events, st)
        st = stage_finalize(db, events, st)
        return st
    except Exception as e:  # noqa: BLE001
        DeadletterRepository(db).upsert(ingest_id, repr(e), raw_payload)
        events.append(
            stage="failed",
            created_at=datetime.now(tz=UTC),
            ingest_id=ingest_id,
            case_id=None,
            payload={"error": repr(e)},
        )
        db.execute(
            "UPDATE alerts SET status = 'failed', last_error = ? WHERE ingest_id = ?",
            (repr(e), ingest_id),
        )
        db.commit()
        log.exception("pipeline_failed", ingest_id=ingest_id)
        raise
