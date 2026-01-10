from __future__ import annotations

from pathlib import Path
from typing import Any

from autotriage.core.models.decisions import Decision, RoutingDecision
from autotriage.core.routing.routing_rules import choose_queue, load_routing_rules


def route(rules_dir: Path, decision: Decision, enrichments: dict[str, Any]) -> RoutingDecision:
    rules = load_routing_rules(rules_dir)
    queue, rationale = choose_queue(rules, decision=decision, enrichments=enrichments)
    return RoutingDecision(decision=decision, queue=queue, rationale=rationale)
