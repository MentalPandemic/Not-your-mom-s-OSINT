from __future__ import annotations

import abc
import logging
from dataclasses import dataclass
from typing import Any

from backend.config.social_media_auth import SocialMediaAuthManager
from backend.modules.http_client import AsyncHttpClient
from backend.modules.rate_limit import AsyncRateLimiter, RateLimitPolicy
from backend.modules.resilience import RetryPolicy, with_retry
from backend.modules.social_extraction import NormalizedPost, NormalizedProfile

logger = logging.getLogger(__name__)


class SocialClientError(RuntimeError):
    pass


class NotFoundError(SocialClientError):
    pass


@dataclass(frozen=True)
class FetchContext:
    username: str
    max_items: int | None = None


class SocialClient(abc.ABC):
    platform: str
    rate_limit: RateLimitPolicy
    retry_policy: RetryPolicy = RetryPolicy()

    def __init__(
        self,
        auth: SocialMediaAuthManager,
        http: AsyncHttpClient | None = None,
        rate_limiter: AsyncRateLimiter | None = None,
    ):
        self.auth = auth
        self.http = http or AsyncHttpClient()
        self.rate_limiter = rate_limiter or AsyncRateLimiter(self.rate_limit)

    @abc.abstractmethod
    def profile_url(self, username: str) -> str:
        raise NotImplementedError

    @abc.abstractmethod
    async def fetch_profile(self, username: str) -> NormalizedProfile | None:
        raise NotImplementedError

    async def fetch_posts(self, username: str, max_items: int = 50) -> list[NormalizedPost]:
        return []

    async def _limited(self, fn):
        await self.rate_limiter.acquire()
        return await with_retry(fn, self.retry_policy)

    def _token(self) -> str | None:
        return self.auth.get_token_round_robin(self.platform)

    def _raise_for_status(self, status: int, context: str) -> None:
        if status == 404:
            raise NotFoundError(context)
        if status >= 400:
            raise SocialClientError(f"{self.platform}: HTTP {status} - {context}")

    def _int(self, value: Any) -> int | None:
        try:
            if value is None:
                return None
            return int(value)
        except Exception:
            return None
