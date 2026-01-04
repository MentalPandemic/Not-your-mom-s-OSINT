"""
SecurityTrails API Client for domain intelligence and historical data.

Uses SecurityTrails API for historical DNS, WHOIS, and domain data.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)


@dataclass
class SecurityTrailsDomain:
    """Domain information from SecurityTrails."""
    hostname: str
    created_date: Optional[datetime] = None
    updated_date: Optional[datetime] = None
    registrar: Optional[str] = None
    registrant_email: Optional[str] = None
    registrant_name: Optional[str] = None
    registrant_organization: Optional[str] = None
    registrant_address: Optional[str] = None
    registrant_city: Optional[str] = None
    registrant_state: Optional[str] = None
    registrant_country: Optional[str] = None
    registrant_phone: Optional[str] = None
    admin_email: Optional[str] = None
    admin_name: Optional[str] = None
    admin_organization: Optional[str] = None
    admin_address: Optional[str] = None
    admin_city: Optional[str] = None
    admin_state: Optional[str] = None
    admin_country: Optional[str] = None
    admin_phone: Optional[str] = None
    tech_email: Optional[str] = None
    tech_name: Optional[str] = None
    tech_organization: Optional[str] = None
    tech_address: Optional[str] = None
    tech_city: Optional[str] = None
    tech_state: Optional[str] = None
    tech_country: Optional[str] = None
    tech_phone: Optional[str] = None
    zone_email: Optional[str] = None
    zone_name: Optional[str] = None
    nameservers: List[str] = field(default_factory=list)
    dnssec: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "hostname": self.hostname,
            "created_date": self.created_date.isoformat() if self.created_date else None,
            "updated_date": self.updated_date.isoformat() if self.updated_date else None,
            "registrar": self.registrar,
            "registrant_email": self.registrant_email,
            "registrant_name": self.registrant_name,
            "registrant_organization": self.registrant_organization,
            "registrant_address": self.registrant_address,
            "registrant_city": self.registrant_city,
            "registrant_state": self.registrant_state,
            "registrant_country": self.registrant_country,
            "registrant_phone": self.registrant_phone,
            "admin_email": self.admin_email,
            "admin_name": self.admin_name,
            "admin_organization": self.admin_organization,
            "admin_address": self.admin_address,
            "admin_city": self.admin_city,
            "admin_state": self.admin_state,
            "admin_country": self.admin_country,
            "admin_phone": self.admin_phone,
            "tech_email": self.tech_email,
            "tech_name": self.tech_name,
            "tech_organization": self.tech_organization,
            "tech_address": self.tech_address,
            "tech_city": self.tech_city,
            "tech_state": self.tech_state,
            "tech_country": self.tech_country,
            "tech_phone": self.tech_phone,
            "zone_email": self.zone_email,
            "zone_name": self.zone_name,
            "nameservers": self.nameservers,
            "dnssec": self.dnssec,
        }


@dataclass
class HistoricalRecord:
    """Historical DNS record."""
    values: List[str] = field(default_factory=list)
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "values": self.values,
            "first_seen": self.first_seen.isoformat() if self.first_seen else None,
            "last_seen": self.last_seen.isoformat() if self.last_seen else None,
        }


@dataclass
class SecurityTrailsHistory:
    """Historical DNS records."""
    hostname: str
    a_records: List[HistoricalRecord] = field(default_factory=list)
    aaaa_records: List[HistoricalRecord] = field(default_factory=list)
    mx_records: List[HistoricalRecord] = field(default_factory=list)
    ns_records: List[HistoricalRecord] = field(default_factory=list)
    txt_records: List[HistoricalRecord] = field(default_factory=list)
    soa_records: List[HistoricalRecord] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "hostname": self.hostname,
            "a_records": [r.to_dict() for r in self.a_records],
            "aaaa_records": [r.to_dict() for r in self.aaaa_records],
            "mx_records": [r.to_dict() for r in self.mx_records],
            "ns_records": [r.to_dict() for r in self.ns_records],
            "txt_records": [r.to_dict() for r in self.txt_records],
            "soa_records": [r.to_dict() for r in self.soa_records],
        }


@dataclass
class SubdomainInfo:
    """Subdomain information."""
    subdomain: str
    ip_addresses: List[str] = field(default_factory=list)
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "subdomain": self.subdomain,
            "ip_addresses": self.ip_addresses,
            "first_seen": self.first_seen.isoformat() if self.first_seen else None,
            "last_seen": self.last_seen.isoformat() if self.last_seen else None,
        }


class SecurityTrailsClient:
    """
    Client for SecurityTrails API.
    
    Provides access to SecurityTrails data for:
    - Domain WHOIS and registration details
    - Historical DNS records
    - Subdomain enumeration
    - IP address history
    - Associated domains
    
    Requires SecurityTrails API key.
    """
    
    BASE_URL = "https://api.securitytrails.com/v1"
    DEFAULT_TIMEOUT = 30.0
    RATE_LIMIT_REQUESTS_PER_SEC = 5
    
    def __init__(
        self,
        api_key: str,
        timeout: float = DEFAULT_TIMEOUT,
        rate_limit: float = 1.0 / RATE_LIMIT_REQUESTS_PER_SEC,
    ):
        self.api_key = api_key
        self.timeout = timeout
        self.rate_limit = rate_limit
        self._client: Optional[httpx.Client] = None
        self._last_request_time = 0.0
        
    @property
    def client(self) -> httpx.Client:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.Client(
                timeout=self.timeout,
                follow_redirects=True,
                headers={
                    "APIKEY": self.api_key,
                    "Content-Type": "application/json",
                },
            )
        return self._client
    
    async def get_domain(
        self,
        domain: str,
    ) -> Optional[SecurityTrailsDomain]:
        """
        Get domain details including WHOIS information.
        
        Args:
            domain: Domain name to look up
            
        Returns:
            SecurityTrailsDomain or None if not found
        """
        await self._rate_limit()
        
        try:
            url = f"{self.BASE_URL}/domain/{domain}"
            
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.get(url, timeout=self.timeout),
            )
            
            response.raise_for_status()
            data = response.json()
            
            return self._parse_domain(data.get("data", {}))
            
        except httpx.HTTPStatusError as e:
            logger.error(f"SecurityTrails domain lookup error: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to get domain {domain}: {e}")
            return None
    
    async def get_dns_history(
        self,
        domain: str,
        record_type: str = "A",
    ) -> Optional[SecurityTrailsHistory]:
        """
        Get historical DNS records.
        
        Args:
            domain: Domain name
            record_type: DNS record type (A, AAAA, MX, NS, TXT, SOA)
            
        Returns:
            SecurityTrailsHistory or None if not found
        """
        await self._rate_limit()
        
        try:
            url = f"{self.BASE_URL}/history/{domain}/dns/{record_type}"
            
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.get(url, timeout=self.timeout),
            )
            
            response.raise_for_status()
            data = response.json()
            
            return self._parse_history(domain, data.get("data", {}), record_type)
            
        except httpx.HTTPStatusError as e:
            logger.error(f"SecurityTrails DNS history error: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to get DNS history for {domain}: {e}")
            return None
    
    async def get_subdomains(
        self,
        domain: str,
        include_old: bool = False,
    ) -> List[SubdomainInfo]:
        """
        Get all subdomains for a domain.
        
        Args:
            domain: Domain name
            include_old: Include subdomains that no longer resolve
            
        Returns:
            List of SubdomainInfo objects
        """
        await self._rate_limit()
        
        try:
            url = f"{self.BASE_URL}/domain/{domain}/subdomains"
            params = {"include_old": "true"} if include_old else {}
            
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.get(url, params=params, timeout=self.timeout),
            )
            
            response.raise_for_status()
            data = response.json()
            
            subdomains = []
            for sub in data.get("subdomains", []):
                subdomain = SubdomainInfo(
                    subdomain=f"{sub}.{domain}" if sub else domain,
                    ip_addresses=data.get("records", {}).get(sub, {}).get("ip", []),
                )
                subdomains.append(subdomain)
            
            return subdomains
            
        except httpx.HTTPStatusError as e:
            logger.error(f"SecurityTrails subdomain error: {e}")
            return []
        except Exception as e:
            logger.error(f"Failed to get subdomains for {domain}: {e}")
            return []
    
    async def get_ip_history(
        self,
        domain: str,
    ) -> List[Dict[str, Any]]:
        """
        Get IP address history for a domain.
        
        Args:
            domain: Domain name
            
        Returns:
            List of IP history records
        """
        await self._rate_limit()
        
        try:
            url = f"{self.BASE_URL}/history/{domain}/ip"
            
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.get(url, timeout=self.timeout),
            )
            
            response.raise_for_status()
            data = response.json()
            
            return data.get("records", [])
            
        except httpx.HTTPStatusError as e:
            logger.error(f"SecurityTrails IP history error: {e}")
            return []
        except Exception as e:
            logger.error(f"Failed to get IP history for {domain}: {e}")
            return []
    
    async def search_domains_by_ip(
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
        await self._rate_limit()
        
        try:
            url = f"{self.BASE_URL}/domains/list"
            params = {"ipv4": ip}
            
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.get(url, params=params, timeout=self.timeout),
            )
            
            response.raise_for_status()
            data = response.json()
            
            return [d.get("hostname") for d in data.get("records", [])]
            
        except httpx.HTTPStatusError as e:
            logger.error(f"SecurityTrails reverse IP error: {e}")
            return []
        except Exception as e:
            logger.error(f"Failed to search domains for IP {ip}: {e}")
            return []
    
    async def search_domains_by_ns(
        self,
        nameserver: str,
    ) -> List[str]:
        """
        Find all domains using a specific nameserver.
        
        Args:
            nameserver: Nameserver domain
            
        Returns:
            List of domain names
        """
        await self._rate_limit()
        
        try:
            url = f"{self.BASE_URL}/domains/list"
            params = {"nameserver": nameserver}
            
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.get(url, params=params, timeout=self.timeout),
            )
            
            response.raise_for_status()
            data = response.json()
            
            return [d.get("hostname") for d in data.get("records", [])]
            
        except httpx.HTTPStatusError as e:
            logger.error(f"SecurityTrails nameserver search error: {e}")
            return []
        except Exception as e:
            logger.error(f"Failed to search domains for nameserver {nameserver}: {e}")
            return []
    
    async def search_by_email(
        self,
        email: str,
    ) -> List[str]:
        """
        Find all domains registered with an email address.
        
        Args:
            email: Email address
            
        Returns:
            List of domain names
        """
        await self._rate_limit()
        
        try:
            url = f"{self.BASE_URL}/domains/list"
            params = {"email": email}
            
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.get(url, params=params, timeout=self.timeout),
            )
            
            response.raise_for_status()
            data = response.json()
            
            return [d.get("hostname") for d in data.get("records", [])]
            
        except httpx.HTTPStatusError as e:
            logger.error(f"SecurityTrails email search error: {e}")
            return []
        except Exception as e:
            logger.error(f"Failed to search domains for email {email}: {e}")
            return []
    
    async def get_associated_domains(
        self,
        domain: str,
    ) -> Dict[str, List[str]]:
        """
        Get domains associated with the same registrant, IP, or NS.
        
        Args:
            domain: Domain name
            
        Returns:
            Dictionary with keys: "registrant", "ip", "nameserver"
        """
        await self._rate_limit()
        
        try:
            url = f"{self.BASE_URL}/domain/{domain}/associated"
            
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.get(url, timeout=self.timeout),
            )
            
            response.raise_for_status()
            data = response.json()
            
            return {
                "registrant": data.get("registrant", []),
                "ip": data.get("ip", []),
                "nameserver": data.get("nameserver", []),
            }
            
        except httpx.HTTPStatusError as e:
            logger.error(f"SecurityTrails associated domains error: {e}")
            return {"registrant": [], "ip": [], "nameserver": []}
        except Exception as e:
            logger.error(f"Failed to get associated domains for {domain}: {e}")
            return {"registrant": [], "ip": [], "nameserver": []}
    
    def _parse_domain(self, data: Dict[str, Any]) -> SecurityTrailsDomain:
        """Parse domain data from SecurityTrails response."""
        whois = data.get("whois", {})
        records = data.get("current_dns", {})
        
        created_date = data.get("created_date")
        if created_date:
            created_date = datetime.fromisoformat(created_date.replace("Z", "+00:00"))
        
        updated_date = data.get("updated_date")
        if updated_date:
            updated_date = datetime.fromisoformat(updated_date.replace("Z", "+00:00"))
        
        return SecurityTrailsDomain(
            hostname=data.get("hostname", ""),
            created_date=created_date,
            updated_date=updated_date,
            registrar=data.get("registrar"),
            registrant_email=whois.get("registrant", {}).get("email"),
            registrant_name=whois.get("registrant", {}).get("name"),
            registrant_organization=whois.get("registrant", {}).get("organization"),
            registrant_address=whois.get("registrant", {}).get("streetAddress"),
            registrant_city=whois.get("registrant", {}).get("city"),
            registrant_state=whois.get("registrant", {}).get("state"),
            registrant_country=whois.get("registrant", {}).get("country"),
            registrant_phone=whois.get("registrant", {}).get("telephone"),
            admin_email=whois.get("admin", {}).get("email"),
            admin_name=whois.get("admin", {}).get("name"),
            admin_organization=whois.get("admin", {}).get("organization"),
            admin_address=whois.get("admin", {}).get("streetAddress"),
            admin_city=whois.get("admin", {}).get("city"),
            admin_state=whois.get("admin", {}).get("state"),
            admin_country=whois.get("admin", {}).get("country"),
            admin_phone=whois.get("admin", {}).get("telephone"),
            tech_email=whois.get("tech", {}).get("email"),
            tech_name=whois.get("tech", {}).get("name"),
            tech_organization=whois.get("tech", {}).get("organization"),
            tech_address=whois.get("tech", {}).get("streetAddress"),
            tech_city=whois.get("tech", {}).get("city"),
            tech_state=whois.get("tech", {}).get("state"),
            tech_country=whois.get("tech", {}).get("country"),
            tech_phone=whois.get("tech", {}).get("telephone"),
            nameservers=records.get("ns", []),
            dnssec=data.get("dnssec", False),
        )
    
    def _parse_history(
        self,
        domain: str,
        data: Dict[str, Any],
        record_type: str,
    ) -> SecurityTrailsHistory:
        """Parse historical DNS records."""
        history = SecurityTrailsHistory(hostname=domain)
        
        records = data.get("records", [])
        
        for record in records:
            values = record.get("values", [])
            first_seen = record.get("first_seen")
            last_seen = record.get("last_seen")
            
            if first_seen:
                first_seen = datetime.fromisoformat(first_seen.replace("Z", "+00:00"))
            if last_seen:
                last_seen = datetime.fromisoformat(last_seen.replace("Z", "+00:00"))
            
            hist_record = HistoricalRecord(
                values=values,
                first_seen=first_seen,
                last_seen=last_seen,
            )
            
            if record_type == "A":
                history.a_records.append(hist_record)
            elif record_type == "AAAA":
                history.aaaa_records.append(hist_record)
            elif record_type == "MX":
                history.mx_records.append(hist_record)
            elif record_type == "NS":
                history.ns_records.append(hist_record)
            elif record_type == "TXT":
                history.txt_records.append(hist_record)
            elif record_type == "SOA":
                history.soa_records.append(hist_record)
        
        return history
    
    async def _rate_limit(self):
        """Enforce rate limiting."""
        now = asyncio.get_event_loop().time()
        elapsed = now - self._last_request_time
        
        if elapsed < self.rate_limit:
            await asyncio.sleep(self.rate_limit - elapsed)
        
        self._last_request_time = asyncio.get_event_loop().time()
    
    async def close(self):
        """Close the HTTP client."""
        if self._client:
            self._client.close()
            self._client = None
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
