from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from autotriage.config import load_effective_config
from autotriage.core.models.alert import CanonicalAlert
from autotriage.core.models.entities import Entity, EntityType
from autotriage.enrichers.manager import EnricherManager
from autotriage.storage.db import init_db


def test_enricher_manager_runs_offline(tmp_path: Path, monkeypatch) -> None:
    db_path = tmp_path / "t.db"
    monkeypatch.setenv("AUTOTRIAGE_DB_PATH", str(db_path))
    init_db()
    db = sqlite3.connect(str(db_path))
    db.row_factory = sqlite3.Row
    cfg = load_effective_config()
    alert = CanonicalAlert(
        vendor="vendor_a",
        alert_type="dns",
        ts=datetime.now(tz=timezone.utc),
        title="DNS query",
        severity=10,
        entities=[Entity(type=EntityType.domain, value="example.com")],
        raw={},
    )
    mgr = EnricherManager(db=db, data_dir=cfg.data_dir, enabled=["whois"])
    out = mgr.enrich(alert)
    assert "whois" in out
    db.close()
