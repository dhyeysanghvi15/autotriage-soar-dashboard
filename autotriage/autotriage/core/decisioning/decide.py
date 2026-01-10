from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from autotriage.core.models.case import ScoreExplanation
from autotriage.core.models.decisions import Decision, RoutingDecision


@dataclass(frozen=True)
class Thresholds:
    auto_close_max_severity: int = 25
    auto_close_min_confidence: float = 0.8
    escalate_min_severity: int = 85


def load_thresholds(rules_dir: Path) -> Thresholds:
    data = yaml.safe_load((rules_dir / "thresholds.yml").read_text(encoding="utf-8")) or {}
    d = data.get("decisioning") or {}
    return Thresholds(
        auto_close_max_severity=int(d.get("auto_close_max_severity", 25)),
        auto_close_min_confidence=float(d.get("auto_close_min_confidence", 0.8)),
        escalate_min_severity=int(d.get("escalate_min_severity", 85)),
    )


def decide(score: ScoreExplanation, enrichments: dict[str, Any], thresholds: Thresholds) -> Decision:
    allowlisted = False
    for v in (enrichments.get("allowlist") or {}).values():
        data = (v or {}).get("data") or {}
        if data.get("allowlisted") is True:
            allowlisted = True

    critical = False
    for v in (enrichments.get("asset_context") or {}).values():
        data = (v or {}).get("data") or {}
        if str(data.get("criticality") or "").lower() == "critical":
            critical = True

    bad_rep = False
    for v in (enrichments.get("ip_reputation") or {}).values():
        data = (v or {}).get("data") or {}
        if str(data.get("rep") or "").lower() == "bad":
            bad_rep = True

    if allowlisted and score.severity <= thresholds.auto_close_max_severity and score.confidence >= thresholds.auto_close_min_confidence:
        return Decision.auto_close
    if score.severity >= thresholds.escalate_min_severity or critical or bad_rep:
        return Decision.escalate
    return Decision.create_ticket


def as_routing_decision(decision: Decision, queue: str, rationale: list[str]) -> RoutingDecision:
    return RoutingDecision(decision=decision, queue=queue, rationale=rationale)
