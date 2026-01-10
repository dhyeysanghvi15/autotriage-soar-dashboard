from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from autotriage.core.models.alert import CanonicalAlert
from autotriage.enrichers.base import BaseEnricher


class AssetContextEnricher(BaseEnricher):
    name = "asset_context"
    ttl_seconds = 24 * 3600
    rate_limit_per_minute = 300

    def __init__(self, data_dir: Path) -> None:
        self._by_host: dict[str, dict[str, Any]] = {}
        with (data_dir / "asset_inventory.csv").open("r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                host = (row.get("host") or "").strip()
                if host:
                    self._by_host[host] = row

    def keys(self, alert: CanonicalAlert) -> list[str]:
        hosts = [e.value for e in alert.entities if e.type.value == "host"]
        return sorted(set(hosts))

    def enrich_one(self, key: str) -> dict[str, Any] | None:
        return self._by_host.get(key)
