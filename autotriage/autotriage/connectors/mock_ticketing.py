from __future__ import annotations

import sqlite3
from typing import Any

from autotriage.connectors.base import TicketingConnector
from autotriage.storage.repositories.tickets_repo import TicketsRepository


class MockTicketingConnector(TicketingConnector):
    def __init__(self, db: sqlite3.Connection) -> None:
        self._repo = TicketsRepository(db)

    def create_ticket(self, *, case_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        return self._repo.upsert_ticket(case_id, payload)
