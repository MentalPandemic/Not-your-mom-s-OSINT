"""Tests for social media model classes."""

from __future__ import annotations

from datetime import datetime

import pytest

from osint.core.models import EngagementMetrics, Post, SocialPlatform, SocialProfile


def test_social_profile_creation():
    """Test SocialProfile dataclass creation."""
    profile = SocialProfile(
        platform=SocialPlatform.TWITTER,
        user_id="123",
        username="testuser",
        display_name="Test User",
        bio="Test bio",
        profile_url="https://twitter.com/testuser",
        profile_picture_url="https://example.com/pic.jpg",
        follower_count=1000,
        following_count=500,
        post_count=100,
        verified=True,
        created_date=datetime(2020, 1, 1),
    )

    assert profile.platform == SocialPlatform.TWITTER
    assert profile.user_id == "123"
    assert profile.username == "testuser"
    assert profile.follower_count == 1000
    assert profile.verified is True


def test_social_profile_to_dict():
    """Test SocialProfile serialization."""
    profile = SocialProfile(
        platform=SocialPlatform.INSTAGRAM,
        user_id="456",
        username="instauser",
        display_name="Insta User",
        bio="Insta bio",
        profile_url="https://instagram.com/instauser",
        profile_picture_url=None,
        follower_count=2000,
    )

    profile_dict = profile.to_dict()

    assert profile_dict["platform"] == "instagram"
    assert profile_dict["username"] == "instauser"
    assert profile_dict["verified"] is False
    assert profile_dict["last_update"] is not None


def test_post_creation():
    """Test Post dataclass creation."""
    post = Post(
        id="789",
        platform=SocialPlatform.FACEBOOK,
        text="Test post #hashtag @mention",
        timestamp=datetime(2023, 5, 15, 10, 30),
        likes=100,
        shares=50,
        comments=25,
        hashtags=["hashtag"],
        mentions=["mention"],
        sentiment=0.5,
    )

    assert post.id == "789"
    assert post.platform == SocialPlatform.FACEBOOK
    assert post.likes == 100
    assert post.sentiment == 0.5
    assert "#hashtag" not in post.text


def test_post_to_dict():
    """Test Post serialization."""
    post = Post(
        id="999",
        platform=SocialPlatform.LINKEDIN,
        text="LinkedIn post",
        timestamp=None,
        likes=10,
        shares=5,
        comments=2,
    )

    post_dict = post.to_dict()

    assert post_dict["id"] == "999"
    assert post_dict["platform"] == "linkedin"
    assert post_dict["timestamp"] is None
    assert post_dict["sentiment"] == 0.0


def test_engagement_metrics_creation():
    """Test EngagementMetrics dataclass creation."""
    metrics = EngagementMetrics(
        avg_engagement_rate=5.5,
        total_engagement=1000,
        post_frequency=2.3,
        most_active_hours=["10:00", "14:00"],
        audience_demographics={"age": "25-34"},
    )

    assert metrics.avg_engagement_rate == 5.5
    assert metrics.total_engagement == 1000
    assert metrics.post_frequency == 2.3
    assert len(metrics.most_active_hours) == 2


def test_engagement_metrics_to_dict():
    """Test EngagementMetrics serialization."""
    metrics = EngagementMetrics(
        avg_engagement_rate=3.2,
        total_engagement=500,
        post_frequency=1.5,
    )

    metrics_dict = metrics.to_dict()

    assert metrics_dict["avg_engagement_rate"] == 3.2
    assert metrics_dict["total_engagement"] == 500
    assert metrics_dict["post_frequency"] == 1.5
    assert len(metrics_dict["most_active_hours"]) == 0


def test_social_platform_enum():
    """Test SocialPlatform enum values."""
    assert SocialPlatform.TWITTER.value == "twitter"
    assert SocialPlatform.FACEBOOK.value == "facebook"
    assert SocialPlatform.LINKEDIN.value == "linkedin"
    assert SocialPlatform.INSTAGRAM.value == "instagram"


def test_post_default_values():
    """Test Post default field values."""
    post = Post(
        id="123",
        platform=SocialPlatform.TWITTER,
        text="Test",
        timestamp=None,
    )

    assert post.likes == 0
    assert post.shares == 0
    assert post.comments == 0
    assert post.hashtags == []
    assert post.mentions == []
    assert post.media_urls == []
    assert post.sentiment == 0.0
    assert post.metadata == {}


def test_social_profile_default_values():
    """Test SocialProfile default field values."""
    profile = SocialProfile(
        platform=SocialPlatform.FACEBOOK,
        user_id="123",
        username="test",
        display_name="Test",
        bio="",
        profile_url="https://facebook.com/test",
        profile_picture_url=None,
    )

    assert profile.follower_count == 0
    assert profile.following_count == 0
    assert profile.post_count == 0
    assert profile.verified is False
    assert profile.created_date is None
    assert profile.posts == []
    assert profile.engagement_metrics is None


def test_profile_with_posts():
    """Test SocialProfile with posts."""
    profile = SocialProfile(
        platform=SocialPlatform.TWITTER,
        user_id="123",
        username="test",
        display_name="Test",
        bio="Test",
        profile_url="https://twitter.com/test",
        profile_picture_url=None,
        posts=[
            Post(
                id="1",
                platform=SocialPlatform.TWITTER,
                text="Post 1",
                timestamp=None,
            ),
            Post(
                id="2",
                platform=SocialPlatform.TWITTER,
                text="Post 2",
                timestamp=None,
            ),
        ],
    )

    assert len(profile.posts) == 2
    assert profile.posts[0].text == "Post 1"
    assert profile.posts[1].text == "Post 2"


def test_profile_serialization_with_posts():
    """Test profile serialization includes posts."""
    profile = SocialProfile(
        platform=SocialPlatform.INSTAGRAM,
        user_id="123",
        username="test",
        display_name="Test",
        bio="Test",
        profile_url="https://instagram.com/test",
        profile_picture_url=None,
        posts=[
            Post(
                id="1",
                platform=SocialPlatform.INSTAGRAM,
                text="Post",
                timestamp=None,
            ),
        ],
    )

    profile_dict = profile.to_dict()

    assert "posts" in profile_dict
    assert len(profile_dict["posts"]) == 1
    assert profile_dict["posts"][0]["text"] == "Post"


def test_sentiment_range():
    """Test that sentiment values are in expected range."""
    positive_post = Post(
        id="1",
        platform=SocialPlatform.TWITTER,
        text="Great!",
        timestamp=None,
        sentiment=0.8,
    )

    negative_post = Post(
        id="2",
        platform=SocialPlatform.TWITTER,
        text="Terrible!",
        timestamp=None,
        sentiment=-0.7,
    )

    neutral_post = Post(
        id="3",
        platform=SocialPlatform.TWITTER,
        text="Okay.",
        timestamp=None,
        sentiment=0.0,
    )

    assert -1 <= positive_post.sentiment <= 1
    assert -1 <= negative_post.sentiment <= 1
    assert -1 <= neutral_post.sentiment <= 1
