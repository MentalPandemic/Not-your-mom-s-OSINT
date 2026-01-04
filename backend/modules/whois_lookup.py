"""
WHOIS Lookup Module for domain and IP intelligence.

Provides comprehensive WHOIS lookups for domains and IP addresses,
including registrant information, registrar details, and privacy detection.
"""

import asyncio
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

import whois
from dateutil import parser as date_parser

from clients.geoip_client import GeoIpClient, GeoIpResult
from clients.securitytrails_client import SecurityTrailsClient, SecurityTrailsDomain

logger = logging.getLogger(__name__)


@dataclass
class RegistrantInfo:
    """WHOIS registrant information."""
    name: Optional[str] = None
    organization: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    fax: Optional[str] = None
    street: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "organization": self.organization,
            "email": self.email,
            "phone": self.phone,
            "fax": self.fax,
            "street": self.street,
            "city": self.city,
            "state": self.state,
            "postal_code": self.postal_code,
            "country": self.country,
        }
    
    def is_empty(self) -> bool:
        """Check if registrant info is empty (likely privacy protected)."""
        return all(v is None for v in [
            self.name, self.organization, self.email, self.phone,
            self.street, self.city, self.state, self.country,
        ])


@dataclass
class RegistrarInfo:
    """Registrar information."""
    name: Optional[str] = None
    iana_id: Optional[str] = None
    url: Optional[str] = None
    abuse_email: Optional[str] = None
    abuse_phone: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "iana_id": self.iana_id,
            "url": self.url,
            "abuse_email": self.abuse_email,
            "abuse_phone": self.abuse_phone,
        }


@dataclass
class DomainWhoisResult:
    """Complete WHOIS result for a domain."""
    domain: str
    registrars: List[RegistrarInfo] = field(default_factory=list)
    registrant: RegistrantInfo = field(default_factory=lambda: RegistrantInfo())
    admin: RegistrantInfo = field(default_factory=lambda: RegistrantInfo())
    tech: RegistrantInfo = field(default_factory=lambda: RegistrantInfo())
    registrant_email: Optional[str] = None
    admin_email: Optional[str] = None
    tech_email: Optional[str] = None
    
    # Dates
    registration_date: Optional[datetime] = None
    expiration_date: Optional[datetime] = None
    last_updated: Optional[datetime] = None
    
    # Technical
    nameservers: List[str] = field(default_factory=list)
    dnssec: bool = False
    status: List[str] = field(default_factory=list)
    
    # Privacy
    privacy_protected: bool = False
    privacy_service: Optional[str] = None
    
    # Raw
    raw_whois: Optional[str] = None
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "domain": self.domain,
            "registrars": [r.to_dict() for r in self.registrars],
            "registrant": self.registrant.to_dict(),
            "admin": self.admin.to_dict(),
            "tech": self.tech.to_dict(),
            "registrant_email": self.registrant_email,
            "admin_email": self.admin_email,
            "tech_email": self.tech_email,
            "registration_date": self.registration_date.isoformat() if self.registration_date else None,
            "expiration_date": self.expiration_date.isoformat() if self.expiration_date else None,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None,
            "nameservers": self.nameservers,
            "dnssec": self.dnssec,
            "status": self.status,
            "privacy_protected": self.privacy_protected,
            "privacy_service": self.privacy_service,
            "raw_whois": self.raw_whois,
            "error": self.error,
        }


@dataclass
class IpWhoisResult:
    """Complete WHOIS result for an IP address."""
    ip_address: str
    network_name: Optional[str] = None
    description: Optional[str] = None
    
    # Registrant
    registrant: Optional[str] = None
    registration_date: Optional[datetime] = None
    updated_date: Optional[datetime] = None
    
    # ASN
    asn: Optional[str] = None
    asn_name: Optional[str] = None
    asn_organization: Optional[str] = None
    asn_decimal: Optional[int] = None
    
    # Network
    network_range: Optional[str] = None
    network_prefix: Optional[str] = None
    
    # Geolocation
    geolocation: Optional[Dict[str, Any]] = None
    
    # Abuse contacts
    abuse_email: Optional[str] = None
    abuse_phone: Optional[str] = None
    
    # Raw
    raw_whois: Optional[str] = None
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "ip_address": self.ip_address,
            "network_name": self.network_name,
            "description": self.description,
            "registrant": self.registrant,
            "registration_date": self.registration_date.isoformat() if self.registration_date else None,
            "updated_date": self.updated_date.isoformat() if self.updated_date else None,
            "asn": self.asn,
            "asn_name": self.asn_name,
            "asn_organization": self.asn_organization,
            "asn_decimal": self.asn_decimal,
            "network_range": self.network_range,
            "network_prefix": self.network_prefix,
            "geolocation": self.geolocation,
            "abuse_email": self.abuse_email,
            "abuse_phone": self.abuse_phone,
            "raw_whois": self.raw_whois,
            "error": self.error,
        }


