from __future__ import annotations

from typing import Any


def recommended_actions_for_case(
    case: dict[str, Any], graph: dict[str, Any] | None = None
) -> list[dict[str, Any]]:
    decision = str(case.get("decision") or "")
    severity = int(case.get("severity") or 0)

    hosts: set[str] = set()
    users: set[str] = set()
    ips: set[str] = set()
    if graph:
        for n in graph.get("nodes") or []:
            t = str(n.get("entity_type") or "")
            v = str(n.get("entity_value") or "")
            if t == "host":
                hosts.add(v)
            if t == "user":
                users.add(v)
            if t in {"src_ip", "dst_ip"}:
                ips.add(v)

    actions: list[dict[str, Any]] = []
    if decision in {"ESCALATE", "CREATE_TICKET"} and severity >= 70:
        for h in sorted(hosts)[:2]:
            actions.append(
                {
                    "title": f"Isolate host {h}",
                    "playbook": "/playbooks/actions/isolate_host.md",
                    "params": {"host": h},
                }
            )
        for u in sorted(users)[:2]:
            actions.append(
                {
                    "title": f"Disable user {u}",
                    "playbook": "/playbooks/actions/disable_user.md",
                    "params": {"user": u},
                }
            )
        for ip in sorted(ips)[:2]:
            actions.append(
                {
                    "title": f"Block IP {ip}",
                    "playbook": "/playbooks/actions/block_ip.md",
                    "params": {"ip": ip},
                }
            )
    if not actions and decision == "AUTO_CLOSE":
        actions.append(
            {"title": "No action required (auto-closed)", "playbook": "/playbooks/README.md"}
        )
    if not actions:
        actions.append(
            {"title": "Review evidence and confirm triage", "playbook": "/playbooks/README.md"}
        )
    return actions
