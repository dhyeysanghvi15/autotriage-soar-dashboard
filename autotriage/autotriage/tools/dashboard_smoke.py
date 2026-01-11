from __future__ import annotations

from dataclasses import dataclass

import httpx
import typer

app = typer.Typer(add_completion=False)


@dataclass(frozen=True)
class Result:
    ok: bool
    message: str


@app.command()
def main(base_url: str = "http://127.0.0.1:8080") -> None:
    base = base_url.rstrip("/")
    try:
        with httpx.Client(timeout=5) as client:
            r = client.get(f"{base}/")
            if r.status_code != 200:
                raise RuntimeError(f"/ HTTP {r.status_code}")
            r = client.get(f"{base}/api/overview")
            if r.status_code != 200:
                raise RuntimeError(f"/api/overview HTTP {r.status_code}")
            r = client.get(f"{base}/api/cases")
            if r.status_code != 200:
                raise RuntimeError(f"/api/cases HTTP {r.status_code}")
    except Exception as e:  # noqa: BLE001
        typer.echo(Result(False, f"dashboard_smoke_failed: {e}").message)
        raise typer.Exit(code=1) from e

    typer.echo(Result(True, "dashboard_smoke_ok").message)


if __name__ == "__main__":
    app()
