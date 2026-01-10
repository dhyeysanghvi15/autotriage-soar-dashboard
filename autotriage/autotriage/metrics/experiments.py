from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime
from typing import Any


class ExperimentsService:
    def __init__(self, db: sqlite3.Connection) -> None:
        self._db = db

    def run_replay(self, since: datetime, until: datetime, config_overrides: dict[str, Any]) -> str:
        experiment_id = str(uuid.uuid4())
        self._db.execute(
            "INSERT OR IGNORE INTO experiments (experiment_id, created_at, since, until, overrides_json) VALUES (?, ?, ?, ?, ?)",
            (
                experiment_id,
                datetime.utcnow().isoformat(),
                since.isoformat(),
                until.isoformat(),
                json.dumps(config_overrides),
            ),
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
        return {"experiment": dict(row), "before": {}, "after": {}, "timeseries": []}
