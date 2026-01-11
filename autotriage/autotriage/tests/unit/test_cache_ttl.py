from __future__ import annotations

import sqlite3
from datetime import UTC, datetime, timedelta

from autotriage.storage.repositories.cache_repo import CacheRepository


def test_cache_ttl_expires_and_is_deleted() -> None:
    db = sqlite3.connect(":memory:")
    db.row_factory = sqlite3.Row
    db.executescript(
        """
        CREATE TABLE cache (
          enricher TEXT NOT NULL,
          cache_key TEXT NOT NULL,
          created_at TEXT NOT NULL,
          expires_at TEXT NOT NULL,
          value_json TEXT NOT NULL,
          PRIMARY KEY (enricher, cache_key)
        );
        """
    )
    repo = CacheRepository(db)

    now = datetime.now(tz=UTC)
    db.execute(
        "INSERT INTO cache (enricher, cache_key, created_at, expires_at, value_json) VALUES (?, ?, ?, ?, ?)",
        ("x", "k", now.isoformat(), (now + timedelta(seconds=60)).isoformat(), '{"a":1}'),
    )
    db.commit()
    assert repo.get("x", "k") == {"a": 1}

    db.execute(
        "UPDATE cache SET expires_at = ? WHERE enricher = ? AND cache_key = ?",
        ((now - timedelta(seconds=60)).isoformat(), "x", "k"),
    )
    db.commit()
    assert repo.get("x", "k") is None
    assert (
        db.execute(
            "SELECT COUNT(*) FROM cache WHERE enricher = ? AND cache_key = ?", ("x", "k")
        ).fetchone()[0]
        == 0
    )
