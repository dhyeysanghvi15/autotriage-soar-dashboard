from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import httpx


def ingest_file(path: Path, url: str = "http://127.0.0.1:8080/webhook/alerts") -> None:
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            payload = json.loads(line)
            key = f"file-{path.name}-{hash(line)}"
            httpx.post(
                url,
                json=payload,
                headers={"Idempotency-Key": key, "X-Ingested-At": datetime.now(tz=timezone.utc).isoformat()},
                timeout=5,
            )

