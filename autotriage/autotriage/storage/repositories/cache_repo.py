from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime, timedelta
from typing import Any, cast


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
        if expires_at < datetime.now(tz=UTC):
            self._db.execute(
                "DELETE FROM cache WHERE enricher = ? AND cache_key = ?", (enricher, key)
            )
            self._db.commit()
            return None
        value = json.loads(str(row["value_json"]))
        if not isinstance(value, dict):
            return None
        return cast(dict[str, Any], value)

    def set(self, enricher: str, key: str, value: dict[str, Any], ttl_seconds: int) -> None:
        now = datetime.now(tz=UTC)
        expires_at = now + timedelta(seconds=ttl_seconds)
        self._db.execute(
            """
            INSERT OR REPLACE INTO cache (enricher, cache_key, created_at, expires_at, value_json)
            VALUES (?, ?, ?, ?, ?)
            """,
            (enricher, key, now.isoformat(), expires_at.isoformat(), json.dumps(value)),
        )
        self._db.commit()
