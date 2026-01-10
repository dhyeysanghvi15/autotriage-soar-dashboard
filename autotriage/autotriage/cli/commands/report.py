from __future__ import annotations

import typer

from autotriage.storage.db import get_db


def report() -> None:
    db = get_db()
    try:
        cur = db.execute("SELECT COUNT(*) AS c FROM alerts")
        typer.echo(f"alerts={cur.fetchone()[0]}")
        cur = db.execute("SELECT COUNT(*) AS c FROM cases")
        typer.echo(f"cases={cur.fetchone()[0]}")
    finally:
        db.close()
