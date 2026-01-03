from __future__ import annotations

from datetime import datetime

from backend.clients.base import SocialClient
from backend.modules.rate_limit import RateLimitPolicy
from backend.modules.social_extraction import NormalizedPost, NormalizedProfile


class GitHubClient(SocialClient):
    platform = "github"
    rate_limit = RateLimitPolicy(requests=60, per_seconds=60)

    def profile_url(self, username: str) -> str:
        return f"https://github.com/{username}"

    async def fetch_profile(self, username: str) -> NormalizedProfile | None:
        url = f"https://api.github.com/users/{username}"
        headers = {"Accept": "application/vnd.github+json"}
        token = self._token()
        if token:
            headers["Authorization"] = f"Bearer {token}"

        async def _do():
            resp = await self.http.get(url, headers=headers)
            self._raise_for_status(resp.status, f"fetch_profile({username})")
            return resp.json()

        data = await self._limited(_do)
        created_at = None
        if data.get("created_at"):
            try:
                created_at = datetime.fromisoformat(data["created_at"].replace("Z", "+00:00"))
            except Exception:
                created_at = None

        return NormalizedProfile(
            platform=self.platform,
            username=username,
            profile_url=data.get("html_url") or self.profile_url(username),
            display_name=data.get("name"),
            bio=data.get("bio"),
            location=data.get("location"),
            verified=None,
            follower_count=self._int(data.get("followers")),
            following_count=self._int(data.get("following")),
            post_count=self._int(data.get("public_repos")),
            profile_image_url=data.get("avatar_url"),
            created_at=created_at,
            raw=data,
        )

    async def fetch_posts(self, username: str, max_items: int = 100) -> list[NormalizedPost]:
        # Use public events as a lightweight activity source.
        url = f"https://api.github.com/users/{username}/events/public?per_page={min(100, max_items)}"
        headers = {"Accept": "application/vnd.github+json"}
        token = self._token()
        if token:
            headers["Authorization"] = f"Bearer {token}"

        async def _do():
            resp = await self.http.get(url, headers=headers)
            self._raise_for_status(resp.status, f"fetch_posts({username})")
            return resp.json()

        events = await self._limited(_do)
        posts: list[NormalizedPost] = []
        for e in (events or [])[:max_items]:
            created_at = None
            if e.get("created_at"):
                try:
                    created_at = datetime.fromisoformat(e["created_at"].replace("Z", "+00:00"))
                except Exception:
                    created_at = None
            posts.append(
                NormalizedPost(
                    platform=self.platform,
                    username=username,
                    post_id=e.get("id"),
                    url=self.profile_url(username),
                    title=e.get("type"),
                    content=None,
                    created_at=created_at,
                    raw=e,
                )
            )
        return posts

    async def extract_emails_from_recent_commits(self, username: str, max_repos: int = 5, max_commits_per_repo: int = 50) -> list[str]:
        token = self._token()
        headers = {"Accept": "application/vnd.github+json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"

        # List repos
        repos_url = f"https://api.github.com/users/{username}/repos?per_page={min(100, max_repos)}&sort=updated"

        async def _do_repos():
            resp = await self.http.get(repos_url, headers=headers)
            self._raise_for_status(resp.status, f"repos({username})")
            return resp.json()

        repos = await self._limited(_do_repos)
        emails: set[str] = set()
        for repo in (repos or [])[:max_repos]:
            full_name = repo.get("full_name")
            if not full_name:
                continue
            commits_url = f"https://api.github.com/repos/{full_name}/commits?per_page={min(100, max_commits_per_repo)}&author={username}"

            async def _do_commits(url=commits_url):
                resp = await self.http.get(url, headers=headers)
                if resp.status >= 400:
                    return []
                try:
                    return resp.json()
                except Exception:
                    return []

            commits = await self._limited(_do_commits)
            for c in commits or []:
                commit = (c.get("commit") or {})
                author = (commit.get("author") or {})
                email = author.get("email")
                if email and "noreply" not in email:
                    emails.add(email)
        return sorted(emails)
