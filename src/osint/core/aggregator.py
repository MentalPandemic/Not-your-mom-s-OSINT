from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from osint.core.models import QueryResult, QueryStatus
from osint.utils.config_manager import read_config


@dataclass(slots=True)
class AggregationStats:
    total: int
    found: int
    not_found: int
    error: int


@dataclass(slots=True)
class AggregationResult:
    results: list[QueryResult]
    stats: AggregationStats


class Aggregator:
    def __init__(self, config: dict[str, Any] | None = None) -> None:
        self.config = config or read_config()

    def _get_sources(self) -> dict[str, Any]:
        sources: dict[str, Any] = {}

        try:
            from osint.sources.sherlock_source import SherlockSource

            sources["sherlock"] = SherlockSource(self.config)
        except ImportError:
            pass

        return sources

    def search_usernames(
        self,
        usernames: list[str],
        *,
        sources: list[str] | None = None,
        category: str | None = None,
        sites: list[str] | None = None,
        timeout: float | None = None,
        threads: int | None = None,
        no_nsfw: bool | None = None,
        progress_callback: Any | None = None,
    ) -> AggregationResult:
        sources_map = self._get_sources()

        source_names = sources or ["all"]
        if "all" in [s.lower() for s in source_names]:
            source_names = list(sources_map.keys())

        all_results: list[QueryResult] = []

        for source_name in source_names:
            src = sources_map.get(source_name.lower())
            if src is None:
                raise ValueError(f"Unknown source: {source_name}")

            all_results.extend(
                src.search(
                    usernames,
                    sites=sites,
                    category=category,
                    timeout=timeout,
                    threads=threads,
                    no_nsfw=no_nsfw,
                    progress_callback=progress_callback,
                )
            )

        stats = AggregationStats(
            total=len(all_results),
            found=sum(1 for r in all_results if r.status == QueryStatus.FOUND),
            not_found=sum(1 for r in all_results if r.status == QueryStatus.NOT_FOUND),
            error=sum(1 for r in all_results if r.status == QueryStatus.ERROR),
        )

        return AggregationResult(results=all_results, stats=stats)
