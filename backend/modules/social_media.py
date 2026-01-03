from __future__ import annotations

import asyncio
import logging
from typing import Any

from backend.clients import (
    BlueskyClient,
    DiscordClient,
    FacebookClient,
    GitHubClient,
    InstagramClient,
    LinkedInClient,
    MastodonClient,
    MediumClient,
    RedditClient,
    TikTokClient,
    TwitchClient,
    TwitterClient,
    YouTubeClient,
)
from backend.clients.base import NotFoundError, SocialClient, SocialClientError
from backend.config.social_media_auth import SocialMediaAuthManager, load_dotenv_if_available
from backend.modules.caching import TTLCache
from backend.modules.http_client import AsyncHttpClient
from backend.modules.neo4j_integration import Neo4jGraph, create_graph
from backend.modules.persistence import SocialMediaStore, create_store
from backend.modules.scraping import scrape_open_graph
from backend.modules.social_extraction import LinkedAccount, NormalizedPost, NormalizedProfile, discover_linked_accounts

logger = logging.getLogger(__name__)


SUPPORTED_PLATFORMS_PRIORITY: list[str] = [
    "twitter",
    "reddit",
    "instagram",
    "tiktok",
    "facebook",
    "linkedin",
    "youtube",
    "github",
    "medium",
    "mastodon",
    "bluesky",
    "discord",
    "twitch",
]


