from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from autotriage.core.models.alert import CanonicalAlert, NormalizationResult
from autotriage.core.models.entities import Entity, EntityType


def normalize_vendor_a(payload: dict[str, Any]) -> NormalizationResult:
    # Vendor A example:
    # { "vendor":"vendor_a", "time":"2025-01-01T00:00:00Z", "rule":"R-123", "severity":7,
    #   "src_ip":"1.2.3.4", "user":"alice", "host":"host1", "title":"Suspicious login" }
    ts = datetime.fromisoformat(payload.get("time", "").replace("Z", "+00:00"))
    entities: list[Entity] = []
    if payload.get("user"):
        entities.append(Entity(type=EntityType.user, value=str(payload["user"])))
    if payload.get("host"):
        entities.append(Entity(type=EntityType.host, value=str(payload["host"])))
    if payload.get("src_ip"):
        entities.append(Entity(type=EntityType.src_ip, value=str(payload["src_ip"])))
    if payload.get("dst_ip"):
        entities.append(Entity(type=EntityType.dst_ip, value=str(payload["dst_ip"])))
    if payload.get("domain"):
        entities.append(Entity(type=EntityType.domain, value=str(payload["domain"])))

    sev = int(payload.get("severity", 0))
    mapped = max(0, min(100, sev * 10))  # vendor A uses 0-10
    alert = CanonicalAlert(
        vendor="vendor_a",
        alert_type=str(payload.get("type") or "generic"),
        ts=ts if ts.tzinfo else ts.replace(tzinfo=timezone.utc),
        title=str(payload.get("title") or "vendor_a alert"),
        rule_id=str(payload.get("rule") or "") or None,
        technique_id=str(payload.get("technique_id") or "") or None,
        severity=mapped,
        entities=entities,
        raw=payload,
    )
    return NormalizationResult(alert=alert)

