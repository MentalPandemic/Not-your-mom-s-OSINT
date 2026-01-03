from __future__ import annotations

from datetime import datetime
from urllib.parse import quote

from backend.clients.base import SocialClient
from backend.modules.rate_limit import RateLimitPolicy
from backend.modules.social_extraction import NormalizedPost, NormalizedProfile, extract_hashtags, extract_mentions


class MastodonClient(SocialClient):
    platform = "mastodon"
    rate_limit = RateLimitPolicy(requests=60, per_seconds=60)

    def profile_url(self, username: str) -> str:
        handle, instance = _split_handle(username)
        if instance:
            return f"https://{instance}/@{handle}"
        return f"https://mastodon.social/@{handle}"

    async def fetch_profile(self, username: str) -> NormalizedProfile | None:
        handle, instance = _split_handle(username)
        instance = instance or "mastodon.social"
        base = f"https://{instance}"
        q = quote(f"@{handle}@{instance}")
        search_url = f"{base}/api/v2/search?q={q}&type=accounts&limit=1"
        headers = {"Accept": "application/json"}
        token = self._token()
        if token:
            headers["Authorization"] = f"Bearer {token}"

        async def _do_search():
            resp = await self.http.get(search_url, headers=headers)
            if resp.status >= 400:
                return None
            return resp.json()

        data = await self._limited(_do_search)
        accounts = (data or {}).get("accounts") or []
        if not accounts:
            return None

        acct = accounts[0]
        created_at = None
        if acct.get("created_at"):
            try:
                created_at = datetime.fromisoformat(acct["created_at"].replace("Z", "+00:00"))
            except Exception:
                created_at = None

        return NormalizedProfile(
            platform=self.platform,
            username=f"{handle}@{instance}",
            profile_url=acct.get("url") or self.profile_url(username),
            display_name=acct.get("display_name"),
            bio=acct.get("note"),
            follower_count=self._int(acct.get("followers_count")),
            following_count=self._int(acct.get("following_count")),
            post_count=self._int(acct.get("statuses_count")),
            profile_image_url=acct.get("avatar"),
            created_at=created_at,
            raw=acct,
        )

    async def fetch_posts(self, username: str, max_items: int = 50) -> list[NormalizedPost]:
        profile = await self.fetch_profile(username)
        if not profile:
            return []
        acct = profile.raw
        instance = None
        if profile.profile_url:
            try:
                instance = profile.profile_url.split("/")[2]
            except Exception:
                instance = None
        instance = instance or "mastodon.social"
        base = f"https://{instance}"
        acct_id = acct.get("id")
        if not acct_id:
            return []
        url = f"{base}/api/v1/accounts/{acct_id}/statuses?limit={min(40, max_items)}"
        headers = {"Accept": "application/json"}
        token = self._token()
        if token:
            headers["Authorization"] = f"Bearer {token}"

        async def _do():
            resp = await self.http.get(url, headers=headers)
            if resp.status >= 400:
                return []
            return resp.json()

        statuses = await self._limited(_do)
        posts: list[NormalizedPost] = []
        for st in (statuses or [])[:max_items]:
            created_at = None
            if st.get("created_at"):
                try:
                    created_at = datetime.fromisoformat(st["created_at"].replace("Z", "+00:00"))
                except Exception:
                    created_at = None
            content = st.get("content")
            text = content or ""
            posts.append(
                NormalizedPost(
                    platform=self.platform,
                    username=profile.username,
                    post_id=str(st.get("id")) if st.get("id") is not None else None,
                    url=st.get("url"),
                    content=content,
                    created_at=created_at,
                    like_count=self._int(st.get("favourites_count")),
                    comment_count=self._int(st.get("replies_count")),
                    share_count=self._int(st.get("reblogs_count")),
                    hashtags=extract_hashtags(text),
                    mentions=extract_mentions(text),
                    raw=st,
                )
            )
        return posts


def _split_handle(username: str) -> tuple[str, str | None]:
    u = username.strip()
    if u.startswith("@"):
        u = u[1:]
    if "@" in u:
        handle, instance = u.split("@", 1)
        return handle, instance
    return u, None
