from __future__ import annotations

import json
from pathlib import Path

from _pytest.monkeypatch import MonkeyPatch
from fastapi.testclient import TestClient

from autotriage.app.main import create_app
from autotriage.core.pipeline.orchestrator import process_ingest
from autotriage.storage.db import get_db, init_db


def _process(ingest_id: str) -> None:
    db = get_db()
    try:
        row = db.execute("SELECT raw_json FROM alerts WHERE ingest_id = ?", (ingest_id,)).fetchone()
        assert row is not None
        process_ingest(db, ingest_id, json.loads(str(row["raw_json"])))
    finally:
        db.close()


def test_dedup_window_prevents_duplicate_ticket(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("AUTOTRIAGE_DB_PATH", str(tmp_path / "db.sqlite"))
    init_db()
    client = TestClient(create_app())

    payload = {
        "vendor": "vendor_a",
        "time": "2025-01-01T00:00:00Z",
        "rule": "R-LOGIN-001",
        "title": "Suspicious login",
        "severity": 7,
        "src_ip": "1.2.3.4",
        "user": "alice",
        "host": "workstation-1",
    }
    r1 = client.post("/webhook/alerts", json=payload, headers={"Idempotency-Key": "d1"})
    r2 = client.post("/webhook/alerts", json=payload, headers={"Idempotency-Key": "d2"})
    assert r1.status_code == 202 and r2.status_code == 202
    id1 = r1.json()["ingest_id"]
    id2 = r2.json()["ingest_id"]

    _process(id1)
    _process(id2)

    db = get_db()
    try:
        tickets = int(db.execute("SELECT COUNT(*) FROM tickets").fetchone()[0])
        assert tickets == 1
        deduped_events = int(
            db.execute("SELECT COUNT(*) FROM events WHERE stage = 'deduped'").fetchone()[0]
        )
        assert deduped_events >= 1
    finally:
        db.close()


def test_correlation_merges_entity_overlap_into_one_case(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    monkeypatch.setenv("AUTOTRIAGE_DB_PATH", str(tmp_path / "db.sqlite"))
    init_db()
    client = TestClient(create_app())

    p1 = {
        "vendor": "vendor_a",
        "time": "2025-01-01T00:00:00Z",
        "rule": "R-LOGIN-001",
        "title": "Suspicious login",
        "severity": 7,
        "src_ip": "1.2.3.4",
        "user": "alice",
        "host": "workstation-1",
    }
    p2 = {
        "vendor": "vendor_a",
        "time": "2025-01-01T00:05:00Z",
        "rule": "R-EDR-777",
        "title": "New admin group membership",
        "severity": 9,
        "src_ip": "5.6.7.8",
        "user": "alice",
        "host": "workstation-1",
    }
    r1 = client.post("/webhook/alerts", json=p1, headers={"Idempotency-Key": "c1"})
    r2 = client.post("/webhook/alerts", json=p2, headers={"Idempotency-Key": "c2"})
    assert r1.status_code == 202 and r2.status_code == 202
    id1 = r1.json()["ingest_id"]
    id2 = r2.json()["ingest_id"]

    _process(id1)
    _process(id2)

    db = get_db()
    try:
        cases = int(db.execute("SELECT COUNT(*) FROM cases").fetchone()[0])
        assert cases == 1
    finally:
        db.close()