@dataclass
class EmailWhoisResult:
    """WHOIS results for an email search."""
    email: str
    domains: List[Dict[str, Any]] = field(default_factory=list)
    variations: List[str] = field(default_factory=list)
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "email": self.email,
            "domains": self.domains,
            "variations": self.variations,
            "error": self.error,
        }


class PrivacyDetector:
    """Detect privacy protection in WHOIS data."""
    
    # Known privacy services
    PRIVACY_SERVICES = [
        "redacted for privacy",
        "privacy protection",
        "domains by proxy",
        "namecheap",
        "godaddy privacy",
        "enom",
        "tucows",
        "1api",
        "gname",
        "dynadot",
        "name.com",
        "hover",
        "register.com",
        "markmonitor",
        "cscglobal",
        "network solutions",
        "internet.bs",
        "pdrm",
        "safe names",
        "magnet domain",
    ]
    
    # Privacy-related email patterns
    PRIVACY_EMAILS = [
        "privacy",
        "redacted",
        "proxy",
        "anon",
        "hidden",
        "confidential",
    ]
    
    def is_privacy_protected(self, whois_result: DomainWhoisResult) -> bool:
        """Check if WHOIS data shows privacy protection."""
        # Check if all contact info is empty
        if whois_result.registrant.is_empty():
            return True
        
        # Check for privacy service mentions
        raw = (whois_result.raw_whois or "").lower()
        for service in self.PRIVACY_SERVICES:
            if service in raw:
                return True
        
        # Check for redacted email
        email = (whois_result.registrant_email or "").lower()
        for pattern in self.PRIVACY_EMAILS:
            if pattern in email:
                return True
        
        # Check for obvious privacy email patterns
        if email and "redacted" in email:
            return True
        if email and email.endswith("@example.com"):
            return True
        
        return False
    
    def get_privacy_service(self, whois_result: DomainWhoisResult) -> Optional[str]:
        """Identify the privacy service being used."""
        raw = (whois_result.raw_whois or "").lower()
        
        service_patterns = {
            "Namecheap": ["namecheap", "whoisguard", "id protection"],
            "GoDaddy": ["godaddy privacy", "domains by proxy"],
            "eNom": ["enom", "privacy"],
            "Tucows": ["tucows", "openname"],
            "MarkMonitor": ["markmonitor", "cscglobal"],
            "Privacy Guardian": ["privacy guardian"],
            "Proxy.kg": ["proxy.kg"],
            "Njal.la": ["njal.la"],
        }
        
        for service, patterns in service_patterns.items():
            for pattern in patterns:
                if pattern in raw:
                    return service
        
        return None


