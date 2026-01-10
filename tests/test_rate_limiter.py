"""Tests for rate limiter."""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from osint.core.rate_limiter import (
    RateLimiter,
    RateLimitConfig,
    RateLimitStatus,
    RequestEntry,
)


def test_rate_limiter_init():
    """Test RateLimiter initialization."""
    limiter = RateLimiter()
    assert "twitter" in limiter._configs
    assert "facebook" in limiter._configs
    assert "linkedin" in limiter._configs
    assert "instagram" in limiter._configs


def test_acquire_request():
    """Test acquiring a request slot."""
    limiter = RateLimiter()
    limiter.acquire("twitter")
    limiter.record_request("twitter", "default", True, 0.5)

    status = limiter.get_status("twitter")
    assert status is not None
    assert status.requests_made == 1


def test_rate_limit_enforcement():
    """Test that rate limits are enforced."""
    config = RateLimitConfig(requests_per_window=5, window_seconds=1)
    limiter = RateLimiter()
    limiter.configure_platform("test_platform", config)

    for _ in range(5):
        limiter.acquire("test_platform")

    with pytest.raises(Exception):
        limiter.acquire("test_platform")


def test_window_reset():
    """Test that request window resets after time passes."""
    import time

    config = RateLimitConfig(requests_per_window=2, window_seconds=1)
    limiter = RateLimiter()
    limiter.configure_platform("test_platform", config)

    limiter.acquire("test_platform")
    limiter.record_request("test_platform", "default", True, 0.1)

    limiter.acquire("test_platform")
    limiter.record_request("test_platform", "default", True, 0.1)

    time.sleep(1.1)

    limiter.acquire("test_platform")
    limiter.record_request("test_platform", "default", True, 0.1)

    status = limiter.get_status("test_platform")
    assert status.requests_made == 3


def test_record_request():
    """Test recording request metrics."""
    limiter = RateLimiter()
    limiter.acquire("twitter")
    limiter.record_request("twitter", "get_profile", True, 1.5)

    status = limiter.get_status("twitter")
    assert status.requests_made == 1


def test_record_failed_request():
    """Test recording failed request."""
    limiter = RateLimiter()
    limiter.acquire("twitter")
    limiter.record_request("twitter", "get_profile", False, 0.5)

    stats = limiter.get_statistics()
    assert stats["total_errors"]["twitter"] == 1


def test_cooldown_on_high_error_rate():
    """Test that cooldown is triggered on high error rate."""
    config = RateLimitConfig(
        requests_per_window=10,
        window_seconds=60,
        cooldown_seconds=10,
    )
    limiter = RateLimiter()
    limiter.configure_platform("test_platform", config)

    for _ in range(5):
        limiter.acquire("test_platform")
        limiter.record_request("test_platform", "default", False, 0.1)

    status = limiter.get_status("test_platform")
    assert status.in_cooldown is True


def test_get_all_statuses():
    """Test getting all platform statuses."""
    limiter = RateLimiter()
    limiter.acquire("twitter")
    limiter.record_request("twitter", "default", True, 0.1)

    limiter.acquire("facebook")
    limiter.record_request("facebook", "default", True, 0.1)

    all_statuses = limiter.get_all_statuses()

    assert "twitter" in all_statuses
    assert "facebook" in all_statuses
    assert "linkedin" in all_statuses
    assert "instagram" in all_statuses


def test_reset_platform():
    """Test resetting a specific platform."""
    limiter = RateLimiter()
    limiter.acquire("twitter")
    limiter.record_request("twitter", "default", True, 0.1)

    limiter.reset("twitter")

    status = limiter.get_status("twitter")
    assert status.requests_made == 0


def test_reset_all():
    """Test resetting all platforms."""
    limiter = RateLimiter()

    for platform in ["twitter", "facebook", "linkedin", "instagram"]:
        limiter.acquire(platform)
        limiter.record_request(platform, "default", True, 0.1)

    limiter.reset_all()

    for platform in ["twitter", "facebook", "linkedin", "instagram"]:
        status = limiter.get_status(platform)
        assert status.requests_made == 0


def test_get_statistics():
    """Test getting usage statistics."""
    limiter = RateLimiter()

    for _ in range(10):
        limiter.acquire("twitter")
        limiter.record_request("twitter", "default", True, 0.1)

    for _ in range(5):
        limiter.acquire("twitter")
        limiter.record_request("twitter", "default", False, 0.1)

    stats = limiter.get_statistics()

    assert stats["total_requests"]["twitter"] == 15
    assert stats["total_errors"]["twitter"] == 5
    assert "error_rates" in stats
    assert "statuses" in stats


def test_configure_custom_platform():
    """Test configuring a custom platform."""
    limiter = RateLimiter()

    custom_config = RateLimitConfig(
        requests_per_window=100,
        window_seconds=3600,
        burst_limit=10,
        cooldown_seconds=60,
    )

    limiter.configure_platform("custom", custom_config)

    assert "custom" in limiter._configs
    assert limiter._configs["custom"].requests_per_window == 100


def test_burst_limit():
    """Test burst limit enforcement."""
    config = RateLimitConfig(
        requests_per_window=100,
        window_seconds=60,
        burst_limit=3,
    )
    limiter = RateLimiter()
    limiter.configure_platform("test_platform", config)

    for _ in range(3):
        limiter.acquire("test_platform")

    import time

    with pytest.raises(Exception):
        limiter.acquire("test_platform")

    time.sleep(1)
    limiter.acquire("test_platform")


def test_rate_limit_status_to_dict():
    """Test RateLimitStatus serialization."""
    from osint.core.rate_limiter import RateLimitStatus

    status = RateLimitStatus(
        platform="twitter",
        requests_made=10,
        requests_remaining=440,
        window_start=datetime.now() - timedelta(seconds=100),
        window_end=datetime.now(),
        reset_at=datetime.now() + timedelta(seconds=800),
    )

    status_dict = status.to_dict()

    assert status_dict["platform"] == "twitter"
    assert status_dict["requests_made"] == 10
    assert status_dict["requests_remaining"] == 440
    assert "window_start" in status_dict
    assert "reset_at" in status_dict
