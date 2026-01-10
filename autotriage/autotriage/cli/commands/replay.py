from __future__ import annotations

from datetime import UTC, datetime, timedelta

import httpx


def replay(
    since_minutes: int = 60,
    url: str = "http://127.0.0.1:8080/api/replay",
) -> None:
    until = datetime.now(tz=UTC)
    since = until - timedelta(minutes=since_minutes)
    httpx.post(url, json={"since": since.isoformat(), "until": until.isoformat()}, timeout=30)
