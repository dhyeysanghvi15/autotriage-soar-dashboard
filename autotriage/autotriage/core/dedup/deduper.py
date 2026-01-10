from __future__ import annotations

import sqlite3

from autotriage.core.fingerprint.strategies import Fingerprint


def find_duplicate_of(db: sqlite3.Connection, fp: Fingerprint) -> str | None:
    row = db.execute(
        """
        SELECT ingest_id FROM fingerprints
        WHERE fp_hash = ? AND window_start = ?
        ORDER BY created_at ASC
        LIMIT 1
        """,
        (fp.fp_hash, fp.window_start.isoformat()),
    ).fetchone()
    return str(row["ingest_id"]) if row is not None else None


def record_fingerprint(db: sqlite3.Connection, ingest_id: str, fp: Fingerprint) -> None:
    db.execute(
        """
        INSERT OR REPLACE INTO fingerprints (ingest_id, created_at, strategy, fp_hash, window_start)
        VALUES (?, datetime('now'), ?, ?, ?)
        """,
        (ingest_id, fp.strategy, fp.fp_hash, fp.window_start.isoformat()),
    )
    db.commit()

