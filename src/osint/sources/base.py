"""Abstract base class for OSINT data sources."""

from abc import ABC, abstractmethod
from typing import Optional

from osint.core.result import SearchResult


class BaseSource(ABC):
    """Abstract base class that all OSINT data sources must inherit from.

    This class defines the interface that all data sources must implement
    to be compatible with the Aggregator class.
    """

    def __init__(self, timeout: int = 30) -> None:
        """Initialize the data source.

        Args:
            timeout: Request timeout in seconds
        """
        self.timeout = timeout
        self.enabled = True

    @abstractmethod
    def search_username(self, username: str) -> list[SearchResult]:
        """Search for a username across this data source.

        Args:
            username: The username to search for

        Returns:
            List of SearchResult objects
        """
        pass

    @abstractmethod
    def get_source_name(self) -> str:
        """Return the name of this data source.

        Returns:
            String name of the source
        """
        pass

    def enable(self) -> None:
        """Enable this data source."""
        self.enabled = True

    def disable(self) -> None:
        """Disable this data source."""
        self.enabled = False

    def is_enabled(self) -> bool:
        """Check if this data source is enabled.

        Returns:
            True if enabled, False otherwise
        """
        return self.enabled
