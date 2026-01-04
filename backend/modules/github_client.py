import asyncio
import aiohttp
from github import Github, RateLimitExceededException
import logging
import time

logger = logging.getLogger(__name__)

class GitHubClient:
    def __init__(self, token=None):
        self.token = token
        self.github = Github(token) if token else Github()
        self.session = None

    async def get_session(self):
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                headers={"Authorization": f"token {self.token}"} if self.token else {}
            )
        return self.session

    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()

    def handle_rate_limit(self):
        rate_limit = self.github.get_rate_limit()
        core = rate_limit.core
        if core.remaining == 0:
            reset_time = core.reset.timestamp()
            sleep_time = reset_time - time.time() + 1
            if sleep_time > 0:
                logger.warning(f"Rate limit exceeded. Sleeping for {sleep_time} seconds")
                time.sleep(sleep_time)

    async def request(self, method, url, **kwargs):
        session = await self.get_session()
        async with session.request(method, url, **kwargs) as response:
            if response.status == 403 and "X-RateLimit-Remaining" in response.headers:
                if response.headers["X-RateLimit-Remaining"] == "0":
                    reset_time = int(response.headers["X-RateLimit-Reset"])
                    sleep_time = reset_time - time.time() + 1
                    if sleep_time > 0:
                        logger.warning(f"Async rate limit exceeded. Sleeping for {sleep_time} seconds")
                        await asyncio.sleep(sleep_time)
                        return await self.request(method, url, **kwargs)
            
            response.raise_for_status()
            return await response.json()

    async def get_user(self, username):
        self.handle_rate_limit()
        return self.github.get_user(username)

    async def get_repo(self, full_name):
        self.handle_rate_limit()
        return self.github.get_repo(full_name)
