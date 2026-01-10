from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import structlog

from autotriage.core.models.alert import CanonicalAlert
from autotriage.enrichers.allowlist import AllowlistEnricher
from autotriage.enrichers.asset_context import AssetContextEnricher
from autotriage.enrichers.base import BaseEnricher
from autotriage.enrichers.cache import EnricherCache
from autotriage.enrichers.geo_asn import GeoAsnEnricher
from autotriage.enrichers.ip_reputation import IpReputationEnricher
from autotriage.enrichers.rate_limit import TokenBucket
from autotriage.enrichers.whois import WhoisEnricher

log = structlog.get_logger(__name__)


@dataclass
class _Breaker:
    failures: int = 0
    open_until: float = 0.0

    def is_open(self) -> bool:
        return time.time() < self.open_until


class EnricherManager:
    def __init__(self, *, db, data_dir: Path, enabled: list[str]) -> None:
        self._db = db
        self._enrichers: list[BaseEnricher] = []
        self._buckets: dict[str, TokenBucket] = {}
        self._breakers: dict[str, _Breaker] = {}

        available: dict[str, BaseEnricher] = {
            "allowlist": AllowlistEnricher(data_dir),
            "asset_context": AssetContextEnricher(data_dir),
            "ip_reputation": IpReputationEnricher(data_dir),
            "geo_asn": GeoAsnEnricher(data_dir),
            "whois": WhoisEnricher(data_dir),
        }
        for name in enabled:
            enricher = available.get(name)
            if enricher is not None:
                self._enrichers.append(enricher)
                self._buckets[enricher.name] = TokenBucket.per_minute(enricher.rate_limit_per_minute)
                self._breakers[enricher.name] = _Breaker()

    def enrich(self, alert: CanonicalAlert) -> dict[str, Any]:
        out: dict[str, Any] = {}
        for enricher in self._enrichers:
            breaker = self._breakers[enricher.name]
            if breaker.is_open():
                out[enricher.name] = {"status": "circuit_open"}
                continue

            bucket = self._buckets[enricher.name]
            cache = EnricherCache(self._db, enricher.name)
            results: dict[str, Any] = {}
            for key in enricher.keys(alert):
                cached = cache.get(key)
                if cached is not None:
                    results[key] = {"status": "cache_hit", "data": cached}
                    continue
                if not bucket.allow():
                    results[key] = {"status": "rate_limited"}
                    continue
                try:
                    data = enricher.enrich_one(key)
                    if data is None:
                        results[key] = {"status": "miss"}
                    else:
                        cache.set(key, data, ttl_seconds=enricher.ttl_seconds)
                        results[key] = {"status": "ok", "data": data}
                    breaker.failures = 0
                except Exception as e:  # noqa: BLE001
                    breaker.failures += 1
                    log.warning("enricher_error", enricher=enricher.name, key=key, error=repr(e))
                    results[key] = {"status": "error", "error": repr(e)}
                    if breaker.failures >= enricher.breaker_failure_threshold:
                        breaker.open_until = time.time() + enricher.breaker_cooldown_seconds
                        log.warning("enricher_circuit_open", enricher=enricher.name, open_until=breaker.open_until)
            out[enricher.name] = results
        return out

