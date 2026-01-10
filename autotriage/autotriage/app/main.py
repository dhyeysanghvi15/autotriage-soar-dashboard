from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from autotriage.app.middleware.request_id import RequestIdMiddleware
from autotriage.app.routes import cases, config, health, ingest, metrics, replay


def create_app(static_dir: Path | None = None) -> FastAPI:
    app = FastAPI(title="AutoTriage", docs_url="/api/docs", openapi_url="/api/openapi.json")

    app.add_middleware(RequestIdMiddleware)

    app.include_router(health.router)
    app.include_router(ingest.router)
    app.include_router(cases.router, prefix="/api")
    app.include_router(replay.router, prefix="/api")
    app.include_router(config.router, prefix="/api")
    app.include_router(metrics.router)

    static_root = static_dir or (Path(__file__).resolve().parent / "static")
    if static_root.exists():
        assets = static_root / "assets"
        if assets.exists():
            app.mount("/assets", StaticFiles(directory=str(assets)), name="assets")

        @app.get("/", include_in_schema=False)
        def spa_index() -> FileResponse:
            return FileResponse(static_root / "index.html")

        @app.get("/{full_path:path}", include_in_schema=False)
        def spa_fallback(full_path: str) -> FileResponse:
            path = static_root / full_path
            if path.exists() and path.is_file():
                return FileResponse(path)
            return FileResponse(static_root / "index.html")

    return app
