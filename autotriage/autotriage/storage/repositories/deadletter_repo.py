from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from typing import Any


class DeadletterRepository:
    def __init__(self, db: sqlite3.Connection) -> None:
        self._db = db

    def upsert(self, ingest_id: str, error: str, payload: dict[str, Any]) -> None:
        now = datetime.utcnow().isoformat()
        self._db.execute(
            """
            INSERT INTO deadletter (ingest_id, created_at, updated_at, attempts, error, payload_json)
            VALUES (?, ?, ?, 1, ?, ?)
            ON CONFLICT(ingest_id) DO UPDATE SET
              updated_at = excluded.updated_at,
              attempts = deadletter.attempts + 1,
              error = excluded.error,
              payload_json = excluded.payload_json
            """,
            (ingest_id, now, now, error, json.dumps(payload)),
        )
        self._db.commit()

