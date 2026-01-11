from __future__ import annotations

import sqlite3
import time as time_mod
from datetime import UTC, datetime
from pathlib import Path

from _pytest.monkeypatch import MonkeyPatch

from autotriage.config import load_effective_config
from autotriage.core.models.alert import CanonicalAlert
from autotriage.core.models.entities import Entity, EntityType
from autotriage.enrichers.manager import EnricherManager
from autotriage.enrichers.whois import WhoisEnricher
from autotriage.storage.db import init_db


def test_circuit_breaker_recovers_after_cooldown(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("AUTOTRIAGE_DB_PATH", str(tmp_path / "db.sqlite"))
    init_db()
    cfg = load_effective_config()

    now = 1000.0

    def fake_time() -> float:
        return now

    monkeypatch.setattr(time_mod, "time", fake_time)
    monkeypatch.setattr("autotriage.enrichers.manager.time.time", fake_time)

    def boom(self: WhoisEnricher, key: str) -> None:
        raise RuntimeError("boom")

    monkeypatch.setattr(WhoisEnricher, "enrich_one", boom)

    db = sqlite3.connect(str(tmp_path / "db.sqlite"), check_same_thread=False)
    db.row_factory = sqlite3.Row
    mgr = EnricherManager(db=db, data_dir=cfg.data_dir, enabled=["whois"])
    alert = CanonicalAlert(
        vendor="vendor_a",
        alert_type="dns",
        ts=datetime.now(tz=UTC),
        title="DNS query",
        severity=10,
        entities=[Entity(type=EntityType.domain, value="evil.example")],
        raw={},
    )

    for _ in range(6):
        out = mgr.enrich(alert)
    assert out["whois"] == {"status": "circuit_open"}

    def ok(self: WhoisEnricher, key: str) -> dict[str, str]:
        return {"domain": key, "registrar": "MockRegistrar"}

    monkeypatch.setattr(WhoisEnricher, "enrich_one", ok)

    now += 999.0
    out2 = mgr.enrich(alert)
    assert "evil.example" in out2["whois"]
    assert out2["whois"]["evil.example"]["status"] in {"ok", "cache_hit"}
    db.close()
