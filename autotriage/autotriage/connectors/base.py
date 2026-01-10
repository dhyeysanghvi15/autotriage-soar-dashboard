from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class TicketingConnector(ABC):
    @abstractmethod
    def create_ticket(self, *, case_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError
