from __future__ import annotations

from datetime import datetime

from backend.clients.base import SocialClient
from backend.modules.rate_limit import RateLimitPolicy
from backend.modules.social_extraction import NormalizedPost, NormalizedProfile


class TwitchClient(SocialClient):
    platform = "twitch"
    rate_limit = RateLimitPolicy(requests=800, per_seconds=60)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._app_access_token: str | None = None

    def profile_url(self, username: str) -> str:
        return f"https://www.twitch.tv/{username}"

    async def fetch_profile(self, username: str) -> NormalizedProfile | None:
        token = await self._get_app_access_token()
        client_id = self._client_id()
        if not token or not client_id:
            return None

        url = f"https://api.twitch.tv/helix/users?login={username}"
        headers = {
            "Authorization": f"Bearer {token}",
            "Client-Id": client_id,
            "Accept": "application/json",
        }

        async def _do():
            resp = await self.http.get(url, headers=headers)
            if resp.status >= 400:
                return None
            return resp.json()

        data = await self._limited(_do)
        users = (data or {}).get("data") or []
        if not users:
            return None

        u = users[0]
        return NormalizedProfile(
            platform=self.platform,
            username=u.get("login") or username,
            profile_url=self.profile_url(u.get("login") or username),
            display_name=u.get("display_name"),
            bio=u.get("description"),
            profile_image_url=u.get("profile_image_url"),
            banner_image_url=u.get("offline_image_url"),
            raw=u,
        )

    async def fetch_posts(self, username: str, max_items: int = 50) -> list[NormalizedPost]:
        # Use videos endpoint.
        profile = await self.fetch_profile(username)
        if not profile:
            return []
        user_id = profile.raw.get("id")
        if not user_id:
            return []

        token = await self._get_app_access_token()
        client_id = self._client_id()
        if not token or not client_id:
            return []

        url = f"https://api.twitch.tv/helix/videos?user_id={user_id}&first={min(100, max_items)}"
        headers = {
            "Authorization": f"Bearer {token}",
            "Client-Id": client_id,
            "Accept": "application/json",
        }

        async def _do():
            resp = await self.http.get(url, headers=headers)
            if resp.status >= 400:
                return []
            return resp.json()

        data = await self._limited(_do)
        videos = (data or {}).get("data") or []
        posts: list[NormalizedPost] = []
        for v in videos[:max_items]:
            created_at = None
            if v.get("created_at"):
                try:
                    created_at = datetime.fromisoformat(v["created_at"].replace("Z", "+00:00"))
                except Exception:
                    created_at = None
            posts.append(
                NormalizedPost(
                    platform=self.platform,
                    username=username,
                    post_id=v.get("id"),
                    url=v.get("url"),
                    title=v.get("title"),
                    content=v.get("description"),
                    created_at=created_at,
                    view_count=self._int(v.get("view_count")),
                    raw=v,
                )
            )
        return posts

    def _client_id(self) -> str | None:
        return self.auth._env.get("TWITCH_CLIENT_ID")  # noqa: SLF001

    def _client_secret(self) -> str | None:
        return self.auth._env.get("TWITCH_CLIENT_SECRET")  # noqa: SLF001

    async def _get_app_access_token(self) -> str | None:
        if self._app_access_token:
            return self._app_access_token

        client_id = self._client_id()
        client_secret = self._client_secret()
        if not client_id or not client_secret:
            return None

        url = "https://id.twitch.tv/oauth2/token"
        form = {
            "client_id": client_id,
            "client_secret": client_secret,
            "grant_type": "client_credentials",
        }

        async def _do():
            resp = await self.http.post_form(url, form=form)
            if resp.status >= 400:
                return None
            return resp.json()

        data = await self._limited(_do)
        token = (data or {}).get("access_token")
        if token:
            self._app_access_token = token
        return token
