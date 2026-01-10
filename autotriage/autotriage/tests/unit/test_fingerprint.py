from __future__ import annotations

from datetime import UTC, datetime

from autotriage.core.fingerprint.strategies import compute_fingerprint
from autotriage.core.models.alert import CanonicalAlert
from autotriage.core.models.entities import Entity, EntityType


def test_fingerprint_deterministic() -> None:
    alert = CanonicalAlert(
        vendor="vendor_a",
        alert_type="auth",
        ts=datetime(2025, 1, 1, 0, 0, 0, tzinfo=UTC),
        title="Suspicious login",
        rule_id="R-1",
        severity=70,
        entities=[
            Entity(type=EntityType.user, value="alice"),
            Entity(type=EntityType.src_ip, value="1.2.3.4"),
        ],
        raw={},
    )
    a = compute_fingerprint(alert, 600)
    b = compute_fingerprint(alert, 600)
    assert a.fp_hash == b.fp_hash
    assert a.window_start == b.window_start
