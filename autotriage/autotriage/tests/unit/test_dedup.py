from __future__ import annotations

import sqlite3
from datetime import datetime, timezone

from autotriage.core.dedup.deduper import find_duplicate_of, record_fingerprint
from autotriage.core.fingerprint.strategies import Fingerprint


def test_dedup_finds_existing() -> None:
    db = sqlite3.connect(":memory:")
    db.row_factory = sqlite3.Row
    db.executescript(
        """
        CREATE TABLE fingerprints (
          ingest_id TEXT PRIMARY KEY,
          created_at TEXT NOT NULL,
          strategy TEXT NOT NULL,
          fp_hash TEXT NOT NULL,
          window_start TEXT NOT NULL
        );
        """
    )
    fp = Fingerprint(strategy="default", fp_hash="abc", window_start=datetime(2025, 1, 1, tzinfo=timezone.utc))
    record_fingerprint(db, "id-1", fp)
    assert find_duplicate_of(db, fp) == "id-1"

