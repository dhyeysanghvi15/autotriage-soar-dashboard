from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

import httpx
import typer

app = typer.Typer(add_completion=False)


@dataclass(frozen=True)
class SmokeResult:
    ok: bool
    message: str


def _fail(msg: str) -> SmokeResult:
    return SmokeResult(ok=False, message=msg)


def _ok(msg: str) -> SmokeResult:
    return SmokeResult(ok=True, message=msg)


@app.command()
def main(base_url: str = "http://127.0.0.1:8080") -> None:
    base = base_url.rstrip("/")
    payload = {
        "vendor": "vendor_a",
        "time": datetime.now(tz=UTC).isoformat().replace("+00:00", "Z"),
        "rule": "R-SMOKE-1",
        "severity": 3,
        "src_ip": "10.0.0.10",
        "user": "alice",
        "host": "workstation-1",
        "title": "Smoke test alert",
    }
    try:
        with httpx.Client(timeout=5) as client:
            r = client.get(f"{base}/healthz")
            if r.status_code != 200:
                raise RuntimeError(f"/healthz HTTP {r.status_code}")

            r = client.get(f"{base}/api/overview")
            if r.status_code != 200:
                raise RuntimeError(f"/api/overview HTTP {r.status_code}")

            r = client.post(f"{base}/webhook/alerts", json=payload)
            if r.status_code != 202:
                raise RuntimeError(f"/webhook/alerts HTTP {r.status_code}")

    except Exception as e:  # noqa: BLE001
        typer.echo(_fail(f"smoke_failed: {e}").message)
        raise typer.Exit(code=1) from e

    typer.echo(_ok("smoke_ok").message)


if __name__ == "__main__":
    app()
