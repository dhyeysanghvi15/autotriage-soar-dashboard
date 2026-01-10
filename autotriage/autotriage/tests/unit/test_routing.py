from __future__ import annotations

from autotriage.core.models.decisions import Decision
from autotriage.core.routing.routing_rules import RoutingRule, RoutingRules, choose_queue


def test_routing_escalate_to_l3() -> None:
    rules = RoutingRules(
        default_queue="soc-triage",
        rules=[RoutingRule(when={"decision": "ESCALATE"}, queue="soc-l3", rationale="x")],
    )
    queue, rationale = choose_queue(rules, decision=Decision.escalate, enrichments={})
    assert queue == "soc-l3"
    assert rationale
