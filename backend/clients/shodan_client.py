"""
Shodan API Client for internet search and vulnerability data.

Uses Shodan API to find devices, services, and vulnerabilities.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

import shodan
from shodan import APIError

logger = logging.getLogger(__name__)


@dataclass
class ShodanHost:
    """Host information from Shodan."""
    ip: str
    ports: List[int] = field(default_factory=list)
    services: Dict[int, Dict[str, Any]] = field(default_factory=dict)
    location: Dict[str, Any] = field(default_factory=dict)
    autonomous_system: Dict[str, Any] = field(default_factory=dict)
    uptime: int = 0
    last_update: Optional[datetime] = None
    tags: List[str] = field(default_factory=list)
    vulns: List[str] = field(default_factory=list)
    hostnames: List[str] = field(default_factory=list)
    domains: List[str] = field(default_factory=list)
    org: str = ""
    operating_system: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "ip": self.ip,
            "ports": self.ports,
            "services": self.services,
            "location": self.location,
            "autonomous_system": self.autonomous_system,
            "uptime": self.uptime,
            "last_update": self.last_update.isoformat() if self.last_update else None,
            "tags": self.tags,
            "vulnerabilities": self.vulns,
            "hostnames": self.hostnames,
            "domains": self.domains,
            "organization": self.org,
            "operating_system": self.operating_system,
        }


@dataclass
class ShodanService:
    """Service information from Shodan."""
    port: int
    product: Optional[str] = None
    version: Optional[str] = None
    banner: Optional[str] = None
    module: Optional[str] = None
    transport: str = "tcp"
    ssl: Dict[str, Any] = field(default_factory=dict)
    http: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "port": self.port,
            "product": self.product,
            "version": self.version,
            "banner": self.banner,
            "module": self.module,
            "transport": self.transport,
            "ssl": self.ssl,
            "http": self.http,
        }


@dataclass
class ShodanSearchResult:
    """Result from Shodan search."""
    query: str
    hosts: List[ShodanHost] = field(default_factory=list)
    total: int = 0
    facets: Dict[str, List[Dict[str, Any]]] = field(default_factory=dict)
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "query": self.query,
            "hosts": [h.to_dict() for h in self.hosts],
            "total": self.total,
            "facets": self.facets,
            "error": self.error,
        }


@dataclass
class ShodanExploit:
    """Exploit information from Shodan."""
    id: str
    title: Optional[str] = None
    description: Optional[str] = None
    author: Optional[str] = None
    platform: Optional[str] = None
    type: Optional[str] = None
    port: Optional[int] = None
    cve: List[str] = field(default_factory=list)
    osvdb: List[str] = field(default_factory=list)
    bid: List[str] = field(default_factory=list)
    source: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "author": self.author,
            "platform": self.platform,
            "type": self.type,
            "port": self.port,
            "cve": self.cve,
            "osvdb": self.osvdb,
            "bid": self.bid,
            "source": self.source,
        }


class ShodanClient:
    """
    Client for Shodan API.
    
    Provides access to Shodan data for:
    - Host discovery and enumeration
    - Service detection
    - Vulnerability information
    - Exploit search
    - Network alerts
    
    Requires Shodan API key.
    """
    
    DEFAULT_TIMEOUT = 30.0
    RATE_LIMIT_DELAY = 1.0  # Shodan free tier limit
    
    def __init__(
        self,
        api_key: str,
        timeout: float = DEFAULT_TIMEOUT,
        rate_limit_delay: float = RATE_LIMIT_DELAY,
    ):
        self.api_key = api_key
        self.timeout = timeout
        self.rate_limit_delay = rate_limit_delay
        self._client: Optional[shodan.Shodan] = None
        self._last_request_time = 0.0
        
    @property
    def client(self) -> shodan.Shodan:
        """Get or create Shodan client."""
        if self._client is None:
            self._client = shodan.Shodan(self.api_key)
        return self._client
    
    async def search(
        self,
        query: str,
        limit: int = 100,
        offset: int = 0,
        facets: Optional[List[str]] = None,
    ) -> ShodanSearchResult:
        """
        Search Shodan for hosts matching a query.
        
        Args:
            query: Shodan search query
            limit: Maximum number of results
            offset: Result offset for pagination
            facets: Facet fields to aggregate
            
        Returns:
            ShodanSearchResult with matching hosts
        """
        await self._rate_limit()
        
        try:
            loop = asyncio.get_event_loop()
            
            def _search():
                return self.client.search(
                    query,
                    limit=limit,
                    offset=offset,
                    facets=facets or [],
                )
            
            result = await loop.run_in_executor(None, _search)
            
            hosts = []
            for match in result.get("matches", []):
                host = self._parse_host(match)
                hosts.append(host)
            
            return ShodanSearchResult(
                query=query,
                hosts=hosts,
                total=result.get("total", 0),
                facets=result.get("facets", {}),
            )
            
        except APIError as e:
            logger.error(f"Shodan search error: {e}")
            return ShodanSearchResult(query=query, error=str(e))
        except Exception as e:
            logger.error(f"Shodan search failed: {e}")
            return ShodanSearchResult(query=query, error=str(e))
    
    async def host(
        self,
        ip: str,
        history: bool = False,
    ) -> Optional[ShodanHost]:
        """
        Get detailed information about a host.
        
        Args:
            ip: IP address to look up
            history: Include historical data
            
        Returns:
            ShodanHost or None if not found
        """
        await self._rate_limit()
        
        try:
            loop = asyncio.get_event_loop()
            
            def _get():
                return self.client.host(ip, history=history, timeout=self.timeout)
            
            result = await loop.run_in_executor(None, _get)
            
            if result:
                return self._parse_host_details(result)
            return None
            
        except APIError as e:
            logger.error(f"Shodan host lookup error: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to get host {ip}: {e}")
            return None
    
    async def search_exploits(
        self,
        query: str,
        limit: int = 100,
    ) -> List[ShodanExploit]:
        """
        Search for exploits in Exploit DB.
        
        Args:
            query: Search query
            limit: Maximum results
            
        Returns:
            List of ShodanExploit objects
        """
        await self._rate_limit()
        
        try:
            loop = asyncio.get_event_loop()
            
            def _search():
                return self.client.exploits.search(query, limit=limit)
            
            result = await loop.run_in_executor(None, _search)
            
            exploits = []
            for match in result.get("matches", []):
                exploit = self._parse_exploit(match)
                exploits.append(exploit)
            
            return exploits
            
        except APIError as e:
            logger.error(f"Shodan exploit search error: {e}")
            return []
        except Exception as e:
            logger.error(f"Exploit search failed: {e}")
            return []
    
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
        host = await self.host(ip)
        
        if not host:
            return []
        
        domains = set(host.domains)
        for hostname in host.hostnames:
            if hostname:
                domains.add(hostname)
        
        return list(domains)
    
    async def search_services(
        self,
        service: str,
        product: Optional[str] = None,
        limit: int = 100,
    ) -> ShodanSearchResult:
        """
        Search for specific services.
        
        Args:
            service: Service name (http, ssh, ftp, etc.)
            product: Specific product name
            limit: Maximum results
            
        Returns:
            ShodanSearchResult with matching hosts
        """
        query = f'product:"{product}"' if product else ""
        query = f"{service} {query}".strip()
        
        return await self.search(query, limit=limit)
    
    async def search_vulnerabilities(
        self,
        cve: Optional[str] = None,
        kb: Optional[str] = None,
        limit: int = 100,
    ) -> ShodanSearchResult:
        """
        Search for hosts with vulnerabilities.
        
        Args:
            cve: CVE ID
            kb: Knowledge base ID
            limit: Maximum results
            
        Returns:
            ShodanSearchResult with vulnerable hosts
        """
        query_parts = []
        
        if cve:
            query_parts.append(f"vuln:{cve}")
        if kb:
            query_parts.append(f"kb:{kb}")
        
        query = " ".join(query_parts)
        
        if not query:
            query = "vuln:*"
        
        return await self.search(query, limit=limit)
    
    async def get_dns_domain(
        self,
        domain: str,
    ) -> Dict[str, Any]:
        """
        Get DNS information for a domain.
        
        Args:
            domain: Domain name
            
        Returns:
            DNS information dictionary
        """
        await self._rate_limit()
        
        try:
            loop = asyncio.get_event_loop()
            
            def _get():
                return self.client.dns.domain_info(domain, timeout=self.timeout)
            
            return await loop.run_in_executor(None, _get)
            
        except APIError as e:
            logger.error(f"Shodan DNS lookup error: {e}")
            return {}
        except Exception as e:
            logger.error(f"Failed to get DNS info for {domain}: {e}")
            return {}
    
    def _parse_host(self, data: Dict[str, Any]) -> ShodanHost:
        """Parse host data from Shodan search response."""
        services = {}
        ports = data.get("port", 0)
        if isinstance(ports, list):
            ports = ports
        else:
            ports = [ports]
        
        # Parse services
        for service_data in data.get("services", []):
            port = service_data.get("port", 0)
            services[port] = {
                "product": service_data.get("product"),
                "version": service_data.get("version"),
                "banner": service_data.get("banner"),
                "module": service_data.get("_shodan", {}).get("module"),
                "transport": service_data.get("transport"),
                "ssl": service_data.get("ssl"),
                "http": service_data.get("http"),
            }
        
        location = data.get("location", {})
        if location:
            location = {
                "country_code": location.get("country_code"),
                "country_name": location.get("country_name"),
                "city": location.get("city"),
                "latitude": location.get("latitude"),
                "longitude": location.get("longitude"),
                "org": location.get("org"),
            }
        
        asn_info = data.get("asn", "")
        if asn_info:
            autonomous_system = {
                "asn": asn_info,
                "name": data.get("org", ""),
                "route": data.get("ip", ""),
            }
        else:
            autonomous_system = {}
        
        last_update = data.get("last_update")
        if last_update:
            last_update = datetime.fromisoformat(last_update.replace("Z", "+00:00"))
        
        return ShodanHost(
            ip=data.get("ip", ""),
            ports=ports,
            services=services,
            location=location,
            autonomous_system=autonomous_system,
            uptime=data.get("uptime", 0),
            last_update=last_update,
            tags=data.get("tags", []),
            vulns=data.get("vulns", []),
            hostnames=data.get("hostnames", []),
            domains=data.get("domains", []),
            org=data.get("org", ""),
            operating_system=data.get("os", {}).get("product") if isinstance(data.get("os"), dict) else None,
        )
    
    def _parse_host_details(self, data: Dict[str, Any]) -> ShodanHost:
        """Parse detailed host data from Shodan host response."""
        services = {}
        ports = []
        
        for service_data in data.get("data", []):
            port = service_data.get("port", 0)
            ports.append(port)
            
            service = {
                "product": service_data.get("product"),
                "version": service_data.get("version"),
                "banner": service_data.get("data"),
                "module": service_data.get("module"),
                "transport": service_data.get("transport"),
                "ssl": service_data.get("ssl"),
                "http": service_data.get("http"),
            }
            services[port] = service
        
        location = data.get("location", {})
        
        autonomous_system = {
            "asn": data.get("asn", ""),
            "name": data.get("org", ""),
            "route": data.get("ip", ""),
        }
        
        last_update = data.get("last_update")
        if last_update:
            last_update = datetime.fromisoformat(last_update.replace("Z", "+00:00"))
        
        return ShodanHost(
            ip=data.get("ip", ""),
            ports=list(set(ports)),
            services=services,
            location=location,
            autonomous_system=autonomous_system,
            uptime=data.get("uptime", 0),
            last_update=last_update,
            tags=data.get("tags", []),
            vulns=data.get("vulns", []),
            hostnames=data.get("hostnames", []),
            domains=data.get("domains", []),
            org=data.get("org", ""),
            operating_system=data.get("os", {}).get("product") if isinstance(data.get("os"), dict) else None,
        )
    
    def _parse_exploit(self, data: Dict[str, Any]) -> ShodanExploit:
        """Parse exploit data from Shodan response."""
        return ShodanExploit(
            id=data.get("_id", ""),
            title=data.get("title"),
            description=data.get("description"),
            author=data.get("author"),
            platform=data.get("platform"),
            type=data.get("type"),
            port=data.get("port"),
            cve=data.get("cve", []),
            osvdb=data.get("osvdb", []),
            bid=data.get("bid", []),
            source=data.get("source", ""),
        )
    
    async def _rate_limit(self):
        """Enforce rate limiting."""
        now = asyncio.get_event_loop().time()
        elapsed = now - self._last_request_time
        
        if elapsed < self.rate_limit_delay:
            await asyncio.sleep(self.rate_limit_delay - elapsed)
        
        self._last_request_time = asyncio.get_event_loop().time()
    
    async def close(self):
        """Close the Shodan client."""
        self._client = None
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