class WhoisLookup:
    """
    WHOIS lookup module for domain and IP intelligence.
    
    Provides:
    - Domain WHOIS lookups
    - IP WHOIS lookups
    - Email extraction from WHOIS
    - Privacy detection
    - Alternative domain discovery
    """
    
    DEFAULT_TIMEOUT = 30.0
    
    def __init__(
        self,
        securitytrails_api_key: Optional[str] = None,
        geoip_db_path: Optional[str] = None,
        timeout: float = DEFAULT_TIMEOUT,
    ):
        """
        Initialize WHOIS lookup module.
        
        Args:
            securitytrails_api_key: SecurityTrails API key for enhanced lookups
            geoip_db_path: Path to MaxMind GeoIP database
            timeout: Request timeout in seconds
        """
        self.timeout = timeout
        self._securitytrails: Optional[SecurityTrailsClient] = None
        self._geoip: Optional[GeoIpClient] = None
        self._privacy_detector = PrivacyDetector()
        
        if securitytrails_api_key:
            self._securitytrails = SecurityTrailsClient(securitytrails_api_key)
        if geoip_db_path:
            self._geoip = GeoIpClient(city_db_path=geoip_db_path)
    
    async def lookup_domain(
        self,
        domain: str,
        include_raw: bool = False,
    ) -> DomainWhoisResult:
        """
        Perform WHOIS lookup for a domain.
        
        Args:
            domain: Domain name to look up
            include_raw: Include raw WHOIS response
            
        Returns:
            DomainWhoisResult with all WHOIS information
        """
        logger.info(f"Performing WHOIS lookup for {domain}")
        
        result = DomainWhoisResult(domain=domain)
        
        try:
            # Try SecurityTrails first for enhanced data
            if self._securitytrails:
                st_domain = await self._securitytrails.get_domain(domain)
                if st_domain:
                    result = self._parse_securitytrails_domain(st_domain, result)
            
            # Fall back to python-whois
            if result.registrant.is_empty() or not result.nameservers:
                w = await self._whois_lookup(domain)
                result = self._parse_whois_response(w, result)
            
            # Check for privacy protection
            result.privacy_protected = self._privacy_detector.is_privacy_protected(result)
            result.privacy_service = self._privacy_detector.get_privacy_service(result)
            
        except Exception as e:
            logger.error(f"WHOIS lookup failed for {domain}: {e}")
            result.error = str(e)
        
        return result
    
    async def lookup_ip(
        self,
        ip_address: str,
        include_raw: bool = False,
    ) -> IpWhoisResult:
        """
        Perform IP WHOIS lookup.
        
        Args:
            ip_address: IP address to look up
            include_raw: Include raw WHOIS response
            
        Returns:
            IpWhoisResult with IP WHOIS information
        """
        logger.info(f"Performing IP WHOIS lookup for {ip_address}")
        
        result = IpWhoisResult(ip_address=ip_address)
        
        try:
            # Use GeoIP for location data
            if self._geoip:
                geo_result = self._geoip.lookup(ip_address)
                result.geolocation = geo_result.location.to_dict() if geo_result.location else None
                
                if geo_result.asn:
                    result.asn = geo_result.asn.asn
                    result.asn_organization = geo_result.asn.organization
                    result.asn_decimal = geo_result.asn.asn_decimal
                
                if geo_result.isp:
                    result.network_name = geo_result.isp
            
            # Perform IP WHOIS lookup
            whois_data = await self._ip_whois_lookup(ip_address)
            result = self._parse_ip_whois(whois_data, result)
            
        except Exception as e:
            logger.error(f"IP WHOIS lookup failed for {ip_address}: {e}")
            result.error = str(e)
        
        return result
    
    async def extract_emails(
        self,
        domain: str,
    ) -> EmailWhoisResult:
        """
        Extract and find all emails associated with a domain.
        
        Args:
            domain: Domain name to analyze
            
        Returns:
            EmailWhoisResult with extracted emails and related domains
        """
        logger.info(f"Extracting emails from WHOIS for {domain}")
        
        result = EmailWhoisResult(email=domain)
        
        try:
            whois_result = await self.lookup_domain(domain)
            
            # Collect all emails
            emails = set()
            for attr in ['registrant_email', 'admin_email', 'tech_email']:
                email = getattr(whois_result, attr)
                if email and self._is_valid_email(email):
                    emails.add(email.lower())
            
            result.domains = []
            
            # Find domains for each email
            if self._securitytrails and emails:
                for email in emails:
                    domains = await self._securitytrails.search_by_email(email)
                    for d in domains:
                        result.domains.append({
                            "domain": d,
                            "email": email,
                            "relationship": "same_registrant_email",
                        })
            
            result.variations = self._generate_email_variations(list(emails))
            
        except Exception as e:
            logger.error(f"Email extraction failed for {domain}: {e}")
            result.error = str(e)
        
        return result
    
    async def find_domains_by_email(
        self,
        email: str,
    ) -> List[Dict[str, Any]]:
        """
        Find all domains registered with an email address.
        
        Args:
            email: Email address to search
            
        Returns:
            List of domain dictionaries with registration info
        """
        logger.info(f"Finding domains for email {email}")
        
        if not self._securitytrails:
            logger.warning("SecurityTrails not configured, cannot search by email")
            return []
        
        try:
            domains = await self._securitytrails.search_by_email(email)
            
            results = []
            for domain in domains:
                domain_info = await self._securitytrails.get_domain(domain)
                if domain_info:
                    results.append({
                        "domain": domain_info.hostname,
                        "registrar": domain_info.registrar,
                        "registration_date": domain_info.created_date.isoformat() if domain_info.created_date else None,
                        "expiration_date": domain_info.expiration_date.isoformat() if domain_info.expiration_date else None,
                        "registrant_name": domain_info.registrant_name,
                        "registrant_email": domain_info.registrant_email,
                        "nameservers": domain_info.nameservers,
                    })
            
            return results
            
        except Exception as e:
            logger.error(f"Domain search by email failed: {e}")
            return []
    
    def _parse_whois_response(
        self,
        w: whois.WhoisEntry,
        result: DomainWhoisResult,
    ) -> DomainWhoisResult:
        """Parse python-whois response into DomainWhoisResult."""
        
        # Basic info
        result.domain = w.domain or result.domain
        
        # Dates
        if w.creation_date:
            if isinstance(w.creation_date, list):
                result.registration_date = w.creation_date[0]
            else:
                result.registration_date = w.creation_date
        
        if w.expiration_date:
            if isinstance(w.expiration_date, list):
                result.expiration_date = w.expiration_date[0]
            else:
                result.expiration_date = w.expiration_date
        
        if w.updated_date:
            if isinstance(w.updated_date, list):
                result.last_updated = w.updated_date[0]
            else:
                result.last_updated = w.updated_date
        
        # Registrant
        if hasattr(w, 'registrant') and w.registrant:
            result.registrant.name = w.registrant
        if hasattr(w, 'registrant_name') and w.registrant_name:
            result.registrant.name = w.registrant_name
        if hasattr(w, 'registrant_org') and w.registrant_org:
            result.registrant.organization = w.registrant_org
        if hasattr(w, 'registrant_country') and w.registrant_country:
            result.registrant.country = w.registrant_country
        if hasattr(w, 'registrant_state') and w.registrant_state:
            result.registrant.state = w.registrant_state
        if hasattr(w, 'registrant_city') and w.registrant_city:
            result.registrant.city = w.registrant_city
        if hasattr(w, 'registrant_email') and w.registrant_email:
            result.registrant_email = w.registrant_email
            result.registrant.email = w.registrant_email
        if hasattr(w, 'registrant_phone') and w.registrant_phone:
            result.registrant.phone = w.registrant_phone
        
        # Admin
        if hasattr(w, 'admin') and w.admin:
            result.admin.name = w.admin
        if hasattr(w, 'admin_email') and w.admin_email:
            result.admin_email = w.admin_email
            result.admin.email = w.admin_email
        if hasattr(w, 'admin_phone') and w.admin_phone:
            result.admin.phone = w.admin_phone
        if hasattr(w, 'admin_country') and w.admin_country:
            result.admin.country = w.admin_country
        
        # Tech
        if hasattr(w, 'tech') and w.tech:
            result.tech.name = w.tech
        if hasattr(w, 'tech_email') and w.tech_email:
            result.tech_email = w.tech_email
            result.tech.email = w.tech_email
        if hasattr(w, 'tech_phone') and w.tech_phone:
            result.tech.phone = w.tech_phone
        
        # Registrar
        if hasattr(w, 'registrar') and w.registrar:
            registrar = RegistrarInfo(name=w.registrar)
            if hasattr(w, 'registrar_url') and w.registrar_url:
                registrar.url = w.registrar_url
            result.registrars.append(registrar)
        
        # Nameservers
        if hasattr(w, 'nameservers') and w.nameservers:
            if isinstance(w.nameservers, list):
                result.nameservers = [ns.lower() for ns in w.nameservers]
            else:
                result.nameservers = [w.nameservers.lower()]
        
        # DNSSEC
        if hasattr(w, 'dnssec') and w.dnssec:
            result.dnssec = True
        
        # Status
        if hasattr(w, 'status') and w.status:
            if isinstance(w.status, list):
                result.status = [s for s in w.status if s]
            else:
                result.status = [w.status]
        
        return result
    
    def _parse_securitytrails_domain(
        self,
        st_domain: SecurityTrailsDomain,
        result: DomainWhoisResult,
    ) -> DomainWhoisResult:
        """Parse SecurityTrails domain data."""
        
        result.registrar = st_domain.registrar
        result.nameservers = st_domain.nameservers
        result.dnssec = st_domain.dnssec
        
        # Registrant
        result.registrant.name = st_domain.registrant_name
        result.registrant.email = st_domain.registrant_email
        result.registrant.organization = st_domain.registrant_organization
        result.registrant.phone = st_domain.registrant_phone
        result.registrant.country = st_domain.registrant_country
        result.registrant.state = st_domain.registrant_state
        result.registrant.city = st_domain.registrant_city
        result.registrant_email = st_domain.registrant_email
        
        # Admin
        result.admin.name = st_domain.admin_name
        result.admin.email = st_domain.admin_email
        result.admin.organization = st_domain.admin_organization
        result.admin.phone = st_domain.admin_phone
        result.admin.country = st_domain.admin_country
        result.admin_email = st_domain.admin_email
        
        # Tech
        result.tech.name = st_domain.tech_name
        result.tech.email = st_domain.tech_email
        result.tech.organization = st_domain.tech_organization
        result.tech.phone = st_domain.tech_phone
        result.tech.country = st_domain.tech_country
        result.tech_email = st_domain.tech_email
        
        # Dates
        result.registration_date = st_domain.created_date
        result.expiration_date = st_domain.updated_date
        
        return result
    
    def _parse_ip_whois(
        self,
        data: Dict[str, Any],
        result: IpWhoisResult,
    ) -> IpWhoisResult:
        """Parse IP WHOIS data."""
        
        result.network_name = data.get("network", {}).get("name")
        result.description = data.get("network", {}).get("description")
        result.registrant = data.get("network", {}).get("org")
        
        # Dates
        if "network" in data:
            created = data["network"].get("created")
            if created:
                try:
                    result.registration_date = date_parser.parse(created)
                except Exception:
                    pass
        
        # ASN
        if "asn" in data:
            result.asn = str(data["asn"])
            result.asn_name = data.get("asn_name")
            result.asn_organization = data.get("asn_description")
            try:
                result.asn_decimal = int(data["asn"])
            except (ValueError, TypeError):
                pass
        
        # Network range
        if "network" in data:
            inetnums = data["network"].get("inetnum")
            if inetnums:
                result.network_range = inetnums
        
        # Abuse contacts
        if "network" in data:
            abuse = data["network"].get("abuse-c")
            if abuse:
                result.abuse_email = abuse
        
        return result
    
    async def _whois_lookup(self, domain: str) -> whois.WhoisEntry:
        """Perform synchronous WHOIS lookup."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: whois.query(domain),
        )
    
    async def _ip_whois_lookup(self, ip_address: str) -> Dict[str, Any]:
        """Perform IP WHOIS lookup using external service."""
        # Use ipwhois library
        loop = asyncio.get_event_loop()
        
        def _lookup():
            from ipwhois import IPWhois
            obj = IPWhois(ip_address)
            return obj.lookup_rdap(depth=1)
        
        return await loop.run_in_executor(None, _lookup)
    
    def _is_valid_email(self, email: str) -> bool:
        """Check if email is valid (not privacy protected)."""
        if not email:
            return False
        
        email = email.lower().strip()
        
        # Check for obvious invalid patterns
        invalid_patterns = [
            "@",
            "@example.com",
            "@localhost",
            "@redacted",
            "@privacy",
            "admin@",
            "support@",
            "info@",
        ]
        
        for pattern in invalid_patterns:
            if pattern in email:
                if pattern == "@":
                    # Must have valid format
                    return bool(re.match(r"[^@]+@[^@]+\.[^@]+", email))
                return False
        
        return bool(re.match(r"[^@]+@[^@]+\.[^@]+", email))
    
    def _generate_email_variations(self, emails: List[str]) -> List[str]:
        """Generate email variations for a domain."""
        variations = set()
        
        for email in emails:
            if "@" not in email:
                continue
            
            local, domain = email.split("@", 1)
            
            # Common variations
            variations.add(f"{local}@{domain}")
            variations.add(f"{local.replace('.', '')}@{domain}")
            variations.add(f"{local.replace('-', '')}@{domain}")
            variations.add(f"{local.replace('_', '')}@{domain}")
            
            # Add common prefixes
            for prefix in ["admin", "support", "contact", "info", "webmaster"]:
                variations.add(f"{prefix}@{domain}")
                variations.add(f"{prefix}.{local}@{domain}")
                variations.add(f"{local}.{prefix}@{domain}")
        
        return list(variations)
    
    async def close(self):
        """Close client connections."""
        if self._securitytrails:
            await self._securitytrails.close()
            self._securitytrails = None
