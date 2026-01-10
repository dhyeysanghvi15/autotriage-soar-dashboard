from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from autotriage.core.models.alert import CanonicalAlert
from autotriage.enrichers.base import BaseEnricher


class IpReputationEnricher(BaseEnricher):
    name = "ip_reputation"
    ttl_seconds = 6 * 3600
    rate_limit_per_minute = 120

    def __init__(self, data_dir: Path) -> None:
        self._by_ip: dict[str, dict[str, Any]] = {}
        with (data_dir / "mock_reputation.csv").open("r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                ip = (row.get("ip") or "").strip()
                if ip:
                    self._by_ip[ip] = row

    def keys(self, alert: CanonicalAlert) -> list[str]:
        ips = [e.value for e in alert.entities if e.type.value in {"src_ip", "dst_ip"}]
        return sorted(set(ips))

    def enrich_one(self, key: str) -> dict[str, Any] | None:
        return self._by_ip.get(key)

