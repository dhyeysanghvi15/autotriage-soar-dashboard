from __future__ import annotations

from pathlib import Path

from _pytest.monkeypatch import MonkeyPatch
from fastapi.testclient import TestClient

from autotriage.app.main import create_app
from autotriage.storage.db import init_db


def test_webhook_idempotency(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("AUTOTRIAGE_DB_PATH", str(tmp_path / "db.sqlite"))
    init_db()
    client = TestClient(create_app())
    payload = {"vendor": "vendor_a", "time": "2025-01-01T00:00:00Z", "title": "x", "severity": 1}
    r1 = client.post("/webhook/alerts", json=payload, headers={"Idempotency-Key": "k1"})
    r2 = client.post("/webhook/alerts", json=payload, headers={"Idempotency-Key": "k1"})
    assert r1.status_code == 202 and r2.status_code == 202
    assert r1.json()["ingest_id"] == r2.json()["ingest_id"]


def test_webhook_idempotency_computed_key(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("AUTOTRIAGE_DB_PATH", str(tmp_path / "db.sqlite"))
    init_db()
    client = TestClient(create_app())
    payload = {"vendor": "vendor_a", "time": "2025-01-01T00:00:00Z", "title": "x", "severity": 1}
    r1 = client.post("/webhook/alerts", json=payload)
    r2 = client.post("/webhook/alerts", json=payload)
    assert r1.status_code == 202 and r2.status_code == 202
    assert r1.json()["ingest_id"] == r2.json()["ingest_id"]
