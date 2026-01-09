from __future__ import annotations

from typing import Any

__all__ = ["SherlockSource"]


def __getattr__(name: str) -> Any:
    if name == "SherlockSource":
        from osint.sources.sherlock_source import SherlockSource

        return SherlockSource
    raise AttributeError(name)
