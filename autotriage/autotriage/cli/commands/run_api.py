from __future__ import annotations

import uvicorn

from autotriage.app.main import create_app


def run_api(host: str, port: int) -> None:
    app = create_app()
    uvicorn.run(app, host=host, port=port, log_level="info")

