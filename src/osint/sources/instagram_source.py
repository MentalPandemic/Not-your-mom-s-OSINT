from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from instagrapi import Client
from instagrapi.exceptions import (ChallengeRequired, LoginRequired,
                                    PrivateError, UserNotFound)

from osint.core.models import EngagementMetrics, Post, SocialPlatform, SocialProfile
from osint.sources.api_client import APIClient, User

logger = logging.getLogger(__name__)


class InstagramSource(APIClient):
    """Instagram API client for OSINT data collection."""

    name = "instagram"

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        super().__init__(config)
        self._username = self._config.get("username", "")
        self._password = self._config.get("password", "")
        self._session_id = self._config.get("session_id", "")
        self._rate_limit_default = self._config.get("rate_limit", 200)
        self._client: Client | None = None

        if self._session_id:
            try:
                self._client = Client()
                self._client.login_by_sessionid(self._session_id)
            except Exception as e:
                logger.warning(f"Failed to initialize Instagram client with session: {e}")
        elif self._username and self._password:
            try:
                self._client = Client()
                self._client.login(self._username, self._password)
            except Exception as e:
                logger.warning(f"Failed to initialize Instagram client: {e}")

    def validate_credentials(self) -> bool:
        """Validate Instagram API credentials."""
        if not self._client:
            return False

        try:
            self._client.user_info(self._client.user_id)
            return True
        except Exception as e:
            logger.warning(f"Instagram credentials validation failed: {e}")
            return False

    def handle_rate_limiting(self) -> None:
        """Handle rate limiting."""
        pass

    def get_profile(self, identifier: str) -> SocialProfile:
        """Get Instagram profile by username."""
        cache_key = self._get_cache_key("profile", identifier)
        cached = self.get_cached_response(cache_key)
        if cached:
            return SocialProfile(**cached)

        if not self._client:
            raise RuntimeError("Instagram client not initialized. Check credentials in config.")

        try:
            user_info = self._retry_with_backoff(lambda: self._client.user_info_by_username(identifier))

            if not user_info:
                raise ValueError(f"User '{identifier}' not found on Instagram")

            profile = SocialProfile(
                platform=SocialPlatform.INSTAGRAM,
                user_id=str(user_info.pk),
                username=user_info.username,
                display_name=user_info.full_name,
                bio=user_info.biography or "",
                profile_url=f"https://instagram.com/{user_info.username}",
                profile_picture_url=user_info.profile_pic_url_hd or user_info.profile_pic_url,
                follower_count=user_info.follower_count or 0,
                following_count=user_info.following_count or 0,
                post_count=user_info.media_count or 0,
                verified=user_info.is_verified or False,
                created_date=None,
                metadata={
                    "external_url": user_info.external_url,
                    "is_private": user_info.is_private,
                    "is_business": user_info.is_business,
                    "category": user_info.category,
                    "account_type": "business" if user_info.is_business else "personal",
                },
            )

            self.cache_response(cache_key, profile.to_dict(), ttl_seconds=86400)
            return profile

        except UserNotFound:
            raise ValueError(f"User '{identifier}' not found on Instagram")
        except PrivateError:
            logger.warning(f"User '{identifier}' has a private account")
            return SocialProfile(
                platform=SocialPlatform.INSTAGRAM,
                user_id="",
                username=identifier,
                display_name=identifier,
                bio="Private account",
                profile_url=f"https://instagram.com/{identifier}",
                profile_picture_url=None,
                metadata={"is_private": True, "error": "Private account - limited data available"},
            )
        except (ChallengeRequired, LoginRequired) as e:
            raise RuntimeError(f"Instagram authentication required: {e}")
        except Exception as e:
            logger.error(f"Error fetching Instagram profile: {e}")
            raise

    def get_posts(self, user_id: str, limit: int = 100) -> list[Post]:
        """Get posts for an Instagram user."""
        cache_key = self._get_cache_key("posts", user_id)
        cached = self.get_cached_response(cache_key)
        if cached:
            return [Post(**p) for p in cached]

        if not self._client:
            raise RuntimeError("Instagram client not initialized")

        try:
            user_medias = self._retry_with_backoff(
                lambda: self._client.user_medias(int(user_id), amount=min(limit, 50))
            )

            if not user_medias:
                return []

            posts = []
            for media in user_medias[:limit]:
                post = Post(
                    id=str(media.pk),
                    platform=SocialPlatform.INSTAGRAM,
                    text=media.caption_text or "",
                    timestamp=media.taken_at,
                    likes=media.like_count or 0,
                    shares=0,
                    comments=media.comment_count or 0,
                    hashtags=self._extract_hashtags(media.caption_text or ""),
                    mentions=self._extract_mentions(media.caption_text or ""),
                    media_urls=self._extract_media_urls(media),
                    sentiment=self._analyze_sentiment(media.caption_text or ""),
                    metadata={
                        "media_type": media.media_type,
                        "play_count": media.play_count,
                        "view_count": media.view_count,
                        "location": media.location.name if media.location else None,
                    },
                )

                posts.append(post)

            self.cache_response(cache_key, [p.to_dict() for p in posts], ttl_seconds=604800)
            return posts

        except Exception as e:
            logger.error(f"Error fetching Instagram posts: {e}")
            raise

    def get_followers(self, user_id: str, limit: int = 100) -> list[User]:
        """Get followers for an Instagram user."""
        cache_key = self._get_cache_key("followers", user_id)
        cached = self.get_cached_response(cache_key)
        if cached:
            return [User(**u) for u in cached]

        if not self._client:
            raise RuntimeError("Instagram client not initialized")

        try:
            followers_data = self._retry_with_backoff(
                lambda: self._client.user_followers(int(user_id), amount=min(limit, 50))
            )

            if not followers_data:
                return []

            users = [
                User(
                    id=str(user.pk),
                    username=user.username,
                    display_name=user.full_name,
                    profile_url=f"https://instagram.com/{user.username}",
                    profile_picture_url=user.profile_pic_url,
                    metadata={
                        "is_private": user.is_private,
                        "is_verified": user.is_verified,
                    },
                )
                for user in list(followers_data.values())[:limit]
            ]

            self.cache_response(cache_key, [u.to_dict() for u in users], ttl_seconds=86400)
            return users

        except Exception as e:
            logger.error(f"Error fetching Instagram followers: {e}")
            raise

    def search_user(self, query: str) -> list[User]:
        """Search for users by query."""
        cache_key = self._get_cache_key("search", query)
        cached = self.get_cached_response(cache_key)
        if cached:
            return [User(**u) for u in cached]

        if not self._client:
            raise RuntimeError("Instagram client not initialized")

        try:
            search_results = self._retry_with_backoff(lambda: self._client.search_users(query, count=10))

            if not search_results:
                return []

            user_list = [
                User(
                    id=str(user.pk),
                    username=user.username,
                    display_name=user.full_name,
                    profile_url=f"https://instagram.com/{user.username}",
                    profile_picture_url=user.profile_pic_url,
                    metadata={
                        "is_private": user.is_private,
                        "is_verified": user.is_verified,
                    },
                )
                for user in search_results[:10]
            ]

            self.cache_response(cache_key, [u.to_dict() for u in user_list], ttl_seconds=3600)
            return user_list

        except Exception as e:
            logger.error(f"Error searching Instagram users: {e}")
            raise

    def get_following(self, user_id: str, limit: int = 100) -> list[User]:
        """Get users that an Instagram user is following."""
        if not self._client:
            raise RuntimeError("Instagram client not initialized")

        try:
            following_data = self._retry_with_backoff(
                lambda: self._client.user_following(int(user_id), amount=min(limit, 50))
            )

            if not following_data:
                return []

            users = [
                User(
                    id=str(user.pk),
                    username=user.username,
                    display_name=user.full_name,
                    profile_url=f"https://instagram.com/{user.username}",
                    profile_picture_url=user.profile_pic_url,
                    metadata={
                        "is_private": user.is_private,
                        "is_verified": user.is_verified,
                    },
                )
                for user in list(following_data.values())[:limit]
            ]

            return users

        except Exception as e:
            logger.error(f"Error fetching Instagram following: {e}")
            raise

    def search_hashtag(self, hashtag: str, limit: int = 100) -> list[Post]:
        """Search for posts by hashtag."""
        if not self._client:
            raise RuntimeError("Instagram client not initialized")

        try:
            hashtag_obj = self._retry_with_backoff(lambda: self._client.hashtag_info(hashtag))

            if not hashtag_obj:
                return []

            posts_data = self._retry_with_backoff(
                lambda: self._client.hashtag_medias_recent(hashtag_obj.pk, amount=min(limit, 50))
            )

            if not posts_data:
                return []

            posts = []
            for media in posts_data[:limit]:
                post = Post(
                    id=str(media.pk),
                    platform=SocialPlatform.INSTAGRAM,
                    text=media.caption_text or "",
                    timestamp=media.taken_at,
                    likes=media.like_count or 0,
                    shares=0,
                    comments=media.comment_count or 0,
                    hashtags=self._extract_hashtags(media.caption_text or ""),
                    mentions=self._extract_mentions(media.caption_text or ""),
                    media_urls=self._extract_media_urls(media),
                    sentiment=self._analyze_sentiment(media.caption_text or ""),
                    metadata={
                        "hashtag": hashtag,
                        "media_type": media.media_type,
                    },
                )

                posts.append(post)

            return posts

        except Exception as e:
            logger.error(f"Error searching Instagram hashtag: {e}")
            raise

    def _extract_media_urls(self, media: Any) -> list[str]:
        """Extract media URLs from Instagram media object."""
        urls = []

        if hasattr(media, 'thumbnail_url'):
            urls.append(media.thumbnail_url)
        if hasattr(media, 'video_url') and media.video_url:
            urls.append(media.video_url)
        if hasattr(media, 'image_versions2') and media.image_versions2:
            candidates = media.image_versions2.get('candidates', [])
            if candidates:
                urls.append(candidates[0].get('url', ''))

        return [url for url in urls if url]

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
