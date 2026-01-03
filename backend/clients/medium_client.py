from __future__ import annotations

import xml.etree.ElementTree as ET
from datetime import datetime

from backend.clients.base import SocialClient
from backend.modules.rate_limit import RateLimitPolicy
from backend.modules.social_extraction import NormalizedPost, NormalizedProfile, extract_urls


class MediumClient(SocialClient):
    platform = "medium"
    rate_limit = RateLimitPolicy(requests=30, per_seconds=60)

    def profile_url(self, username: str) -> str:
        if username.startswith("@"):
            return f"https://medium.com/{username}"
        return f"https://medium.com/@{username}"

    async def fetch_profile(self, username: str) -> NormalizedProfile | None:
        # Medium provides RSS but not a stable public JSON API for profiles.
        # We'll treat the feed metadata as profile.
        rss = f"https://medium.com/feed/@{username.lstrip('@')}"

        async def _do():
            resp = await self.http.get(rss, headers={"Accept": "application/rss+xml, application/xml"})
            if resp.status >= 400:
                return None
            return resp.text

        text = await self._limited(_do)
        if not text:
            return None

        try:
            root = ET.fromstring(text)
        except Exception:
            return None

        channel = root.find("channel")
        if channel is None:
            return None

        title = (channel.findtext("title") or "").strip() or None
        desc = (channel.findtext("description") or "").strip() or None
        link = (channel.findtext("link") or "").strip() or self.profile_url(username)

        return NormalizedProfile(
            platform=self.platform,
            username=username.lstrip("@"),
            profile_url=link,
            display_name=title,
            bio=desc,
            raw={"rss": True},
        )

    async def fetch_posts(self, username: str, max_items: int = 50) -> list[NormalizedPost]:
        rss = f"https://medium.com/feed/@{username.lstrip('@')}"

        async def _do():
            resp = await self.http.get(rss, headers={"Accept": "application/rss+xml, application/xml"})
            if resp.status >= 400:
                return None
            return resp.text

        text = await self._limited(_do)
        if not text:
            return []

        try:
            root = ET.fromstring(text)
        except Exception:
            return []

        channel = root.find("channel")
        if channel is None:
            return []

        posts: list[NormalizedPost] = []
        for item in channel.findall("item")[:max_items]:
            title = item.findtext("title")
            link = item.findtext("link")
            pub = item.findtext("pubDate")
            created_at = None
            if pub:
                try:
                    created_at = datetime.strptime(pub, "%a, %d %b %Y %H:%M:%S %Z")
                except Exception:
                    created_at = None
            content = item.findtext("description")
            urls = extract_urls(content)
            posts.append(
                NormalizedPost(
                    platform=self.platform,
                    username=username.lstrip("@"),
                    post_id=link,
                    url=link or (urls[0] if urls else None),
                    title=title,
                    content=content,
                    created_at=created_at,
                    raw={"rss": True},
                )
            )
        return posts
