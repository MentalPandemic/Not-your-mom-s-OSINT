from __future__ import annotations

import logging
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from osint.core.models import EngagementMetrics, Post, SocialPlatform, SocialProfile

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class ActivityPattern:
    """Activity pattern analysis results."""
    peak_hours: list[int]
    peak_days: list[str]
    avg_posts_per_day: float
    most_active_hour: int
    most_active_day: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "peak_hours": self.peak_hours,
            "peak_days": self.peak_days,
            "avg_posts_per_day": self.avg_posts_per_day,
            "most_active_hour": self.most_active_hour,
            "most_active_day": self.most_active_day,
        }


@dataclass(slots=True)
class SentimentAnalysis:
    """Sentiment analysis results."""
    avg_sentiment: float
    positive_count: int
    negative_count: int
    neutral_count: int
    sentiment_distribution: dict[str, float]

    def to_dict(self) -> dict[str, Any]:
        return {
            "avg_sentiment": self.avg_sentiment,
            "positive_count": self.positive_count,
            "negative_count": self.negative_count,
            "neutral_count": self.neutral_count,
            "sentiment_distribution": self.sentiment_distribution,
        }


@dataclass(slots=True)
class InfluenceScore:
    """Influence score calculation results."""
    score: float
    normalized_score: float
    factors: dict[str, float]
    rank: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "score": self.score,
            "normalized_score": self.normalized_score,
            "factors": self.factors,
            "rank": self.rank,
        }


@dataclass(slots=True)
class BotDetection:
    """Bot detection analysis results."""
    is_bot: bool
    confidence: float
    indicators: list[str]
    details: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "is_bot": self.is_bot,
            "confidence": self.confidence,
            "indicators": self.indicators,
            "details": self.details,
        }


