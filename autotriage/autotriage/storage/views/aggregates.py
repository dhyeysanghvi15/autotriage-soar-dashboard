from __future__ import annotations

import sqlite3
from datetime import UTC, datetime, timedelta


def overview_24h(db: sqlite3.Connection) -> dict[str, int]:
    since = datetime.now(tz=UTC) - timedelta(hours=24)

    def c(sql: str, params: tuple[object, ...] = ()) -> int:
        return int(db.execute(sql, params).fetchone()[0])

    return {
        "ingested": c("SELECT COUNT(*) FROM alerts WHERE received_at >= ?", (since.isoformat(),)),
        "deduped": c(
            "SELECT COUNT(*) FROM events WHERE stage = 'deduped' AND created_at >= ?",
            (since.isoformat(),),
        ),
        "cases": c("SELECT COUNT(*) FROM cases WHERE created_at >= ?", (since.isoformat(),)),
        "auto_closed": c(
            "SELECT COUNT(*) FROM cases WHERE decision = 'AUTO_CLOSE' AND created_at >= ?",
            (since.isoformat(),),
        ),
        "tickets": c("SELECT COUNT(*) FROM tickets WHERE created_at >= ?", (since.isoformat(),)),
        "errors": c(
            "SELECT COUNT(*) FROM events WHERE stage = 'failed' AND created_at >= ?",
            (since.isoformat(),),
        ),
    }
