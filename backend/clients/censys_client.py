"""
Censys API Client for domain and IP intelligence.

Uses Censys Search API to find certificates, hosts, and infrastructure.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from censys.search import SearchClient
from censis.exceptions import CensysException

logger = logging.getLogger(__name__)


@dataclass
class CensysHost:
    """Host information from Censys."""
    ip: str
    ports: List[int] = field(default_factory=list)
    services: Dict[int, Dict[str, str]] = field(default_factory=dict)
    protocols: List[str] = field(default_factory=list)
    location: Dict[str, Any] = field(default_factory=dict)
    autonomous_system: Dict[str, Any] = field(default_factory=dict)
    dns: Dict[str, Any] = field(default_factory=dict)
    last_updated: Optional[datetime] = None
    operating_system: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "ip": self.ip,
            "ports": self.ports,
            "services": self.services,
            "protocols": self.protocols,
            "location": self.location,
            "autonomous_system": self.autonomous_system,
            "dns": self.dns,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None,
            "operating_system": self.operating_system,
        }


@dataclass
class CensysCertificate:
    """Certificate information from Censys."""
    fingerprint: str
    common_name: str
    subject_alternative_names: List[str] = field(default_factory=list)
    issuer: Dict[str, str] = field(default_factory=dict)
    validity: Dict[str, datetime] = field(default_factory=dict)
    signature_algorithm: str = ""
    public_key: Dict[str, Any] = field(default_factory=dict)
    serial_number: str = ""
    crl_distribution: List[str] = field(default_factory=list)
    ca_certificate: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "fingerprint": self.fingerprint,
            "common_name": self.common_name,
            "subject_alternative_names": self.subject_alternative_names,
            "issuer": self.issuer,
            "validity": {
                "not_before": self.validity.get("not_before").isoformat() if self.validity.get("not_before") else None,
                "not_after": self.validity.get("not_after").isoformat() if self.validity.get("not_after") else None,
            } if self.validity else {},
            "signature_algorithm": self.signature_algorithm,
            "public_key": self.public_key,
            "serial_number": self.serial_number,
            "crl_distribution": self.crl_distribution,
            "ca_certificate": self.ca_certificate,
        }


@dataclass
class CensysSearchResult:
    """Result from Censys search."""
    query: str
    hosts: List[CensysHost] = field(default_factory=list)
    certificates: List[CensysCertificate] = field(default_factory=list)
    total_hosts: int = 0
    total_certificates: int = 0
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "query": self.query,
            "hosts": [h.to_dict() for h in self.hosts],
            "certificates": [c.to_dict() for c in self.certificates],
            "total_hosts": self.total_hosts,
            "total_certificates": self.total_certificates,
            "error": self.error,
        }


class CensysClient:
    """
    Client for Censys Search API.
    
    Provides access to Censys data for:
    - Host discovery and enumeration
    - Certificate search
    - ASN and IP range analysis
    - Service detection
    
    Requires Censys API credentials.
    """
    
    DEFAULT_TIMEOUT = 30.0
    RATE_LIMIT_REQUESTS_PER_SEC = 2
    MAX_RESULTS = 100
    
    def __init__(
        self,
        api_id: str,
        api_secret: str,
        timeout: float = DEFAULT_TIMEOUT,
        rate_limit: float = 1.0 / RATE_LIMIT_REQUESTS_PER_SEC,
    ):
        self.api_id = api_id
        self.api_secret = api_secret
        self.timeout = timeout
        self.rate_limit = rate_limit
        self._client: Optional[SearchClient] = None
        self._last_request_time = 0.0
        
    @property
    def client(self) -> SearchClient:
        """Get or create Censys client."""
        if self._client is None:
            self._client = SearchClient(
                api_id=self.api_id,
                api_secret=self.api_secret,
            )
        return self._client
    
    async def search_hosts(
        self,
        query: str,
        per_page: int = 50,
        cursor: Optional[str] = None,
    ) -> CensysSearchResult:
        """
        Search for hosts matching a query.
        
        Args:
            query: Censys search query (e.g., "services.http.response.headers.location: /admin")
            per_page: Results per page
            cursor: Pagination cursor
            
        Returns:
            CensysSearchResult with matching hosts
        """
        await self._rate_limit()
        
        try:
            loop = asyncio.get_event_loop()
            
            def _search():
                return self.client.hosts.search(
                    query,
                    per_page=per_page,
                    cursor=cursor,
                    timeout=self.timeout,
                )
            
            result = await loop.run_in_executor(None, _search)
            
            hosts = []
            for hit in result.get("hits", []):
                host = self._parse_host(hit)
                hosts.append(host)
            
            return CensysSearchResult(
                query=query,
                hosts=hosts,
                total_hosts=result.get("total", 0),
            )
            
        except CensysException as e:
            logger.error(f"Censys host search error: {e}")
            return CensysSearchResult(query=query, error=str(e))
        except Exception as e:
            logger.error(f"Censys search failed: {e}")
            return CensysSearchResult(query=query, error=str(e))
    
    async def search_certificates(
        self,
        query: str,
        per_page: int = 50,
        cursor: Optional[str] = None,
    ) -> CensysSearchResult:
        """
        Search for certificates matching a query.
        
        Args:
            query: Censys search query
            per_page: Results per page
            cursor: Pagination cursor
            
        Returns:
            CensysSearchResult with matching certificates
        """
        await self._rate_limit()
        
        try:
            loop = asyncio.get_event_loop()
            
            def _search():
                return self.client.certificates.search(
                    query,
                    per_page=per_page,
                    cursor=cursor,
                    timeout=self.timeout,
                )
            
            result = await loop.run_in_executor(None, _search)
            
            certificates = []
            for hit in result.get("hits", []):
                cert = self._parse_certificate(hit)
                certificates.append(cert)
            
            return CensysSearchResult(
                query=query,
                certificates=certificates,
                total_certificates=result.get("total", 0),
            )
            
        except CensysException as e:
            logger.error(f"Censys cert search error: {e}")
            return CensysSearchResult(query=query, error=str(e))
        except Exception as e:
            logger.error(f"Censys certificate search failed: {e}")
            return CensysSearchResult(query=query, error=str(e))
    
    async def get_host_by_ip(
        self,
        ip: str,
    ) -> Optional[CensysHost]:
        """
        Get host details by IP address.
        
        Args:
            ip: IP address to look up
            
        Returns:
            CensysHost or None if not found
        """
        await self._rate_limit()
        
        try:
            loop = asyncio.get_event_loop()
            
            def _get():
                return self.client.hosts.get(ip, timeout=self.timeout)
            
            result = await loop.run_in_executor(None, _get)
            
            if result:
                return self._parse_host(result)
            return None
            
        except Exception as e:
            logger.error(f"Failed to get host {ip}: {e}")
            return None
    
    async def get_certificate_by_fingerprint(
        self,
        fingerprint: str,
    ) -> Optional[CensysCertificate]:
        """
        Get certificate details by fingerprint.
        
        Args:
            fingerprint: SHA-256 fingerprint of certificate
            
        Returns:
            CensysCertificate or None if not found
        """
        await self._rate_limit()
        
        try:
            loop = asyncio.get_event_loop()
            
            def _get():
                return self.client.certificates.get(fingerprint, timeout=self.timeout)
            
            result = await loop.run_in_executor(None, _get)
            
            if result:
                return self._parse_certificate(result)
            return None
            
        except Exception as e:
            logger.error(f"Failed to get certificate {fingerprint}: {e}")
            return None
    
    async def search_domains_on_ip(
        self,
        ip: str,
    ) -> List[str]:
        """
        Find all domains hosted on an IP address.
        
        Args:
            ip: IP address to search
            
        Returns:
            List of domain names
        """
        result = await self.search_hosts(f"ip: {ip}")
        
        domains = set()
        for host in result.hosts:
            for hostname in host.dns.get("reverse_dns", {}).get("names", []):
                domains.add(hostname)
            for service in host.services.values():
                if "hostname" in service:
                    domains.add(service["hostname"])
        
        return list(domains)
    
    async def search_by_issuer(
        self,
        issuer: str,
        limit: int = 100,
    ) -> List[CensysCertificate]:
        """
        Find certificates by issuer organization.
        
        Args:
            issuer: Issuer organization name
            limit: Maximum results
            
        Returns:
            List of CensysCertificate objects
        """
        query = f'issuer.organization: "{issuer}"'
        result = await self.search_certificates(query, per_page=limit)
        return result.certificates
    
    async def search_by_common_name(
        self,
        common_name: str,
        limit: int = 100,
    ) -> List[CensysCertificate]:
        """
        Find certificates by common name.
        
        Args:
            common_name: Certificate common name
            limit: Maximum results
            
        Returns:
            List of CensysCertificate objects
        """
        query = f'names: "{common_name}"'
        result = await self.search_certificates(query, per_page=limit)
        return result.certificates
    
    def _parse_host(self, data: Dict[str, Any]) -> CensysHost:
        """Parse host data from Censys response."""
        services = {}
        ports = []
        protocols = []
        
        for service in data.get("services", []):
            port = service.get("port", 0)
            ports.append(port)
            protocols.append(service.get("service_name", ""))
            
            services[port] = {
                "service_name": service.get("service_name"),
                "banner": service.get("banner"),
                "response": service.get("response"),
                "transport": service.get("transport_protocol"),
                "http": service.get("http"),
            }
        
        location = data.get("location", {})
        if location:
            location = {
                "country": location.get("country"),
                "country_code": location.get("country_code"),
                "city": location.get("city"),
                "latitude": location.get("latitude"),
                "longitude": location.get("longitude"),
                "timezone": location.get("time_zone"),
            }
        
        autonomous_system = data.get("autonomous_system", {})
        
        dns = data.get("dns", {})
        reverse_dns = dns.get("reverse_dns", {})
        
        last_updated = data.get("last_updated")
        if last_updated:
            last_updated = datetime.fromisoformat(last_updated.replace("Z", "+00:00"))
        
        return CensysHost(
            ip=data.get("ip", ""),
            ports=list(set(ports)),
            services=services,
            protocols=list(set(protocols)),
            location=location,
            autonomous_system=autonomous_system,
            dns={
                "reverse_dns": {
                    "names": reverse_dns.get("names", []),
                    "record_type": reverse_dns.get("record_type"),
                },
                "nameservers": dns.get("nameservers", []),
            },
            last_updated=last_updated,
            operating_system=data.get("operating_system", {}).get("product"),
        )
    
    def _parse_certificate(self, data: Dict[str, Any]) -> CensysCertificate:
        """Parse certificate data from Censys response."""
        validity = data.get("validity", {})
        
        not_before = validity.get("not_before")
        not_after = validity.get("not_after")
        
        if not_before:
            not_before = datetime.fromisoformat(not_before.replace("Z", "+00:00"))
        if not_after:
            not_after = datetime.fromisoformat(not_after.replace("Z", "+00:00"))
        
        return CensysCertificate(
            fingerprint=data.get("fingerprint_sha256", ""),
            common_name=data.get("parsed.subject", {}).get("common_name", ""),
            subject_alternative_names=data.get("parsed.subject_alternative_name", {}).get("dns_names", []),
            issuer={
                "organization": data.get("parsed.issuer", {}).get("organization"),
                "common_name": data.get("parsed.issuer", {}).get("common_name"),
                "organizational_unit": data.get("parsed.issuer", {}).get("organizational_unit"),
            },
            validity={"not_before": not_before, "not_after": not_after},
            signature_algorithm=data.get("signature_algorithm", ""),
            public_key={
                "algorithm": data.get("parsed.public_key", {}).get("algorithm"),
                "key_size": data.get("parsed.public_key", {}).get("key_size"),
                "curve": data.get("parsed.public_key", {}).get("curve"),
            },
            serial_number=data.get("serial_number", ""),
            crl_distribution=data.get("crl_distribution_points", []),
            ca_certificate=data.get("extensions", {}).get("basic_constraints", {}).get("is_ca", False),
        )
    
    async def _rate_limit(self):
        """Enforce rate limiting."""
        now = asyncio.get_event_loop().time()
        elapsed = now - self._last_request_time
        
        if elapsed < self.rate_limit:
            await asyncio.sleep(self.rate_limit - elapsed)
        
        self._last_request_time = asyncio.get_event_loop().time()
    
    async def close(self):
        """Close the Censys client."""
        if self._client:
            self._client.close()
            self._client = None
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
