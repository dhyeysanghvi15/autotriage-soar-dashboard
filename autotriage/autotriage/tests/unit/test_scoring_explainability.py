from __future__ import annotations

from datetime import UTC, datetime

from autotriage.core.models.alert import CanonicalAlert
from autotriage.core.models.entities import Entity, EntityType
from autotriage.core.scoring.rule_parser import ScoringRules
from autotriage.core.scoring.score_engine import score_alert


def test_scoring_contributions_sum_matches_severity_delta() -> None:
    alert = CanonicalAlert(
        vendor="vendor_a",
        alert_type="auth",
        ts=datetime(2025, 1, 1, 0, 0, tzinfo=UTC),
        title="Suspicious login",
        severity=60,
        entities=[
            Entity(type=EntityType.user, value="alice"),
            Entity(type=EntityType.src_ip, value="1.2.3.4"),
        ],
        raw={},
    )

    rules = ScoringRules(
        weights={
            "base.alert_severity": 0.0,
            "signal.allowlisted": -40.0,
            "signal.ip_rep.bad": 25.0,
        }
    )
    enrichments = {
        "allowlist": {"user:alice": {"status": "ok", "data": {"allowlisted": True}}},
        "ip_reputation": {"1.2.3.4": {"status": "ok", "data": {"rep": "bad", "score": 90}}},
    }

    score = score_alert(alert, enrichments, rules)
    names = {c.name for c in score.contributions}
    assert "signal.allowlisted" in names
    assert "signal.ip_rep.bad" in names
    total_points = sum(c.points for c in score.contributions)
    assert score.severity == max(0, min(100, alert.severity + int(total_points)))
