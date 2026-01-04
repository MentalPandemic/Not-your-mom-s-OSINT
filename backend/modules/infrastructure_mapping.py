"""
Infrastructure Mapping Module for domain intelligence.

Maps domain infrastructure including:
- IP to domain relationships
- ASN analysis
- Service identification
- Geolocation
- Reverse IP lookups
- Virtual hosting detection
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from clients.censys_client import CensysClient, CensysHost
from clients.shodan_client import ShodanClient, ShodanHost
from clients.securitytrails_client import SecurityTrailsClient
from clients.geoip_client import GeoIpClient, GeoIpResult, AsnInfo, GeoLocation

from modules.dns_enumeration import DnsEnumeration
from modules.ssl_analysis import SslAnalysis

logger = logging.getLogger(__name__)


@dataclass
class ServiceInfo:
    """Information about a detected service."""
    port: int
    protocol: str = "tcp"
    product: Optional[str] = None
    version: Optional[str] = None
    banner: Optional[str] = None
    cpe: Optional[str] = None
    is_https: bool = False
    technologies: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "port": self.port,
            "protocol": self.protocol,
            "product": self.product,
            "version": self.version,
            "banner": self.banner,
            "cpe": self.cpe,
            "is_https": self.is_https,
            "technologies": self.technologies,
        }


@dataclass
class AsnInfoResult:
    """ASN information with analysis."""
    asn: str
    asn_decimal: Optional[int] = None
    name: Optional[str] = None
    organization: Optional[str] = None
    country_code: Optional[str] = None
    
    # Network
    network_prefix: Optional[str] = None
    network_range: Optional[str] = None
    route: Optional[str] = None
    
    # Analysis
    is_cdn: bool = False
    is_hosting: bool = False
    is_isp: bool = False
    is_cloud: bool = False
    
    # Related IPs
    total_ips: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "asn": self.asn,
            "asn_decimal": self.asn_decimal,
            "name": self.name,
            "organization": self.organization,
            "country_code": self.country_code,
            "network_prefix": self.network_prefix,
            "network_range": self.network_range,
            "route": self.route,
            "is_cdn": self.is_cdn,
            "is_hosting": self.is_hosting,
            "is_isp": self.is_isp,
            "is_cloud": self.is_cloud,
            "total_ips": self.total_ips,
        }


@dataclass
class HostInfo:
    """Host information from reconnaissance."""
    ip_address: str
    hostname: Optional[str] = None
    domain: Optional[str] = None
    
    # Services
    services: List[ServiceInfo] = field(default_factory=list)
    ports: List[int] = field(default_factory=list)
    
    # Geolocation
    location: Optional[GeoLocation] = None
    
    # Network
    asn: Optional[AsnInfo] = None
    isp: Optional[str] = None
    organization: Optional[str] = None
    
    # SSL
    has_ssl: bool = False
    ssl_info: Optional[Dict[str, Any]] = None
    
    # Analysis
    is_datacenter: bool = False
    is_cdn: bool = False
    is_proxy: bool = False
    is_tor_exit: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "ip_address": self.ip_address,
            "hostname": self.hostname,
            "domain": self.domain,
            "services": [s.to_dict() for s in self.services],
            "ports": self.ports,
            "location": self.location.to_dict() if self.location else None,
            "asn": self.asn.to_dict() if self.asn else None,
            "isp": self.isp,
            "organization": self.organization,
            "has_ssl": self.has_ssl,
            "ssl_info": self.ssl_info,
            "is_datacenter": self.is_datacenter,
            "is_cdn": self.is_cdn,
            "is_proxy": self.is_proxy,
            "is_tor_exit": self.is_tor_exit,
        }


@dataclass
class InfrastructureMap:
    """Complete infrastructure map for a domain."""
    domain: str
    
    # IPs and hosts
    ip_addresses: List[str] = field(default_factory=list)
    hosts: List[HostInfo] = field(default_factory=list)
    
    # ASN information
    asns: List[AsnInfoResult] = field(default_factory=list)
    
    # Services summary
    services_summary: Dict[str, int] = field(default_factory=dict)
    port_summary: Dict[int, int] = field(default_factory=dict)
    
    # Geolocation summary
    countries: List[str] = field(default_factory=list)
    cities: List[str] = field(default_factory=list)
    
    # Analysis
    hosting_provider: Optional[str] = None
    is_cloud: bool = False
    is_cdn: bool = False
    infrastructure_type: str = "unknown"  # shared, dedicated, cloud, cdn
    
    # Related domains
    related_domains: List[str] = field(default_factory=list)
    domains_on_same_ip: Dict[str, List[str]] = field(default_factory=dict)
    
    # Metadata
    total_hosts: int = 0
    total_ports: int = 0
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "domain": self.domain,
            "ip_addresses": self.ip_addresses,
            "hosts": [h.to_dict() for h in self.hosts],
            "asns": [a.to_dict() for a in self.asns],
            "services_summary": self.services_summary,
            "port_summary": self.port_summary,
            "countries": self.countries,
            "cities": self.cities,
            "hosting_provider": self.hosting_provider,
            "is_cloud": self.is_cloud,
            "is_cdn": self.is_cdn,
            "infrastructure_type": self.infrastructure_type,
            "related_domains": self.related_domains,
            "domains_on_same_ip": self.domains_on_same_ip,
            "total_hosts": self.total_hosts,
            "total_ports": self.total_ports,
            "error": self.error,
        }


@dataclass
class ReverseIpResult:
    """Reverse IP lookup result."""
    ip_address: str
    domains: List[str] = field(default_factory=list)
    host_info: Optional[HostInfo] = None
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "ip_address": self.ip_address,
            "domains": self.domains,
            "host_info": self.host_info.to_dict() if self.host_info else None,
            "error": self.error,
        }


# Known CDN providers
CDN_PROVIDERS = {
    "cloudflare": ["cloudflare", "cloudflare.com"],
    "akamai": ["akamai", "akamaitechnologies", "akamaiedge", "edgesuite.net"],
    "fastly": ["fastly", "fastly.net"],
    "cloudfront": ["cloudfront", "aws.amazon.com"],
    "google": ["google", "googleusercontent", "doubleclick.net"],
    "azure": ["azure", "azureedge", "azure.com"],
    "limelight": ["limelight", "llnw", "cdn"],
    "incapsula": ["incapsula", "imperva"],
    "sucuri": ["sucuri", "sucuri.net"],
    "stackpath": ["stackpath", "highwinds"],
    "cdn77": ["cdn77", "cdn77.net"],
    " BunnyCDN": ["bunnycdn", "bunny.net"],
}

# Known cloud providers
CLOUD_PROVIDERS = {
    "aws": ["amazon", "aws", "amazonaws", "amazon.com"],
    "azure": ["azure", "microsoft.com"],
    "gcp": ["google cloud", "googlecloud", "gcp", "cloud.google"],
    "digitalocean": ["digitalocean"],
    "linode": ["linode"],
    "vultr": ["vultr"],
    "ovh": ["ovh", "ovh.net"],
    "hetzner": ["hetzner"],
}


class InfrastructureMapping:
    """
    Infrastructure mapping module for domain reconnaissance.
    
    Provides:
    - IP to domain mapping
    - ASN analysis
    - Service identification
    - Geolocation
    - Reverse IP lookups
    - Infrastructure classification
    """
    
    # Common ports to check
    COMMON_PORTS = [21, 22, 25, 53, 80, 110, 143, 443, 465, 587, 993, 995, 3306, 5432, 8080, 8443]
    
    def __init__(
        self,
        censys_api_id: Optional[str] = None,
        censys_api_secret: Optional[str] = None,
        shodan_api_key: Optional[str] = None,
        securitytrails_api_key: Optional[str] = None,
        geoip_db_path: Optional[str] = None,
        timeout: float = 30.0,
    ):
        """
        Initialize infrastructure mapping module.
        
        Args:
            censys_api_id: Censys API ID
            censys_api_secret: Censys API secret
            shodan_api_key: Shodan API key
            securitytrails_api_key: SecurityTrails API key
            geoip_db_path: Path to MaxMind GeoIP database
            timeout: Request timeout
        """
        self.timeout = timeout
        self._dns = DnsEnumeration(securitytrails_api_key)
        self._ssl = SslAnalysis(censys_api_id, censys_api_secret, shodan_api_key)
        self._geoip: Optional[GeoIpClient] = None
        self._censys: Optional[CensysClient] = None
        self._shodan: Optional[ShodanClient] = None
        self._securitytrails: Optional[SecurityTrailsClient] = None
        
        if geoip_db_path:
            self._geoip = GeoIpClient(city_db_path=geoip_db_path)
        if censys_api_id and censys_api_secret:
            self._censys = CensysClient(censys_api_id, censys_api_secret)
        if shodan_api_key:
            self._shodan = ShodanClient(shodan_api_key)
        if securitytrails_api_key:
            self._securitytrails = SecurityTrailsClient(securitytrails_api_key)
    
    async def map_infrastructure(
        self,
        domain: str,
        check_common_ports: bool = True,
        find_related_domains: bool = True,
    ) -> InfrastructureMap:
        """
        Map complete infrastructure for a domain.
        
        Args:
            domain: Domain to analyze
            check_common_ports: Check common ports on discovered IPs
            find_related_domains: Find related domains
            
        Returns:
            InfrastructureMap with all infrastructure data
        """
        logger.info(f"Mapping infrastructure for {domain}")
        
        result = InfrastructureMap(domain=domain)
        
        try:
            # Get DNS records to find IPs
            dns_result = await self._dns.enumerate_all(domain)
            result.ip_addresses = dns_result.get_all_ips()
            
            if not result.ip_addresses:
                result.error = "No IP addresses found for domain"
                return result
            
            # Get detailed host information for each IP
            host_tasks = [
                self._analyze_host(ip, domain)
                for ip in result.ip_addresses
            ]
            
            hosts = await asyncio.gather(*host_tasks, return_exceptions=True)
            
            for host in hosts:
                if isinstance(host, Exception):
                    logger.warning(f"Host analysis failed: {host}")
                    continue
                if host:
                    result.hosts.append(host)
            
            # Analyze ASN information
            result.asns = await self._analyze_asns(result.hosts)
            
            # Summarize services
            self._summarize_services(result)
            
            # Classify infrastructure type
            self._classify_infrastructure(result)
            
            # Find related domains if requested
            if find_related_domains:
                result.related_domains = await self._find_related_domains(domain)
                result.domains_on_same_ip = await self._find_domains_on_ips(result.ip_addresses)
            
        except Exception as e:
            logger.error(f"Infrastructure mapping failed for {domain}: {e}")
            result.error = str(e)
        
        return result
    
    async def reverse_ip_lookup(
        self,
        ip_address: str,
    ) -> ReverseIpResult:
        """
        Find all domains hosted on an IP address.
        
        Args:
            ip_address: IP address to look up
            
        Returns:
            ReverseIpResult with domains and host info
        """
        logger.info(f"Performing reverse IP lookup for {ip_address}")
        
        result = ReverseIpResult(ip_address=ip_address)
        
        try:
            # Get host info
            result.host_info = await self._analyze_host(ip_address)
            
            # Find domains using multiple sources
            domains = set()
            
            # Search Censys
            if self._censys:
                censys_domains = await self._censys.search_domains_on_ip(ip_address)
                domains.update(censys_domains)
            
            # Search Shodan
            if self._shodan:
                shodan_domains = await self._shodan.search_domains_on_ip(ip_address)
                domains.update(shodan_domains)
            
            # Search SecurityTrails
            if self._securitytrails:
                st_domains = await self._securitytrails.search_domains_by_ip(ip_address)
                domains.update(st_domains)
            
            # Get reverse DNS
            if result.host_info and result.host_info.hostname:
                domains.add(result.host_info.hostname)
            
            result.domains = list(domains)
            
        except Exception as e:
            logger.error(f"Reverse IP lookup failed for {ip_address}: {e}")
            result.error = str(e)
        
        return result
    
    async def get_asn_info(
        self,
        asn: str,
    ) -> AsnInfoResult:
        """
        Get detailed information about an ASN.
        
        Args:
            asn: ASN string (e.g., "AS15169")
            
        Returns:
            AsnInfoResult with ASN details
        """
        logger.info(f"Getting ASN info for {asn}")
        
        result = AsnInfoResult(asn=asn)
        
        try:
            # Parse ASN
            asn_decimal = 0
            if asn.startswith("AS"):
                try:
                    asn_decimal = int(asn[2:])
                    result.asn_decimal = asn_decimal
                except ValueError:
                    pass
            
            # Get IP range info from ASN database
            if self._geoip:
                # GeoIP doesn't directly support ASN lookups by number
                # This would require a separate ASN database
                pass
            
            # Search for network info using Censys
            if self._censys:
                query = f"autonomous_system.asn: {asn_decimal}"
                search_result = await self._censys.search_hosts(query, per_page=10)
                
                if search_result.hosts:
                    host = search_result.hosts[0]
                    if host.autonomous_system:
                        result.name = host.autonomous_system.get("asn_name")
                        result.organization = host.autonomous_system.get("organization")
                    
                    result.total_ips = search_result.total_hosts
            
            # Analyze provider type
            result.is_cdn = self._check_cdn(result.organization or "")
            result.is_cloud = self._check_cloud(result.organization or "")
            result.is_hosting = any(x in (result.organization or "").lower() 
                                   for x in ["hosting", "server", "datacenter"])
            result.is_isp = not (result.is_cdn or result.is_cloud or result.is_hosting)
            
        except Exception as e:
            logger.error(f"ASN info lookup failed for {asn}: {e}")
        
        return result
    
    async def find_shared_hosting(
        self,
        domain: str,
    ) -> Dict[str, List[str]]:
        """
        Find domains hosted on the same infrastructure.
        
        Args:
            domain: Domain to analyze
            
        Returns:
            Dictionary with IPs as keys and domains as values
        """
        # Get all IPs for the domain
        dns_result = await self._dns.enumerate_all(domain)
        ip_addresses = dns_result.get_all_ips()
        
        # Find domains on each IP
        shared_domains = {}
        
        for ip in ip_addresses:
            reverse_result = await self.reverse_ip_lookup(ip)
            if reverse_result.domains:
                shared_domains[ip] = reverse_result.domains
        
        return shared_domains
    
    async def get_geolocation(
        self,
        ip_address: str,
    ) -> Optional[GeoLocation]:
        """
        Get geolocation for an IP address.
        
        Args:
            ip_address: IP address
            
        Returns:
            GeoLocation or None if not found
        """
        if not self._geoip:
            return None
        
        result = self._geoip.lookup(ip_address)
        return result.location
    
    async def check_ports(
        self,
        ip_address: str,
        ports: Optional[List[int]] = None,
    ) -> List[ServiceInfo]:
        """
        Check ports on an IP address.
        
        Args:
            ip_address: IP address to scan
            ports: Ports to check (defaults to COMMON_PORTS)
            
        Returns:
            List of ServiceInfo objects
        """
        if ports is None:
            ports = self.COMMON_PORTS
        
        services = []
        
        # Use Shodan for port info if available
        if self._shodan:
            host = await self._shodan.host(ip_address)
            
            if host:
                for port, service_info in host.services.items():
                    service = ServiceInfo(
                        port=port,
                        product=service_info.get("product"),
                        version=service_info.get("version"),
                        banner=service_info.get("banner"),
                    )
                    
                    # Detect HTTPS
                    if port in [443, 8443]:
                        service.is_https = True
                    
                    services.append(service)
                
                return services
        
        # Fallback: basic socket checks
        for port in ports:
            try:
                import socket
                
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2)
                result = sock.connect_ex((ip_address, port))
                sock.close()
                
                if result == 0:
                    service = ServiceInfo(port=port)
                    
                    # Try to get banner
                    try:
                        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        sock.settimeout(2)
                        sock.connect((ip_address, port))
                        banner = sock.recv(1024).decode('utf-8', errors='ignore').strip()
                        sock.close()
                        
                        if banner:
                            service.banner = banner
                            
                            # Try to identify service
                            banner_lower = banner.lower()
                            if "nginx" in banner_lower:
                                service.product = "Nginx"
                            elif "apache" in banner_lower:
                                service.product = "Apache"
                            elif "iis" in banner_lower:
                                service.product = "IIS"
                            elif "ssh" in banner_lower:
                                service.product = "OpenSSH"
                            elif "mysql" in banner_lower:
                                service.product = "MySQL"
                            elif "postgresql" in banner_lower:
                                service.product = "PostgreSQL"
                            
                    except Exception:
                        pass
                    
                    if port in [443, 8443]:
                        service.is_https = True
                    
                    services.append(service)
                    
            except Exception:
                pass
        
        return services
    
    async def _analyze_host(
        self,
        ip_address: str,
        domain: Optional[str] = None,
    ) -> Optional[HostInfo]:
        """Analyze a single host."""
        host = HostInfo(ip_address=ip_address, domain=domain)
        
        try:
            # Get geolocation
            if self._geoip:
                geo_result = self._geoip.lookup(ip_address)
                if geo_result:
                    host.location = geo_result.location
                    host.isp = geo_result.isp
                    host.asn = geo_result.asn
            
            # Check for reverse DNS
            try:
                import socket
                hostname, _, _ = socket.gethostbyaddr(ip_address)
                host.hostname = hostname
            except Exception:
                pass
            
            # Get services/ports
            services = await self.check_ports(ip_address)
            host.services = services
            host.ports = [s.port for s in services]
            
            # Check for SSL
            if 443 in host.ports or 8443 in host.ports:
                ssl_result = await self._ssl.analyze_ip(ip_address)
                if ssl_result.certificates:
                    host.has_ssl = True
                    host.ssl_info = ssl_result.certificates[0].to_dict()
            
            # Classify host
            host.is_datacenter = self._is_datacenter_ip(ip_address)
            host.is_cdn = self._check_cdn(host.isp or "")
            host.is_tor_exit = self._is_tor_exit(ip_address)
            
            return host
            
        except Exception as e:
            logger.error(f"Host analysis failed for {ip_address}: {e}")
            return None
    
    async def _analyze_asns(
        self,
        hosts: List[HostInfo],
    ) -> List[AsnInfoResult]:
        """Analyze ASN information from hosts."""
        asn_map = {}
        
        for host in hosts:
            if host.asn and host.asn.asn:
                if host.asn.asn not in asn_map:
                    asn_info = AsnInfoResult(
                        asn=host.asn.asn,
                        asn_decimal=host.asn.asn_decimal,
                        name=host.asn.network,
                        organization=host.asp if hasattr(host, 'isp') else host.asn.organization,
                    )
                    asn_info.is_cdn = self._check_cdn(asn_info.organization or "")
                    asn_info.is_cloud = self._check_cloud(asn_info.organization or "")
                    asn_map[host.asn.asn] = asn_info
        
        return list(asn_map.values())
    
    def _summarize_services(self, infra: InfrastructureMap):
        """Summarize services and ports."""
        product_counts = {}
        port_counts = {}
        
        for host in infra.hosts:
            for service in host.services:
                if service.product:
                    product_counts[service.product] = product_counts.get(service.product, 0) + 1
                port_counts[service.port] = port_counts.get(service.port, 0) + 1
        
        infra.services_summary = product_counts
        infra.port_summary = port_counts
        infra.total_hosts = len(infra.hosts)
        infra.total_ports = sum(port_counts.values())
        
        # Extract locations
        countries = set()
        cities = set()
        for host in infra.hosts:
            if host.location:
                if host.location.country_code:
                    countries.add(host.location.country_code)
                if host.location.city:
                    cities.add(host.location.city)
        
        infra.countries = list(countries)
        infra.cities = list(cities)
    
    def _classify_infrastructure(self, infra: InfrastructureMap):
        """Classify the infrastructure type."""
        # Check if using CDN
        for host in infra.hosts:
            if host.is_cdn:
                infra.is_cdn = True
                infra.infrastructure_type = "cdn"
                return
        
        # Check if cloud-based
        for asn in infra.asns:
            if asn.is_cloud:
                infra.is_cloud = True
                infra.infrastructure_type = "cloud"
                return
        
        # Check hosting provider
        for host in infra.hosts:
            if host.isp:
                provider = host.isp.lower()
                if any(x in provider for x in ["amazon", "aws", "google cloud", "azure"]):
                    infra.is_cloud = True
                    infra.infrastructure_type = "cloud"
                    return
        
        # Count unique IPs
        unique_ips = len(set(infra.ip_addresses))
        
        if unique_ips == 1:
            infra.infrastructure_type = "dedicated"
        else:
            infra.infrastructure_type = "shared"
    
    async def _find_related_domains(self, domain: str) -> List[str]:
        """Find domains related to the target domain."""
        related = set()
        
        # Get from SSL SANs
        ssl_result = await self._ssl.analyze(domain)
        if ssl_result.related_domains:
            related.update(ssl_result.related_domains)
        
        # Get from SecurityTrails
        if self._securitytrails:
            associated = await self._securitytrails.get_associated_domains(domain)
            for domain_list in associated.values():
                related.update(domain_list)
        
        related.discard(domain)  # Remove self
        return list(related)
    
    async def _find_domains_on_ips(
        self,
        ip_addresses: List[str],
    ) -> Dict[str, List[str]]:
        """Find domains hosted on IPs."""
        domains_on_ips = {}
        
        for ip in ip_addresses:
            reverse_result = await self.reverse_ip_lookup(ip)
            if reverse_result.domains:
                domains_on_ips[ip] = reverse_result.domains
        
        return domains_on_ips
    
    def _check_cdn(self, provider: str) -> bool:
        """Check if provider is a CDN."""
        provider_lower = provider.lower()
        for cdn, patterns in CDN_PROVIDERS.items():
            for pattern in patterns:
                if pattern in provider_lower:
                    return True
        return False
    
    def _check_cloud(self, provider: str) -> bool:
        """Check if provider is a cloud provider."""
        provider_lower = provider.lower()
        for cloud, patterns in CLOUD_PROVIDERS.items():
            for pattern in patterns:
                if pattern in provider_lower:
                    return True
        return False
    
    def _is_datacenter_ip(self, ip_address: str) -> bool:
        """Check if IP is from a datacenter."""
        # Common datacenter IP ranges
        datacenter_prefixes = [
            "64.224", "64.225", "64.226",  # Savvis
            "208.67", "208.68",  # OpenDNS
            "1.1.1",  # Cloudflare
        ]
        
        for prefix in datacenter_prefixes:
            if ip_address.startswith(prefix):
                return True
        
        return False
    
    def _is_tor_exit(self, ip_address: str) -> bool:
        """Check if IP is a known Tor exit node."""
        # This would require a real Tor exit list
        # For now, use basic heuristics
        return False
    
    async def close(self):
        """Close client connections."""
        if self._geoip:
            self._geoip.close()
        if self._censys:
            await self._censys.close()
        if self._shodan:
            await self._shodan.close()
        if self._securitytrails:
            await self._securitytrails.close()
