from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable, Iterable, Sequence

from osint.core.models import QueryResult


ProgressCallback = Callable[[int, int], None]


class DataSource(ABC):
    name: str

    @abstractmethod
    def search(
        self,
        usernames: Sequence[str],
        *,
        sites: Sequence[str] | None = None,
        category: str | None = None,
        timeout: float | None = None,
        threads: int | None = None,
        no_nsfw: bool | None = None,
        progress_callback: ProgressCallback | None = None,
    ) -> list[QueryResult]:
        raise NotImplementedError

    @abstractmethod
    def available_sites(self) -> list[str]:
        raise NotImplementedError

    @abstractmethod
    def available_categories(self) -> list[str]:
        raise NotImplementedError


def normalize_list(values: str | Iterable[str] | None) -> list[str]:
    if values is None:
        return []

    if isinstance(values, str):
        raw = [values]
    else:
        raw = list(values)

    out: list[str] = []
    for item in raw:
        for part in str(item).split(","):
            part = part.strip()
            if part:
                out.append(part)

    return out
