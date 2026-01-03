from __future__ import annotations

import json
import re
from typing import Any

from backend.clients.base import SocialClient
from backend.modules.rate_limit import RateLimitPolicy
from backend.modules.social_extraction import NormalizedProfile


class LinkedInClient(SocialClient):
    platform = "linkedin"
    rate_limit = RateLimitPolicy(requests=15, per_seconds=60)

    def profile_url(self, username: str) -> str:
        return f"https://www.linkedin.com/in/{username}/"

    async def fetch_profile(self, username: str) -> NormalizedProfile | None:
        url = self.profile_url(username)

        async def _do():
            resp = await self.http.get(url)
            if resp.status >= 400:
                return None
            return resp.text

        html = await self._limited(_do)
        if not html:
            return None

        title = _extract_title(html)
        ld = _extract_jsonld(html)
        # JSON-LD is often present for public pages
        display_name = None
        headline = None
        location = None
        employment: list[dict[str, Any]] = []
        if isinstance(ld, dict):
            display_name = ld.get("name")
            headline = ld.get("description")
            location = (ld.get("address") or {}).get("addressLocality")
            if ld.get("worksFor"):
                works_for = ld["worksFor"]
                if isinstance(works_for, dict):
                    employment.append(works_for)
                elif isinstance(works_for, list):
                    employment.extend([w for w in works_for if isinstance(w, dict)])

        return NormalizedProfile(
            platform=self.platform,
            username=username,
            profile_url=url,
            display_name=display_name or title,
            bio=headline,
            location=location,
            verified=None,
            raw={"jsonld": ld, "employment": employment},
        )


def _extract_title(html: str) -> str | None:
    m = re.search(r"<title>(.*?)</title>", html, flags=re.IGNORECASE | re.DOTALL)
    if not m:
        return None
    return re.sub(r"\s+", " ", m.group(1)).strip()


def _extract_jsonld(html: str) -> dict | None:
    m = re.search(
        r"<script[^>]+type=\"application/ld\+json\"[^>]*>(.*?)</script>",
        html,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if not m:
        return None
    try:
        return json.loads(m.group(1).strip())
    except Exception:
        return None
