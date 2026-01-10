from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from autotriage.core.models.alert import CanonicalAlert


@dataclass(frozen=True)
class EnrichmentResult:
    source: str
    data: dict[str, Any]


class BaseEnricher(ABC):
    name: str
    ttl_seconds: int = 3600
    rate_limit_per_minute: int = 120
    breaker_failure_threshold: int = 5
    breaker_cooldown_seconds: int = 30

    @abstractmethod
    def keys(self, alert: CanonicalAlert) -> list[str]:
        raise NotImplementedError

    @abstractmethod
    def enrich_one(self, key: str) -> dict[str, Any] | None:
        raise NotImplementedError

