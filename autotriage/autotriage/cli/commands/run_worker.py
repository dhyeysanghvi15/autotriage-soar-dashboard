from __future__ import annotations


async def run_worker() -> None:
    from autotriage.worker import worker_loop

    await worker_loop()
