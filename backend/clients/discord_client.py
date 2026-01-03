from __future__ import annotations

import re

from backend.clients.base import SocialClient
from backend.modules.rate_limit import RateLimitPolicy
from backend.modules.social_extraction import NormalizedProfile


class DiscordClient(SocialClient):
    platform = "discord"
    rate_limit = RateLimitPolicy(requests=50, per_seconds=60)

    def profile_url(self, username: str) -> str:
        if re.fullmatch(r"\d{16,20}", username.strip()):
            return f"https://discord.com/users/{username.strip()}"
        return "https://discord.com/"

    async def fetch_profile(self, username: str) -> NormalizedProfile | None:
        # Discord does not provide a public API to lookup arbitrary usernames.
        # If the provided identifier looks like a user ID and a bot token is available,
        # attempt a limited fetch.
        user_id = username.strip()
        if not re.fullmatch(r"\d{16,20}", user_id):
            return None

        token = self._token()
        if not token:
            return None

        url = f"https://discord.com/api/v10/users/{user_id}"
        headers = {"Authorization": f"Bot {token}", "Accept": "application/json"}

        async def _do():
            resp = await self.http.get(url, headers=headers)
            if resp.status >= 400:
                return None
            return resp.json()

        data = await self._limited(_do)
        if not data or not data.get("id"):
            return None

        avatar = None
        if data.get("avatar"):
            avatar = f"https://cdn.discordapp.com/avatars/{data['id']}/{data['avatar']}.png"

        return NormalizedProfile(
            platform=self.platform,
            username=data.get("username") or user_id,
            profile_url=self.profile_url(user_id),
            display_name=data.get("global_name"),
            bio=None,
            profile_image_url=avatar,
            raw=data,
        )
