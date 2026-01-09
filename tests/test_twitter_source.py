"""Tests for Twitter source integration."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from osint.core.models import SocialPlatform, SocialProfile
from osint.sources.twitter_source import TwitterSource


@pytest.fixture
def mock_twitter_config():
    """Mock Twitter configuration."""
    return {
        "bearer_token": "test_bearer_token",
        "rate_limit": 450,
        "cache_enabled": False,
    }


@pytest.fixture
def mock_twitter_response():
    """Mock Twitter API response."""
    return {
        "data": {
            "id": "123456789",
            "name": "Test User",
            "username": "testuser",
            "description": "Test bio",
            "profile_image_url": "https://example.com/avatar.jpg",
            "verified": True,
            "created_at": "2020-01-01T00:00:00.000Z",
            "location": "San Francisco",
            "url": "https://example.com",
            "public_metrics": {
                "followers_count": 1000,
                "following_count": 500,
                "tweet_count": 100,
            },
        }
    }


@pytest.fixture
def mock_tweets_response():
    """Mock Twitter tweets response."""
    return {
        "data": [
            {
                "id": "111",
                "text": "This is a test tweet #test @mention",
                "created_at": "2023-01-01T12:00:00.000Z",
                "public_metrics": {
                    "like_count": 10,
                    "retweet_count": 5,
                    "reply_count": 2,
                },
                "entities": {
                    "hashtags": [{"tag": "test"}],
                    "mentions": [{"username": "mention"}],
                },
            }
        ]
    }


def test_twitter_source_init(mock_twitter_config):
    """Test TwitterSource initialization."""
    source = TwitterSource(mock_twitter_config)
    assert source._bearer_token == "test_bearer_token"
    assert source._rate_limit_default == 450


@patch("osint.sources.twitter_source.tweepy")
def test_validate_credentials(mock_tweepy, mock_twitter_config):
    """Test credential validation."""
    mock_client = MagicMock()
    mock_client.get_me.return_value.data = MagicMock(id="123")
    mock_tweepy.Client.return_value = mock_client

    source = TwitterSource(mock_twitter_config)
    assert source.validate_credentials() is True


@patch("osint.sources.twitter_source.tweepy")
def test_get_profile(mock_tweepy, mock_twitter_config, mock_twitter_response):
    """Test getting user profile."""
    mock_client = MagicMock()
    mock_client.get_user.return_value = type('Response', (), {'data': type('User', (), mock_twitter_response['data'])})()
    mock_tweepy.Client.return_value = mock_client

    source = TwitterSource(mock_twitter_config)
    profile = source.get_profile("testuser")

    assert isinstance(profile, SocialProfile)
    assert profile.platform == SocialPlatform.TWITTER
    assert profile.username == "testuser"
    assert profile.display_name == "Test User"
    assert profile.follower_count == 1000
    assert profile.verified is True


@patch("osint.sources.twitter_source.tweepy")
def test_get_posts(mock_tweepy, mock_twitter_config, mock_tweets_response):
    """Test getting user posts."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.data = [
        type('Tweet', (), tweet) for tweet in mock_tweets_response['data']
    ]
    mock_client.get_users_tweets.return_value = mock_response
    mock_tweepy.Client.return_value = mock_client

    source = TwitterSource(mock_twitter_config)
    posts = source.get_posts("123456789", limit=10)

    assert len(posts) == 1
    assert posts[0].platform == SocialPlatform.TWITTER
    assert posts[0].text == "This is a test tweet #test @mention"
    assert "#test" in posts[0].hashtags


@patch("osint.sources.twitter_source.tweepy")
def test_get_followers(mock_tweepy, mock_twitter_config):
    """Test getting followers."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.data = [
        type('User', (), {
            'id': '222',
            'username': 'follower1',
            'name': 'Follower One'
        })
    ]
    mock_client.get_users_followers.return_value = mock_response
    mock_tweepy.Client.return_value = mock_client

    source = TwitterSource(mock_twitter_config)
    followers = source.get_followers("123456789", limit=10)

    assert len(followers) == 1
    assert followers[0].username == "follower1"


@patch("osint.sources.twitter_source.tweepy")
def test_search_user(mock_tweepy, mock_twitter_config, mock_twitter_response):
    """Test searching for users."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.data = [
        type('User', (), {
            'id': '123',
            'username': 'testuser',
            'name': 'Test User',
            'verified': True
        })
    ]
    mock_client.search_users.return_value = mock_response
    mock_tweepy.Client.return_value = mock_client

    source = TwitterSource(mock_twitter_config)
    users = source.search_user("test")

    assert len(users) == 1
    assert users[0].username == "testuser"


@patch("osint.sources.twitter_source.tweepy")
def test_user_not_found(mock_tweepy, mock_twitter_config):
    """Test handling of user not found error."""
    import tweepy

    mock_client = MagicMock()
    mock_client.get_user.side_effect = tweepy.NotFound("Not found")
    mock_tweepy.Client.return_value = mock_client
    mock_tweepy.NotFound = tweepy.NotFound

    source = TwitterSource(mock_twitter_config)

    with pytest.raises(ValueError, match="User .* not found"):
        source.get_profile("nonexistentuser")


def test_engagement_metrics_calculation():
    """Test engagement metrics calculation."""
    config = {"bearer_token": "test", "cache_enabled": False}
    source = TwitterSource(config)

    from osint.core.models import Post, SocialProfile

    profile = SocialProfile(
        platform=SocialPlatform.TWITTER,
        user_id="123",
        username="test",
        display_name="Test",
        bio="Test",
        profile_url="https://twitter.com/test",
        profile_picture_url="https://example.com/pic.jpg",
        follower_count=1000,
    )

    posts = [
        Post(
            id="1",
            platform=SocialPlatform.TWITTER,
            text="Test post",
            timestamp=None,
            likes=100,
            shares=50,
            comments=25,
        ),
        Post(
            id="2",
            platform=SocialPlatform.TWITTER,
            text="Another post",
            timestamp=None,
            likes=200,
            shares=100,
            comments=50,
        ),
    ]

    metrics = source.get_engagement_metrics(profile, posts)

    assert metrics.total_engagement == 525
    assert metrics.avg_engagement_rate > 0
