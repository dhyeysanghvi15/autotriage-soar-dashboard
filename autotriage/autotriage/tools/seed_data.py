from __future__ import annotations

from autotriage.storage.db import init_db


def seed_all() -> None:
    init_db()
