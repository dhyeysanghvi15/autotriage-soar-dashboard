from __future__ import annotations

import sqlite3
from collections.abc import Generator
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
        migrations_dir = Path(__file__).resolve().parent / "migrations"
        for path in sorted(migrations_dir.glob("*.sql")):
            db.executescript(path.read_text(encoding="utf-8"))
        db.commit()
    finally:
        db.close()
