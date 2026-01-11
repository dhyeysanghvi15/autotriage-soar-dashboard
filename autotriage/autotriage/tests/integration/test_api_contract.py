from __future__ import annotations

from fastapi.testclient import TestClient

from autotriage.app.main import create_app


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
