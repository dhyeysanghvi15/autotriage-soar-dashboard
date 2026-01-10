from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime
from typing import Any


class EventsRepository:
    def __init__(self, db: sqlite3.Connection) -> None:
        self._db = db

    def append(
        self,
        stage: str,
        created_at: datetime,
        ingest_id: str | None,
        case_id: str | None,
        payload: dict[str, Any],
    ) -> str:
        event_id = str(uuid.uuid4())
        self._db.execute(
            """
            INSERT INTO events (event_id, created_at, stage, ingest_id, case_id, payload_json)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (event_id, created_at.isoformat(), stage, ingest_id, case_id, json.dumps(payload)),
        )
        self._db.commit()
        return event_id
