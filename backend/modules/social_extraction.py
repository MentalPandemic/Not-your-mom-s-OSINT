from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any
from urllib.parse import urlparse


EMAIL_RE = re.compile(r"(?i)(?<![\w.+-])([a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,})(?![\w.+-])")
URL_RE = re.compile(
    r"(?i)\b((?:https?://|www\.)[a-z0-9\-._~%]+(?:\.[a-z0-9\-._~%]+)+(?:/[\w\-._~%!$&'()*+,;=:@/?#\[\]]*)?)"
)
PHONE_RE = re.compile(r"(?:(?:\+|00)\d{1,3}[\s\-]?)?(?:\(\d+\)[\s\-]?)?[\d\s\-]{7,}")


KNOWN_PLATFORM_DOMAINS: dict[str, list[str]] = {
    "twitter": ["twitter.com", "x.com"],
    "reddit": ["reddit.com"],
    "instagram": ["instagram.com"],
    "tiktok": ["tiktok.com"],
    "facebook": ["facebook.com"],
    "linkedin": ["linkedin.com"],
    "youtube": ["youtube.com", "youtu.be"],
    "github": ["github.com"],
    "medium": ["medium.com"],
    "mastodon": [],
    "bluesky": ["bsky.app"],
    "discord": ["discord.gg", "discord.com"],
    "twitch": ["twitch.tv"],
}


@dataclass
class NormalizedProfile:
    platform: str
    username: str
    profile_url: str | None = None
    display_name: str | None = None
    bio: str | None = None
    location: str | None = None
    verified: bool | None = None
    follower_count: int | None = None
    following_count: int | None = None
    post_count: int | None = None
    profile_image_url: str | None = None
    banner_image_url: str | None = None
    created_at: datetime | None = None
    raw: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        if self.created_at is not None:
            d["created_at"] = self.created_at.isoformat()
        return d


@dataclass
class NormalizedPost:
    platform: str
    username: str
    post_id: str | None
    url: str | None
    content: str | None
    title: str | None = None
    created_at: datetime | None = None
    like_count: int | None = None
    comment_count: int | None = None
    share_count: int | None = None
    view_count: int | None = None
    media_urls: list[str] = field(default_factory=list)
    hashtags: list[str] = field(default_factory=list)
    mentions: list[str] = field(default_factory=list)
    raw: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        if self.created_at is not None:
            d["created_at"] = self.created_at.isoformat()
        return d


@dataclass
class LinkedAccount:
    from_platform: str
    from_username: str
    linked_platform: str
    linked_username: str
    confidence: float
    evidence: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def extract_emails(text: str | None) -> list[str]:
    if not text:
        return []
    return sorted({m.group(1) for m in EMAIL_RE.finditer(text)})


def extract_urls(text: str | None) -> list[str]:
    if not text:
        return []
    urls: set[str] = set()
    for match in URL_RE.finditer(text):
        u = match.group(1)
        if u.lower().startswith("www."):
            u = "https://" + u
        urls.add(u)
    return sorted(urls)


def extract_phone_numbers(text: str | None) -> list[str]:
    if not text:
        return []
    candidates = [c.strip() for c in PHONE_RE.findall(text)]
    # Very light normalization; if phonenumbers is available, use it.
    try:
        import phonenumbers  # type: ignore

        normalized: set[str] = set()
        for c in candidates:
            try:
                num = phonenumbers.parse(c, None)
                if phonenumbers.is_valid_number(num):
                    normalized.add(phonenumbers.format_number(num, phonenumbers.PhoneNumberFormat.E164))
            except Exception:
                continue
        return sorted(normalized)
    except Exception:
        return sorted({re.sub(r"\s+", " ", c) for c in candidates if len(re.sub(r"\D", "", c)) >= 7})


def _domain(url: str) -> str | None:
    try:
        host = urlparse(url).netloc.lower()
    except Exception:
        return None
    if host.startswith("www."):
        host = host[4:]
    return host


