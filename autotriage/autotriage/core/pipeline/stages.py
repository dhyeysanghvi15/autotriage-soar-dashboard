from __future__ import annotations

import json
import sqlite3
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from autotriage.config import AppConfig
from autotriage.connectors.mock_ticketing import MockTicketingConnector
from autotriage.core.correlate.correlator import correlate_into_case
from autotriage.core.decisioning.decide import decide, load_thresholds
from autotriage.core.dedup.deduper import find_duplicate_of, record_fingerprint
from autotriage.core.fingerprint.strategies import compute_fingerprint
from autotriage.core.models.alert import CanonicalAlert
from autotriage.core.normalize.registry import normalize
from autotriage.core.routing.router import route
from autotriage.core.scoring.rule_parser import load_scoring_rules
from autotriage.core.scoring.score_engine import score_alert
from autotriage.enrichers.manager import EnricherManager
from autotriage.metrics.prom import PIPELINE_STAGE_SECONDS, PIPELINE_STAGE_TOTAL
from autotriage.storage.repositories.events_repo import EventsRepository


@dataclass
class PipelineState:
    ingest_id: str
    raw: dict[str, Any]
    alert: CanonicalAlert | None = None
    fingerprint_hash: str | None = None
    duplicate_of: str | None = None
    case_id: str | None = None
    enrichments: dict[str, Any] | None = None
    score: dict[str, Any] | None = None
    routing: dict[str, Any] | None = None


def stage_normalize(
    db: sqlite3.Connection, cfg: AppConfig, events: EventsRepository, st: PipelineState
) -> PipelineState:
    t0 = time.perf_counter()
    res = normalize(st.raw)
    alert = res.alert.model_copy(update={"ingest_id": st.ingest_id})
    db.execute(
        "UPDATE alerts SET normalized_json = ?, vendor = ?, status = 'normalized' WHERE ingest_id = ?",
        (alert.model_dump_json(), alert.vendor, st.ingest_id),
    )
    db.commit()
    events.append(
        stage="normalized",
        created_at=datetime.now(tz=UTC),
        ingest_id=st.ingest_id,
        case_id=None,
        payload={"vendor": alert.vendor, "alert_type": alert.alert_type, "warnings": res.warnings},
    )
    st.alert = alert
    PIPELINE_STAGE_TOTAL.labels("normalized").inc()
    PIPELINE_STAGE_SECONDS.labels("normalized").observe(time.perf_counter() - t0)
    return st


def stage_fingerprint(
    db: sqlite3.Connection, cfg: AppConfig, events: EventsRepository, st: PipelineState
) -> PipelineState:
    t0 = time.perf_counter()
    assert st.alert is not None
    fp = compute_fingerprint(st.alert, cfg.dedup_window_seconds)
    st.fingerprint_hash = fp.fp_hash
    dup_of = find_duplicate_of(db, fp)
    record_fingerprint(db, st.ingest_id, fp)
    st.duplicate_of = dup_of
    events.append(
        stage="fingerprinted",
        created_at=datetime.now(tz=UTC),
        ingest_id=st.ingest_id,
        case_id=None,
        payload={
            "fp_hash": fp.fp_hash,
            "window_start": fp.window_start.isoformat(),
            "duplicate_of": dup_of,
        },
    )
    PIPELINE_STAGE_TOTAL.labels("fingerprinted").inc()
    PIPELINE_STAGE_SECONDS.labels("fingerprinted").observe(time.perf_counter() - t0)
    return st


def stage_dedup(
    db: sqlite3.Connection, events: EventsRepository, st: PipelineState
) -> PipelineState:
    t0 = time.perf_counter()
    if st.duplicate_of is not None and st.duplicate_of != st.ingest_id:
        db.execute("UPDATE alerts SET status = 'deduped' WHERE ingest_id = ?", (st.ingest_id,))
        db.commit()
        events.append(
            stage="deduped",
            created_at=datetime.now(tz=UTC),
            ingest_id=st.ingest_id,
            case_id=None,
            payload={"duplicate_of": st.duplicate_of},
        )
    else:
        db.execute("UPDATE alerts SET status = 'dedup_pass' WHERE ingest_id = ?", (st.ingest_id,))
        db.commit()
    PIPELINE_STAGE_TOTAL.labels("deduped").inc()
    PIPELINE_STAGE_SECONDS.labels("deduped").observe(time.perf_counter() - t0)
    return st


