from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime
from typing import Any


class TicketsRepository:
    def __init__(self, db: sqlite3.Connection) -> None:
        self._db = db

    def upsert_ticket(self, case_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        existing = self._db.execute("SELECT * FROM tickets WHERE case_id = ?", (case_id,)).fetchone()
        if existing is not None:
            return dict(existing)

        ticket_id = str(uuid.uuid4())
        created_at = datetime.utcnow().isoformat()
        url = f"/tickets/{ticket_id}"
        self._db.execute(
            "INSERT INTO tickets (ticket_id, case_id, created_at, url, payload_json) VALUES (?, ?, ?, ?, ?)",
            (ticket_id, case_id, created_at, url, json.dumps(payload)),
        )
        self._db.commit()
        return {"ticket_id": ticket_id, "case_id": case_id, "created_at": created_at, "url": url, "payload": payload}

