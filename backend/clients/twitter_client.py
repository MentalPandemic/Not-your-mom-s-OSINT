from __future__ import annotations

from datetime import datetime
from typing import Any

from backend.clients.base import SocialClient
from backend.modules.rate_limit import RateLimitPolicy
from backend.modules.social_extraction import (
    NormalizedPost,
    NormalizedProfile,
    extract_hashtags,
    extract_mentions,
    extract_urls,
)


class TwitterClient(SocialClient):
    platform = "twitter"
    # Twitter v2: 450 requests / 15 minutes (app context). Use a conservative default.
    rate_limit = RateLimitPolicy(requests=450, per_seconds=15 * 60)

    def profile_url(self, username: str) -> str:
        return f"https://x.com/{username}"

    async def fetch_profile(self, username: str) -> NormalizedProfile | None:
        token = self._token()
        if not token:
            return None

        url = (
            "https://api.twitter.com/2/users/by/username/"
            + username
            + "?user.fields=created_at,description,location,profile_image_url,public_metrics,verified"
        )
        headers = {"Authorization": f"Bearer {token}"}

        async def _do():
            resp = await self.http.get(url, headers=headers)
            self._raise_for_status(resp.status, f"fetch_profile({username})")
            return resp.json()

        data = await self._limited(_do)
        user = (data or {}).get("data")
        if not user:
            return None

        metrics = user.get("public_metrics") or {}
        created_at = None
        if user.get("created_at"):
            try:
                created_at = datetime.fromisoformat(user["created_at"].replace("Z", "+00:00"))
            except Exception:
                created_at = None

        return NormalizedProfile(
            platform=self.platform,
            username=username,
            profile_url=self.profile_url(username),
            display_name=user.get("name"),
            bio=user.get("description"),
            location=user.get("location"),
            verified=user.get("verified"),
            follower_count=self._int(metrics.get("followers_count")),
            following_count=self._int(metrics.get("following_count")),
            post_count=self._int(metrics.get("tweet_count")),
            profile_image_url=user.get("profile_image_url"),
            created_at=created_at,
            raw=user,
        )

    async def fetch_posts(self, username: str, max_items: int = 3200) -> list[NormalizedPost]:
        token = self._token()
        if not token:
            return []

        profile = await self.fetch_profile(username)
        if not profile:
            return []
        user_id = profile.raw.get("id")
        if not user_id:
            return []

        headers = {"Authorization": f"Bearer {token}"}
        posts: list[NormalizedPost] = []
        pagination_token: str | None = None

        while len(posts) < max_items:
            remaining = max_items - len(posts)
            page_size = min(100, remaining)
            url = (
                f"https://api.twitter.com/2/users/{user_id}/tweets"
                f"?max_results={page_size}"
                "&tweet.fields=created_at,public_metrics,entities"
            )
            if pagination_token:
                url += f"&pagination_token={pagination_token}"

            async def _do():
                resp = await self.http.get(url, headers=headers)
                self._raise_for_status(resp.status, f"fetch_posts({username})")
                return resp.json()

            page = await self._limited(_do)
            for t in (page or {}).get("data") or []:
                metrics: dict[str, Any] = t.get("public_metrics") or {}
                created_at = None
                if t.get("created_at"):
                    try:
                        created_at = datetime.fromisoformat(t["created_at"].replace("Z", "+00:00"))
                    except Exception:
                        created_at = None

                text = t.get("text")
                hashtags = extract_hashtags(text)
                mentions = extract_mentions(text)
                urls = extract_urls(text)

                posts.append(
                    NormalizedPost(
                        platform=self.platform,
                        username=username,
                        post_id=t.get("id"),
                        url=(urls[0] if urls else None),
                        content=text,
                        created_at=created_at,
                        like_count=self._int(metrics.get("like_count")),
                        comment_count=self._int(metrics.get("reply_count")),
                        share_count=self._int(metrics.get("retweet_count")),
                        view_count=self._int(metrics.get("impression_count")),
                        hashtags=hashtags,
                        mentions=mentions,
                        raw=t,
                    )
                )

            meta = (page or {}).get("meta") or {}
            pagination_token = meta.get("next_token")
            if not pagination_token:
                break

        return posts
