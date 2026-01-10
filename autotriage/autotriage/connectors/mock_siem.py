from __future__ import annotations

import sqlite3


class MockSiemConnector:
    def __init__(self, db: sqlite3.Connection) -> None:
        self._db = db

    def ack_alert(self, ingest_id: str) -> None:
        self._db.execute("UPDATE alerts SET status = 'acked' WHERE ingest_id = ?", (ingest_id,))
        self._db.commit()

