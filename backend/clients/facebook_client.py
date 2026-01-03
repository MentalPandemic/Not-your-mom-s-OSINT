from __future__ import annotations

import json
import re
from typing import Any

from backend.clients.base import SocialClient
from backend.modules.rate_limit import RateLimitPolicy
from backend.modules.social_extraction import NormalizedProfile, extract_urls


class FacebookClient(SocialClient):
    platform = "facebook"
    rate_limit = RateLimitPolicy(requests=200, per_seconds=60)

    def profile_url(self, username: str) -> str:
        return f"https://www.facebook.com/{username}"

    async def fetch_profile(self, username: str) -> NormalizedProfile | None:
        token = self._token()
        if token:
            url = (
                f"https://graph.facebook.com/v18.0/{username}"
                "?fields=id,name,about,fan_count,followers_count,link,verification_status"
                f"&access_token={token}"
            )

            async def _do():
                resp = await self.http.get(url)
                if resp.status == 200:
                    return resp.json()
                return None

            data = await self._limited(_do)
            if isinstance(data, dict) and data.get("id"):
                return NormalizedProfile(
                    platform=self.platform,
                    username=username,
                    profile_url=data.get("link") or self.profile_url(username),
                    display_name=data.get("name"),
                    bio=data.get("about"),
                    location=None,
                    verified=(data.get("verification_status") == "verified")
                    if data.get("verification_status") is not None
                    else None,
                    follower_count=self._int(data.get("followers_count") or data.get("fan_count")),
                    raw=data,
                )

        # Scrape fallback
        url = self.profile_url(username)

        async def _do_html():
            resp = await self.http.get(url)
            if resp.status >= 400:
                return None
            return resp.text

        html = await self._limited(_do_html)
        if not html:
            return None

        title = _extract_og(html, "og:title")
        desc = _extract_og(html, "og:description")
        image = _extract_og(html, "og:image")
        return NormalizedProfile(
            platform=self.platform,
            username=username,
            profile_url=url,
            display_name=title,
            bio=desc,
            profile_image_url=image,
            raw={"scrape": True},
        )


def _extract_og(html: str, property_name: str) -> str | None:
    # <meta property="og:title" content="...">
    m = re.search(
        rf"<meta[^>]+property=\"{re.escape(property_name)}\"[^>]+content=\"(.*?)\"",
        html,
        flags=re.IGNORECASE,
    )
    if not m:
        return None
    return m.group(1)
