from __future__ import annotations

from datetime import datetime
from urllib.parse import quote

from backend.clients.base import SocialClient
from backend.modules.rate_limit import RateLimitPolicy
from backend.modules.social_extraction import NormalizedPost, NormalizedProfile, extract_hashtags, extract_mentions


class BlueskyClient(SocialClient):
    platform = "bluesky"
    rate_limit = RateLimitPolicy(requests=60, per_seconds=60)

    def profile_url(self, username: str) -> str:
        handle = username.lstrip("@").strip()
        return f"https://bsky.app/profile/{handle}"

    async def fetch_profile(self, username: str) -> NormalizedProfile | None:
        actor = quote(username.lstrip("@").strip())
        url = f"https://bsky.social/xrpc/app.bsky.actor.getProfile?actor={actor}"

        async def _do():
            resp = await self.http.get(url, headers={"Accept": "application/json"})
            if resp.status >= 400:
                return None
            return resp.json()

        data = await self._limited(_do)
        if not data or not data.get("handle"):
            return None

        return NormalizedProfile(
            platform=self.platform,
            username=data.get("handle"),
            profile_url=self.profile_url(data.get("handle")),
            display_name=data.get("displayName"),
            bio=data.get("description"),
            follower_count=self._int(data.get("followersCount")),
            following_count=self._int(data.get("followsCount")),
            post_count=self._int(data.get("postsCount")),
            profile_image_url=data.get("avatar"),
            banner_image_url=data.get("banner"),
            raw=data,
        )

    async def fetch_posts(self, username: str, max_items: int = 50) -> list[NormalizedPost]:
        actor = quote(username.lstrip("@").strip())
        url = f"https://bsky.social/xrpc/app.bsky.feed.getAuthorFeed?actor={actor}&limit={min(100, max_items)}"

        async def _do():
            resp = await self.http.get(url, headers={"Accept": "application/json"})
            if resp.status >= 400:
                return []
            return resp.json()

        data = await self._limited(_do)
        feed = (data or {}).get("feed") or []
        posts: list[NormalizedPost] = []
        for item in feed[:max_items]:
            post = ((item.get("post") or {}).get("record") or {})
            text = post.get("text")
            created_at = None
            if post.get("createdAt"):
                try:
                    created_at = datetime.fromisoformat(post["createdAt"].replace("Z", "+00:00"))
                except Exception:
                    created_at = None
            uri = (item.get("post") or {}).get("uri")
            posts.append(
                NormalizedPost(
                    platform=self.platform,
                    username=username.lstrip("@").strip(),
                    post_id=uri,
                    url=None,
                    content=text,
                    created_at=created_at,
                    hashtags=extract_hashtags(text or ""),
                    mentions=extract_mentions(text or ""),
                    raw=item,
                )
            )
        return posts
