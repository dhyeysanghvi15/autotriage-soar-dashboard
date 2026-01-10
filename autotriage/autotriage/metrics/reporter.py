from __future__ import annotations

import sqlite3


def quick_counts(db: sqlite3.Connection) -> dict[str, int]:
    def c(sql: str) -> int:
        return int(db.execute(sql).fetchone()[0])

    return {
        "alerts_total": c("SELECT COUNT(*) FROM alerts"),
        "alerts_ingested": c("SELECT COUNT(*) FROM alerts WHERE status = 'ingested'"),
        "alerts_deduped": c("SELECT COUNT(*) FROM alerts WHERE status = 'deduped'"),
        "cases_total": c("SELECT COUNT(*) FROM cases"),
        "tickets_total": c("SELECT COUNT(*) FROM tickets"),
        "deadletter_total": c("SELECT COUNT(*) FROM deadletter"),
    }
