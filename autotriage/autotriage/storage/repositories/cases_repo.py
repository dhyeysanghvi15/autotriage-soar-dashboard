from __future__ import annotations

import sqlite3
from typing import Any


class CasesRepository:
    def __init__(self, db: sqlite3.Connection) -> None:
        self._db = db

    def list_cases(
        self,
        time_range: str | None,
        severity_min: int | None,
        decision: str | None,
        queue: str | None,
        q: str | None,
    ) -> list[dict[str, Any]]:
        where: list[str] = []
        params: list[Any] = []
        if severity_min is not None:
            where.append("severity >= ?")
            params.append(severity_min)
        if decision:
            where.append("decision = ?")
            params.append(decision)
        if queue:
            where.append("queue = ?")
            params.append(queue)
        if q:
            where.append("(summary LIKE ? OR case_id LIKE ?)")
            params.extend([f"%{q}%", f"%{q}%"])
        sql = "SELECT case_id, created_at, severity, decision, queue, summary FROM cases"
        if where:
            sql += " WHERE " + " AND ".join(where)
        sql += " ORDER BY created_at DESC LIMIT 200"
        cur = self._db.execute(sql, params)
        return [dict(r) for r in cur.fetchall()]

    def get_case_detail(self, case_id: str) -> dict[str, Any]:
        cur = self._db.execute("SELECT * FROM cases WHERE case_id = ?", (case_id,))
        row = cur.fetchone()
        if row is None:
            return {"case_id": case_id, "missing": True}
        events = [
            dict(r)
            for r in self._db.execute(
                "SELECT * FROM events WHERE case_id = ? ORDER BY created_at ASC", (case_id,)
            ).fetchall()
        ]
        nodes = [
            dict(r)
            for r in self._db.execute(
                "SELECT * FROM case_entities WHERE case_id = ?", (case_id,)
            ).fetchall()
        ]
        edges = [
            dict(r)
            for r in self._db.execute(
                "SELECT * FROM case_edges WHERE case_id = ?", (case_id,)
            ).fetchall()
        ]
        ticket = self._db.execute("SELECT * FROM tickets WHERE case_id = ?", (case_id,)).fetchone()
        return {
            "case": dict(row),
            "timeline": events,
            "graph": {"nodes": nodes, "edges": edges},
            "ticket": dict(ticket) if ticket else None,
        }

    def upsert_edge(
        self, case_id: str, src_type: str, src_value: str, dst_type: str, dst_value: str, edge_type: str
    ) -> None:
        self._db.execute(
            """
            INSERT OR IGNORE INTO case_edges (case_id, src_type, src_value, dst_type, dst_value, edge_type)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (case_id, src_type, src_value, dst_type, dst_value, edge_type),
        )
        self._db.commit()
