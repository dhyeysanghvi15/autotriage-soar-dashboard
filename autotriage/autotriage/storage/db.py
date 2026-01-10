from __future__ import annotations

import sqlite3
import inspect
from collections.abc import Callable
from pathlib import Path
from typing import Any, Awaitable, ParamSpec, TypeVar, overload

from autotriage.config import load_effective_config

P = ParamSpec("P")
R = TypeVar("R")


def get_db() -> sqlite3.Connection:
    cfg = load_effective_config()
    cfg.db_path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(str(cfg.db_path))
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA journal_mode=WAL;")
    db.execute("PRAGMA foreign_keys=ON;")
    return db


def init_db() -> None:
    db = get_db()
    try:
        migrations_dir = Path(__file__).resolve().parent / "migrations"
        for path in sorted(migrations_dir.glob("*.sql")):
            db.executescript(path.read_text(encoding="utf-8"))
        db.commit()
    finally:
        db.close()


@overload
def with_db(fn: Callable[..., Awaitable[R]]) -> Callable[..., Awaitable[R]]: ...


@overload
def with_db(fn: Callable[..., R]) -> Callable[..., R]: ...


def with_db(fn: Callable[..., Any]) -> Callable[..., Any]:
    if inspect.iscoroutinefunction(fn):
        async def _async_wrapper(*args: Any, **kwargs: Any) -> Any:
            db = get_db()
            try:
                return await fn(*args, db=db, **kwargs)
            finally:
                db.close()

        return _async_wrapper

    def _wrapper(*args: Any, **kwargs: Any) -> Any:
        db = get_db()
        try:
            return fn(*args, db=db, **kwargs)
        finally:
            db.close()

    return _wrapper
