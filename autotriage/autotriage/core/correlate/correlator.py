from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from autotriage.core.correlate.heuristics import correlation_entities
from autotriage.core.models.alert import CanonicalAlert


def _find_existing_case(
    db: sqlite3.Connection, entities: list[tuple[str, str]], since: datetime
) -> str | None:
    if not entities:
        return None
    placeholders = ",".join(["(?, ?)"] * len(entities))
    params: list[Any] = []
    for t, v in entities:
        params.extend([t, v])
    params.append(since.isoformat())
    row = db.execute(
        f"""
        SELECT ce.case_id
        FROM case_entities ce
        JOIN cases c ON c.case_id = ce.case_id
        WHERE (ce.entity_type, ce.entity_value) IN ({placeholders})
          AND c.created_at >= ?
        ORDER BY c.created_at DESC
        LIMIT 1
        """,
        params,
    ).fetchone()
    return str(row["case_id"]) if row else None


def correlate_into_case(
    db: sqlite3.Connection,
    alert: CanonicalAlert,
    *,
    correlation_window_seconds: int,
    base_severity: int,
    decision: str,
    queue: str,
    score: dict[str, Any],
    routing: dict[str, Any],
) -> str:
    now = datetime.now(tz=UTC)
    since = now - timedelta(seconds=correlation_window_seconds)
    ents = correlation_entities(alert.entities)
    pairs = [(e.type.value, e.value) for e in ents]
    case_id = _find_existing_case(db, pairs, since)
    if case_id is None:
        case_id = str(uuid.uuid4())
        db.execute(
            """
            INSERT INTO cases (case_id, created_at, updated_at, severity, confidence, decision, queue, summary, score_json, routing_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                case_id,
                now.isoformat(),
                now.isoformat(),
                base_severity,
                float(score.get("confidence", 0.5)),
                decision,
                queue,
                alert.title,
                json.dumps(score),
                json.dumps(routing),
            ),
        )
    else:
        db.execute(
            """
            UPDATE cases
            SET updated_at = ?, severity = MAX(severity, ?), decision = ?, queue = ?, summary = ?
            WHERE case_id = ?
            """,
            (now.isoformat(), base_severity, decision, queue, alert.title, case_id),
        )

    for e in ents:
        db.execute(
            "INSERT OR IGNORE INTO case_entities (case_id, entity_type, entity_value) VALUES (?, ?, ?)",
            (case_id, e.type.value, e.value),
        )
    db.commit()
    return case_id
