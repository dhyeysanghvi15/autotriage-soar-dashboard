from __future__ import annotations

import json
from pathlib import Path

from _pytest.monkeypatch import MonkeyPatch
from fastapi.testclient import TestClient

from autotriage.app.main import create_app
from autotriage.core.pipeline.orchestrator import process_ingest
from autotriage.storage.db import get_db, init_db


def test_healthz_contract() -> None:
    with TestClient(create_app()) as client:
        r = client.get("/healthz")
        assert r.status_code == 200
        body = r.json()
        assert body["status"] == "ok"
        assert "version" in body


def test_overview_contract() -> None:
    with TestClient(create_app()) as client:
        r = client.get("/api/overview")
        assert r.status_code == 200
        body = r.json()
        assert body["window"] == "24h"
        stats = body["stats"]
        for k in ["ingested", "deduped", "cases", "auto_closed", "tickets", "errors"]:
            assert k in stats


def test_metrics_contract_contains_key_counters() -> None:
    with TestClient(create_app()) as client:
        r = client.get("/metrics")
        assert r.status_code == 200
        text = r.text
        assert "autotriage_ingest_total" in text
        assert "autotriage_pipeline_stage_total" in text


def test_cases_endpoints_contract(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
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
    r = client.post("/webhook/alerts", json=payload, headers={"Idempotency-Key": "ac-1"})
    assert r.status_code == 202
    ingest_id = r.json()["ingest_id"]

    db = get_db()
    try:
        row = db.execute("SELECT raw_json FROM alerts WHERE ingest_id = ?", (ingest_id,)).fetchone()
        assert row is not None
        process_ingest(db, ingest_id, json.loads(str(row["raw_json"])))
    finally:
        db.close()

    r_cases = client.get("/api/cases")
    assert r_cases.status_code == 200
    body = r_cases.json()
    assert "items" in body
    assert len(body["items"]) >= 1
    case_id = body["items"][0]["case_id"]

    r_detail = client.get(f"/api/cases/{case_id}")
    assert r_detail.status_code == 200
    detail = r_detail.json()
    for key in [
        "case",
        "timeline",
        "graph",
        "enrichments",
        "scoring",
        "routing",
        "recommended_actions",
        "ticket",
    ]:
        assert key in detail
    assert "nodes" in detail["graph"]
    assert "edges" in detail["graph"]

    r_search = client.get("/api/cases", params={"q": "workstation-1"})
    assert r_search.status_code == 200
    assert len(r_search.json()["items"]) >= 1


def test_config_contract() -> None:
    with TestClient(create_app()) as client:
        r = client.get("/api/config")
        assert r.status_code == 200
        body = r.json()
        for k in [
            "version",
            "rules_dir",
            "data_dir",
            "dedup_window_seconds",
            "correlation_window_seconds",
            "enabled_enrichers",
        ]:
            assert k in body
