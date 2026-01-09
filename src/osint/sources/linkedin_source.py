from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from linkedin_api import Linkedin
from requests.exceptions import RequestException

from osint.core.models import EngagementMetrics, Post, SocialPlatform, SocialProfile
from osint.sources.api_client import APIClient, User

logger = logging.getLogger(__name__)


class LinkedInSource(APIClient):
    """LinkedIn API client for OSINT data collection."""

    name = "linkedin"

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        super().__init__(config)
        self._username = self._config.get("username", "")
        self._password = self._config.get("password", "")
        self._api_key = self._config.get("api_key", "")
        self._rate_limit_default = self._config.get("rate_limit", 100)
        self._client: Linkedin | None = None

        if self._username and self._password:
            try:
                self._client = Linkedin(self._username, self._password)
            except Exception as e:
                logger.warning(f"Failed to initialize LinkedIn client: {e}")

    def validate_credentials(self) -> bool:
        """Validate LinkedIn API credentials."""
        if not self._client:
            return False

        try:
            profile = self._client.get_profile()
            return bool(profile)
        except Exception as e:
            logger.warning(f"LinkedIn credentials validation failed: {e}")
            return False

    def handle_rate_limiting(self) -> None:
        """Handle rate limiting."""
        pass

    def get_profile(self, identifier: str) -> SocialProfile:
        """Get LinkedIn profile by profile ID or public URL."""
        cache_key = self._get_cache_key("profile", identifier)
        cached = self.get_cached_response(cache_key)
        if cached:
            return SocialProfile(**cached)

        if not self._client:
            raise RuntimeError("LinkedIn client not initialized. Check credentials in config.")

        try:
            profile_data = self._retry_with_backoff(lambda: self._client.get_profile(identifier))

            if not profile_data:
                raise ValueError(f"Profile '{identifier}' not found on LinkedIn")

            profile = SocialProfile(
                platform=SocialPlatform.LINKEDIN,
                user_id=profile_data.get("profile_id", identifier),
                username=profile_data.get("public_id", identifier),
                display_name=f"{profile_data.get('firstName', '')} {profile_data.get('lastName', '')}".strip(),
                bio=profile_data.get("summary", ""),
                profile_url=f"https://linkedin.com/in/{identifier}",
                profile_picture_url=profile_data.get("picture", {}).get("displayImage~", {}).get("elements", [{}])[0].get("identifiers", [{}])[0].get("identifier") if profile_data.get("picture") else None,
                follower_count=profile_data.get("follower_count", 0),
                verified=profile_data.get("verified", False),
                metadata={
                    "industry": profile_data.get("industryName"),
                    "location": profile_data.get("locationName"),
                    "headline": profile_data.get("headline"),
                    "experience": profile_data.get("experience", []),
                    "education": profile_data.get("education", []),
                    "skills": profile_data.get("skills", []),
                },
            )

            self.cache_response(cache_key, profile.to_dict(), ttl_seconds=86400)
            return profile

        except RequestException as e:
            if "404" in str(e):
                raise ValueError(f"Profile '{identifier}' not found on LinkedIn")
            raise RuntimeError(f"Error fetching LinkedIn profile: {e}")
        except Exception as e:
            logger.error(f"Error fetching LinkedIn profile: {e}")
            raise

    def get_posts(self, user_id: str, limit: int = 100) -> list[Post]:
        """Get posts for a LinkedIn profile."""
        cache_key = self._get_cache_key("posts", user_id)
        cached = self.get_cached_response(cache_key)
        if cached:
            return [Post(**p) for p in cached]

        if not self._client:
            raise RuntimeError("LinkedIn client not initialized")

        try:
            posts_data = self._retry_with_backoff(
                lambda: self._client.get_profile_posts(user_id, limit=min(limit, 100))
            )

            if not posts_data:
                return []

            posts = []
            for post_data in posts_data[:limit]:
                post = Post(
                    id=str(post_data.get("activityUrn", post_data.get("id", ""))),
                    platform=SocialPlatform.LINKEDIN,
                    text=post_data.get("text", ""),
                    timestamp=self._parse_linkedin_date(post_data.get("createdTime")),
                    likes=post_data.get("likes", {}).get("total", 0),
                    shares=post_data.get("shares", {}).get("total", 0),
                    comments=post_data.get("comments", {}).get("total", 0),
                    hashtags=self._extract_hashtags(post_data.get("text", "")),
                    mentions=self._extract_mentions(post_data.get("text", "")),
                    sentiment=self._analyze_sentiment(post_data.get("text", "")),
                    metadata={
                        "author_urn": post_data.get("author"),
                        "activity_urn": post_data.get("activityUrn"),
                    },
                )

                posts.append(post)

            self.cache_response(cache_key, [p.to_dict() for p in posts], ttl_seconds=604800)
            return posts

        except Exception as e:
            logger.error(f"Error fetching LinkedIn posts: {e}")
            raise

    def get_followers(self, user_id: str, limit: int = 100) -> list[User]:
        """Get followers for a LinkedIn profile."""
        cache_key = self._get_cache_key("followers", user_id)
        cached = self.get_cached_response(cache_key)
        if cached:
            return [User(**u) for u in cached]

        if not self._client:
            raise RuntimeError("LinkedIn client not initialized")

        try:
            followers_data = self._retry_with_backoff(
                lambda: self._client.get_profile_network(user_id, network_depth="F", limit=limit)
            )

            if not followers_data or not followers_data.get("connections"):
                return []

            users = []
            for conn in followers_data["connections"][:limit]:
                users.append(
                    User(
                        id=conn.get("profileUrn", "").split(":")[-1],
                        username=conn.get("publicId", conn.get("profileUrn", "").split(":")[-1]),
                        display_name=f"{conn.get('firstName', '')} {conn.get('lastName', '')}".strip(),
                        profile_url=f"https://linkedin.com/in/{conn.get('publicId', '')}",
                        metadata={
                            "headline": conn.get("headline"),
                            "location": conn.get("location"),
                        },
                    )
                )

            self.cache_response(cache_key, [u.to_dict() for u in users], ttl_seconds=86400)
            return users

        except Exception as e:
            logger.error(f"Error fetching LinkedIn followers: {e}")
            raise

    def search_user(self, query: str) -> list[User]:
        """Search for users by query."""
        cache_key = self._get_cache_key("search", query)
        cached = self.get_cached_response(cache_key)
        if cached:
            return [User(**u) for u in cached]

        if not self._client:
            raise RuntimeError("LinkedIn client not initialized")

        try:
            search_results = self._retry_with_backoff(
                lambda: self._client.search_people(keywords=query, limit=10)
            )

            if not search_results:
                return []

            user_list = []
            for result in search_results[:10]:
                user_list.append(
                    User(
                        id=result.get("profileUrn", "").split(":")[-1],
                        username=result.get("publicId", ""),
                        display_name=f"{result.get('firstName', '')} {result.get('lastName', '')}".strip(),
                        profile_url=f"https://linkedin.com/in/{result.get('publicId', '')}",
                        metadata={
                            "headline": result.get("headline"),
                            "location": result.get("location"),
                            "company": result.get("companyName"),
                        },
                    )
                )

            self.cache_response(cache_key, [u.to_dict() for u in user_list], ttl_seconds=3600)
            return user_list

        except Exception as e:
            logger.error(f"Error searching LinkedIn users: {e}")
            raise

    def get_connections(self, user_id: str, limit: int = 100) -> list[User]:
        """Get connections (similar to followers) for a LinkedIn profile."""
        return self.get_followers(user_id, limit)

    def get_profile_experience(self, user_id: str) -> list[dict[str, Any]]:
        """Get work experience for a LinkedIn profile."""
        if not self._client:
            raise RuntimeError("LinkedIn client not initialized")

        try:
            profile = self._retry_with_backoff(lambda: self._client.get_profile(user_id))
            return profile.get("experience", [])
        except Exception as e:
            logger.error(f"Error fetching LinkedIn experience: {e}")
            raise

    def get_profile_skills(self, user_id: str) -> list[dict[str, Any]]:
        """Get skills for a LinkedIn profile."""
        if not self._client:
            raise RuntimeError("LinkedIn client not initialized")

        try:
            profile = self._retry_with_backoff(lambda: self._client.get_profile(user_id))
            return profile.get("skills", [])
        except Exception as e:
            logger.error(f"Error fetching LinkedIn skills: {e}")
            raise

    def _parse_linkedin_date(self, date_str: str | None) -> datetime | None:
        """Parse LinkedIn date string to datetime."""
        if not date_str:
            return None

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

        return re.findall(r"@(\w+)", text)

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
