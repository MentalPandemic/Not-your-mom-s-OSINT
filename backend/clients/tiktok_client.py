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


class TikTokClient(SocialClient):
    platform = "tiktok"
    rate_limit = RateLimitPolicy(requests=20, per_seconds=60)

    def profile_url(self, username: str) -> str:
        return f"https://www.tiktok.com/@{username}"

    async def fetch_profile(self, username: str) -> NormalizedProfile | None:
        url = self.profile_url(username)

        async def _do():
            resp = await self.http.get(url)
            self._raise_for_status(resp.status, f"fetch_profile({username})")
            return resp.text

        html = await self._limited(_do)
        state = _extract_sigi_state(html)
        if not state:
            return None

        user_info = (state.get("UserModule") or {}).get("users") or {}
        # Some pages key by username.
        user = user_info.get(username) or next(iter(user_info.values()), None)
        stats = ((state.get("UserModule") or {}).get("stats") or {}).get(username)
        if not user:
            return None

        bio = user.get("signature")
        return NormalizedProfile(
            platform=self.platform,
            username=username,
            profile_url=url,
            display_name=user.get("nickname"),
            bio=bio,
            location=None,
            verified=bool(user.get("verified")) if user.get("verified") is not None else None,
            follower_count=self._int((stats or {}).get("followerCount")),
            following_count=self._int((stats or {}).get("followingCount")),
            post_count=self._int((stats or {}).get("videoCount")),
            profile_image_url=user.get("avatarLarger") or user.get("avatarMedium"),
            banner_image_url=None,
            created_at=None,
            raw={"user": user, "stats": stats},
        )

    async def fetch_posts(self, username: str, max_items: int = 50) -> list[NormalizedPost]:
        url = self.profile_url(username)

        async def _do():
            resp = await self.http.get(url)
            self._raise_for_status(resp.status, f"fetch_posts({username})")
            return resp.text

        html = await self._limited(_do)
        state = _extract_sigi_state(html)
        if not state:
            return []

        items: list[NormalizedPost] = []
        item_module = state.get("ItemModule") or {}
        for item_id, item in list(item_module.items())[:max_items]:
            desc = item.get("desc")
            created_at = None
            if item.get("createTime"):
                try:
                    created_at = datetime.utcfromtimestamp(int(item["createTime"]))
                except Exception:
                    created_at = None
            text = desc or ""
            stats = item.get("stats") or {}
            share_count = self._int(stats.get("shareCount"))
            items.append(
                NormalizedPost(
                    platform=self.platform,
                    username=username,
                    post_id=item_id,
                    url=item.get("video", {}).get("downloadAddr") or url,
                    content=desc,
                    created_at=created_at,
                    like_count=self._int(stats.get("diggCount")),
                    comment_count=self._int(stats.get("commentCount")),
                    share_count=share_count,
                    view_count=self._int(stats.get("playCount")),
                    media_urls=[item.get("video", {}).get("playAddr")].copy()
                    if item.get("video", {}).get("playAddr")
                    else [],
                    hashtags=extract_hashtags(text),
                    mentions=extract_mentions(text),
                    raw=item,
                )
            )

        return items


_SIGI_RE = re.compile(r"<script[^>]+id=\"SIGI_STATE\"[^>]*>(.*?)</script>", re.DOTALL)


def _extract_sigi_state(html: str) -> dict | None:
    m = _SIGI_RE.search(html)
    if not m:
        return None
    try:
        return json.loads(m.group(1))
    except Exception:
        return None
