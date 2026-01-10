from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from autotriage.core.models.alert import CanonicalAlert
from autotriage.core.models.case import ScoreContribution, ScoreExplanation
from autotriage.core.scoring.explain import make_explanation
from autotriage.core.scoring.rule_parser import ScoringRules


@dataclass(frozen=True)
class DerivedSignals:
    allowlisted: bool
    asset_criticality: str | None
    has_bad_rep: bool
    has_suspicious_rep: bool
    has_phishing_domain: bool


def derive_signals(enrichments: dict[str, Any]) -> DerivedSignals:
    allowlisted = False
    asset_criticality: str | None = None
    has_bad_rep = False
    has_suspicious_rep = False
    has_phishing_domain = False

    allow = enrichments.get("allowlist") or {}
    for v in allow.values():
        data = (v or {}).get("data") or {}
        if data.get("allowlisted") is True:
            allowlisted = True

    assets = enrichments.get("asset_context") or {}
    for v in assets.values():
        data = (v or {}).get("data") or {}
        if data.get("criticality"):
            asset_criticality = str(data["criticality"])

    rep = enrichments.get("ip_reputation") or {}
    for v in rep.values():
        data = (v or {}).get("data") or {}
        label = str(data.get("rep") or "").lower()
        try:
            score = int(float(data.get("score") or 0))
        except ValueError:
            score = 0
        if label == "bad" or score >= 80:
            has_bad_rep = True
        elif label == "suspicious" or score >= 50:
            has_suspicious_rep = True

    whois = enrichments.get("whois") or {}
    for v in whois.values():
        data = (v or {}).get("data") or {}
        if str(data.get("category") or "").lower() in {"phishing", "malware"}:
            has_phishing_domain = True

    return DerivedSignals(
        allowlisted=allowlisted,
        asset_criticality=asset_criticality,
        has_bad_rep=has_bad_rep,
        has_suspicious_rep=has_suspicious_rep,
        has_phishing_domain=has_phishing_domain,
    )


def score_alert(
    alert: CanonicalAlert, enrichments: dict[str, Any], rules: ScoringRules
) -> ScoreExplanation:
    sig = derive_signals(enrichments)
    contributions: list[ScoreContribution] = []

    def add(name: str, value: float, reason: str) -> None:
        weight = float(rules.weights.get(name, 0.0))
        points = weight * value
        contributions.append(
            ScoreContribution(name=name, weight=weight, value=value, points=points, reason=reason)
        )

    add("base.alert_severity", value=1.0, reason=f"base severity={alert.severity}")
    if sig.allowlisted:
        add("signal.allowlisted", value=1.0, reason="entity is allowlisted")
    if sig.asset_criticality:
        add(
            f"signal.asset_criticality.{sig.asset_criticality}",
            value=1.0,
            reason="asset criticality",
        )
    if sig.has_bad_rep:
        add("signal.ip_rep.bad", value=1.0, reason="known bad IP reputation")
    elif sig.has_suspicious_rep:
        add("signal.ip_rep.suspicious", value=1.0, reason="suspicious IP reputation")
    if sig.has_phishing_domain:
        add(
            "signal.domain.phishing",
            value=1.0,
            reason="domain WHOIS category indicates phishing/malware",
        )

    total_points = sum(c.points for c in contributions)
    severity = int(max(0, min(100, alert.severity + total_points)))

    confidence = 0.55
    if sig.allowlisted:
        confidence = max(confidence, 0.85)
    if sig.has_bad_rep or sig.has_phishing_domain:
        confidence = max(confidence, 0.75)
    if sig.has_suspicious_rep:
        confidence = max(confidence, 0.65)
    if sig.asset_criticality in {"critical", "high"}:
        confidence = max(confidence, 0.6)
    confidence = float(max(0.0, min(1.0, confidence)))

    return make_explanation(severity=severity, confidence=confidence, contributions=contributions)
