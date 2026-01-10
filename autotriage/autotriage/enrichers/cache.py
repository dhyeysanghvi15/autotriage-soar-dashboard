from __future__ import annotations

import sqlite3
from typing import Any

from autotriage.storage.repositories.cache_repo import CacheRepository


class EnricherCache:
    def __init__(self, db: sqlite3.Connection, enricher: str) -> None:
        self._repo = CacheRepository(db)
        self._enricher = enricher

    def get(self, key: str) -> dict[str, Any] | None:
        return self._repo.get(self._enricher, key)

    def set(self, key: str, value: dict[str, Any], ttl_seconds: int) -> None:
        self._repo.set(self._enricher, key, value, ttl_seconds)
