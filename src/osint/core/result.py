"""
Result data structures for OSINT operations.

This module defines the standardized result objects used throughout the OSINT platform.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime


@dataclass
class SearchResult:
    """Represents a single OSINT search result."""
    
    platform: str
    username: str
    url: str
    found: bool
    additional_data: Dict[str, Any] = field(default_factory=dict)
    timestamp: Optional[datetime] = None
    
    def __post_init__(self):
        """Initialize timestamp if not provided."""
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "platform": self.platform,
            "username": self.username,
            "url": self.url,
            "found": self.found,
            "additional_data": self.additional_data,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }


@dataclass
class OSINTResult:
    """Aggregated result from OSINT operations."""
    
    query: str
    query_type: str  # "username", "email", "phone", etc.
    found_accounts: List[SearchResult] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: Optional[datetime] = None
    
    def __post_init__(self):
        """Initialize timestamp if not provided."""
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
    
    def add_result(self, result: SearchResult):
        """Add a search result to the collection."""
        self.found_accounts.append(result)
    
    @property
    def total_found(self) -> int:
        """Get the total number of found accounts."""
        return len([r for r in self.found_accounts if r.found])
    
    @property
    def total_searched(self) -> int:
        """Get the total number of platforms searched."""
        return len(self.found_accounts)
    
    def get_by_platform(self, platform: str) -> Optional[SearchResult]:
        """Get result for a specific platform."""
        for result in self.found_accounts:
            if result.platform.lower() == platform.lower():
                return result
        return None
    
    def get_found_accounts(self) -> List[SearchResult]:
        """Get only the accounts that were found."""
        return [r for r in self.found_accounts if r.found]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "query": self.query,
            "query_type": self.query_type,
            "found_accounts": [r.to_dict() for r in self.found_accounts],
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "summary": {
                "total_found": self.total_found,
                "total_searched": self.total_searched,
            }
        }
    
    def __str__(self) -> str:
        """String representation of the result."""
        return f"OSINTResult(query='{self.query}', found={self.total_found}/{self.total_searched})"
