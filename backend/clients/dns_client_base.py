"""
Base DNS Client for domain intelligence operations.

Defines the interface for DNS clients that can be extended for different
implementations (sync, async, cached, etc.).
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from abc import ABC, abstractmethod


@dataclass
class DnsRecord:
    """Represents a single DNS record."""
    value: str
    ttl: Optional[int] = None
    type: str = "A"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "value": self.value,
            "ttl": self.ttl,
            "type": self.type,
        }


@dataclass
class DnsResult:
    """Result of a DNS query."""
    domain: str
    record_type: str
    records: List[DnsRecord] = field(default_factory=list)
    found: bool = False
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "domain": self.domain,
            "record_type": self.record_type,
            "records": [r.to_dict() for r in self.records],
            "found": self.found,
            "error": self.error,
        }
    
    @property
    def values(self) -> List[str]:
        """Get list of record values."""
        return [r.value for r in self.records]


class BaseDnsClient(ABC):
    """Base class for DNS clients."""
    
    @abstractmethod
    async def resolve(
        self,
        domain: str,
        record_type: str = "A",
        timeout: Optional[float] = None,
    ) -> DnsResult:
        """
        Resolve DNS records for a domain.
        
        Args:
            domain: The domain name to query
            record_type: DNS record type (A, AAAA, MX, TXT, CNAME, NS, SOA, PTR, SRV, CAA)
            timeout: Query timeout in seconds
            
        Returns:
            DnsResult containing the DNS records
        """
        pass
    
    @abstractmethod
    async def resolve_all(self, domain: str) -> Dict[str, DnsResult]:
        """
        Resolve all common record types for a domain.
        
        Args:
            domain: The domain name to query
            
        Returns:
            Dictionary mapping record type to DnsResult
        """
        pass
    
    @abstractmethod
    async def resolve_multiple(
        self,
        domains: List[str],
        record_type: str = "A",
        timeout: Optional[float] = None,
    ) -> Dict[str, DnsResult]:
        """
        Resolve DNS records for multiple domains concurrently.
        
        Args:
            domains: List of domain names to query
            record_type: DNS record type
            timeout: Query timeout in seconds
            
        Returns:
            Dictionary mapping domain to DnsResult
        """
        pass
