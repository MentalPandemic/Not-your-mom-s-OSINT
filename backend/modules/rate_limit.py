from __future__ import annotations

import asyncio
import time
from collections import deque
from dataclasses import dataclass


@dataclass(frozen=True)
class RateLimitPolicy:
    requests: int
    per_seconds: float


class AsyncRateLimiter:
    """Simple sliding-window rate limiter for async code."""

    def __init__(self, policy: RateLimitPolicy):
        self.policy = policy
        self._lock = asyncio.Lock()
        self._hits: deque[float] = deque()

    async def acquire(self) -> None:
        while True:
            async with self._lock:
                now = time.time()
                window_start = now - self.policy.per_seconds
                while self._hits and self._hits[0] <= window_start:
                    self._hits.popleft()

                if len(self._hits) < self.policy.requests:
                    self._hits.append(now)
                    return

                sleep_for = self._hits[0] + self.policy.per_seconds - now
            await asyncio.sleep(max(0.0, sleep_for))
