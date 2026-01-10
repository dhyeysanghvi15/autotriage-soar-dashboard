from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import UTC, datetime
from typing import Any


class AlertsRepository:
    def __init__(self, db: sqlite3.Connection) -> None:
        self._db = db

    def insert_or_get_ingest(
        self,
        *,
        idempotency_key: str,
        received_at: datetime,
        raw_payload: dict[str, Any],
        vendor: str | None = None,
    ) -> tuple[str, bool]:
        existing = self._db.execute(
            "SELECT ingest_id FROM alerts WHERE idempotency_key = ?",
            (idempotency_key,),
        ).fetchone()
        if existing is not None:
            return str(existing["ingest_id"]), True

        ingest_id = str(uuid.uuid4())
        self._db.execute(
            """
            INSERT INTO alerts (ingest_id, idempotency_key, received_at, updated_at, vendor, raw_json, status)
            VALUES (?, ?, ?, ?, ?, ?, 'ingested')
            """,
            (
                ingest_id,
                idempotency_key,
                received_at.isoformat(),
                received_at.isoformat(),
                vendor,
                json.dumps(raw_payload),
            ),
        )
        self._db.commit()
        return ingest_id, False

    def claim_next(self) -> sqlite3.Row | None:
        row: sqlite3.Row | None = self._db.execute(
            """
            SELECT * FROM alerts
            WHERE status = 'ingested'
            ORDER BY received_at ASC
            LIMIT 1
            """
        ).fetchone()
        if row is None:
            return None
        updated = datetime.now(tz=UTC).isoformat()
        cur = self._db.execute(
            """
            UPDATE alerts
            SET status = 'processing', processing_started_at = ?, updated_at = ?, attempts = attempts + 1
            WHERE ingest_id = ? AND status = 'ingested'
            """,
            (updated, updated, row["ingest_id"]),
        )
        if cur.rowcount != 1:
            self._db.commit()
            return None
        self._db.commit()
        return row

    def mark_processed(self, ingest_id: str, status: str = "processed") -> None:
        now = datetime.now(tz=UTC).isoformat()
        self._db.execute(
            "UPDATE alerts SET status = ?, processed_at = ?, updated_at = ?, last_error = NULL WHERE ingest_id = ?",
            (status, now, now, ingest_id),
        )
        self._db.commit()

    def mark_failed(self, ingest_id: str, error: str) -> None:
        now = datetime.now(tz=UTC).isoformat()
        self._db.execute(
            "UPDATE alerts SET status = 'failed', updated_at = ?, last_error = ? WHERE ingest_id = ?",
            (now, error, ingest_id),
        )
        self._db.commit()
