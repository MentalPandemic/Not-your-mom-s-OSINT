from __future__ import annotations

from typing import Any

__all__ = [
    "SherlockSource",
    "TwitterSource",
    "FacebookSource",
    "LinkedInSource",
    "InstagramSource",
]


def __getattr__(name: str) -> Any:
    if name == "SherlockSource":
        from osint.sources.sherlock_source import SherlockSource

        return SherlockSource
    if name == "TwitterSource":
        from osint.sources.twitter_source import TwitterSource

        return TwitterSource
    if name == "FacebookSource":
        from osint.sources.facebook_source import FacebookSource

        return FacebookSource
    if name == "LinkedInSource":
        from osint.sources.linkedin_source import LinkedInSource

        return LinkedInSource
    if name == "InstagramSource":
        from osint.sources.instagram_source import InstagramSource

        return InstagramSource
    raise AttributeError(name)