class SocialMediaModule:
    def __init__(
        self,
        auth: SocialMediaAuthManager | None = None,
        store: SocialMediaStore | None = None,
        graph: Neo4jGraph | None = None,
        cache: TTLCache[Any] | None = None,
        max_concurrency: int = 5,
    ):
        load_dotenv_if_available()
        self.auth = auth or SocialMediaAuthManager()
        self.store = store or create_store()
        self.graph = graph or create_graph()
        self.cache: TTLCache[Any] = cache or TTLCache(default_ttl_seconds=86400)
        self._http = AsyncHttpClient()
        self._sem = asyncio.Semaphore(max_concurrency)
        self.clients: dict[str, SocialClient] = {
            "twitter": TwitterClient(self.auth),
            "reddit": RedditClient(self.auth),
            "instagram": InstagramClient(self.auth),
            "tiktok": TikTokClient(self.auth),
            "facebook": FacebookClient(self.auth),
            "linkedin": LinkedInClient(self.auth),
            "youtube": YouTubeClient(self.auth),
            "github": GitHubClient(self.auth),
            "medium": MediumClient(self.auth),
            "mastodon": MastodonClient(self.auth),
            "bluesky": BlueskyClient(self.auth),
            "discord": DiscordClient(self.auth),
            "twitch": TwitchClient(self.auth),
        }

    def _get_client(self, platform: str) -> SocialClient:
        p = platform.lower().strip()
        if p not in self.clients:
            raise ValueError(f"Unsupported platform: {platform}")
        return self.clients[p]

    async def search_social_profiles(self, username: str, platforms: list[str] | None = None) -> dict[str, Any]:
        plats = self._normalize_platforms(platforms)

        async def _one(p: str):
            client = self._get_client(p)
            async with self._sem:
                try:
                    prof = await client.fetch_profile(username)
                except NotFoundError:
                    prof = None
                except SocialClientError as e:
                    logger.info("%s profile fetch failed for %s: %s", p, username, e)
                    prof = None

                if not prof:
                    og = await scrape_open_graph(client.profile_url(username), http=self._http)
                    if og:
                        prof = NormalizedProfile(
                            platform=p,
                            username=username,
                            profile_url=og.get("url"),
                            display_name=og.get("title"),
                            bio=og.get("description"),
                            profile_image_url=og.get("image"),
                            raw={"scrape_fallback": True, "open_graph": og},
                        )

                if not prof:
                    return None

                return {
                    "platform": p,
                    "profile_url": prof.profile_url or client.profile_url(username),
                    "follower_count": prof.follower_count,
                    "verified": prof.verified,
                }

        results = [r for r in await asyncio.gather(*[_one(p) for p in plats]) if r]
        return {"results": results}

    async def get_detailed_profile(self, username: str, platform: str, force_refresh: bool = False) -> dict[str, Any]:
        p = platform.lower().strip()
        client = self._get_client(p)

        profile_key = f"profile:{p}:{username.lower()}"
        posts_key = f"posts:{p}:{username.lower()}"
        links_key = f"linked:{p}:{username.lower()}"

        if force_refresh:
            await self.cache.delete(profile_key)
            await self.cache.delete(posts_key)
            await self.cache.delete(links_key)

        cached_profile: NormalizedProfile | None = await self.cache.get(profile_key)
        cached_posts: list[NormalizedPost] | None = await self.cache.get(posts_key)
        cached_links: list[LinkedAccount] | None = await self.cache.get(links_key)

        profile = cached_profile
        posts = cached_posts
        linked = cached_links

        if not profile:
            async with self._sem:
                profile = await client.fetch_profile(username)

            if not profile:
                og = await scrape_open_graph(client.profile_url(username), http=self._http)
                if og:
                    profile = NormalizedProfile(
                        platform=p,
                        username=username,
                        profile_url=og.get("url"),
                        display_name=og.get("title"),
                        bio=og.get("description"),
                        profile_image_url=og.get("image"),
                        raw={"scrape_fallback": True, "open_graph": og},
                    )

            if not profile:
                raise NotFoundError(f"Profile not found on {p} for {username}")

            await self.cache.set(profile_key, profile)

        if posts is None:
            async with self._sem:
                posts = await client.fetch_posts(username)
            await self.cache.set(posts_key, posts)

        if linked is None:
            linked = discover_linked_accounts(profile, posts)
            await self.cache.set(links_key, linked)

        stored = await self.store.upsert_profile(profile)
        await self.store.replace_posts(stored.id, posts)
        await self.store.replace_linked_accounts(profile.platform, profile.username, linked)

        await self.graph.upsert_profile(profile)
        await self.graph.upsert_posts(profile, posts)
        await self.graph.upsert_linked_accounts(profile, linked)

        return {
            "profile": profile.to_dict(),
            "posts": [p.to_dict() for p in posts],
            "linked_accounts": [a.to_dict() for a in linked],
            "last_updated": stored.last_updated.isoformat(),
        }

    async def get_recent_posts(self, username: str, platform: str, page: int = 1, page_size: int = 50) -> dict[str, Any]:
        p = platform.lower().strip()
        stored = await self.store.get_profile(p, username)
        if not stored:
            # hydrate
            await self.get_detailed_profile(username, platform)
            stored = await self.store.get_profile(p, username)
        if not stored:
            raise NotFoundError(f"No stored profile for {username} on {p}")

        page = max(1, page)
        page_size = max(1, min(200, page_size))
        offset = (page - 1) * page_size

        posts = await self.store.get_posts(stored.id, offset=offset, limit=page_size)
        return {
            "profile": {"platform": p, "username": username, "id": stored.id},
            "page": page,
            "page_size": page_size,
            "posts": posts,
        }

    async def find_linked_accounts(self, username: str, platform: str) -> dict[str, Any]:
        p = platform.lower().strip()
        stored = await self.store.get_profile(p, username)
        if not stored:
            await self.get_detailed_profile(username, platform)
        linked = await self.store.get_linked_accounts(p, username)
        return {"linked_accounts": linked}

    async def refresh_social_data(self, username: str, platform: str) -> dict[str, Any]:
        return await self.get_detailed_profile(username, platform, force_refresh=True)

    def _normalize_platforms(self, platforms: list[str] | None) -> list[str]:
        if not platforms:
            return SUPPORTED_PLATFORMS_PRIORITY.copy()
        requested = [p.lower().strip() for p in platforms]
        dedup: list[str] = []
        for p in requested:
            if p in self.clients and p not in dedup:
                dedup.append(p)
        return dedup
