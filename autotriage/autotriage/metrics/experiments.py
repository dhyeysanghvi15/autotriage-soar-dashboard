from __future__ import annotations

import json
import sqlite3
import uuid
from collections import Counter
from datetime import datetime, timezone
from typing import Any

from autotriage.config import load_effective_config
from autotriage.core.fingerprint.strategies import compute_fingerprint
from autotriage.core.normalize.registry import normalize
from autotriage.core.scoring.rule_parser import load_scoring_rules
from autotriage.core.scoring.score_engine import score_alert
from autotriage.core.decisioning.decide import decide, load_thresholds
from autotriage.core.routing.router import route

class ExperimentsService:
    def __init__(self, db: sqlite3.Connection) -> None:
        self._db = db

    def run_replay(self, since: datetime, until: datetime, config_overrides: dict[str, Any]) -> str:
        cfg = load_effective_config()
        experiment_id = str(uuid.uuid4())
        created_at = datetime.now(tz=timezone.utc).isoformat()
        self._db.execute(
            "INSERT INTO experiments (experiment_id, created_at, since, until, overrides_json) VALUES (?, ?, ?, ?, ?)",
            (experiment_id, created_at, since.isoformat(), until.isoformat(), json.dumps(config_overrides)),
        )

        rows = self._db.execute(
            """
            SELECT ingest_id, received_at, raw_json
            FROM alerts
            WHERE received_at >= ? AND received_at <= ?
            ORDER BY received_at ASC
            """,
            (since.isoformat(), until.isoformat()),
        ).fetchall()

        before_decisions: Counter[str] = Counter()
        before_queues: Counter[str] = Counter()
        after_decisions: Counter[str] = Counter()
        after_queues: Counter[str] = Counter()

        # BEFORE: use stored cases via correlated event mapping.
        for r in rows:
            case_row = self._db.execute(
                """
                SELECT c.decision, c.queue
                FROM events e
                JOIN cases c ON c.case_id = e.case_id
                WHERE e.ingest_id = ? AND e.stage = 'correlated'
                ORDER BY e.created_at DESC
                LIMIT 1
                """,
                (r["ingest_id"],),
            ).fetchone()
            if case_row is None:
                continue
            before_decisions[str(case_row["decision"])] += 1
            before_queues[str(case_row["queue"])] += 1

        dedup_window = int(config_overrides.get("dedup_window_seconds", cfg.dedup_window_seconds))
        scoring_rules = load_scoring_rules(cfg.rules_dir)
        thresholds = load_thresholds(cfg.rules_dir)

        # Allow overriding a few scoring weights (demo knob).
        override_weights = ((config_overrides.get("scoring") or {}).get("weights") or {}) if isinstance(config_overrides.get("scoring"), dict) else {}
        if override_weights:
            scoring_rules = type(scoring_rules)(weights={**scoring_rules.weights, **{str(k): float(v) for k, v in override_weights.items()}})

        seen_fp: set[tuple[str, str]] = set()
        for r in rows:
            raw = json.loads(str(r["raw_json"]))
            alert = normalize(raw).alert.model_copy(update={"ingest_id": str(r["ingest_id"])})
            fp = compute_fingerprint(alert, dedup_window_seconds=dedup_window)
            fp_key = (fp.fp_hash, fp.window_start.isoformat())
            if fp_key in seen_fp:
                after_decisions["DEDUPED"] += 1
                continue
            seen_fp.add(fp_key)

            # Replay uses offline enrichments already stored in DB cache; reuse manager via pipeline would be heavier.
            # For experiments we approximate routing/decision from stored enrichments stage if available.
            enriched_row = self._db.execute(
                """
                SELECT payload_json FROM events
                WHERE ingest_id = ? AND stage = 'enriched'
                ORDER BY created_at DESC LIMIT 1
                """,
                (r["ingest_id"],),
            ).fetchone()
            enrichments = {}
            if enriched_row is not None:
                try:
                    enrichments = json.loads(str(enriched_row["payload_json"])).get("enrichments") or {}
                except Exception:  # noqa: BLE001
                    enrichments = {}

            score = score_alert(alert, enrichments, scoring_rules)
            decision = decide(score, enrichments, thresholds)
            routing = route(cfg.rules_dir, decision, enrichments)
            after_decisions[str(decision)] += 1
            after_queues[routing.queue] += 1

        def pct(n: float, d: float) -> float:
            return 0.0 if d <= 0 else (n / d) * 100.0

        before_total = sum(before_decisions.values())
        after_total = sum(after_decisions.values())
        before_tickets = before_decisions.get("CREATE_TICKET", 0) + before_decisions.get("ESCALATE", 0)
        after_tickets = after_decisions.get("CREATE_TICKET", 0) + after_decisions.get("ESCALATE", 0)
        before_auto_close = before_decisions.get("AUTO_CLOSE", 0)
        after_auto_close = after_decisions.get("AUTO_CLOSE", 0)

        results = {
            "before_decisions": dict(before_decisions),
            "after_decisions": dict(after_decisions),
            "before_queues": dict(before_queues),
            "after_queues": dict(after_queues),
            "before": {
                "total_cases": before_total,
                "tickets": before_tickets,
                "auto_close": before_auto_close,
                "auto_close_rate_pct": pct(before_auto_close, before_total),
            },
            "after": {
                "total_cases": after_total,
                "tickets": after_tickets,
                "auto_close": after_auto_close,
                "auto_close_rate_pct": pct(after_auto_close, after_total),
            },
            "ticket_reduction_pct": pct(max(0, before_tickets - after_tickets), max(1, before_tickets)),
        }

        for metric_name, before_val, after_val in [
            ("tickets", float(before_tickets), float(after_tickets)),
            ("auto_close_rate_pct", float(results["before"]["auto_close_rate_pct"]), float(results["after"]["auto_close_rate_pct"])),
            ("ticket_reduction_pct", 0.0, float(results["ticket_reduction_pct"])),
        ]:
            self._db.execute(
                """
                INSERT INTO experiment_results (experiment_id, metric_name, before_value, after_value, details_json)
                VALUES (?, ?, ?, ?, ?)
                """,
                (experiment_id, metric_name, before_val, after_val, json.dumps(results)),
            )
        self._db.commit()
        return experiment_id

    def list_experiments(self) -> list[dict[str, Any]]:
        cur = self._db.execute(
            "SELECT experiment_id, created_at, since, until FROM experiments ORDER BY created_at DESC LIMIT 100"
        )
        return [dict(r) for r in cur.fetchall()]

    def get_experiment(self, experiment_id: str) -> dict[str, Any]:
        cur = self._db.execute("SELECT * FROM experiments WHERE experiment_id = ?", (experiment_id,))
        row = cur.fetchone()
        if row is None:
            return {"experiment_id": experiment_id, "missing": True}
        results = self._db.execute(
            "SELECT metric_name, before_value, after_value, details_json FROM experiment_results WHERE experiment_id = ?",
            (experiment_id,),
        ).fetchall()
        details: dict[str, Any] = {}
        before: dict[str, Any] = {}
        after: dict[str, Any] = {}
        for r in results:
            details[str(r["metric_name"])] = {
                "before": r["before_value"],
                "after": r["after_value"],
            }
            try:
                payload = json.loads(str(r["details_json"]))
                before = payload.get("before") or before
                after = payload.get("after") or after
            except Exception:  # noqa: BLE001
                pass
        return {"experiment": dict(row), "before": before, "after": after, "details": details}