class ProfileAnalyzer:
    """Analyze social media profiles for insights."""

    def __init__(self) -> None:
        self._sentiment_cache = {}

    def analyze_profile(self, profile: SocialProfile) -> dict[str, Any]:
        """Perform comprehensive profile analysis."""
        results: dict[str, Any] = {}

        results["engagement"] = self.analyze_engagement(profile)
        results["sentiment"] = self.analyze_sentiment(profile.posts)
        results["activity"] = self.analyze_activity_pattern(profile.posts)
        results["hashtags"] = self.analyze_hashtags(profile.posts)
        results["mentions"] = self.analyze_mentions(profile.posts)
        results["influence"] = self.calculate_influence_score(profile)
        results["bot_detection"] = self.detect_bot(profile)

        return results

    def analyze_engagement(self, profile: SocialProfile) -> EngagementMetrics | None:
        """Analyze engagement metrics."""
        if not profile.posts:
            return None

        total_likes = sum(p.likes for p in profile.posts)
        total_shares = sum(p.shares for p in profile.posts)
        total_comments = sum(p.comments for p in profile.posts)
        total_engagement = total_likes + total_shares + total_comments

        avg_engagement = total_engagement / len(profile.posts) if profile.posts else 0.0

        follower_count = profile.follower_count or 1
        engagement_rate = (total_engagement / follower_count) * 100

        if profile.created_date:
            account_age_days = (datetime.now() - profile.created_date).days
            post_frequency = profile.post_count / max(account_age_days, 1)
        else:
            post_frequency = 0.0

        return EngagementMetrics(
            avg_engagement_rate=engagement_rate,
            total_engagement=total_engagement,
            post_frequency=post_frequency,
            most_active_hours=self._get_active_hours(profile.posts),
            audience_demographics=self._estimate_demographics(profile),
        )

    def analyze_sentiment(self, posts: list[Post]) -> SentimentAnalysis:
        """Analyze sentiment of posts."""
        if not posts:
            return SentimentAnalysis(
                avg_sentiment=0.0,
                positive_count=0,
                negative_count=0,
                neutral_count=0,
                sentiment_distribution={"positive": 0.0, "negative": 0.0, "neutral": 0.0},
            )

        sentiments = [p.sentiment for p in posts if p.sentiment != 0]
        all_sentiments = [p.sentiment for p in posts]

        avg_sentiment = sum(all_sentiments) / len(all_sentiments) if all_sentiments else 0.0

        positive_count = sum(1 for s in sentiments if s > 0.1)
        negative_count = sum(1 for s in sentiments if s < -0.1)
        neutral_count = sum(1 for s in sentiments if -0.1 <= s <= 0.1)

        total = len(sentiments) or 1
        sentiment_distribution = {
            "positive": positive_count / total,
            "negative": negative_count / total,
            "neutral": neutral_count / total,
        }

        return SentimentAnalysis(
            avg_sentiment=avg_sentiment,
            positive_count=positive_count,
            negative_count=negative_count,
            neutral_count=neutral_count,
            sentiment_distribution=sentiment_distribution,
        )

    def analyze_activity_pattern(self, posts: list[Post]) -> ActivityPattern:
        """Analyze posting activity patterns."""
        if not posts:
            return ActivityPattern(
                peak_hours=[],
                peak_days=[],
                avg_posts_per_day=0.0,
                most_active_hour=0,
                most_active_day="",
            )

        hour_counts: Counter[int] = Counter()
        day_counts: Counter[str] = Counter()

        for post in posts:
            if post.timestamp:
                hour_counts[post.timestamp.hour] += 1
                day_counts[post.timestamp.strftime("%A")] += 1

        peak_hours = [h for h, _ in hour_counts.most_common(3)]
        peak_days = [d for d, _ in day_counts.most_common(3)]

        most_active_hour = hour_counts.most_common(1)[0][0] if hour_counts else 0
        most_active_day = day_counts.most_common(1)[0][0] if day_counts else ""

        date_range_days = 1
        timestamps = [p.timestamp for p in posts if p.timestamp]
        if timestamps:
            min_date = min(timestamps)
            max_date = max(timestamps)
            date_range_days = max((max_date - min_date).days, 1)

        avg_posts_per_day = len(posts) / date_range_days

        return ActivityPattern(
            peak_hours=peak_hours,
            peak_days=peak_days,
            avg_posts_per_day=avg_posts_per_day,
            most_active_hour=most_active_hour,
            most_active_day=most_active_day,
        )

    def analyze_hashtags(self, posts: list[Post]) -> dict[str, Any]:
        """Analyze hashtag usage."""
        all_hashtags: list[str] = []

        for post in posts:
            all_hashtags.extend(post.hashtags)

        hashtag_counts = Counter(all_hashtags)
        top_hashtags = hashtag_counts.most_common(20)

        return {
            "total_unique_hashtags": len(hashtag_counts),
            "total_hashtag_mentions": len(all_hashtags),
            "avg_hashtags_per_post": len(all_hashtags) / len(posts) if posts else 0.0,
            "top_hashtags": [{"tag": tag, "count": count} for tag, count in top_hashtags],
        }

    def analyze_mentions(self, posts: list[Post]) -> dict[str, Any]:
        """Analyze mention patterns."""
        all_mentions: list[str] = []

        for post in posts:
            all_mentions.extend(post.mentions)

        mention_counts = Counter(all_mentions)
        top_mentions = mention_counts.most_common(20)

        return {
            "total_unique_mentions": len(mention_counts),
            "total_mentions": len(all_mentions),
            "avg_mentions_per_post": len(all_mentions) / len(posts) if posts else 0.0,
            "top_mentions": [{"username": user, "count": count} for user, count in top_mentions],
        }

    def calculate_influence_score(self, profile: SocialProfile) -> InfluenceScore:
        """Calculate an influence score for the profile."""
        factors: dict[str, float] = {}

        follower_score = min(profile.follower_count / 10000, 10.0)
        factors["followers"] = follower_score

        if profile.engagement_metrics:
            engagement_score = min(profile.engagement_metrics.avg_engagement_rate, 10.0)
            factors["engagement"] = engagement_score

            post_frequency_score = min(profile.engagement_metrics.post_frequency * 100, 10.0)
            factors["post_frequency"] = post_frequency_score
        else:
            factors["engagement"] = 0.0
            factors["post_frequency"] = 0.0

        verification_score = 5.0 if profile.verified else 0.0
        factors["verified"] = verification_score

        content_quality_score = 0.0
        if profile.posts:
            avg_post_length = sum(len(p.text) for p in profile.posts) / len(profile.posts)
            content_quality_score = min(avg_post_length / 50, 10.0)
        factors["content_quality"] = content_quality_score

        total_score = sum(factors.values())
        normalized_score = min(total_score / 40.0 * 100, 100.0)

        if normalized_score >= 80:
            rank = "Very High"
        elif normalized_score >= 60:
            rank = "High"
        elif normalized_score >= 40:
            rank = "Medium"
        elif normalized_score >= 20:
            rank = "Low"
        else:
            rank = "Very Low"

        return InfluenceScore(
            score=total_score,
            normalized_score=normalized_score,
            factors=factors,
            rank=rank,
        )

    def detect_bot(self, profile: SocialProfile) -> BotDetection:
        """Detect potential bot indicators."""
        indicators: list[str] = []
        details: dict[str, Any] = {}
        bot_confidence = 0.0

        if profile.follower_count > 0 and profile.following_count > 0:
            ratio = profile.following_count / profile.follower_count
            if ratio > 100:
                indicators.append("High following-to-follower ratio")
                bot_confidence += 30
                details["following_ratio"] = ratio

        if profile.post_count > 0:
            if profile.created_date:
                account_age_days = (datetime.now() - profile.created_date).days
                if account_age_days > 0:
                    posts_per_day = profile.post_count / account_age_days
                    if posts_per_day > 50:
                        indicators.append("Extremely high posting frequency")
                        bot_confidence += 40
                        details["posts_per_day"] = posts_per_day

            if profile.posts:
                texts = [p.text for p in profile.posts if p.text]
                if texts:
                    avg_length = sum(len(t) for t in texts) / len(texts)
                    if avg_length < 20:
                        indicators.append("Very short post length average")
                        bot_confidence += 20
                        details["avg_post_length"] = avg_length

                    text_variance = len(set(texts)) / len(texts)
                    if text_variance < 0.3:
                        indicators.append("Highly repetitive content")
                        bot_confidence += 35
                        details["content_variance"] = text_variance

        if profile.posts:
            sentiment_analysis = self.analyze_sentiment(profile.posts)
            if sentiment_analysis.neutral_count / len(profile.posts) > 0.8:
                indicators.append("Unusually neutral sentiment profile")
                bot_confidence += 15
                details["neutral_ratio"] = sentiment_analysis.neutral_count / len(profile.posts)

        hashtag_analysis = self.analyze_hashtags(profile.posts)
        if hashtag_analysis.get("avg_hashtags_per_post", 0) > 15:
            indicators.append("Excessive hashtag usage")
            bot_confidence += 25
            details["avg_hashtags"] = hashtag_analysis["avg_hashtags_per_post"]

        is_bot = bot_confidence >= 60
        details["confidence_score"] = bot_confidence

        return BotDetection(
            is_bot=is_bot,
            confidence=min(bot_confidence, 100.0),
            indicators=indicators,
            details=details,
        )

    def compare_profiles(self, profiles: list[SocialProfile]) -> dict[str, Any]:
        """Compare multiple profiles."""
        if len(profiles) < 2:
            return {"error": "Need at least 2 profiles to compare"}

        comparison: dict[str, Any] = {
            "platforms": [p.platform.value for p in profiles],
            "usernames": [p.username for p in profiles],
            "metrics": {},
        }

        comparison["metrics"]["followers"] = [
            {"platform": p.platform.value, "username": p.username, "count": p.follower_count}
            for p in profiles
        ]

        comparison["metrics"]["posts"] = [
            {"platform": p.platform.value, "username": p.username, "count": p.post_count}
            for p in profiles
        ]

        engagement_rates = []
        for profile in profiles:
            if profile.engagement_metrics:
                engagement_rates.append(profile.engagement_metrics.avg_engagement_rate)
            else:
                engagement_rates.append(0.0)

        comparison["metrics"]["engagement_rates"] = [
            {"platform": p.platform.value, "username": p.username, "rate": rate}
            for p, rate in zip(profiles, engagement_rates)
        ]

        comparison["highest_followers"] = max(
            comparison["metrics"]["followers"], key=lambda x: x["count"]
        )

        comparison["most_engaging"] = max(
            comparison["metrics"]["engagement_rates"], key=lambda x: x["rate"]
        )

        return comparison

    def _get_active_hours(self, posts: list[Post]) -> list[str]:
        """Get most active posting hours as formatted strings."""
        if not posts:
            return []

        hour_counts: Counter[int] = Counter()
        for post in posts:
            if post.timestamp:
                hour_counts[post.timestamp.hour] += 1

        return [f"{h:02d}:00" for h, _ in hour_counts.most_common(5)]

    def _estimate_demographics(self, profile: SocialProfile) -> dict[str, Any]:
        """Estimate audience demographics (placeholder)."""
        return {
            "age_groups": {},
            "gender": {},
            "location": {},
            "language": {},
        }
