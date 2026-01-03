from __future__ import annotations

import json
import re
from datetime import datetime

from backend.clients.base import SocialClient
from backend.modules.rate_limit import RateLimitPolicy
from backend.modules.social_extraction import (
    NormalizedPost,
    NormalizedProfile,
    extract_hashtags,
    extract_mentions,
    extract_urls,
)


class InstagramClient(SocialClient):
    platform = "instagram"
    # Scraping should be conservative.
    rate_limit = RateLimitPolicy(requests=30, per_seconds=60)

    def profile_url(self, username: str) -> str:
        return f"https://www.instagram.com/{username}/"

    async def fetch_profile(self, username: str) -> NormalizedProfile | None:
        # Try lightweight JSON endpoint first (often blocked without cookies).
        json_url = f"https://www.instagram.com/{username}/?__a=1&__d=dis"

        async def _do_json():
            resp = await self.http.get(json_url, headers={"Accept": "application/json"})
            if resp.status == 200:
                try:
                    return resp.json()
                except Exception:
                    return None
            return None

        data = await self._limited(_do_json)
        user = None
        if data:
            user = (data.get("graphql") or {}).get("user")

        if not user:
            # Fallback to HTML scraping.
            html_url = self.profile_url(username)

            async def _do_html():
                resp = await self.http.get(html_url)
                self._raise_for_status(resp.status, f"fetch_profile({username})")
                return resp.text

            html = await self._limited(_do_html)
            user = _extract_user_from_html(html)
            if not user:
                return None

        created_at = None
        # Instagram doesn't expose creation date publicly.

        follower_count = _safe_get(user, ["edge_followed_by", "count"])
        following_count = _safe_get(user, ["edge_follow", "count"])
        post_count = _safe_get(user, ["edge_owner_to_timeline_media", "count"])

        bio = user.get("biography")
        return NormalizedProfile(
            platform=self.platform,
            username=username,
            profile_url=self.profile_url(username),
            display_name=user.get("full_name"),
            bio=bio,
            location=None,
            verified=bool(user.get("is_verified")) if user.get("is_verified") is not None else None,
            follower_count=self._int(follower_count),
            following_count=self._int(following_count),
            post_count=self._int(post_count),
            profile_image_url=user.get("profile_pic_url_hd") or user.get("profile_pic_url"),
            banner_image_url=None,
            created_at=created_at,
            raw=user,
        )

    async def fetch_posts(self, username: str, max_items: int = 50) -> list[NormalizedPost]:
        # Use the same scrape payload if possible.
        json_url = f"https://www.instagram.com/{username}/?__a=1&__d=dis"

        async def _do_json():
            resp = await self.http.get(json_url, headers={"Accept": "application/json"})
            if resp.status != 200:
                return None
            try:
                return resp.json()
            except Exception:
                return None

        data = await self._limited(_do_json)
        user = None
        if data:
            user = (data.get("graphql") or {}).get("user")

        edges = []
        if user:
            edges = ((user.get("edge_owner_to_timeline_media") or {}).get("edges")) or []

        posts: list[NormalizedPost] = []
        for e in edges[:max_items]:
            node = (e or {}).get("node") or {}
            caption_edges = ((node.get("edge_media_to_caption") or {}).get("edges")) or []
            caption = None
            if caption_edges:
                caption = (caption_edges[0].get("node") or {}).get("text")
            created_at = None
            if node.get("taken_at_timestamp"):
                try:
                    created_at = datetime.utcfromtimestamp(int(node["taken_at_timestamp"]))
                except Exception:
                    created_at = None
            text = caption or ""
            posts.append(
                NormalizedPost(
                    platform=self.platform,
                    username=username,
                    post_id=str(node.get("id")) if node.get("id") is not None else None,
                    url=self.profile_url(username),
                    content=caption,
                    created_at=created_at,
                    like_count=self._int(_safe_get(node, ["edge_liked_by", "count"]))
                    or self._int(_safe_get(node, ["edge_media_preview_like", "count"])),
                    comment_count=self._int(_safe_get(node, ["edge_media_to_comment", "count"])),
                    media_urls=[node.get("display_url")].copy() if node.get("display_url") else [],
                    hashtags=extract_hashtags(text),
                    mentions=extract_mentions(text),
                    raw=node,
                )
            )
        return posts


def _safe_get(obj, path):
    cur = obj
    for p in path:
        if not isinstance(cur, dict):
            return None
        cur = cur.get(p)
    return cur


_SHARED_DATA_RE = re.compile(r"window\._sharedData\s*=\s*(\{.*?\});", re.DOTALL)


def _extract_user_from_html(html: str):
    # Best-effort extraction: attempt sharedData JSON.
    m = _SHARED_DATA_RE.search(html)
    if not m:
        return None
    try:
        data = json.loads(m.group(1))
    except Exception:
        return None

    try:
        # Old sharedData format
        return (
            data.get("entry_data", {})
            .get("ProfilePage", [{}])[0]
            .get("graphql", {})
            .get("user")
        )
    except Exception:
        return None
