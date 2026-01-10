from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from autotriage.core.models.alert import CanonicalAlert, NormalizationResult
from autotriage.core.models.entities import Entity, EntityType


def normalize_vendor_c(payload: dict[str, Any]) -> NormalizationResult:
    # Vendor C example:
    # {"vendor":"vendor_c","observed_at":"2025-01-01T00:00:00Z","finding":{"title":"...","priority":"high"}, "principal":{"user":"x"}}
    ts = datetime.fromisoformat(str(payload.get("observed_at", "")).replace("Z", "+00:00"))
    finding = payload.get("finding") or {}
    priority = str(finding.get("priority") or "low").lower()
    mapped = {"low": 20, "medium": 55, "high": 80, "critical": 95}.get(priority, 30)

    entities: list[Entity] = []
    principal = payload.get("principal") or {}
    if principal.get("user"):
        entities.append(Entity(type=EntityType.user, value=str(principal["user"])))
    if principal.get("host"):
        entities.append(Entity(type=EntityType.host, value=str(principal["host"])))
    if payload.get("ioc", {}).get("domain"):
        entities.append(Entity(type=EntityType.domain, value=str(payload["ioc"]["domain"])))
    if payload.get("ioc", {}).get("ip"):
        entities.append(Entity(type=EntityType.src_ip, value=str(payload["ioc"]["ip"])))

    alert = CanonicalAlert(
        vendor="vendor_c",
        alert_type=str(finding.get("type") or "generic"),
        ts=ts if ts.tzinfo else ts.replace(tzinfo=timezone.utc),
        title=str(finding.get("title") or "vendor_c finding"),
        rule_id=str(finding.get("rule_id") or "") or None,
        technique_id=str(finding.get("technique_id") or "") or None,
        severity=mapped,
        entities=entities,
        raw=payload,
    )
    return NormalizationResult(alert=alert)

