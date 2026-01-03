from __future__ import annotations

from datetime import datetime
from typing import Any

from backend.clients.base import SocialClient
from backend.modules.rate_limit import RateLimitPolicy
from backend.modules.social_extraction import NormalizedPost, NormalizedProfile, extract_urls


class RedditClient(SocialClient):
    platform = "reddit"
    # Reddit guideline: ~60 requests/minute per app/user-agent.
    rate_limit = RateLimitPolicy(requests=60, per_seconds=60)

    def profile_url(self, username: str) -> str:
        return f"https://www.reddit.com/user/{username}/"

    async def fetch_profile(self, username: str) -> NormalizedProfile | None:
        # Prefer unauthenticated public endpoint; PRAW if installed and credentials exist.
        about_url = f"https://www.reddit.com/user/{username}/about.json"

        async def _do():
            resp = await self.http.get(about_url, headers={"Accept": "application/json"})
            self._raise_for_status(resp.status, f"fetch_profile({username})")
            return resp.json()

        data = await self._limited(_do)
        d = (data or {}).get("data")
        if not d:
            return None

        created_at = None
        if d.get("created_utc"):
            try:
                created_at = datetime.utcfromtimestamp(float(d["created_utc"]))
            except Exception:
                created_at = None

        return NormalizedProfile(
            platform=self.platform,
            username=username,
            profile_url=self.profile_url(username),
            display_name=d.get("subreddit", {}).get("title"),
            bio=d.get("subreddit", {}).get("public_description"),
            verified=None,
            follower_count=None,
            following_count=None,
            post_count=None,
            profile_image_url=d.get("icon_img"),
            created_at=created_at,
            raw=d,
        )

    async def fetch_posts(self, username: str, max_items: int = 1000) -> list[NormalizedPost]:
        items: list[NormalizedPost] = []
        after: str | None = None
        per_page = 100

        def _parse_listing(children: list[dict[str, Any]]):
            nonlocal items
            for c in children:
                kind = c.get("kind")
                d = c.get("data") or {}
                created_at = None
                if d.get("created_utc"):
                    try:
                        created_at = datetime.utcfromtimestamp(float(d["created_utc"]))
                    except Exception:
                        created_at = None

                if kind == "t3":  # post
                    content = d.get("selftext") or d.get("title")
                    urls = extract_urls(content)
                    items.append(
                        NormalizedPost(
                            platform=self.platform,
                            username=username,
                            post_id=d.get("id"),
                            url=d.get("url") or (urls[0] if urls else None),
                            title=d.get("title"),
                            content=d.get("selftext"),
                            created_at=created_at,
                            like_count=self._int(d.get("score")),
                            comment_count=self._int(d.get("num_comments")),
                            raw=d,
                        )
                    )
                elif kind == "t1":  # comment
                    body = d.get("body")
                    urls = extract_urls(body)
                    items.append(
                        NormalizedPost(
                            platform=self.platform,
                            username=username,
                            post_id=d.get("id"),
                            url=(urls[0] if urls else None),
                            content=body,
                            created_at=created_at,
                            like_count=self._int(d.get("score")),
                            raw=d,
                        )
                    )

        # Pull submitted posts then comments, merging until max_items.
        for listing in ("submitted", "comments"):
            after = None
            while len(items) < max_items:
                limit = min(per_page, max_items - len(items))
                url = f"https://www.reddit.com/user/{username}/{listing}.json?limit={limit}"
                if after:
                    url += f"&after={after}"

                async def _do():
                    resp = await self.http.get(url, headers={"Accept": "application/json"})
                    self._raise_for_status(resp.status, f"fetch_posts({username})")
                    return resp.json()

                data = await self._limited(_do)
                listing_data = (data or {}).get("data") or {}
                children = listing_data.get("children") or []
                if not children:
                    break
                _parse_listing(children)
                after = listing_data.get("after")
                if not after:
                    break

        return items[:max_items]
