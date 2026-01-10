from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from autotriage.core.models.alert import CanonicalAlert
from autotriage.enrichers.base import BaseEnricher


class AllowlistEnricher(BaseEnricher):
    name = "allowlist"
    ttl_seconds = 24 * 3600
    rate_limit_per_minute = 600

    def __init__(self, data_dir: Path) -> None:
        cfg = yaml.safe_load((data_dir / "allowlists.yml").read_text(encoding="utf-8")) or {}
        self._ips = set(cfg.get("ips") or [])
        self._domains = set((d or "").lower() for d in (cfg.get("domains") or []))
        self._users = set(cfg.get("users") or [])
        self._hosts = set(cfg.get("hosts") or [])

    def keys(self, alert: CanonicalAlert) -> list[str]:
        out: list[str] = []
        for e in alert.entities:
            if e.type.value in {"src_ip", "dst_ip"}:
                out.append(f"ip:{e.value}")
            if e.type.value == "domain":
                out.append(f"domain:{e.value.lower()}")
            if e.type.value == "user":
                out.append(f"user:{e.value}")
            if e.type.value == "host":
                out.append(f"host:{e.value}")
        return sorted(set(out))

    def enrich_one(self, key: str) -> dict[str, Any] | None:
        prefix, _, value = key.partition(":")
        if prefix == "ip":
            return {"allowlisted": value in self._ips}
        if prefix == "domain":
            return {"allowlisted": value.lower() in self._domains}
        if prefix == "user":
            return {"allowlisted": value in self._users}
        if prefix == "host":
            return {"allowlisted": value in self._hosts}
        return None

