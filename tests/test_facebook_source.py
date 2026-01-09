"""Tests for Facebook source integration."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from osint.core.models import SocialPlatform
from osint.sources.facebook_source import FacebookSource


@pytest.fixture
def mock_facebook_config():
    """Mock Facebook configuration."""
    return {
        "access_token": "test_access_token",
        "rate_limit": 200,
        "cache_enabled": False,
    }


def test_facebook_source_init(mock_facebook_config):
    """Test FacebookSource initialization."""
    source = FacebookSource(mock_facebook_config)
    assert source._access_token == "test_access_token"
    assert source._rate_limit_default == 200


@patch("osint.sources.facebook_source.facebook")
def test_validate_credentials(mock_facebook, mock_facebook_config):
    """Test credential validation."""
    mock_client = MagicMock()
    mock_client.get_object.return_value = {"id": "123"}
    mock_facebook.GraphAPI.return_value = mock_client

    source = FacebookSource(mock_facebook_config)
    assert source.validate_credentials() is True


def test_extract_hashtags():
    """Test hashtag extraction."""
    source = FacebookSource({})
    text = "This is a #test post with #multiple #hashtags"

    hashtags = source._extract_hashtags(text)

    assert "test" in hashtags
    assert "multiple" in hashtags
    assert "hashtags" in hashtags


def test_extract_mentions():
    """Test mention extraction."""
    source = FacebookSource({})
    text = "Hello @[User One] and @[User Two]"

    mentions = source._extract_mentions(text)

    assert len(mentions) == 2


def test_parse_facebook_date():
    """Test Facebook date parsing."""
    source = FacebookSource({})

    date_str = "2023-01-15T10:30:00+0000"
    result = source._parse_facebook_date(date_str)

    assert result is not None
    assert result.year == 2023
    assert result.month == 1
    assert result.day == 15


def test_sentiment_analysis():
    """Test sentiment analysis."""
    source = FacebookSource({})

    positive = source._analyze_sentiment("I love this!")
    assert positive > 0

    negative = source._analyze_sentiment("I hate this!")
    assert negative < 0

    neutral = source._analyze_sentiment("This is just a fact.")
    assert -0.1 <= neutral <= 0.1


def test_engagement_metrics_calculation():
    """Test engagement metrics calculation."""
    from osint.core.models import SocialProfile, Post

    config = {"access_token": "test", "cache_enabled": False}
    source = FacebookSource(config)

    profile = SocialProfile(
        platform=SocialPlatform.FACEBOOK,
        user_id="123",
        username="test",
        display_name="Test",
        bio="Test",
        profile_url="https://facebook.com/test",
        profile_picture_url=None,
        follower_count=500,
    )

    posts = [
        Post(
            id="1",
            platform=SocialPlatform.FACEBOOK,
            text="Test post",
            timestamp=None,
            likes=50,
            shares=25,
            comments=10,
        ),
    ]

    metrics = source.get_engagement_metrics(profile, posts)

    assert metrics.total_engagement == 85
    assert metrics.avg_engagement_rate > 0
