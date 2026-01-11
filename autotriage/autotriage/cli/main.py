from __future__ import annotations

import asyncio
from pathlib import Path

import httpx
import typer

from autotriage.cli.commands.ingest_file import ingest_file
from autotriage.cli.commands.replay import replay
from autotriage.cli.commands.report import report
from autotriage.cli.commands.run_api import run_api
from autotriage.cli.commands.run_worker import run_worker
from autotriage.cli.commands.seed import seed
from autotriage.config import load_effective_config
from autotriage.logging import configure_logging
from autotriage.metrics.reporter import quick_counts
from autotriage.storage.db import get_db
from autotriage.tools.alert_generator import generate_alerts

app = typer.Typer(add_completion=False)
tools_app = typer.Typer(add_completion=False)


@app.command()
def run(mode: str = "all", host: str = "127.0.0.1", port: int = 8080) -> None:
    cfg = load_effective_config()
    configure_logging(cfg.log_level)
    if mode == "api":
        run_api(host, port)
        return
    if mode == "worker":
        asyncio.run(run_worker())
        return
    if mode == "all":

        async def _all() -> None:
            await asyncio.gather(
                asyncio.to_thread(run_api, host, port),
                run_worker(),
            )

        asyncio.run(_all())
        return
    raise typer.BadParameter("mode must be one of: api, worker, all")


@app.command()
def build_web(dist_dir: Path = Path("web/dist")) -> None:
    target = Path("autotriage/app/static")
    target.mkdir(parents=True, exist_ok=True)
    if not dist_dir.exists():
        raise typer.BadParameter(f"{dist_dir} does not exist; run npm build first")
    for p in target.glob("*"):
        if p.is_file():
            p.unlink()
    for src in dist_dir.rglob("*"):
        if src.is_dir():
            continue
        rel = src.relative_to(dist_dir)
        dst = target / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(src.read_bytes())


@tools_app.command("alert-generator")
def alert_generator(
    out: Path = Path("data/sample_alerts/generated.jsonl"),
    n: int = 200,
    seed: int = 1337,
) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(generate_alerts(n, seed=seed)) + "\n", encoding="utf-8")
    typer.echo(str(out))


@app.command()
def demo(
    host: str = "127.0.0.1",
    port: int = 8080,
    n: int = 200,
    demo_seed: int = 1337,
) -> None:
    cfg = load_effective_config()
    configure_logging(cfg.log_level)

    async def _demo() -> None:
        seed()

        api_task = asyncio.to_thread(run_api, host, port)
        worker_task = asyncio.create_task(run_worker())

        async with httpx.AsyncClient(timeout=2) as client:
            for _ in range(50):
                try:
                    r = await client.get(f"http://{host}:{port}/readyz")
                    if r.status_code == 200:
                        break
                except Exception:  # noqa: BLE001
                    pass
                await asyncio.sleep(0.1)

        out = Path("data/sample_alerts/generated.jsonl")
        out.write_text("\n".join(generate_alerts(n, seed=demo_seed)) + "\n", encoding="utf-8")
        await asyncio.to_thread(ingest_file, out, f"http://{host}:{port}/webhook/alerts")

        db = get_db()
        try:
            counts = quick_counts(db)
        finally:
            db.close()

        typer.echo(f"demo_seed={demo_seed} n={n}")
        typer.echo(
            f"demo_ingested alerts={counts['alerts_total']} cases={counts['cases_total']} tickets={counts['tickets_total']}"
        )
        typer.echo(f"Open http://{host}:{port}")
        await asyncio.gather(api_task, worker_task)

    asyncio.run(_demo())


app.command("seed")(seed)
app.command("ingest-file")(ingest_file)
app.command("replay")(replay)
app.command("report")(report)

app.add_typer(tools_app, name="tools")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
