from __future__ import annotations

import asyncio
import random
from collections.abc import Awaitable, Callable
from dataclasses import dataclass


@dataclass(frozen=True)
class RetryPolicy:
    max_attempts: int = 4
    base_delay_seconds: float = 0.5
    max_delay_seconds: float = 8.0
    jitter: float = 0.2


async def with_retry(fn: Callable[[], Awaitable[object]], policy: RetryPolicy | None = None):
    pol = policy or RetryPolicy()
    attempt = 0
    while True:
        attempt += 1
        try:
            return await fn()
        except Exception:
            if attempt >= pol.max_attempts:
                raise
            delay = min(pol.max_delay_seconds, pol.base_delay_seconds * (2 ** (attempt - 1)))
            delay = delay * (1.0 + random.uniform(-pol.jitter, pol.jitter))
            await asyncio.sleep(max(0.0, delay))
