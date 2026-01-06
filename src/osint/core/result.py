"""Result data structures for OSINT operations."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional


@dataclass
class SearchResult:
    """Represents a single search result from an OSINT source.

    Attributes:
        source: The name of the source where the result was found
        url: The URL where the result was found
        found: Whether the username/data was found
        data: Additional data associated with the result
        timestamp: When the result was obtained
    """

    source: str
    url: Optional[str] = None
    found: bool = False
    data: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict[str, Any]:
        """Convert the SearchResult to a dictionary.

        Returns:
            Dictionary representation of the result
        """
        return {
            "source": self.source,
            "url": self.url,
            "found": self.found,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SearchResult":
        """Create a SearchResult from a dictionary.

        Args:
            data: Dictionary containing result data

        Returns:
            SearchResult instance
        """
        timestamp = data.get("timestamp")
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)

        return cls(
            source=data["source"],
            url=data.get("url"),
            found=data.get("found", False),
            data=data.get("data", {}),
            timestamp=timestamp or datetime.utcnow(),
        )


@dataclass
class CorrelationResult:
    """Represents a correlation between data points.

    Attributes:
        correlation_type: Type of correlation (e.g., "username", "email", "ip")
        confidence: Confidence score of the correlation (0.0 to 1.0)
        sources: List of sources involved in the correlation
        data: Correlated data points
        metadata: Additional metadata about the correlation
    """

    correlation_type: str
    confidence: float
    sources: list[str] = field(default_factory=list)
    data: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert the CorrelationResult to a dictionary.

        Returns:
            Dictionary representation of the correlation
        """
        return {
            "correlation_type": self.correlation_type,
            "confidence": self.confidence,
            "sources": self.sources,
            "data": self.data,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CorrelationResult":
        """Create a CorrelationResult from a dictionary.

        Args:
            data: Dictionary containing correlation data

        Returns:
            CorrelationResult instance
        """
        return cls(
            correlation_type=data["correlation_type"],
            confidence=data.get("confidence", 0.0),
            sources=data.get("sources", []),
            data=data.get("data", {}),
            metadata=data.get("metadata", {}),
        )
