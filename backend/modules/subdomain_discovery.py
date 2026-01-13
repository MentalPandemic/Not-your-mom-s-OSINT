"""
Subdomain Discovery Module for domain intelligence.

Provides comprehensive subdomain enumeration using multiple methods:
- Certificate Transparency (CT) logs
- Brute force with wordlists
- Zone transfer attempts
- Search engine dorks
- DNS enumeration
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Set

from clients.ct_client import CtClient, CertificateInfo
from clients.dns_client import DnsClient
from clients.securitytrails_client import SecurityTrailsClient, SubdomainInfo

logger = logging.getLogger(__name__)


@dataclass
class SubdomainInfoResult:
    """Discovered subdomain information."""
    subdomain: str
    domain: str
    ip_addresses: List[str] = field(default_factory=list)
    
    # Services
    services: Dict[str, Any] = field(default_factory=dict)
    ports: List[int] = field(default_factory=list)
    http_status: Optional[int] = None
    http_title: Optional[str] = None
    
    # Discovery
    discovery_method: str = ""
    source: Optional[str] = None
    first_discovered: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    
    # Status
    is_active: bool = True
    is_wildcard: bool = False
    
    # SSL
    has_ssl: bool = False
    ssl_info: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "subdomain": self.subdomain,
            "domain": self.domain,
            "ip_addresses": self.ip_addresses,
            "services": self.services,
            "ports": self.ports,
            "http_status": self.http_status,
            "http_title": self.http_title,
            "discovery_method": self.discovery_method,
            "source": self.source,
            "first_discovered": self.first_discovered.isoformat() if self.first_discovered else None,
            "last_seen": self.last_seen.isoformat() if self.last_seen else None,
            "is_active": self.is_active,
            "is_wildcard": self.is_wildcard,
            "has_ssl": self.has_ssl,
            "ssl_info": self.ssl_info,
        }


@dataclass
class SubdomainDiscoveryResult:
    """Complete subdomain discovery result."""
    domain: str
    subdomains: List[SubdomainInfoResult] = field(default_factory=list)
    
    # Statistics
    total_found: int = 0
    total_active: int = 0
    total_wildcard: int = 0
    
    # Methods used
    methods_used: List[str] = field(default_factory=list)
    
    # Wildcard detection
    wildcard_detected: bool = False
    wildcard_pattern: Optional[str] = None
    
    # Metadata
    duration_seconds: float = 0.0
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "domain": self.domain,
            "subdomains": [s.to_dict() for s in self.subdomains],
            "total_found": self.total_found,
            "total_active": self.total_active,
            "total_wildcard": self.total_wildcard,
            "methods_used": self.methods_used,
            "wildcard_detected": self.wildcard_detected,
            "wildcard_pattern": self.wildcard_pattern,
            "duration_seconds": self.duration_seconds,
            "error": self.error,
        }


# Common subdomains for brute force
COMMON_SUBDOMAINS = [
    # Administration
    "admin", "administrator", "admins", "manage", "management", "manager",
    "cpanel", "whm", "webmail", "mail", "email", "smtp", "imap", "pop",
    "ssh", "ftp", "sftp", "vpn", "proxy", "firewall",
    
    # Development
    "dev", "development", "test", "testing", "staging", "stage", "prod",
    "production", "demo", "sandbox", "ci", "cd", "jenkins", "travis",
    "gitlab", "github", "bitbucket", "build", "builder", "ci-cd",
    
    # API
    "api", "apis", "api-dev", "api-test", "api-staging", "api-prod",
    "rest", "graphql", "soap", "ws", "webapi", "gateway",
    
    # Web
    "www", "web", "www2", "blog", "forum", "shop", "store", "cdn",
    "assets", "static", "media", "files", "downloads", "docs",
    
    # Database
    "db", "database", "mysql", "postgres", "mongodb", "redis",
    "elasticsearch", "solr", "cassandra", "oracle", "mssql",
    
    # Monitoring
    "monitor", "monitoring", "metrics", "grafana", "prometheus",
    "alert", "alerts", "logs", "log", "kibana", "newrelic",
    "datadog", "cloudwatch",
    
    # Services
    "service", "services", "service-dev", "service-test",
    "auth", "authentication", "login", "signin", "signup",
    "account", "accounts", "user", "users", "profile", "profiles",
    
    # Cloud
    "aws", "azure", "gcp", "s3", "ec2", "lambda", "cloud",
    "internal", "intranet", "local", "localhost",
    
    # Email
    "mail", "smtp", "imap", "pop3", "mx", "mailer", "newsletter",
    
    # Misc
    "status", "health", "ping", "heartbeat", "metrics",
    "docs", "documentation", "help", "support", "helpdesk",
    "about", "contact", "terms", "privacy", "legal",
    "careers", "jobs", "career", "hr", "recruiting",
    "press", "media", "news", "blog", "articles",
    "cdn", "static", "assets", "img", "images",
    "video", "videos", "audio", "podcast",
    "app", "apps", "mobile", "ios", "android",
    "backup", "backups", "restore", "data",
    "security", "secure", "private", "hidden",
    "old", "legacy", "archive", "archives",
    "beta", "alpha", "preview", "preview",
    "preprod", "pre-prod", "uat", "qa",
]

# High-value targets
HIGH_VALUE_SUBDOMAINS = [
    "admin", "administrator", "admins", "manage", "management",
    "cpanel", "whm", "webmail",
    "dev", "development", "test", "testing", "staging", "prod",
    "api", "apis", "rest", "graphql",
    "vpn", "proxy", "ssh", "ftp", "sftp",
    "internal", "intranet", "local",
    "backup", "backups",
    "jenkins", "gitlab", "github",
    "monitor", "monitoring",
    "mysql", "postgres", "mongodb", "redis",
    "aws", "s3", "ec2",
]


class SubdomainDiscovery:
    """
    Subdomain discovery module using multiple enumeration methods.
    
    Provides:
    - Certificate Transparency log search
    - Brute force with wordlists
    - Zone transfer attempts
    - DNS enumeration
    - Search engine scraping
    """
    
    def __init__(
        self,
        securitytrails_api_key: Optional[str] = None,
        ct_rate_limit: float = 1.0,
        dns_timeout: float = 5.0,
        max_concurrent: int = 100,
    ):
        """
        Initialize subdomain discovery module.
        
        Args:
            securitytrails_api_key: SecurityTrails API key
            ct_rate_limit: CT log rate limit delay
            dns_timeout: DNS query timeout
            max_concurrent: Maximum concurrent queries
        """
        self.ct_client = CtClient(rate_limit_delay=ct_rate_limit)
        self.dns_client = DnsClient(timeout=dns_timeout)
        self._securitytrails: Optional[SecurityTrailsClient] = None
        self._semaphore = asyncio.Semaphore(max_concurrent)
        
        if securitytrails_api_key:
            self._securitytrails = SecurityTrailsClient(securitytrails_api_key)
    
    async def discover(
        self,
        domain: str,
        methods: Optional[List[str]] = None,
        brute_force: bool = True,
        include_inactive: bool = False,
        max_subdomains: int = 1000,
    ) -> SubdomainDiscoveryResult:
        """
        Discover subdomains using multiple methods.
        
        Args:
            domain: Domain to enumerate
            methods: Specific methods to use (ct, bruteforce, zonetransfer, securitytrails)
            brute_force: Whether to use brute force
            include_inactive: Include subdomains that don't resolve
            max_subdomains: Maximum subdomains to return
            
        Returns:
            SubdomainDiscoveryResult with all discovered subdomains
        """
        import time
        start_time = time.time()
        
        logger.info(f"Starting subdomain discovery for {domain}")
        
        result = SubdomainDiscoveryResult(domain=domain)
        
        try:
            # Default methods
            if methods is None:
                methods = ["ct", "securitytrails"]
                if brute_force:
                    methods.append("bruteforce")
            
            # Track methods used
            result.methods_used = methods.copy()
            
            # Discover subdomains using all methods
            all_subdomains: Set[str] = set()
            
            tasks = []
            
            if "ct" in methods:
                tasks.append(self._search_ct_logs(domain))
            if "securitytrails" in methods:
                tasks.append(self._search_securitytrails(domain))
            if "bruteforce" in methods:
                tasks.append(self._brute_force(domain))
            
            if tasks:
                method_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for method_result in method_results:
                    if isinstance(method_result, Exception):
                        logger.warning(f"Subdomain method failed: {method_result}")
                        continue
                    
                    if method_result:
                        all_subdomains.update(method_result)
            
            # Check for wildcards
            wildcard_result = await self._detect_wildcard(domain)
            result.wildcard_detected = wildcard_result["detected"]
            result.wildcard_pattern = wildcard_result.get("pattern")
            
            # Resolve each subdomain
            subdomain_list = list(all_subdomains)[:max_subdomains]
            
            result.subdomains = await self._resolve_subdomains(
                subdomain_list,
                domain,
                include_inactive,
            )
            
            # Calculate statistics
            result.total_found = len(result.subdomains)
            result.total_active = sum(1 for s in result.subdomains if s.is_active)
            result.total_wildcard = sum(1 for s in result.subdomains if s.is_wildcard)
            
        except Exception as e:
            logger.error(f"Subdomain discovery failed for {domain}: {e}")
            result.error = str(e)
        
        result.duration_seconds = time.time() - start_time
        
        return result
    
    async def search_ct_logs(
        self,
        domain: str,
    ) -> List[str]:
        """
        Search Certificate Transparency logs for subdomains.
        
        Args:
            domain: Domain to search
            
        Returns:
            List of subdomain strings
        """
        logger.info(f"Searching CT logs for {domain}")
        
        try:
            ct_result = await self.ct_client.search_certificates(domain, include_subdomains=True)
            
            if ct_result.error:
                logger.warning(f"CT search error: {ct_result.error}")
                return []
            
            return ct_result.subdomains
            
        except Exception as e:
            logger.error(f"CT log search failed: {e}")
            return []
    
    async def brute_force(
        self,
        domain: str,
        wordlist: Optional[List[str]] = None,
        max_concurrent: int = 100,
    ) -> List[str]:
        """
        Brute force subdomains using a wordlist.
        
        Args:
            domain: Domain to enumerate
            wordlist: List of subdomains to try
            max_concurrent: Maximum concurrent DNS queries
            
        Returns:
            List of valid subdomains
        """
        logger.info(f"Starting brute force for {domain}")
        
        if wordlist is None:
            wordlist = COMMON_SUBDOMAINS
        
        subdomains = []
        
        async with asyncio.TaskGroup() as tg:
            for sub in wordlist:
                subdomain = f"{sub}.{domain}"
                task = tg.create_task(self._check_subdomain_exists(subdomain))
                subdomains.append((subdomain, task))
        
        valid = [sub for sub, task in subdomains if task.result()]
        
        return valid
    
    async def zone_transfer(
        self,
        domain: str,
    ) -> List[Dict[str, Any]]:
        """
        Attempt zone transfer to get all DNS records.
        
        Args:
            domain: Domain to attempt zone transfer
            
        Returns:
            List of DNS records from zone transfer
        """
        logger.info(f"Attempting zone transfer for {domain}")
        
        records = []
        
        try:
            # Get nameservers
            ns_result = await self.dns_client.resolve(domain, "NS")
            nameservers = [r.value for r in ns_result.records]
            
            for ns in nameservers:
                # Try AXFR
                try:
                    import socket
                    
                    # Resolve nameserver IP
                    ns_ips = await self._resolve_hostname(ns)
                    if not ns_ips:
                        continue
                    
                    ns_ip = ns_ips[0]
                    
                    # Connect and request zone transfer
                    # Note: Full AXFR implementation requires custom DNS handling
                    # This is a simplified version
                    
                    records.append({
                        "nameserver": ns,
                        "nameserver_ip": ns_ip,
                        "success": False,
                        "error": "AXFR requires custom DNS implementation",
                    })
                    
                except Exception as e:
                    records.append({
                        "nameserver": ns,
                        "success": False,
                        "error": str(e),
                    })
                    
        except Exception as e:
            logger.error(f"Zone transfer failed: {e}")
        
        return records
    
    async def get_subdomains_from_ct_certificate(
        self,
        cert_id: str,
    ) -> List[str]:
        """
        Get subdomains from a specific certificate.
        
        Args:
            cert_id: Certificate ID from crt.sh
            
        Returns:
            List of subdomain strings
        """
        try:
            cert = await self.ct_client.get_certificate_details(cert_id)
            
            if cert:
                return cert.subject_alternative_names
            
            return []
            
        except Exception as e:
            logger.error(f"Failed to get certificate details: {e}")
            return []
    
    async def _search_ct_logs(self, domain: str) -> Set[str]:
        """Search CT logs for subdomains."""
        subdomains = await self.search_ct_logs(domain)
        return set(subdomains)
    
    async def _search_securitytrails(self, domain: str) -> Set[str]:
        """Search SecurityTrails for subdomains."""
        if not self._securitytrails:
            return set()
        
        try:
            subdomains = await self._securitytrails.get_subdomains(domain)
            return {s.subdomain for s in subdomains}
            
        except Exception as e:
            logger.warning(f"SecurityTrails subdomain search failed: {e}")
            return set()
    
    async def _brute_force(self, domain: str) -> Set[str]:
        """Perform brute force subdomain enumeration."""
        return set(await self.brute_force(domain))
    
    async def _resolve_subdomains(
        self,
        subdomains: List[str],
        domain: str,
        include_inactive: bool,
    ) -> List[SubdomainInfoResult]:
        """Resolve each subdomain to get IP addresses and services."""
        
        results = []
        
        async with asyncio.TaskGroup() as tg:
            tasks = {}
            for sub in subdomains:
                task = tg.create_task(self._resolve_single_subdomain(sub, domain))
                tasks[sub] = task
            
            for sub, task in tasks.items():
                result = task.result()
                if result:
                    results.append(result)
        
        # Filter inactive if needed
        if not include_inactive:
            results = [r for r in results if r.is_active]
        
        return results
    
    async def _resolve_single_subdomain(
        self,
        subdomain: str,
        domain: str,
    ) -> Optional[SubdomainInfoResult]:
        """Resolve a single subdomain."""
        
        info = SubdomainInfoResult(
            subdomain=subdomain,
            domain=domain,
            discovery_method="resolution",
        )
        
        try:
            # Resolve A records
            async with self._semaphore:
                a_result = await self.dns_client.resolve(subdomain, "A")
                aaaa_result = await self.dns_client.resolve(subdomain, "AAAA")
            
            ip_addresses = [r.value for r in a_result.records]
            ip_addresses.extend(r.value for r in aaaa_result.records)
            
            if ip_addresses:
                info.ip_addresses = ip_addresses
                info.is_active = True
            else:
                info.is_active = False
            
            # Check for wildcards
            if not info.ip_addresses:
                # Check if this is a wildcard
                parent = subdomain.rsplit(".", 2)[0]
                wildcard_check = f"*.{parent}.{domain}"
                
                async with self._semaphore:
                    wildcard_result = await self.dns_client.resolve(wildcard_check, "A")
                
                if wildcard_result.records:
                    info.is_wildcard = True
                    info.ip_addresses = [r.value for r in wildcard_result.records]
                    info.is_active = True
            
            # Basic HTTP check (optional)
            if info.is_active and info.ip_addresses:
                try:
                    import httpx
                    
                    async with self._semaphore:
                        async with httpx.AsyncClient(timeout=5.0) as client:
                            for ip in info.ip_addresses[:2]:  # Check first 2 IPs
                                try:
                                    response = await client.get(
                                        f"http://{subdomain}",
                                        follow_redirects=True,
                                        timeout=5.0,
                                    )
                                    info.http_status = response.status_code
                                    
                                    # Try to get title
                                    title_match = response.text.lower().split("<title>")
                                    if len(title_match) > 1:
                                        info.http_title = title_match[1].split("</title>")[0].strip()
                                    
                                    break
                                except Exception:
                                    continue
                                    
                except ImportError:
                    pass
            
            return info
            
        except Exception as e:
            logger.debug(f"Failed to resolve subdomain {subdomain}: {e}")
            return None
    
    async def _check_subdomain_exists(self, subdomain: str) -> bool:
        """Check if a subdomain exists."""
        try:
            async with self._semaphore:
                result = await self.dns_client.resolve(subdomain, "A")
                return result.found and len(result.records) > 0
        except Exception:
            return False
    
    async def _detect_wildcard(self, domain: str) -> Dict[str, Any]:
        """Detect wildcard DNS configuration."""
        
        # Generate random subdomain
        import uuid
        random_sub = f"{uuid.uuid4().hex[:8]}.{domain}"
        
        try:
            async with self._semaphore:
                result = await self.dns_client.resolve(random_sub, "A")
            
            if result.found and result.records:
                return {
                    "detected": True,
                    "pattern": "*.{parent}",
                    "ip_addresses": [r.value for r in result.records],
                }
            
            return {"detected": False}
            
        except Exception:
            return {"detected": False}
    
    async def _resolve_hostname(self, hostname: str) -> List[str]:
        """Resolve hostname to IP addresses."""
        try:
            a_result = await self.dns_client.resolve(hostname, "A")
            aaaa_result = await self.dns_client.resolve(hostname, "AAAA")
            
            ips = [r.value for r in a_result.records]
            ips.extend(r.value for r in aaaa_result.records)
            
            return ips
            
        except Exception:
            return []
    
    async def find_high_value_targets(
        self,
        domain: str,
    ) -> List[SubdomainInfoResult]:
        """
        Find high-value target subdomains.
        
        Args:
            domain: Domain to search
            
        Returns:
            List of high-value subdomain results
        """
        # Get all subdomains first
        result = await self.discover(domain, brute_force=True)
        
        # Filter for high-value targets
        high_value = []
        
        for subdomain in result.subdomains:
            sub_name = subdomain.subdomain.split(".")[0]
            
            for target in HIGH_VALUE_SUBDOMAINS:
                if sub_name == target or sub_name.startswith(target + "-"):
                    high_value.append(subdomain)
                    break
        
        return high_value
    
    async def close(self):
        """Close client connections."""
        await self.ct_client.close()
        if self._securitytrails:
            await self._securitytrails.close()
