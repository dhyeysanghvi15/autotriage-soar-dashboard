from __future__ import annotations

import asyncio


async def run_worker() -> None:
    from autotriage.worker import worker_loop

    await worker_loop()

