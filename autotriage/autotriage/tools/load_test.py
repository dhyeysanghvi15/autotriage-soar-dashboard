from __future__ import annotations

import asyncio
from pathlib import Path

import httpx


async def post_jsonl(path: Path, url: str, *, concurrency: int = 10) -> None:
    lines = [l for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]
    sem = asyncio.Semaphore(concurrency)

    async with httpx.AsyncClient(timeout=5) as client:
        async def _one(i: int, payload: str) -> None:
            async with sem:
                await client.post(url, content=payload, headers={"Content-Type": "application/json", "Idempotency-Key": f"lt-{i}"})

        await asyncio.gather(*[_one(i, line) for i, line in enumerate(lines)])

