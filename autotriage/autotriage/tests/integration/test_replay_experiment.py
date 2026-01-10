from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from autotriage.app.main import create_app
from autotriage.storage.db import init_db


def test_replay_experiment_roundtrip(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("AUTOTRIAGE_DB_PATH", str(tmp_path / "db.sqlite"))
    init_db()
    client = TestClient(create_app())

    since = "2025-01-01T00:00:00Z"
    until = "2025-01-02T00:00:00Z"
    r = client.post("/api/replay", json={"since": since, "until": until, "config_overrides": {}})
    assert r.status_code == 200
    exp_id = r.json()["experiment_id"]
    r2 = client.get(f"/api/experiments/{exp_id}")
    assert r2.status_code == 200

