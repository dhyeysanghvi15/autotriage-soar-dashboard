from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from autotriage.config import AppConfig
from autotriage.core.correlate.correlator import correlate_into_case
from autotriage.core.dedup.deduper import find_duplicate_of, record_fingerprint
from autotriage.core.fingerprint.strategies import compute_fingerprint
from autotriage.core.models.alert import CanonicalAlert
from autotriage.core.normalize.registry import normalize
from autotriage.storage.repositories.events_repo import EventsRepository


@dataclass
class PipelineState:
    ingest_id: str
    raw: dict[str, Any]
    alert: CanonicalAlert | None = None
    fingerprint_hash: str | None = None
    duplicate_of: str | None = None
    case_id: str | None = None


def stage_normalize(db: sqlite3.Connection, cfg: AppConfig, events: EventsRepository, st: PipelineState) -> PipelineState:
    res = normalize(st.raw)
    alert = res.alert.model_copy(update={"ingest_id": st.ingest_id})
    db.execute(
        "UPDATE alerts SET normalized_json = ?, vendor = ?, status = 'normalized' WHERE ingest_id = ?",
        (alert.model_dump_json(), alert.vendor, st.ingest_id),
    )
    db.commit()
    events.append(
        stage="normalized",
        created_at=datetime.now(tz=timezone.utc),
        ingest_id=st.ingest_id,
        case_id=None,
        payload={"vendor": alert.vendor, "alert_type": alert.alert_type, "warnings": res.warnings},
    )
    st.alert = alert
    return st


def stage_fingerprint(db: sqlite3.Connection, cfg: AppConfig, events: EventsRepository, st: PipelineState) -> PipelineState:
    assert st.alert is not None
    fp = compute_fingerprint(st.alert, cfg.dedup_window_seconds)
    st.fingerprint_hash = fp.fp_hash
    dup_of = find_duplicate_of(db, fp)
    record_fingerprint(db, st.ingest_id, fp)
    st.duplicate_of = dup_of
    events.append(
        stage="fingerprinted",
        created_at=datetime.now(tz=timezone.utc),
        ingest_id=st.ingest_id,
        case_id=None,
        payload={"fp_hash": fp.fp_hash, "window_start": fp.window_start.isoformat(), "duplicate_of": dup_of},
    )
    return st


def stage_dedup(db: sqlite3.Connection, events: EventsRepository, st: PipelineState) -> PipelineState:
    if st.duplicate_of is not None and st.duplicate_of != st.ingest_id:
        db.execute("UPDATE alerts SET status = 'deduped' WHERE ingest_id = ?", (st.ingest_id,))
        db.commit()
        events.append(
            stage="deduped",
            created_at=datetime.now(tz=timezone.utc),
            ingest_id=st.ingest_id,
            case_id=None,
            payload={"duplicate_of": st.duplicate_of},
        )
    else:
        db.execute("UPDATE alerts SET status = 'dedup_pass' WHERE ingest_id = ?", (st.ingest_id,))
        db.commit()
    return st


def stage_correlate(db: sqlite3.Connection, cfg: AppConfig, events: EventsRepository, st: PipelineState) -> PipelineState:
    assert st.alert is not None
    if st.duplicate_of is not None and st.duplicate_of != st.ingest_id:
        return st
    score = {"severity": st.alert.severity, "confidence": 0.6, "contributions": []}
    routing = {"queue": "triage", "rationale": ["default_queue"]}
    case_id = correlate_into_case(
        db,
        st.alert,
        correlation_window_seconds=cfg.correlation_window_seconds,
        base_severity=st.alert.severity,
        decision="CREATE_TICKET",
        queue="triage",
        score=score,
        routing=routing,
    )
    st.case_id = case_id
    events.append(
        stage="correlated",
        created_at=datetime.now(tz=timezone.utc),
        ingest_id=st.ingest_id,
        case_id=case_id,
        payload={"case_id": case_id, "entity_count": len(st.alert.entities)},
    )
    db.execute("UPDATE alerts SET status = 'correlated' WHERE ingest_id = ?", (st.ingest_id,))
    db.commit()
    return st


def stage_finalize(db: sqlite3.Connection, events: EventsRepository, st: PipelineState) -> PipelineState:
    db.execute("UPDATE alerts SET status = 'processed' WHERE ingest_id = ?", (st.ingest_id,))
    db.commit()
    events.append(
        stage="processed",
        created_at=datetime.now(tz=timezone.utc),
        ingest_id=st.ingest_id,
        case_id=st.case_id,
        payload={"status": "processed"},
    )
    return st

