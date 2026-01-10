from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from autotriage.core.models.decisions import Decision


@dataclass(frozen=True)
class RoutingRule:
    when: dict[str, Any]
    queue: str
    rationale: str


@dataclass(frozen=True)
class RoutingRules:
    rules: list[RoutingRule]
    default_queue: str


def load_routing_rules(rules_dir: Path) -> RoutingRules:
    data = yaml.safe_load((rules_dir / "routing.yml").read_text(encoding="utf-8")) or {}
    rules: list[RoutingRule] = []
    for item in data.get("rules") or []:
        rules.append(
            RoutingRule(
                when=dict(item.get("when") or {}),
                queue=str(item.get("queue") or "triage"),
                rationale=str(item.get("rationale") or "matched_rule"),
            )
        )
    return RoutingRules(rules=rules, default_queue=str(data.get("default_queue") or "triage"))


def _match(when: dict[str, Any], attrs: dict[str, Any]) -> bool:
    return all(attrs.get(k) == v for k, v in when.items())


def choose_queue(
    rules: RoutingRules, *, decision: Decision, enrichments: dict[str, Any]
) -> tuple[str, list[str]]:
    asset_crit = None
    for v in (enrichments.get("asset_context") or {}).values():
        data = (v or {}).get("data") or {}
        if data.get("criticality"):
            asset_crit = str(data["criticality"]).lower()
            break
    attrs = {"decision": str(decision), "asset_criticality": asset_crit}
    for r in rules.rules:
        if _match(r.when, attrs):
            return r.queue, [r.rationale]
    return rules.default_queue, ["default_queue"]
