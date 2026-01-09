from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

import facebook

from osint.core.models import EngagementMetrics, Post, SocialPlatform, SocialProfile
from osint.sources.api_client import APIClient, User

logger = logging.getLogger(__name__)


class FacebookSource(APIClient):
    """Facebook Graph API client for OSINT data collection."""

    name = "facebook"

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        super().__init__(config)
        self._access_token = self._config.get("access_token", "")
        self._app_id = self._config.get("app_id", "")
        self._app_secret = self._config.get("app_secret", "")
        self._rate_limit_default = self._config.get("rate_limit", 200)
        self._client: facebook.GraphAPI | None = None

        if self._access_token:
            self._client = facebook.GraphAPI(access_token=self._access_token, version="18.0")

    def validate_credentials(self) -> bool:
        """Validate Facebook API credentials."""
        if not self._client:
            return False

        try:
            self._client.get_object("me")
            return True
        except Exception as e:
            logger.warning(f"Facebook credentials validation failed: {e}")
            return False

    def handle_rate_limiting(self) -> None:
        """Handle rate limiting."""
        pass

    def get_profile(self, identifier: str) -> SocialProfile:
        """Get Facebook user profile by username or ID."""
        cache_key = self._get_cache_key("profile", identifier)
        cached = self.get_cached_response(cache_key)
        if cached:
            return SocialProfile(**cached)

        if not self._client:
            raise RuntimeError("Facebook client not initialized. Check access_token in config.")

        try:
            user_data = self._retry_with_backoff(
                lambda: self._client.get_object(
                    identifier,
                    fields="id,name,username,picture.width(400),about,link,followers_count,accounts_limit",
                )
            )

            profile = SocialProfile(
                platform=SocialPlatform.FACEBOOK,
                user_id=str(user_data.get("id", "")),
                username=user_data.get("username", user_data.get("id", "")),
                display_name=user_data.get("name", ""),
                bio=user_data.get("about", ""),
                profile_url=user_data.get("link", ""),
                profile_picture_url=self._extract_picture_url(user_data.get("picture")),
                follower_count=user_data.get("followers_count", 0),
                metadata={"accounts_limit": user_data.get("accounts_limit")},
            )

            self.cache_response(cache_key, profile.to_dict(), ttl_seconds=86400)
            return profile

        except facebook.GraphAPIError as e:
            if e.type == "OAuthException":
                raise RuntimeError("Unauthorized: Check your Facebook API access token")
            raise ValueError(f"Error fetching Facebook profile: {e.message}")
        except Exception as e:
            logger.error(f"Error fetching Facebook profile: {e}")
            raise

    def get_posts(self, user_id: str, limit: int = 100) -> list[Post]:
        """Get posts for a Facebook user."""
        cache_key = self._get_cache_key("posts", user_id)
        cached = self.get_cached_response(cache_key)
        if cached:
            return [Post(**p) for p in cached]

        if not self._client:
            raise RuntimeError("Facebook client not initialized")

        try:
            posts_data = self._retry_with_backoff(
                lambda: self._client.get_all_connections(
                    user_id,
                    "posts",
                    fields="id,message,created_time,likes.summary(true),comments.summary(true),shares,permalink_url",
                    limit=min(limit, 25),
                )
            )

            posts = []
            count = 0

            for post_data in posts_data:
                if count >= limit:
                    break

                likes_count = 0
                comments_count = 0
                shares_count = 0

                if post_data.get("likes") and post_data["likes"].get("summary"):
                    likes_count = post_data["likes"]["summary"].get("total_count", 0)

                if post_data.get("comments") and post_data["comments"].get("summary"):
                    comments_count = post_data["comments"]["summary"].get("total_count", 0)

                if post_data.get("shares"):
                    shares_count = post_data["shares"].get("count", 0)

                post = Post(
                    id=str(post_data.get("id", "")),
                    platform=SocialPlatform.FACEBOOK,
                    text=post_data.get("message", ""),
                    timestamp=self._parse_facebook_date(post_data.get("created_time")),
                    likes=likes_count,
                    shares=shares_count,
                    comments=comments_count,
                    hashtags=self._extract_hashtags(post_data.get("message", "")),
                    mentions=self._extract_mentions(post_data.get("message", "")),
                    sentiment=self._analyze_sentiment(post_data.get("message", "")),
                    metadata={"permalink_url": post_data.get("permalink_url")},
                )

                posts.append(post)
                count += 1

            self.cache_response(cache_key, [p.to_dict() for p in posts], ttl_seconds=604800)
            return posts

        except facebook.GraphAPIError as e:
            logger.error(f"Error fetching Facebook posts: {e.message}")
            raise
        except Exception as e:
            logger.error(f"Error fetching Facebook posts: {e}")
            raise

    def get_followers(self, user_id: str, limit: int = 100) -> list[User]:
        """Facebook doesn't provide public follower lists for personal profiles."""
        logger.warning("Facebook doesn't provide public follower lists for personal profiles")
        return []

    def search_user(self, query: str) -> list[User]:
        """Search for users by query."""
        cache_key = self._get_cache_key("search", query)
        cached = self.get_cached_response(cache_key)
        if cached:
            return [User(**u) for u in cached]

        if not self._client:
            raise RuntimeError("Facebook client not initialized")

        try:
            search_results = self._retry_with_backoff(
                lambda: self._client.search(
                    type="user",
                    q=query,
                    fields="id,name,picture.width(200)",
                    limit=10,
                )
            )

            if not search_results.get("data"):
                return []

            user_list = [
                User(
                    id=str(user["id"]),
                    username=user["id"],
                    display_name=user["name"],
                    profile_url=f"https://facebook.com/{user['id']}",
                    metadata={"picture_url": self._extract_picture_url(user.get("picture"))},
                )
                for user in search_results["data"][:10]
            ]

            self.cache_response(cache_key, [u.to_dict() for u in user_list], ttl_seconds=3600)
            return user_list

        except facebook.GraphAPIError as e:
            logger.error(f"Error searching Facebook users: {e.message}")
            raise
        except Exception as e:
            logger.error(f"Error searching Facebook users: {e}")
            raise

    def get_page_info(self, page_id: str) -> SocialProfile:
        """Get information for a Facebook page."""
        cache_key = self._get_cache_key("page", page_id)
        cached = self.get_cached_response(cache_key)
        if cached:
            return SocialProfile(**cached)

        if not self._client:
            raise RuntimeError("Facebook client not initialized")

        try:
            page_data = self._retry_with_backoff(
                lambda: self._client.get_object(
                    page_id,
                    fields="id,name,username,picture.width(400),about,link,fan_count,followers_count,talking_about_count",
                )
            )

            profile = SocialProfile(
                platform=SocialPlatform.FACEBOOK,
                user_id=str(page_data.get("id", "")),
                username=page_data.get("username", page_data.get("id", "")),
                display_name=page_data.get("name", ""),
                bio=page_data.get("about", ""),
                profile_url=page_data.get("link", ""),
                profile_picture_url=self._extract_picture_url(page_data.get("picture")),
                follower_count=page_data.get("fan_count", page_data.get("followers_count", 0)),
                metadata={
                    "type": "page",
                    "talking_about_count": page_data.get("talking_about_count", 0),
                },
            )

            self.cache_response(cache_key, profile.to_dict(), ttl_seconds=86400)
            return profile

        except Exception as e:
            logger.error(f"Error fetching Facebook page: {e}")
            raise

    def get_page_posts(self, page_id: str, limit: int = 100) -> list[Post]:
        """Get posts for a Facebook page."""
        return self.get_posts(page_id, limit)

    def _extract_picture_url(self, picture: dict[str, Any] | None) -> str | None:
        """Extract picture URL from Facebook picture object."""
        if not picture:
            return None

        if isinstance(picture, dict):
            if "data" in picture and "url" in picture["data"]:
                return picture["data"]["url"]
            if "url" in picture:
                return picture["url"]

        return None

    def _parse_facebook_date(self, date_str: str | None) -> datetime | None:
        """Parse Facebook date string to datetime."""
        if not date_str:
            return None

        try:
            return datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S%z")
        except ValueError:
            try:
                return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            except Exception:
                return None

    def _extract_hashtags(self, text: str) -> list[str]:
        """Extract hashtags from text."""
        import re

        return re.findall(r"#(\w+)", text)

    def _extract_mentions(self, text: str) -> list[str]:
        """Extract mentions from text."""
        import re

        return re.findall(r"\[([^\]]+)\]", text)

    def _analyze_sentiment(self, text: str) -> float:
        """Analyze sentiment of post text."""
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
