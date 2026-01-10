from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from typing import Any


class DeadletterRepository:
    def __init__(self, db: sqlite3.Connection) -> None:
        self._db = db

    def upsert(self, ingest_id: str, *, stage: str, error: str, payload: dict[str, Any]) -> None:
        now = datetime.now(tz=UTC).isoformat()
        self._db.execute(
            """
            INSERT INTO deadletter (ingest_id, created_at, updated_at, attempts, stage, error, payload_json)
            VALUES (?, ?, ?, 1, ?, ?, ?)
            ON CONFLICT(ingest_id) DO UPDATE SET
              updated_at = excluded.updated_at,
              attempts = deadletter.attempts + 1,
              stage = excluded.stage,
              error = excluded.error,
              payload_json = excluded.payload_json
            """,
            (ingest_id, now, now, stage, error, json.dumps(payload)),
        )
        self._db.commit()
