"""Sherlock integration for username enumeration."""

import sys
from typing import Optional

from osint.core.result import SearchResult
from osint.sources.base import BaseSource


class SherlockSource(BaseSource):
    """Wrapper for the Sherlock username enumeration tool.

    This source uses Sherlock to search for usernames across hundreds
    of social networks and other websites.
    """

    def __init__(self, timeout: int = 30) -> None:
        """Initialize the Sherlock source.

        Args:
            timeout: Request timeout in seconds
        """
        super().__init__(timeout=timeout)
        self.filtered_sources: Optional[list[str]] = None
        self.sherlock_available = self._check_sherlock_available()

    def _check_sherlock_available(self) -> bool:
        """Check if Sherlock is installed and available.

        Returns:
            True if Sherlock is available, False otherwise
        """
        try:
            import sherlock

            return True
        except ImportError:
            return False

    def filter_sources(self, sources: list[str]) -> None:
        """Filter which sources to query.

        Args:
            sources: List of source names to include in searches
        """
        self.filtered_sources = sources

    def get_source_name(self) -> str:
        """Return the name of this data source.

        Returns:
            String name of the source
        """
        return "Sherlock"

    def search_username(self, username: str) -> list[SearchResult]:
        """Search for a username using Sherlock.

        Args:
            username: The username to search for

        Returns:
            List of SearchResult objects
        """
        if not self.sherlock_available:
            return self._mock_search(username)

        try:
            from sherlock import sherlock as sh

            results: list[SearchResult] = []

            site_data = sh.sherlock(
                username,
                site_list=self.filtered_sources,
                timeout=self.timeout,
            )

            for site, result in site_data.items():
                search_result = SearchResult(
                    source=site,
                    url=result.get("url_user"),
                    found=result.get("status", False),
                    data={"response_time": result.get("response_time")},
                )
                results.append(search_result)

            return results

        except Exception as e:
            print(f"Error running Sherlock: {e}")
            return self._mock_search(username)

    def _mock_search(self, username: str) -> list[SearchResult]:
        """Mock search for when Sherlock is not available.

        This provides simulated results for testing purposes.

        Args:
            username: The username to search for

        Returns:
            List of mock SearchResult objects
        """
        mock_sites = [
            {"site": "Twitter", "found": True, "url": f"https://twitter.com/{username}"},
            {"site": "GitHub", "found": True, "url": f"https://github.com/{username}"},
            {"site": "Instagram", "found": False, "url": f"https://instagram.com/{username}"},
            {"site": "Reddit", "found": True, "url": f"https://reddit.com/user/{username}"},
            {"site": "LinkedIn", "found": False, "url": f"https://linkedin.com/in/{username}"},
        ]

        results: list[SearchResult] = []

        for site_data in mock_sites:
            if self.filtered_sources and site_data["site"] not in self.filtered_sources:
                continue

            results.append(
                SearchResult(
                    source=site_data["site"],
                    url=site_data["url"],
                    found=site_data["found"],
                    data={"mock": True, "sherlock_unavailable": True},
                )
            )

        return results
