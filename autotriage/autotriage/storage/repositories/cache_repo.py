from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timedelta, timezone
from typing import Any


class CacheRepository:
    def __init__(self, db: sqlite3.Connection) -> None:
        self._db = db

    def get(self, enricher: str, key: str) -> dict[str, Any] | None:
        row = self._db.execute(
            "SELECT value_json, expires_at FROM cache WHERE enricher = ? AND cache_key = ?",
            (enricher, key),
        ).fetchone()
        if row is None:
            return None
        expires_at = datetime.fromisoformat(str(row["expires_at"]))
        if expires_at < datetime.now(tz=timezone.utc):
            self._db.execute("DELETE FROM cache WHERE enricher = ? AND cache_key = ?", (enricher, key))
            self._db.commit()
            return None
        return json.loads(str(row["value_json"]))

    def set(self, enricher: str, key: str, value: dict[str, Any], ttl_seconds: int) -> None:
        now = datetime.now(tz=timezone.utc)
        expires_at = now + timedelta(seconds=ttl_seconds)
        self._db.execute(
            """
            INSERT OR REPLACE INTO cache (enricher, cache_key, created_at, expires_at, value_json)
            VALUES (?, ?, ?, ?, ?)
            """,
            (enricher, key, now.isoformat(), expires_at.isoformat(), json.dumps(value)),
        )
        self._db.commit()

