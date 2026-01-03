from __future__ import annotations

from datetime import datetime

from backend.clients.base import SocialClient
from backend.modules.rate_limit import RateLimitPolicy
from backend.modules.social_extraction import NormalizedPost, NormalizedProfile, extract_urls


class YouTubeClient(SocialClient):
    platform = "youtube"
    rate_limit = RateLimitPolicy(requests=90, per_seconds=60)

    def profile_url(self, username: str) -> str:
        # YouTube handles use @
        return f"https://www.youtube.com/@{username}"

    async def fetch_profile(self, username: str) -> NormalizedProfile | None:
        api_key = self.auth.get_tokens("youtube")[0] if self.auth.get_tokens("youtube") else None
        if not api_key:
            return None

        url = (
            "https://www.googleapis.com/youtube/v3/channels"
            f"?part=snippet,statistics&forHandle=@{username}&key={api_key}"
        )

        async def _do():
            resp = await self.http.get(url)
            self._raise_for_status(resp.status, f"fetch_profile({username})")
            return resp.json()

        data = await self._limited(_do)
        items = (data or {}).get("items") or []
        if not items:
            return None

        ch = items[0]
        snippet = ch.get("snippet") or {}
        stats = ch.get("statistics") or {}

        return NormalizedProfile(
            platform=self.platform,
            username=username,
            profile_url=self.profile_url(username),
            display_name=snippet.get("title"),
            bio=snippet.get("description"),
            follower_count=self._int(stats.get("subscriberCount")),
            post_count=self._int(stats.get("videoCount")),
            profile_image_url=((snippet.get("thumbnails") or {}).get("high") or {}).get("url"),
            raw=ch,
        )

    async def fetch_posts(self, username: str, max_items: int = 50) -> list[NormalizedPost]:
        api_key = self.auth.get_tokens("youtube")[0] if self.auth.get_tokens("youtube") else None
        if not api_key:
            return []

        profile = await self.fetch_profile(username)
        if not profile:
            return []

        channel_id = profile.raw.get("id")
        if not channel_id:
            return []

        # search recent videos
        url = (
            "https://www.googleapis.com/youtube/v3/search"
            f"?part=snippet&channelId={channel_id}&maxResults={min(50, max_items)}&order=date&type=video&key={api_key}"
        )

        async def _do():
            resp = await self.http.get(url)
            self._raise_for_status(resp.status, f"fetch_posts({username})")
            return resp.json()

        data = await self._limited(_do)
        items = (data or {}).get("items") or []
        posts: list[NormalizedPost] = []
        for it in items[:max_items]:
            snippet = (it.get("snippet") or {})
            video_id = ((it.get("id") or {}).get("videoId"))
            created_at = None
            if snippet.get("publishedAt"):
                try:
                    created_at = datetime.fromisoformat(snippet["publishedAt"].replace("Z", "+00:00"))
                except Exception:
                    created_at = None
            desc = snippet.get("description")
            urls = extract_urls(desc)
            posts.append(
                NormalizedPost(
                    platform=self.platform,
                    username=username,
                    post_id=video_id,
                    url=(f"https://www.youtube.com/watch?v={video_id}" if video_id else (urls[0] if urls else None)),
                    title=snippet.get("title"),
                    content=desc,
                    created_at=created_at,
                    raw=it,
                )
            )
        return posts
