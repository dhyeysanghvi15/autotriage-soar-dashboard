from __future__ import annotations

import json
import random
from datetime import datetime, timedelta, timezone
from typing import Any


def _vendor_a(ts: datetime, rng: random.Random) -> dict[str, Any]:
    users = ["alice", "bob", "carol"]
    hosts = ["workstation-1", "app01", "dc01"]
    ips = ["1.2.3.4", "5.6.7.8", "10.0.0.10"]
    return {
        "vendor": "vendor_a",
        "time": ts.isoformat().replace("+00:00", "Z"),
        "rule": rng.choice(["R-LOGIN-001", "R-DNS-404", "R-EDR-777"]),
        "severity": rng.choice([3, 5, 7, 9]),
        "src_ip": rng.choice(ips),
        "user": rng.choice(users),
        "host": rng.choice(hosts),
        "title": rng.choice(["Suspicious login", "DNS query to suspicious domain", "New admin group membership"]),
    }


def _vendor_b(ts: datetime, rng: random.Random) -> dict[str, Any]:
    users = ["alice", "bob", "carol"]
    hosts = ["workstation-1", "app01", "dc01"]
    ips = ["1.2.3.4", "5.6.7.8", "10.0.0.10"]
    return {
        "source": "vendor_b",
        "event": {
            "ts": int(ts.timestamp()),
            "name": rng.choice(["Impossible travel", "Multiple failed logins", "New process tree suspicious"]),
            "severity": rng.randint(10, 90),
            "rule_id": rng.choice(["B-TRAVEL-9", "B-AUTH-2", "B-EDR-5"]),
            "type": rng.choice(["auth", "edr", "dns"]),
        },
        "entities": {"user": rng.choice(users), "ip": rng.choice(ips), "host": rng.choice(hosts)},
    }


def _vendor_c(ts: datetime, rng: random.Random) -> dict[str, Any]:
    users = ["alice", "bob", "carol"]
    hosts = ["workstation-1", "app01", "dc01"]
    domains = ["evil.example", "example.com"]
    ips = ["1.2.3.4", "5.6.7.8", "10.0.0.10"]
    return {
        "vendor": "vendor_c",
        "observed_at": ts.isoformat().replace("+00:00", "Z"),
        "finding": {
            "title": rng.choice(["Execution of unsigned binary", "Known malware domain contacted", "Suspicious scheduled task"]),
            "priority": rng.choice(["low", "medium", "high", "critical"]),
            "type": "edr",
            "rule_id": rng.choice(["C-EDR-7", "C-EDR-9", "C-EDR-11"]),
        },
        "principal": {"user": rng.choice(users), "host": rng.choice(hosts)},
        "ioc": rng.choice([{"domain": rng.choice(domains)}, {"ip": rng.choice(ips)}]),
    }


def generate_alerts(n: int, *, seed: int = 1337) -> list[str]:
    rng = random.Random(seed)
    start = datetime.now(tz=timezone.utc) - timedelta(minutes=30)
    out: list[str] = []
    for i in range(n):
        ts = start + timedelta(seconds=i * rng.randint(1, 20))
        kind = rng.choice(["a", "b", "c"])
        if kind == "a":
            payload = _vendor_a(ts, rng)
        elif kind == "b":
            payload = _vendor_b(ts, rng)
        else:
            payload = _vendor_c(ts, rng)
        out.append(json.dumps(payload, separators=(",", ":")))
    return out

