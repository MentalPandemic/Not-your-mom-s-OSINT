from __future__ import annotations

import json
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from osint.core.models import EngagementMetrics, Post, SocialPlatform, SocialProfile

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class RateLimitInfo:
    remaining: int
    reset_at: datetime | None
    limit: int


@dataclass(slots=True)
class User:
    id: str
    username: str
    display_name: str
    profile_url: str | None = None
    metadata: dict[str, Any] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "username": self.username,
            "display_name": self.display_name,
            "profile_url": self.profile_url,
            "metadata": self.metadata or {},
        }


class APIClient(ABC):
    """Abstract base class for social media API clients."""

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        self._config = config or {}
        self._cache_enabled = self._config.get("cache_enabled", True)
        self._cache_dir = Path(self._config.get("cache_dir", "~/.osint_cache")).expanduser()
        self._rate_limits: dict[str, RateLimitInfo] = {}

        if self._cache_enabled:
            self._cache_dir.mkdir(parents=True, exist_ok=True)

    @abstractmethod
    def get_profile(self, identifier: str) -> SocialProfile:
        """Get user profile by username or ID."""
        raise NotImplementedError

    @abstractmethod
    def get_posts(self, user_id: str, limit: int = 100) -> list[Post]:
        """Get posts for a user."""
        raise NotImplementedError

    @abstractmethod
    def get_followers(self, user_id: str, limit: int = 100) -> list[User]:
        """Get followers for a user."""
        raise NotImplementedError

    @abstractmethod
    def search_user(self, query: str) -> list[User]:
        """Search for users."""
        raise NotImplementedError

    @abstractmethod
    def validate_credentials(self) -> bool:
        """Validate API credentials."""
        raise NotImplementedError

    @abstractmethod
    def handle_rate_limiting(self) -> None:
        """Handle rate limiting and wait if necessary."""
        raise NotImplementedError

    def cache_response(self, key: str, data: Any, ttl_seconds: int = 3600) -> None:
        """Cache a response."""
        if not self._cache_enabled:
            return

        cache_file = self._cache_dir / f"{key}.json"
        cache_data = {
            "data": data,
            "expires_at": (datetime.now().timestamp() + ttl_seconds),
        }

        try:
            cache_file.write_text(json.dumps(cache_data), encoding="utf-8")
        except Exception as e:
            logger.warning(f"Failed to cache response: {e}")

    def get_cached_response(self, key: str) -> Any | None:
        """Get cached response if valid."""
        if not self._cache_enabled:
            return None

        cache_file = self._cache_dir / f"{key}.json"

        if not cache_file.exists():
            return None

        try:
            cache_data = json.loads(cache_file.read_text(encoding="utf-8"))
            expires_at = cache_data.get("expires_at", 0)

            if datetime.now().timestamp() > expires_at:
                cache_file.unlink()
                return None

            return cache_data.get("data")
        except Exception as e:
            logger.warning(f"Failed to read cache: {e}")
            return None

    def _retry_with_backoff(
        self,
        func: callable,
        max_retries: int = 3,
        base_delay: float = 1.0,
    ) -> Any:
        """Retry function with exponential backoff."""
        last_error = None

        for attempt in range(max_retries):
            try:
                return func()
            except Exception as e:
                last_error = e
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)
                    delay = min(delay, 32.0)
                    logger.debug(f"Retry {attempt + 1}/{max_retries} after {delay:.2f}s")
                    time.sleep(delay)
                else:
                    raise last_error from e

        raise last_error

    def _update_rate_limit(self, endpoint: str, info: RateLimitInfo) -> None:
        """Update rate limit information for an endpoint."""
        self._rate_limits[endpoint] = info

    def _check_rate_limit(self, endpoint: str) -> bool:
        """Check if we can make a request to an endpoint."""
        info = self._rate_limits.get(endpoint)
        if not info:
            return True

        if info.remaining <= 0 and info.reset_at:
            now = datetime.now()
            if now < info.reset_at:
                wait_seconds = (info.reset_at - now).total_seconds()
                logger.info(f"Rate limit reached. Waiting {wait_seconds:.0f}s")
                time.sleep(wait_seconds)
                return True
            else:
                info.remaining = info.limit

        return True

    def _get_cache_key(self, prefix: str, identifier: str) -> str:
        """Generate a cache key."""
        return f"{prefix}_{self.__class__.__name__.lower()}_{identifier}"
