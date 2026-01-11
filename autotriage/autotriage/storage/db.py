from __future__ import annotations

import sqlite3
from collections.abc import Generator
from datetime import UTC, datetime
from pathlib import Path

from autotriage.config import load_effective_config


def get_db() -> sqlite3.Connection:
    cfg = load_effective_config()
    cfg.db_path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(str(cfg.db_path), check_same_thread=False)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA journal_mode=WAL;")
    db.execute("PRAGMA foreign_keys=ON;")
    return db


def db_dependency() -> Generator[sqlite3.Connection, None, None]:
    db = get_db()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    db = get_db()
    try:
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
              id TEXT PRIMARY KEY,
              applied_at TEXT NOT NULL
            )
            """
        )
        applied = {str(r["id"]) for r in db.execute("SELECT id FROM schema_migrations").fetchall()}
        migrations_dir = Path(__file__).resolve().parent / "migrations"
        for path in sorted(migrations_dir.glob("*.sql")):
            mid = path.name
            if mid in applied:
                continue
            try:
                db.executescript(path.read_text(encoding="utf-8"))
            except sqlite3.OperationalError as e:
                if mid == "007_deadletter_stage.sql" and "duplicate column name" in str(e).lower():
                    pass
                else:
                    raise
            db.execute(
                "INSERT OR IGNORE INTO schema_migrations (id, applied_at) VALUES (?, ?)",
                (mid, datetime.now(tz=UTC).isoformat()),
            )
            db.commit()
    finally:
        db.close()
