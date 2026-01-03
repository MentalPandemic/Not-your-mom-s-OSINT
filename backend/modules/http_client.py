from __future__ import annotations

import asyncio
import json
import logging
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class HttpResponse:
    status: int
    headers: dict[str, str]
    text: str

    def json(self) -> Any:
        return json.loads(self.text)


class AsyncHttpClient:
    """Async HTTP client with a stdlib fallback.

    If aiohttp is installed, it will be used. Otherwise, it falls back to urllib
    executed in a thread.
    """

    def __init__(self, user_agent: str = "Not-your-moms-OSINT/1.0"):
        self.user_agent = user_agent
        try:
            import aiohttp  # noqa: F401

            self._aiohttp_available = True
        except Exception:
            self._aiohttp_available = False

    async def get(
        self,
        url: str,
        headers: dict[str, str] | None = None,
        timeout: int = 20,
    ) -> HttpResponse:
        if self._aiohttp_available:
            return await self._aiohttp_request("GET", url, headers=headers, timeout=timeout)
        return await asyncio.to_thread(self._urllib_request, "GET", url, None, headers, timeout)

    async def post(
        self,
        url: str,
        data: bytes | None = None,
        headers: dict[str, str] | None = None,
        timeout: int = 20,
    ) -> HttpResponse:
        if self._aiohttp_available:
            return await self._aiohttp_request("POST", url, data=data, headers=headers, timeout=timeout)
        return await asyncio.to_thread(self._urllib_request, "POST", url, data, headers, timeout)

    async def post_form(
        self,
        url: str,
        form: dict[str, str],
        headers: dict[str, str] | None = None,
        timeout: int = 20,
    ) -> HttpResponse:
        encoded = urllib.parse.urlencode(form).encode("utf-8")
        hdrs = {"Content-Type": "application/x-www-form-urlencoded"}
        if headers:
            hdrs.update(headers)
        return await self.post(url, data=encoded, headers=hdrs, timeout=timeout)

    async def get_json(self, url: str, headers: dict[str, str] | None = None, timeout: int = 20) -> Any:
        resp = await self.get(url, headers=headers, timeout=timeout)
        return resp.json()

    async def post_json(
        self,
        url: str,
        payload: Any,
        headers: dict[str, str] | None = None,
        timeout: int = 20,
    ) -> Any:
        data = json.dumps(payload).encode("utf-8")
        hdrs = {"Content-Type": "application/json", "Accept": "application/json"}
        if headers:
            hdrs.update(headers)
        resp = await self.post(url, data=data, headers=hdrs, timeout=timeout)
        return resp.json()

    async def _aiohttp_request(
        self,
        method: str,
        url: str,
        data: bytes | None = None,
        headers: dict[str, str] | None = None,
        timeout: int = 20,
    ) -> HttpResponse:
        import aiohttp

        hdrs = {"User-Agent": self.user_agent}
        if headers:
            hdrs.update(headers)
        async with aiohttp.ClientSession(headers=hdrs) as session:
            async with session.request(method, url, data=data, timeout=timeout) as r:
                text = await r.text()
                return HttpResponse(
                    status=r.status,
                    headers={k: v for k, v in r.headers.items()},
                    text=text,
                )

    def _urllib_request(
        self,
        method: str,
        url: str,
        data: bytes | None,
        headers: dict[str, str] | None,
        timeout: int,
    ) -> HttpResponse:
        hdrs = {"User-Agent": self.user_agent}
        if headers:
            hdrs.update(headers)

        req = urllib.request.Request(url, headers=hdrs, method=method, data=data)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                text = r.read().decode("utf-8", errors="replace")
                return HttpResponse(
                    status=getattr(r, "status", 200),
                    headers=dict(r.headers.items()),
                    text=text,
                )
        except urllib.error.HTTPError as e:
            text = e.read().decode("utf-8", errors="replace")
            logger.info("HTTP error %s for %s", e.code, url)
            return HttpResponse(status=e.code, headers=dict(e.headers.items()), text=text)
