from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from autotriage.app.middleware.request_id import RequestIdMiddleware
from autotriage.app.routes import cases, config, health, ingest, metrics, overview, replay
from autotriage.storage.db import init_db


def create_app(static_dir: Path | None = None) -> FastAPI:
    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        init_db()
        yield

    app = FastAPI(
        title="AutoTriage",
        docs_url="/api/docs",
        openapi_url="/api/openapi.json",
        lifespan=lifespan,
    )

    app.add_middleware(RequestIdMiddleware)

    app.include_router(health.router)
    app.include_router(ingest.router)
    app.include_router(cases.router, prefix="/api")
    app.include_router(overview.router, prefix="/api")
    app.include_router(replay.router, prefix="/api")
    app.include_router(config.router, prefix="/api")
    app.include_router(metrics.router)

    playbooks_root = (Path(__file__).resolve().parents[1] / "playbooks").resolve()
    if playbooks_root.exists():

        @app.get("/playbooks/{playbook_path:path}", include_in_schema=False)
        def playbook_md(playbook_path: str) -> FileResponse:
            candidate = (playbooks_root / playbook_path).resolve()
            if not candidate.is_relative_to(playbooks_root):
                raise HTTPException(status_code=404)
            if candidate.suffix.lower() != ".md":
                raise HTTPException(status_code=404)
            if not candidate.exists() or not candidate.is_file():
                raise HTTPException(status_code=404)
            return FileResponse(candidate)

    static_root = static_dir or (Path(__file__).resolve().parent / "static")
    if static_root.exists():
        static_root_resolved = static_root.resolve()
        assets = static_root / "assets"
        if assets.exists():
            app.mount("/assets", StaticFiles(directory=str(assets)), name="assets")

        @app.get("/", include_in_schema=False)
        def spa_index() -> FileResponse:
            return FileResponse(static_root / "index.html")

        @app.get("/{full_path:path}", include_in_schema=False)
        def spa_fallback(full_path: str) -> FileResponse:
            candidate = (static_root / full_path).resolve()
            if not candidate.is_relative_to(static_root_resolved):
                raise HTTPException(status_code=404)
            if candidate.exists() and candidate.is_file():
                return FileResponse(candidate)
            return FileResponse(static_root / "index.html")

    return app
