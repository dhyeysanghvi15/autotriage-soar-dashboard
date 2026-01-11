from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from _pytest.monkeypatch import MonkeyPatch

from autotriage.core.correlate.correlator import correlate_into_case
from autotriage.core.models.alert import CanonicalAlert
from autotriage.core.models.entities import Entity, EntityType
from autotriage.storage.db import get_db, init_db


def test_correlate_entity_overlap_merges_into_one_case(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    monkeypatch.setenv("AUTOTRIAGE_DB_PATH", str(tmp_path / "db.sqlite"))
    init_db()
    db: sqlite3.Connection = get_db()
    try:
        a1 = CanonicalAlert(
            ingest_id="i1",
            vendor="vendor_a",
            alert_type="generic",
            ts=datetime(2025, 1, 1, tzinfo=UTC),
            title="t1",
            severity=50,
            entities=[
                Entity(type=EntityType.user, value="alice"),
                Entity(type=EntityType.host, value="dc01"),
            ],
            raw={},
        )
        a2 = CanonicalAlert(
            ingest_id="i2",
            vendor="vendor_a",
            alert_type="generic",
            ts=datetime(2025, 1, 1, tzinfo=UTC),
            title="t2",
            severity=60,
            entities=[
                Entity(type=EntityType.user, value="alice"),
                Entity(type=EntityType.src_ip, value="1.2.3.4"),
            ],
            raw={},
        )
        case1 = correlate_into_case(
            db,
            a1,
            correlation_window_seconds=3600,
            base_severity=a1.severity,
            decision="CREATE_TICKET",
            queue="triage",
            score={"severity": a1.severity, "confidence": 0.5, "contributions": []},
            routing={"queue": "triage", "rationale": ["default_queue"]},
        )
        case2 = correlate_into_case(
            db,
            a2,
            correlation_window_seconds=3600,
            base_severity=a2.severity,
            decision="CREATE_TICKET",
            queue="triage",
            score={"severity": a2.severity, "confidence": 0.5, "contributions": []},
            routing={"queue": "triage", "rationale": ["default_queue"]},
        )
        assert case1 == case2
        assert int(db.execute("SELECT COUNT(*) FROM cases").fetchone()[0]) == 1
    finally:
        db.close()
