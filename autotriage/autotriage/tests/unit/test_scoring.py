from __future__ import annotations

from datetime import UTC, datetime

from autotriage.core.models.alert import CanonicalAlert
from autotriage.core.models.entities import Entity, EntityType
from autotriage.core.scoring.rule_parser import ScoringRules
from autotriage.core.scoring.score_engine import score_alert


def test_scoring_allowlist_reduces_severity() -> None:
    alert = CanonicalAlert(
        vendor="vendor_a",
        alert_type="auth",
        ts=datetime(2025, 1, 1, 0, 0, tzinfo=UTC),
        title="Suspicious login",
        severity=50,
        entities=[Entity(type=EntityType.user, value="alice")],
        raw={},
    )
    rules = ScoringRules(weights={"signal.allowlisted": -40.0, "base.alert_severity": 0.0})
    enrichments = {"allowlist": {"user:alice": {"status": "ok", "data": {"allowlisted": True}}}}
    score = score_alert(alert, enrichments, rules)
    assert score.severity <= 20
