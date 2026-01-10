"""Tests for profile analyzer."""

from __future__ import annotations

from datetime import datetime

import pytest

from osint.core.models import SocialPlatform, SocialProfile
from osint.core.profile_analyzer import ProfileAnalyzer


@pytest.fixture
def sample_profile():
    """Create a sample profile for testing."""
    from osint.core.models import Post

    return SocialProfile(
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
        posts=[
            Post(
                id="1",
                platform=SocialPlatform.TWITTER,
                text="This is a positive tweet #happy #awesome",
                timestamp=datetime(2023, 1, 1, 10, 0),
                likes=100,
                shares=50,
                comments=20,
                hashtags=["happy", "awesome"],
                mentions=["@friend"],
                sentiment=0.5,
            ),
            Post(
                id="2",
                platform=SocialPlatform.TWITTER,
                text="Another positive post #test @test",
                timestamp=datetime(2023, 1, 2, 14, 0),
                likes=50,
                shares=25,
                comments=10,
                hashtags=["test"],
                mentions=["@test"],
                sentiment=0.3,
            ),
            Post(
                id="3",
                platform=SocialPlatform.TWITTER,
                text="A negative tweet #sad",
                timestamp=datetime(2023, 1, 3, 8, 0),
                likes=10,
                shares=5,
                comments=5,
                hashtags=["sad"],
                mentions=[],
                sentiment=-0.4,
            ),
        ],
    )


def test_analyze_engagement(sample_profile):
    """Test engagement analysis."""
    analyzer = ProfileAnalyzer()
    engagement = analyzer.analyze_engagement(sample_profile)

    assert engagement is not None
    assert engagement.total_engagement == 295
    assert engagement.avg_engagement_rate > 0
    assert engagement.post_frequency > 0


def test_analyze_sentiment(sample_profile):
    """Test sentiment analysis."""
    analyzer = ProfileAnalyzer()
    sentiment = analyzer.analyze_sentiment(sample_profile.posts)

    assert sentiment.avg_sentiment > 0
    assert sentiment.positive_count == 2
    assert sentiment.negative_count == 1
    assert sentiment.neutral_count == 0
    assert sentiment.sentiment_distribution["positive"] > 0.5


def test_analyze_activity_pattern(sample_profile):
    """Test activity pattern analysis."""
    analyzer = ProfileAnalyzer()
    activity = analyzer.analyze_activity_pattern(sample_profile.posts)

    assert activity.avg_posts_per_day > 0
    assert activity.most_active_hour in {8, 10, 14}
    assert len(activity.peak_hours) > 0
    assert len(activity.peak_days) > 0


def test_analyze_hashtags(sample_profile):
    """Test hashtag analysis."""
    analyzer = ProfileAnalyzer()
    hashtags = analyzer.analyze_hashtags(sample_profile.posts)

    assert hashtags["total_unique_hashtags"] == 3
    assert hashtags["total_hashtag_mentions"] == 4
    assert hashtags["avg_hashtags_per_post"] > 1
    assert len(hashtags["top_hashtags"]) > 0


def test_analyze_mentions(sample_profile):
    """Test mention analysis."""
    analyzer = ProfileAnalyzer()
    mentions = analyzer.analyze_mentions(sample_profile.posts)

    assert mentions["total_unique_mentions"] == 2
    assert mentions["total_mentions"] == 2
    assert mentions["avg_mentions_per_post"] > 0


def test_calculate_influence_score(sample_profile):
    """Test influence score calculation."""
    analyzer = ProfileAnalyzer()
    influence = analyzer.calculate_influence_score(sample_profile)

    assert influence.score > 0
    assert 0 <= influence.normalized_score <= 100
    assert influence.rank in ["Very Low", "Low", "Medium", "High", "Very High"]
    assert "followers" in influence.factors
    assert "engagement" in influence.factors


def test_detect_bot_normal_profile(sample_profile):
    """Test bot detection for normal profile."""
    analyzer = ProfileAnalyzer()
    bot_detection = analyzer.detect_bot(sample_profile)

    assert bot_detection.is_bot is False
    assert bot_detection.confidence < 60
    assert len(bot_detection.indicators) == 0


def test_detect_bot_suspicious_profile():
    """Test bot detection for suspicious profile."""
    from osint.core.models import Post

    analyzer = ProfileAnalyzer()

    bot_profile = SocialProfile(
        platform=SocialPlatform.TWITTER,
        user_id="999",
        username="botuser",
        display_name="Bot User",
        bio="Bot",
        profile_url="https://twitter.com/botuser",
        profile_picture_url=None,
        follower_count=10,
        following_count=10000,
        post_count=5000,
        verified=False,
        created_date=datetime(2023, 1, 1),
        posts=[
            Post(
                id=str(i),
                platform=SocialPlatform.TWITTER,
                text="Check this out!" * 5,
                timestamp=datetime(2023, 1, 1),
                likes=1,
                shares=0,
                comments=0,
                sentiment=0.0,
            )
            for i in range(100)
        ],
    )

    bot_detection = analyzer.detect_bot(bot_profile)

    assert bot_detection.is_bot is True or bot_detection.confidence > 50
    assert len(bot_detection.indicators) > 0


def test_compare_profiles():
    """Test profile comparison."""
    from osint.core.models import Post

    analyzer = ProfileAnalyzer()

    profile1 = SocialProfile(
        platform=SocialPlatform.TWITTER,
        user_id="1",
        username="user1",
        display_name="User One",
        bio="Bio",
        profile_url="https://twitter.com/user1",
        profile_picture_url=None,
        follower_count=1000,
        following_count=500,
        post_count=100,
        verified=True,
    )

    profile2 = SocialProfile(
        platform=SocialPlatform.TWITTER,
        user_id="2",
        username="user2",
        display_name="User Two",
        bio="Bio",
        profile_url="https://twitter.com/user2",
        profile_picture_url=None,
        follower_count=2000,
        following_count=1000,
        post_count=200,
        verified=False,
    )

    comparison = analyzer.compare_profiles([profile1, profile2])

    assert "platforms" in comparison
    assert "usernames" in comparison
    assert "metrics" in comparison
    assert "most_engaging" in comparison


def test_analyze_empty_profile():
    """Test analysis with empty profile."""
    analyzer = ProfileAnalyzer()

    empty_profile = SocialProfile(
        platform=SocialPlatform.TWITTER,
        user_id="123",
        username="empty",
        display_name="Empty",
        bio="",
        profile_url="https://twitter.com/empty",
        profile_picture_url=None,
        follower_count=0,
        following_count=0,
        post_count=0,
        verified=False,
        posts=[],
    )

    engagement = analyzer.analyze_engagement(empty_profile)
    assert engagement is None

    sentiment = analyzer.analyze_sentiment([])
    assert sentiment.avg_sentiment == 0.0
    assert sentiment.positive_count == 0
    assert sentiment.negative_count == 0
