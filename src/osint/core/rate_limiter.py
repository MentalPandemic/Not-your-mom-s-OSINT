from __future__ import annotations

import json
import logging
import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class RateLimitConfig:
    """Rate limit configuration for a platform."""
    requests_per_window: int
    window_seconds: int
    burst_limit: int = 0
    cooldown_seconds: int = 0


@dataclass(slots=True)
class RateLimitStatus:
    """Current rate limit status for a platform."""
    platform: str
    requests_made: int
    requests_remaining: int
    window_start: datetime
    window_end: datetime
    reset_at: datetime
    in_cooldown: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "platform": self.platform,
            "requests_made": self.requests_made,
            "requests_remaining": self.requests_remaining,
            "window_start": self.window_start.isoformat(),
            "window_end": self.window_end.isoformat(),
            "reset_at": self.reset_at.isoformat(),
            "in_cooldown": self.in_cooldown,
        }


@dataclass(slots=True)
class RequestEntry:
    """Entry for tracking individual requests."""
    timestamp: datetime
    endpoint: str
    success: bool
    response_time: float


class RateLimiter:
    """Intelligent rate limiting manager for API requests."""

    DEFAULT_CONFIGS = {
        "twitter": RateLimitConfig(
            requests_per_window=450,
            window_seconds=900,
            burst_limit=50,
            cooldown_seconds=60,
        ),
        "facebook": RateLimitConfig(
            requests_per_window=200,
            window_seconds=600,
            burst_limit=30,
            cooldown_seconds=120,
        ),
        "linkedin": RateLimitConfig(
            requests_per_window=100,
            window_seconds=600,
            burst_limit=20,
            cooldown_seconds=300,
        ),
        "instagram": RateLimitConfig(
            requests_per_window=200,
            window_seconds=3600,
            burst_limit=20,
            cooldown_seconds=300,
        ),
    }

    def __init__(self, config_path: Path | None = None) -> None:
        self._config_path = config_path
        self._configs: dict[str, RateLimitConfig] = dict(self.DEFAULT_CONFIGS)
        self._request_windows: dict[str, deque[RequestEntry]] = defaultdict(deque)
        self._cooldowns: dict[str, datetime] = {}
        self._lock = threading.RLock()
        self._total_requests: dict[str, int] = defaultdict(int)
        self._total_errors: dict[str, int] = defaultdict(int)
        self._request_queue: dict[str, list[RequestEntry]] = defaultdict(list)

        if config_path and config_path.exists():
            self._load_config()

    def configure_platform(self, platform: str, config: RateLimitConfig) -> None:
        """Configure rate limits for a platform."""
        with self._lock:
            self._configs[platform] = config
            self._save_config()

    def acquire(self, platform: str, endpoint: str = "default") -> None:
        """Acquire permission to make a request."""
        with self._lock:
            config = self._configs.get(platform)
            if not config:
                logger.warning(f"No rate limit config for platform: {platform}")
                return

            now = datetime.now()

            self._cleanup_old_entries(platform, now)

            self._check_cooldown(platform, now)

            window = self._request_windows[platform]
            requests_in_window = len([e for e in window if e.success])

            if requests_in_window >= config.requests_per_window:
                self._wait_for_window_reset(platform, config, now)
            elif config.burst_limit > 0:
                recent = len(
                    [
                        e
                        for e in window
                        if (now - e.timestamp).total_seconds() < 60
                    ]
                )
                if recent >= config.burst_limit:
                    wait_time = 60 - (now - window[-1].timestamp).total_seconds()
                    if wait_time > 0:
                        logger.info(f"Burst limit reached for {platform}. Waiting {wait_time:.1f}s")
                        time.sleep(wait_time)

    def record_request(
        self,
        platform: str,
        endpoint: str,
        success: bool,
        response_time: float,
    ) -> None:
        """Record a completed request."""
        with self._lock:
            entry = RequestEntry(
                timestamp=datetime.now(),
                endpoint=endpoint,
                success=success,
                response_time=response_time,
            )

            self._request_windows[platform].append(entry)
            self._total_requests[platform] += 1

            if not success:
                self._total_errors[platform] += 1
                error_rate = self._total_errors[platform] / self._total_requests[platform]

                if error_rate > 0.3:
                    self._enter_cooldown(platform)

    def get_status(self, platform: str) -> RateLimitStatus | None:
        """Get current rate limit status for a platform."""
        with self._lock:
            config = self._configs.get(platform)
            if not config:
                return None

            now = datetime.now()
            self._cleanup_old_entries(platform, now)

            window = self._request_windows[platform]
            requests_made = len([e for e in window if e.success])

            window_start = now - timedelta(seconds=config.window_seconds)
            window_end = now
            reset_at = now + timedelta(seconds=config.window_seconds)

            if window:
                reset_at = window[0].timestamp + timedelta(seconds=config.window_seconds)

            in_cooldown = platform in self._cooldowns and now < self._cooldowns[platform]

            return RateLimitStatus(
                platform=platform,
                requests_made=requests_made,
                requests_remaining=max(0, config.requests_per_window - requests_made),
                window_start=window_start,
                window_end=window_end,
                reset_at=reset_at,
                in_cooldown=in_cooldown,
            )

    def get_all_statuses(self) -> dict[str, RateLimitStatus]:
        """Get rate limit status for all platforms."""
        with self._lock:
            return {
                platform: status
                for platform in self._configs.keys()
                if (status := self.get_status(platform))
            }

    def reset(self, platform: str) -> None:
        """Reset rate limit tracking for a platform."""
        with self._lock:
            self._request_windows[platform].clear()
            if platform in self._cooldowns:
                del self._cooldowns[platform]
            logger.info(f"Reset rate limiter for platform: {platform}")

    def reset_all(self) -> None:
        """Reset rate limit tracking for all platforms."""
        with self._lock:
            for platform in self._configs.keys():
                self.reset(platform)

    def get_statistics(self) -> dict[str, Any]:
        """Get usage statistics."""
        with self._lock:
            stats = {
                "total_requests": dict(self._total_requests),
                "total_errors": dict(self._total_errors),
                "error_rates": {},
                "statuses": {},
            }

            for platform in self._configs.keys():
                total = self._total_requests.get(platform, 0)
                errors = self._total_errors.get(platform, 0)
                error_rate = (errors / total * 100) if total > 0 else 0
                stats["error_rates"][platform] = error_rate

                status = self.get_status(platform)
                if status:
                    stats["statuses"][platform] = status.to_dict()

            return stats

    def _cleanup_old_entries(self, platform: str, now: datetime) -> None:
        """Remove old request entries from the window."""
        config = self._configs.get(platform)
        if not config:
            return

        window = self._request_windows[platform]
        cutoff = now - timedelta(seconds=config.window_seconds)

        while window and window[0].timestamp < cutoff:
            window.popleft()

    def _check_cooldown(self, platform: str, now: datetime) -> None:
        """Check if platform is in cooldown and wait if necessary."""
        if platform in self._cooldowns:
            cooldown_end = self._cooldowns[platform]
            if now < cooldown_end:
                wait_time = (cooldown_end - now).total_seconds()
                logger.info(f"Platform {platform} in cooldown. Waiting {wait_time:.1f}s")
                time.sleep(wait_time)
            else:
                del self._cooldowns[platform]

    def _enter_cooldown(self, platform: str) -> None:
        """Enter cooldown mode for a platform."""
        config = self._configs.get(platform)
        if config and config.cooldown_seconds > 0:
            cooldown_end = datetime.now() + timedelta(seconds=config.cooldown_seconds)
            self._cooldowns[platform] = cooldown_end
            logger.warning(f"Entering cooldown for {platform} until {cooldown_end}")

    def _wait_for_window_reset(self, platform: str, config: RateLimitConfig, now: datetime) -> None:
        """Wait for the rate limit window to reset."""
        window = self._request_windows[platform]
        if window:
            reset_time = window[0].timestamp + timedelta(seconds=config.window_seconds)
            wait_seconds = max(0, (reset_time - now).total_seconds())
            logger.info(
                f"Rate limit reached for {platform}. "
                f"Waiting {wait_seconds:.1f}s for window reset"
            )
            time.sleep(wait_seconds)

    def _save_config(self) -> None:
        """Save configuration to file."""
        if not self._config_path:
            return

        try:
            config_data = {}
            for platform, cfg in self._configs.items():
                config_data[platform] = {
                    "requests_per_window": cfg.requests_per_window,
                    "window_seconds": cfg.window_seconds,
                    "burst_limit": cfg.burst_limit,
                    "cooldown_seconds": cfg.cooldown_seconds,
                }

            self._config_path.parent.mkdir(parents=True, exist_ok=True)
            self._config_path.write_text(json.dumps(config_data, indent=2), encoding="utf-8")
        except Exception as e:
            logger.warning(f"Failed to save rate limiter config: {e}")

    def _load_config(self) -> None:
        """Load configuration from file."""
        if not self._config_path or not self._config_path.exists():
            return

        try:
            config_data = json.loads(self._config_path.read_text(encoding="utf-8"))

            for platform, data in config_data.items():
                self._configs[platform] = RateLimitConfig(
                    requests_per_window=data.get("requests_per_window", 100),
                    window_seconds=data.get("window_seconds", 600),
                    burst_limit=data.get("burst_limit", 0),
                    cooldown_seconds=data.get("cooldown_seconds", 0),
                )
        except Exception as e:
            logger.warning(f"Failed to load rate limiter config: {e}")
