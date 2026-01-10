from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from autotriage.core.models.alert import CanonicalAlert, NormalizationResult
from autotriage.core.models.entities import Entity, EntityType


def normalize_vendor_b(payload: dict[str, Any]) -> NormalizationResult:
    # Vendor B example:
    # { "source":"vendor_b", "event":{"ts":1700000000,"name":"...","severity":55}, "entities":{"ip":"1.2.3.4"} }
    event = payload.get("event") or {}
    ts_epoch = int(event.get("ts") or 0)
    ts = datetime.fromtimestamp(ts_epoch, tz=UTC)
    entities: list[Entity] = []
    ents = payload.get("entities") or {}
    ip = ents.get("ip") or ents.get("src_ip")
    if ip:
        entities.append(Entity(type=EntityType.src_ip, value=str(ip)))
    user = ents.get("user")
    if user:
        entities.append(Entity(type=EntityType.user, value=str(user)))
    host = ents.get("host")
    if host:
        entities.append(Entity(type=EntityType.host, value=str(host)))

    alert = CanonicalAlert(
        vendor="vendor_b",
        alert_type=str(event.get("type") or "generic"),
        ts=ts,
        title=str(event.get("name") or "vendor_b alert"),
        rule_id=str(event.get("rule_id") or "") or None,
        technique_id=str(event.get("technique") or "") or None,
        severity=max(0, min(100, int(event.get("severity") or 0))),
        entities=entities,
        raw=payload,
    )
    return NormalizationResult(alert=alert)
