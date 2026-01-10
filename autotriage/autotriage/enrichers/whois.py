from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from autotriage.core.models.alert import CanonicalAlert
from autotriage.enrichers.base import BaseEnricher


class WhoisEnricher(BaseEnricher):
    name = "whois"
    ttl_seconds = 7 * 24 * 3600
    rate_limit_per_minute = 60

    def __init__(self, data_dir: Path) -> None:
        self._by_domain: dict[str, dict[str, Any]] = {}
        with (data_dir / "mock_whois.csv").open("r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                domain = (row.get("domain") or "").lower().strip()
                if domain:
                    self._by_domain[domain] = row

    def keys(self, alert: CanonicalAlert) -> list[str]:
        domains = [e.value.lower() for e in alert.entities if e.type.value == "domain"]
        return sorted(set(domains))

    def enrich_one(self, key: str) -> dict[str, Any] | None:
        return self._by_domain.get(key)

