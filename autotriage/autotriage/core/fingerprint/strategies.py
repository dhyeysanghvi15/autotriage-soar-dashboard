from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from autotriage.core.fingerprint.hasher import stable_hash
from autotriage.core.models.alert import CanonicalAlert


@dataclass(frozen=True)
class Fingerprint:
    strategy: str
    fp_hash: str
    window_start: datetime


def compute_fingerprint(alert: CanonicalAlert, dedup_window_seconds: int) -> Fingerprint:
    window = timedelta(seconds=dedup_window_seconds)
    ts = alert.ts.astimezone(UTC)
    window_start = ts - timedelta(seconds=(ts.timestamp() % window.total_seconds()))
    parts: dict[str, str] = {"vendor": alert.vendor, "type": alert.alert_type, "title": alert.title}
    if alert.rule_id:
        parts["rule_id"] = alert.rule_id
    for e in sorted(alert.entities, key=lambda x: (x.type.value, x.value)):
        if e.type.value in {"user", "host", "src_ip", "dst_ip", "domain"}:
            parts[f"{e.type.value}"] = e.value
    return Fingerprint(strategy="default", fp_hash=stable_hash(parts), window_start=window_start)
