from __future__ import annotations

import json
import os
import signal
import sqlite3
import subprocess
import sys
import tempfile
import time
from contextlib import suppress
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

import httpx
import typer

app = typer.Typer(add_completion=False)


@dataclass(frozen=True)
class PerfResult:
    n: int
    ingest_seconds: float
    processing_seconds: float
    cases: int
    tickets: int
    deduped: int
    failed_events: int
    deadletters: int


def _wait_ready(base_url: str, timeout_s: float) -> None:
    deadline = time.monotonic() + timeout_s
    with httpx.Client(timeout=1.0) as client:
        while time.monotonic() < deadline:
            try:
                r = client.get(f"{base_url}/readyz")
                if r.status_code == 200:
                    return
            except Exception:  # noqa: BLE001
                pass
            time.sleep(0.1)
    raise RuntimeError("backend did not become ready")


def _db_counts(db_path: str) -> tuple[int, int, int]:
    with sqlite3.connect(db_path) as db:
        db.row_factory = sqlite3.Row
        pending = int(
            db.execute(
                "SELECT COUNT(*) FROM alerts WHERE status IN ('ingested','processing')"
            ).fetchone()[0]
        )
        failed = int(
            db.execute("SELECT COUNT(*) FROM alerts WHERE status = 'failed'").fetchone()[0]
        )
        processed = int(
            db.execute("SELECT COUNT(*) FROM alerts WHERE status = 'processed'").fetchone()[0]
        )
        return pending, failed, processed


def _final_result(
    db_path: str, *, n: int, ingest_seconds: float, processing_seconds: float
) -> PerfResult:
    with sqlite3.connect(db_path) as db:
        db.row_factory = sqlite3.Row
        cases = int(db.execute("SELECT COUNT(*) FROM cases").fetchone()[0])
        tickets = int(db.execute("SELECT COUNT(*) FROM tickets").fetchone()[0])
        deduped = int(
            db.execute("SELECT COUNT(*) FROM events WHERE stage = 'deduped'").fetchone()[0]
        )
        failed_events = int(
            db.execute("SELECT COUNT(*) FROM events WHERE stage = 'failed'").fetchone()[0]
        )
        deadletters = int(db.execute("SELECT COUNT(*) FROM deadletter").fetchone()[0])

    return PerfResult(
        n=n,
        ingest_seconds=ingest_seconds,
        processing_seconds=processing_seconds,
        cases=cases,
        tickets=tickets,
        deduped=deduped,
        failed_events=failed_events,
        deadletters=deadletters,
    )


def _payloads(n: int, *, start: datetime) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    users = ["alice", "bob", "carol"]
    hosts = ["workstation-1", "app01", "dc01"]
    ips = ["1.2.3.4", "5.6.7.8", "10.0.0.10"]
    rules = ["R-LOGIN-001", "R-DNS-404", "R-EDR-777"]
    for i in range(n):
        ts = start + timedelta(seconds=i)
        out.append(
            {
                "vendor": "vendor_a",
                "time": ts.isoformat().replace("+00:00", "Z"),
                "rule": rules[i % len(rules)],
                "severity": 7 if i % 10 else 9,
                "src_ip": ips[i % len(ips)],
                "user": users[i % len(users)],
                "host": hosts[i % len(hosts)],
                "title": "Synthetic perf alert",
            }
        )
    return out


@app.command()
def main(
    n: int = 1000,
    port: int = 18081,
    seed_db: bool = True,
    startup_timeout_s: float = 15.0,
    completion_timeout_s: float = 120.0,
    max_processing_seconds: float = 120.0,
    max_deadletters: int = 0,
    max_failed_events: int = 0,
) -> None:
    base_url = f"http://127.0.0.1:{port}"
    db_fd, db_path = tempfile.mkstemp(prefix="autotriage-perf-", suffix=".db")
    os.close(db_fd)

    env = {
        **os.environ,
        "AUTOTRIAGE_DB_PATH": db_path,
        "AUTOTRIAGE_LOG_LEVEL": "ERROR",
    }

    if seed_db:
        subprocess.run(
            [sys.executable, "-m", "autotriage.cli.main", "seed"],
            check=True,
            env=env,
        )

    proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "autotriage.cli.main",
            "run",
            "--mode",
            "all",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
        ],
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        _wait_ready(base_url, startup_timeout_s)

        payloads = _payloads(n, start=datetime.now(tz=UTC) - timedelta(minutes=10))
        t0 = time.monotonic()
        with httpx.Client(timeout=5.0) as client:
            for i, payload in enumerate(payloads):
                r = client.post(
                    f"{base_url}/webhook/alerts",
                    headers={"Idempotency-Key": f"perf-{i}"},
                    json=payload,
                )
                if r.status_code != 202:
                    raise RuntimeError(f"ingest failed at {i}: HTTP {r.status_code} {r.text}")
        t1 = time.monotonic()
        ingest_seconds = t1 - t0

        deadline = time.monotonic() + completion_timeout_s
        while time.monotonic() < deadline:
            pending, _failed, processed = _db_counts(db_path)
            if pending == 0 and processed >= n:
                break
            time.sleep(0.2)
        else:
            pending, failed, processed = _db_counts(db_path)
            raise RuntimeError(
                f"timeout waiting for completion: pending={pending} failed={failed} processed={processed}"
            )

        t2 = time.monotonic()
        processing_seconds = t2 - t1
        result = _final_result(
            db_path, n=n, ingest_seconds=ingest_seconds, processing_seconds=processing_seconds
        )

        ingest_rps = result.n / max(result.ingest_seconds, 1e-9)
        typer.echo(
            json.dumps(
                {
                    "n": result.n,
                    "ingest_seconds": round(result.ingest_seconds, 3),
                    "ingest_rps": round(ingest_rps, 1),
                    "processing_seconds": round(result.processing_seconds, 3),
                    "cases": result.cases,
                    "tickets": result.tickets,
                    "deduped": result.deduped,
                    "failed_events": result.failed_events,
                    "deadletters": result.deadletters,
                },
                separators=(",", ":"),
            )
        )

        if result.processing_seconds > max_processing_seconds:
            raise RuntimeError(
                f"processing_seconds={result.processing_seconds:.2f} exceeded {max_processing_seconds:.2f}"
            )
        if result.deadletters > max_deadletters:
            raise RuntimeError(f"deadletters={result.deadletters} exceeded {max_deadletters}")
        if result.failed_events > max_failed_events:
            raise RuntimeError(f"failed_events={result.failed_events} exceeded {max_failed_events}")
    except Exception as e:  # noqa: BLE001
        typer.echo(f"perf_failed: {e}")
        raise typer.Exit(code=1) from e
    finally:
        try:
            proc.send_signal(signal.SIGTERM)
            proc.wait(timeout=5)
        except Exception:  # noqa: BLE001
            with suppress(Exception):
                proc.kill()
        with suppress(OSError):
            os.unlink(db_path)


if __name__ == "__main__":
    app()
