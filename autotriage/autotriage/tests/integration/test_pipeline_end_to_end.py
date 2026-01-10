from __future__ import annotations

import json
from pathlib import Path

from _pytest.monkeypatch import MonkeyPatch
from fastapi.testclient import TestClient

from autotriage.app.main import create_app
from autotriage.core.pipeline.orchestrator import process_ingest
from autotriage.storage.db import get_db, init_db


def test_pipeline_end_to_end(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("AUTOTRIAGE_DB_PATH", str(tmp_path / "db.sqlite"))
    init_db()
    client = TestClient(create_app())
    payload = {
        "vendor": "vendor_a",
        "time": "2025-01-01T00:00:00Z",
        "title": "Suspicious login",
        "severity": 7,
        "src_ip": "1.2.3.4",
    }
    r = client.post("/webhook/alerts", json=payload, headers={"Idempotency-Key": "k2"})
    ingest_id = r.json()["ingest_id"]

    db = get_db()
    try:
        row = db.execute("SELECT raw_json FROM alerts WHERE ingest_id = ?", (ingest_id,)).fetchone()
        assert row is not None
        process_ingest(db, ingest_id, json.loads(str(row["raw_json"])))
        cases = db.execute("SELECT COUNT(*) FROM cases").fetchone()[0]
        assert cases >= 1
    finally:
        db.close()
