from __future__ import annotations

import re
from typing import Any

from backend.modules.http_client import AsyncHttpClient


def _extract_meta(html: str, key: str) -> str | None:
    # Matches both property and name meta tags.
    m = re.search(
        rf"<meta[^>]+(?:property|name)=\"{re.escape(key)}\"[^>]+content=\"(.*?)\"",
        html,
        flags=re.IGNORECASE,
    )
    if not m:
        return None
    return m.group(1)


async def scrape_open_graph(url: str, http: AsyncHttpClient | None = None) -> dict[str, Any] | None:
    client = http or AsyncHttpClient()
    resp = await client.get(url)
    if resp.status >= 400:
        return None

    html = resp.text
    title = _extract_meta(html, "og:title") or _extract_meta(html, "twitter:title")
    desc = _extract_meta(html, "og:description") or _extract_meta(html, "description")
    image = _extract_meta(html, "og:image") or _extract_meta(html, "twitter:image")

    if not any([title, desc, image]):
        return None

    return {"title": title, "description": desc, "image": image, "url": url}
