from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from autotriage.app.main import create_app


def test_playbooks_path_traversal_is_404() -> None:
    client = TestClient(create_app())
    r = client.get("/playbooks/%2e%2e/pyproject.toml")
    assert r.status_code == 404
    r2 = client.get("/playbooks/templates/action_cards.yml")
    assert r2.status_code == 404


def test_playbooks_known_markdown_is_served() -> None:
    client = TestClient(create_app())
    r = client.get("/playbooks/actions/isolate_host.md")
    assert r.status_code == 200
    assert "Isolate Host" in r.text


def test_spa_fallback_blocks_traversal(tmp_path: Path) -> None:
    static_dir = tmp_path / "static"
    static_dir.mkdir(parents=True)
    (static_dir / "index.html").write_text("<html>ok</html>", encoding="utf-8")
    (tmp_path / "secret.txt").write_text("nope", encoding="utf-8")
    client = TestClient(create_app(static_dir=static_dir))

    r = client.get("/cases")
    assert r.status_code == 200
    assert "ok" in r.text

    r2 = client.get("/%2e%2e/secret.txt")
    assert r2.status_code == 404