def stage_correlate(
    db: sqlite3.Connection, cfg: AppConfig, events: EventsRepository, st: PipelineState
) -> PipelineState:
    t0 = time.perf_counter()
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
        created_at=datetime.now(tz=UTC),
        ingest_id=st.ingest_id,
        case_id=case_id,
        payload={"case_id": case_id, "entity_count": len(st.alert.entities)},
    )
    db.execute("UPDATE alerts SET status = 'correlated' WHERE ingest_id = ?", (st.ingest_id,))
    db.commit()
    PIPELINE_STAGE_TOTAL.labels("correlated").inc()
    PIPELINE_STAGE_SECONDS.labels("correlated").observe(time.perf_counter() - t0)
    return st


def stage_enrich(
    db: sqlite3.Connection, cfg: AppConfig, events: EventsRepository, st: PipelineState
) -> PipelineState:
    t0 = time.perf_counter()
    assert st.alert is not None
    if st.duplicate_of is not None and st.duplicate_of != st.ingest_id:
        return st
    mgr = EnricherManager(db=db, data_dir=cfg.data_dir, enabled=cfg.enabled_enrichers)
    enrichments = mgr.enrich(st.alert)
    st.enrichments = enrichments
    events.append(
        stage="enriched",
        created_at=datetime.now(tz=UTC),
        ingest_id=st.ingest_id,
        case_id=st.case_id,
        payload={"enrichments": enrichments},
    )
    PIPELINE_STAGE_TOTAL.labels("enriched").inc()
    PIPELINE_STAGE_SECONDS.labels("enriched").observe(time.perf_counter() - t0)
    return st


def stage_score_decide_route(
    db: sqlite3.Connection, cfg: AppConfig, events: EventsRepository, st: PipelineState
) -> PipelineState:
    t0 = time.perf_counter()
    if st.case_id is None or st.alert is None or st.enrichments is None:
        return st
    scoring_rules = load_scoring_rules(cfg.rules_dir)
    score = score_alert(st.alert, st.enrichments, scoring_rules)
    thresholds_cfg = load_thresholds(cfg.rules_dir)
    decision = decide(score, st.enrichments, thresholds_cfg)
    routing = route(cfg.rules_dir, decision, st.enrichments)

    st.score = score.model_dump()
    st.routing = routing.model_dump()
    db.execute(
        """
        UPDATE cases
        SET severity = ?, confidence = ?, decision = ?, queue = ?, score_json = ?, routing_json = ?
        WHERE case_id = ?
        """,
        (
            score.severity,
            score.confidence,
            str(decision),
            routing.queue,
            json.dumps(st.score),
            json.dumps(st.routing),
            st.case_id,
        ),
    )
    db.commit()
    events.append(
        stage="scored",
        created_at=datetime.now(tz=UTC),
        ingest_id=st.ingest_id,
        case_id=st.case_id,
        payload={"severity": score.severity, "confidence": score.confidence},
    )
    events.append(
        stage="decided",
        created_at=datetime.now(tz=UTC),
        ingest_id=st.ingest_id,
        case_id=st.case_id,
        payload={"decision": str(decision)},
    )
    events.append(
        stage="routed",
        created_at=datetime.now(tz=UTC),
        ingest_id=st.ingest_id,
        case_id=st.case_id,
        payload={"queue": routing.queue, "rationale": routing.rationale},
    )
    if str(decision) in {"CREATE_TICKET", "ESCALATE"}:
        ticket = MockTicketingConnector(db).create_ticket(
            case_id=st.case_id, payload={"case_id": st.case_id}
        )
        events.append(
            stage="ticketed",
            created_at=datetime.now(tz=UTC),
            ingest_id=st.ingest_id,
            case_id=st.case_id,
            payload={"ticket_id": ticket.get("ticket_id"), "url": ticket.get("url")},
        )
    else:
        events.append(
            stage="closed",
            created_at=datetime.now(tz=UTC),
            ingest_id=st.ingest_id,
            case_id=st.case_id,
            payload={"status": "auto_closed"},
        )
    PIPELINE_STAGE_TOTAL.labels("scored_decided_routed").inc()
    PIPELINE_STAGE_SECONDS.labels("scored_decided_routed").observe(time.perf_counter() - t0)
    return st


def stage_finalize(
    db: sqlite3.Connection, events: EventsRepository, st: PipelineState
) -> PipelineState:
    t0 = time.perf_counter()
    db.execute("UPDATE alerts SET status = 'processed' WHERE ingest_id = ?", (st.ingest_id,))
    db.commit()
    events.append(
        stage="processed",
        created_at=datetime.now(tz=UTC),
        ingest_id=st.ingest_id,
        case_id=st.case_id,
        payload={"status": "processed"},
    )
    PIPELINE_STAGE_TOTAL.labels("processed").inc()
    PIPELINE_STAGE_SECONDS.labels("processed").observe(time.perf_counter() - t0)
    return st
