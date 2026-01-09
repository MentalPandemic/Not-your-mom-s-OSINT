from __future__ import annotations

import logging
import re
from datetime import datetime
from typing import Any

import tweepy

from osint.core.models import EngagementMetrics, Post, SocialPlatform, SocialProfile
from osint.sources.api_client import APIClient, RateLimitInfo, User

logger = logging.getLogger(__name__)


class TwitterSource(APIClient):
    """Twitter/X API v2 client for OSINT data collection."""

    name = "twitter"

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        super().__init__(config)
        self._bearer_token = self._config.get("bearer_token", "")
        self._rate_limit_default = self._config.get("rate_limit", 450)
        self._client: tweepy.Client | None = None

        if self._bearer_token:
            self._client = tweepy.Client(
                bearer_token=self._bearer_token,
                wait_on_rate_limit=True,
            )

    def validate_credentials(self) -> bool:
        """Validate Twitter API credentials."""
        if not self._client:
            return False

        try:
            self._client.get_me()
            return True
        except Exception as e:
            logger.warning(f"Twitter credentials validation failed: {e}")
            return False

    def handle_rate_limiting(self) -> None:
        """Handle rate limiting - tweepy handles this automatically."""
        pass

    def get_profile(self, identifier: str) -> SocialProfile:
        """Get Twitter user profile by username."""
        cache_key = self._get_cache_key("profile", identifier)
        cached = self.get_cached_response(cache_key)
        if cached:
            return SocialProfile(**cached)

        if not self._client:
            raise RuntimeError("Twitter client not initialized. Check bearer_token in config.")

        try:
            user = self._retry_with_backoff(
                lambda: self._client.get_user(
                    username=identifier,
                    user_fields=[
                        "id",
                        "name",
                        "username",
                        "description",
                        "profile_image_url",
                        "public_metrics",
                        "verified",
                        "created_at",
                        "location",
                        "url",
                    ],
                )
            )

            if not user.data:
                raise ValueError(f"User '{identifier}' not found")

            data = user.data

            profile = SocialProfile(
                platform=SocialPlatform.TWITTER,
                user_id=str(data.id),
                username=data.username,
                display_name=data.name,
                bio=data.description or "",
                profile_url=f"https://twitter.com/{data.username}",
                profile_picture_url=data.profile_image_url,
                verified=data.verified or False,
                created_date=data.created_at,
                metadata={
                    "location": data.location,
                    "url": data.url,
                    "public_metrics": data.public_metrics,
                },
            )

            if data.public_metrics:
                profile.follower_count = data.public_metrics.get("followers_count", 0)
                profile.following_count = data.public_metrics.get("following_count", 0)
                profile.post_count = data.public_metrics.get("tweet_count", 0)

            self.cache_response(cache_key, profile.to_dict(), ttl_seconds=86400)
            return profile

        except tweepy.NotFound:
            raise ValueError(f"User '{identifier}' not found on Twitter")
        except tweepy.Unauthorized:
            raise RuntimeError("Unauthorized: Check your Twitter API bearer token")
        except Exception as e:
            logger.error(f"Error fetching Twitter profile: {e}")
            raise

    def get_posts(self, user_id: str, limit: int = 100) -> list[Post]:
        """Get tweets for a user."""
        cache_key = self._get_cache_key("posts", user_id)
        cached = self.get_cached_response(cache_key)
        if cached:
            return [Post(**p) for p in cached]

        if not self._client:
            raise RuntimeError("Twitter client not initialized")

        try:
            tweets = self._retry_with_backoff(
                lambda: self._client.get_users_tweets(
                    id=user_id,
                    max_results=min(limit, 100),
                    tweet_fields=[
                        "id",
                        "text",
                        "created_at",
                        "public_metrics",
                        "entities",
                        "context_annotations",
                    ],
                    exclude=["retweets", "replies"],
                )
            )

            if not tweets.data:
                return []

            posts = []
            for tweet in tweets.data:
                hashtags = []
                mentions = []

                if tweet.entities:
                    hashtags = [h["tag"] for h in tweet.entities.get("hashtags", [])]
                    mentions = [m["username"] for m in tweet.entities.get("mentions", [])]

                metrics = tweet.public_metrics or {}

                post = Post(
                    id=str(tweet.id),
                    platform=SocialPlatform.TWITTER,
                    text=tweet.text,
                    timestamp=tweet.created_at,
                    likes=metrics.get("like_count", 0),
                    shares=metrics.get("retweet_count", 0),
                    comments=metrics.get("reply_count", 0),
                    hashtags=hashtags,
                    mentions=mentions,
                    sentiment=self._analyze_sentiment(tweet.text),
                    metadata={"context_annotations": tweet.context_annotations},
                )

                posts.append(post)

            self.cache_response(cache_key, [p.to_dict() for p in posts], ttl_seconds=604800)
            return posts

        except Exception as e:
            logger.error(f"Error fetching Twitter posts: {e}")
            raise

    def get_followers(self, user_id: str, limit: int = 100) -> list[User]:
        """Get followers for a user."""
        cache_key = self._get_cache_key("followers", user_id)
        cached = self.get_cached_response(cache_key)
        if cached:
            return [User(**u) for u in cached]

        if not self._client:
            raise RuntimeError("Twitter client not initialized")

        try:
            followers = self._retry_with_backoff(
                lambda: self._client.get_users_followers(
                    id=user_id,
                    max_results=min(limit, 1000),
                    user_fields=["id", "name", "username", "profile_image_url"],
                )
            )

            if not followers.data:
                return []

            users = [
                User(
                    id=str(user.id),
                    username=user.username,
                    display_name=user.name,
                    profile_url=f"https://twitter.com/{user.username}",
                )
                for user in followers.data
            ]

            self.cache_response(cache_key, [u.to_dict() for u in users], ttl_seconds=86400)
            return users

        except Exception as e:
            logger.error(f"Error fetching Twitter followers: {e}")
            raise

    def search_user(self, query: str) -> list[User]:
        """Search for users by query."""
        cache_key = self._get_cache_key("search", query)
        cached = self.get_cached_response(cache_key)
        if cached:
            return [User(**u) for u in cached]

        if not self._client:
            raise RuntimeError("Twitter client not initialized")

        try:
            users = self._retry_with_backoff(
                lambda: self._client.search_users(
                    query=query,
                    user_fields=["id", "name", "username", "profile_image_url", "verified"],
                )
            )

            if not users.data:
                return []

            user_list = [
                User(
                    id=str(user.id),
                    username=user.username,
                    display_name=user.name,
                    profile_url=f"https://twitter.com/{user.username}",
                    metadata={"verified": user.verified},
                )
                for user in users.data[:10]
            ]

            self.cache_response(cache_key, [u.to_dict() for u in user_list], ttl_seconds=3600)
            return user_list

        except Exception as e:
            logger.error(f"Error searching Twitter users: {e}")
            raise

    def _analyze_sentiment(self, text: str) -> float:
        """Analyze sentiment of tweet text."""
        try:
            from textblob import TextBlob

            blob = TextBlob(text)
            return blob.sentiment.polarity
        except Exception:
            return 0.0

    def get_engagement_metrics(self, profile: SocialProfile, posts: list[Post]) -> EngagementMetrics:
        """Calculate engagement metrics for a profile."""
        if not posts:
            return EngagementMetrics(avg_engagement_rate=0.0, total_engagement=0, post_frequency=0.0)

        total_engagement = sum(p.likes + p.shares + p.comments for p in posts)
        avg_engagement_rate = total_engagement / len(posts) if posts else 0.0

        follower_count = profile.follower_count or 1
        engagement_rate = (total_engagement / follower_count) * 100

        post_frequency = len(posts) / 30.0 if posts else 0.0

        return EngagementMetrics(
            avg_engagement_rate=engagement_rate,
            total_engagement=total_engagement,
            post_frequency=post_frequency,
        )

    def search_hashtags(self, hashtag: str, limit: int = 100) -> list[Post]:
        """Search for tweets by hashtag."""
        if not self._client:
            raise RuntimeError("Twitter client not initialized")

        try:
            query = f"#{hashtag}"
            tweets = self._retry_with_backoff(
                lambda: self._client.search_recent_tweets(
                    query=query,
                    max_results=min(limit, 100),
                    tweet_fields=[
                        "id",
                        "text",
                        "created_at",
                        "public_metrics",
                        "entities",
                        "author_id",
                    ],
                )
            )

            if not tweets.data:
                return []

            posts = []
            for tweet in tweets.data:
                hashtags = []
                mentions = []

                if tweet.entities:
                    hashtags = [h["tag"] for h in tweet.entities.get("hashtags", [])]
                    mentions = [m["username"] for m in tweet.entities.get("mentions", [])]

                metrics = tweet.public_metrics or {}

                post = Post(
                    id=str(tweet.id),
                    platform=SocialPlatform.TWITTER,
                    text=tweet.text,
                    timestamp=tweet.created_at,
                    likes=metrics.get("like_count", 0),
                    shares=metrics.get("retweet_count", 0),
                    comments=metrics.get("reply_count", 0),
                    hashtags=hashtags,
                    mentions=mentions,
                    sentiment=self._analyze_sentiment(tweet.text),
                    metadata={"author_id": tweet.author_id},
                )

                posts.append(post)

            return posts

        except Exception as e:
            logger.error(f"Error searching Twitter hashtags: {e}")
            raise
