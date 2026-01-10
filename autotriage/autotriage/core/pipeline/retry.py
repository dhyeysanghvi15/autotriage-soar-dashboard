from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import TypeVar

T = TypeVar("T")


async def retry_async(
    fn: Callable[[], Awaitable[T]], *, attempts: int = 3, backoff_s: float = 0.2
) -> T:
    last_exc: Exception | None = None
    for i in range(attempts):
        try:
            return await fn()
        except Exception as e:  # noqa: BLE001
            last_exc = e
            await asyncio.sleep(backoff_s * (2**i))
    assert last_exc is not None
    raise last_exc