def identify_platform_from_url(url: str) -> str | None:
    d = _domain(url)
    if not d:
        return None
    for platform, domains in KNOWN_PLATFORM_DOMAINS.items():
        if any(d == dom or d.endswith("." + dom) for dom in domains):
            return platform
    # Mastodon is instance-specific; treat any URL with /@user as mastodon-like.
    if re.search(r"/(@[A-Za-z0-9_\.\-]+)", url):
        return "mastodon"
    return None


def _extract_username_from_platform_url(platform: str, url: str) -> str | None:
    path = urlparse(url).path.strip("/")
    if not path:
        return None

    if platform in {"twitter", "instagram", "tiktok", "twitch"}:
        if path.startswith("@"):
            path = path[1:]
        return path.split("/")[0]

    if platform == "github":
        return path.split("/")[0]

    if platform == "reddit":
        # /user/<name>/
        parts = path.split("/")
        if len(parts) >= 2 and parts[0] in {"user", "u"}:
            return parts[1]
        return None

    if platform == "linkedin":
        parts = path.split("/")
        if len(parts) >= 2 and parts[0] == "in":
            return parts[1]
        return None

    if platform == "facebook":
        # could be /<username>
        return path.split("/")[0]

    if platform == "youtube":
        # handle forms: /@handle, /channel/ID
        parts = path.split("/")
        if parts[0].startswith("@"):
            return parts[0][1:]
        if len(parts) >= 2 and parts[0] in {"c", "user"}:
            return parts[1]
        return None

    if platform == "medium":
        if path.startswith("@"):
            return path[1:].split("/")[0]
        return path.split("/")[0]

    if platform in {"mastodon", "bluesky", "discord"}:
        return None

    return None


def extract_mentions(text: str | None) -> list[str]:
    if not text:
        return []
    # Very simple @handle extraction.
    handles = set(re.findall(r"(?<!\w)@([A-Za-z0-9_\.]{2,50})", text))
    return sorted(handles)


def extract_hashtags(text: str | None) -> list[str]:
    if not text:
        return []
    tags = set(re.findall(r"(?<!\w)#([A-Za-z0-9_]{2,100})", text))
    return sorted(tags)


def discover_linked_accounts(
    profile: NormalizedProfile | None,
    posts: list[NormalizedPost] | None = None,
) -> list[LinkedAccount]:
    if not profile:
        return []

    evidence_texts: list[str] = []
    if profile.bio:
        evidence_texts.append(profile.bio)
    if profile.profile_url:
        evidence_texts.append(profile.profile_url)
    if profile.raw:
        for v in profile.raw.values():
            if isinstance(v, str):
                evidence_texts.append(v)

    urls: set[str] = set()
    for t in evidence_texts:
        urls.update(extract_urls(t))

    if posts:
        for p in posts:
            if p.content:
                urls.update(extract_urls(p.content))
            if p.url:
                urls.add(p.url)

    linked: list[LinkedAccount] = []
    for u in sorted(urls):
        plat = identify_platform_from_url(u)
        if not plat or plat == profile.platform:
            continue
        extracted = _extract_username_from_platform_url(plat, u)
        if not extracted:
            continue
        linked.append(
            LinkedAccount(
                from_platform=profile.platform,
                from_username=profile.username,
                linked_platform=plat,
                linked_username=extracted,
                confidence=0.7,
                evidence={"url": u},
            )
        )

    # Also use mention patterns; confidence lower.
    mentions = set(extract_mentions(profile.bio or ""))
    if posts:
        for p in posts:
            mentions.update(p.mentions)

    for m in sorted(mentions):
        for plat in ("twitter", "instagram", "tiktok", "github", "twitch"):
            if plat == profile.platform:
                continue
            linked.append(
                LinkedAccount(
                    from_platform=profile.platform,
                    from_username=profile.username,
                    linked_platform=plat,
                    linked_username=m,
                    confidence=0.35,
                    evidence={"mention": f"@{m}"},
                )
            )

    # Deduplicate by (platform, username)
    dedup: dict[tuple[str, str], LinkedAccount] = {}
    for a in linked:
        key = (a.linked_platform, a.linked_username.lower())
        existing = dedup.get(key)
        if not existing or a.confidence > existing.confidence:
            dedup[key] = a

    return list(dedup.values())
