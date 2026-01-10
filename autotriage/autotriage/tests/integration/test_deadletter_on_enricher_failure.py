from __future__ import annotations

import json
from contextlib import suppress
from pathlib import Path

from _pytest.monkeypatch import MonkeyPatch

from autotriage.core.pipeline.orchestrator import process_ingest
from autotriage.storage.db import get_db, init_db


def test_deadletter_on_missing_enricher_dataset(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("AUTOTRIAGE_DB_PATH", str(tmp_path / "db.sqlite"))
    monkeypatch.setenv("AUTOTRIAGE_DATA_DIR", str(tmp_path / "empty_data"))
    monkeypatch.setenv("AUTOTRIAGE_ENABLED_ENRICHERS", "whois")

    init_db()
    db = get_db()
    try:
        ingest_id = "ing-1"
        raw = {
            "vendor": "vendor_a",
            "time": "2025-01-01T00:00:00Z",
            "rule": "R-DNS-404",
            "severity": 5,
            "domain": "evil.example",
            "title": "DNS query to suspicious domain",
        }
        db.execute(
            "INSERT INTO alerts (ingest_id, idempotency_key, received_at, raw_json, status) VALUES (?, ?, ?, ?, 'ingested')",
            (ingest_id, "k", "2025-01-01T00:00:00Z", json.dumps(raw)),
        )
        db.commit()

        with suppress(Exception):
            process_ingest(db, ingest_id, raw)

        dl = db.execute("SELECT * FROM deadletter WHERE ingest_id = ?", (ingest_id,)).fetchone()
        assert dl is not None
        assert dl["attempts"] >= 1
        assert dl["stage"] in {
            "enrich",
            "ingested",
            "normalize",
            "fingerprint",
            "dedup",
            "correlate",
        }
    finally:
        db.close()
