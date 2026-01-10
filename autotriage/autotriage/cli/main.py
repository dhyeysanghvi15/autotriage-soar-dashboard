from __future__ import annotations

import asyncio
from pathlib import Path

import typer

from autotriage.cli.commands.run_api import run_api
from autotriage.cli.commands.run_worker import run_worker
from autotriage.cli.commands.seed import seed
from autotriage.cli.commands.ingest_file import ingest_file
from autotriage.cli.commands.replay import replay
from autotriage.cli.commands.report import report
from autotriage.config import load_effective_config
from autotriage.logging import configure_logging
from autotriage.tools.alert_generator import generate_alerts

app = typer.Typer(add_completion=False)


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
    target = Path("autotriage/autotriage/app/static")
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


@app.command()
def tools_alert_generator(out: Path = Path("data/sample_alerts/generated.jsonl"), n: int = 200) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(generate_alerts(n)) + "\n", encoding="utf-8")
    typer.echo(str(out))


@app.command()
def demo() -> None:
    cfg = load_effective_config()
    configure_logging(cfg.log_level)
    seed()
    out = Path("data/sample_alerts/generated.jsonl")
    out.write_text("\n".join(generate_alerts(200)) + "\n", encoding="utf-8")
    ingest_file(out)
    typer.echo("Open http://localhost:8080")


app.command("seed")(seed)
app.command("ingest-file")(ingest_file)
app.command("replay")(replay)
app.command("report")(report)
