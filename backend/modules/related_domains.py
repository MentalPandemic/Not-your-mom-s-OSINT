"""
Related Domain Discovery Module for domain intelligence.

Discovers related domains through:
- WHOIS registrant information
- Certificate Transparency logs
- Shared infrastructure (IP, ASN, nameservers)
- Typosquatting and variations
- Company/brand domain discovery
"""

import asyncio
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Set

from clients.censys_client import CensysClient, CensysCertificate
from clients.ct_client import CtClient, CertificateInfo
from clients.securitytrails_client import SecurityTrailsClient

from modules.whois_lookup import WhoisLookup
from modules.dns_enumeration import DnsEnumeration
from modules.subdomain_discovery import SubdomainDiscovery
from modules.ssl_analysis import SslAnalysis

logger = logging.getLogger(__name__)


@dataclass
class RelatedDomainInfo:
    """Information about a related domain."""
    domain: str
    relationship_type: str  # same_registrant, same_ip, same_ns, same_cert, etc.
    confidence: float = 1.0  # 0.0 to 1.0
    
    # Evidence
    shared_attribute: Optional[str] = None  # email, ip, nameserver, etc.
    evidence: Dict[str, Any] = field(default_factory=dict)
    
    # Domain info
    is_active: bool = True
    registration_date: Optional[datetime] = None
    expiration_date: Optional[datetime] = None
    registrar: Optional[str] = None
    
    # Risk assessment
    risk_score: int = 0  # 0-100
    is_parked: bool = False
    is_suspicious: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "domain": self.domain,
            "relationship_type": self.relationship_type,
            "confidence": self.confidence,
            "shared_attribute": self.shared_attribute,
            "evidence": self.evidence,
            "is_active": self.is_active,
            "registration_date": self.registration_date.isoformat() if self.registration_date else None,
            "expiration_date": self.expiration_date.isoformat() if self.expiration_date else None,
            "registrar": self.registrar,
            "risk_score": self.risk_score,
            "is_parked": self.is_parked,
            "is_suspicious": self.is_suspicious,
        }


@dataclass
class DomainPortfolioResult:
    """Complete domain portfolio for a person or company."""
    query: str  # email or company name
    query_type: str  # email or company
    
    # Direct registrations
    domains: List[RelatedDomainInfo] = field(default_factory=list)
    
    # Statistics
    total_domains: int = 0
    active_domains: int = 0
    parked_domains: int = 0
    
    # Organization
    registrars: List[str] = field(default_factory=list)
    registration_dates: List[datetime] = field(default_factory=list)
    
    # Related entities
    shared_registrars: List[str] = field(default_factory=list)
    shared_nameservers: List[str] = field(default_factory=list)
    shared_countries: List[str] = field(default_factory=list)
    
    # Risk assessment
    total_risk_score: int = 0
    high_risk_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "query": self.query,
            "query_type": self.query_type,
            "domains": [d.to_dict() for d in self.domains],
            "total_domains": self.total_domains,
            "active_domains": self.active_domains,
            "parked_domains": self.parked_domains,
            "registrars": self.registrars,
            "registration_dates": [d.isoformat() for d in self.registration_dates],
            "shared_registrars": self.shared_registrars,
            "shared_nameservers": self.shared_nameservers,
            "shared_countries": self.shared_countries,
            "total_risk_score": self.total_risk_score,
            "high_risk_count": self.high_risk_count,
        }


@dataclass
class DomainVariationsResult:
    """Domain variations and typosquatting results."""
    original_domain: str
    variations: List[RelatedDomainInfo] = field(default_factory=list)
    takeovers: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "original_domain": self.original_domain,
            "variations": [v.to_dict() for v in self.variations],
            "takeovers": self.takeovers,
        }


# Common TLDs for variation generation
COMMON_TLDS = [
    ".com", ".net", ".org", ".io", ".co", ".ai", ".app", ".dev",
    ".cloud", ".tech", ".online", ".site", ".website", ".info",
    ".biz", ".us", ".uk", ".de", ".fr", ".jp", ".cn", ".ru",
    ".me", ".cc", ".tv", ".ws", ".xyz", ".top", ".club", ".win",
]

# Known parking providers
PARKING_PROVIDERS = [
    "sedo", "namecheap parking", "godaddy parking", "enom",
    "domain parking", "parked", "domainindex", "cash parking",
    "fantastic domains", "domain sponsor",
]

# Suspicious patterns
SUSPICIOUS_PATTERNS = [
    "phish", "phishing", "fake", "scam", "spam", "malware",
    "hack", "hacked", "attack", "breach", "leak",
]


class RelatedDomains:
    """
    Related domain discovery module.
    
    Provides:
    - Same registrant discovery via WHOIS
    - Same infrastructure discovery (IP, ASN, NS)
    - Certificate-based discovery
    - Typosquatting detection
    - Brand domain discovery
    - Domain portfolio analysis
    """
    
    def __init__(
        self,
        securitytrails_api_key: Optional[str] = None,
        censys_api_id: Optional[str] = None,
        censys_api_secret: Optional[str] = None,
        shodan_api_key: Optional[str] = None,
    ):
        """
        Initialize related domains module.
        
        Args:
            securitytrails_api_key: SecurityTrails API key
            censys_api_id: Censys API ID
            censys_api_secret: Censys API secret
            shodan_api_key: Shodan API key
        """
        self._whois = WhoisLookup(securitytrails_api_key)
        self._dns = DnsEnumeration(securitytrails_api_key)
        self._subdomain = SubdomainDiscovery(securitytrails_api_key)
        self._ssl = SslAnalysis(censys_api_id, censys_api_secret, shodan_api_key)
        self._securitytrails: Optional[SecurityTrailsClient] = None
        self._censys: Optional[CensysClient] = None
        self._ct: Optional[CtClient] = None
        
        if securitytrails_api_key:
            self._securitytrails = SecurityTrailsClient(securitytrails_api_key)
        if censys_api_id and censys_api_secret:
            self._censys = CensysClient(censys_api_id, censys_api_secret)
        self._ct = CtClient()
    
    async def find_related_domains(
        self,
        domain: str,
        include_infrastructure: bool = True,
        include_certificates: bool = True,
        max_results: int = 100,
    ) -> List[RelatedDomainInfo]:
        """
        Find all domains related to the target domain.
        
        Args:
            domain: Domain to analyze
            include_infrastructure: Find domains on same IP/ASN/NS
            include_certificates: Find domains with same certificate
            max_results: Maximum results to return
            
        Returns:
            List of RelatedDomainInfo objects
        """
        logger.info(f"Finding related domains for {domain}")
        
        related_domains: Dict[str, RelatedDomainInfo] = {}
        
        try:
            # Get domain info
            whois_result = await self._whois.lookup_domain(domain)
            dns_result = await self._dns.enumerate_all(domain)
            
            # 1. Find same registrant via email
            if whois_result.registrant_email:
                registrant_domains = await self._find_by_email(
                    whois_result.registrant_email,
                    exclude=[domain],
                )
                for d in registrant_domains:
                    related_domains[d.domain] = d
            
            # 2. Find same IP
            if include_infrastructure:
                ip_domains = await self._find_by_infrastructure(
                    domain,
                    dns_result.get_all_ips(),
                )
                for d in ip_domains:
                    if d.domain not in related_domains:
                        related_domains[d.domain] = d
            
            # 3. Find same nameservers
            ns_domains = await self._find_by_nameservers(
                domain,
                dns_result.get_all_nameservers(),
            )
            for d in ns_domains:
                if d.domain not in related_domains:
                    related_domains[d.domain] = d
            
            # 4. Find via certificates
            if include_certificates:
                cert_domains = await self._find_by_certificate(domain)
                for d in cert_domains:
                    if d.domain not in related_domains:
                        related_domains[d.domain] = d
            
            # 5. Find via SecurityTrails associated domains
            if self._securitytrails:
                associated = await self._securitytrails.get_associated_domains(domain)
                
                for domain_list in associated.values():
                    for related in domain_list:
                        if related != domain and related not in related_domains:
                            related_domains[related] = RelatedDomainInfo(
                                domain=related,
                                relationship_type="same_infrastructure",
                                shared_attribute="securitytrails",
                                confidence=0.9,
                            )
            
        except Exception as e:
            logger.error(f"Related domain search failed for {domain}: {e}")
        
        # Limit results
        return list(related_domains.values())[:max_results]
    
    async def find_domains_by_email(
        self,
        email: str,
    ) -> DomainPortfolioResult:
        """
        Find all domains registered with an email address.
        
        Args:
            email: Email address to search
            
        Returns:
            DomainPortfolioResult with all registered domains
        """
        logger.info(f"Finding domains for email {email}")
        
        result = DomainPortfolioResult(query=email, query_type="email")
        
        try:
            # Search via SecurityTrails
            if self._securitytrails:
                domains = await self._securitytrails.search_by_email(email)
                
                for domain in domains:
                    domain_info = await self._securitytrails.get_domain(domain)
                    
                    if domain_info:
                        domain_obj = RelatedDomainInfo(
                            domain=domain,
                            relationship_type="same_registrant_email",
                            shared_attribute=email,
                            confidence=1.0,
                            registration_date=domain_info.created_date,
                            expiration_date=domain_info.expiration_date,
                            registrar=domain_info.registrar,
                        )
                        
                        # Check if parked
                        domain_obj.is_parked = self._is_parked(domain_info)
                        domain_obj.risk_score = self._calculate_risk(domain_obj)
                        
                        result.domains.append(domain_obj)
            
            # Also search via Censys
            if self._censys:
                query = f'issuer.email: "{email}" OR subject.email: "{email}"'
                search_result = await self._censys.search_certificates(query, per_page=50)
                
                for cert in search_result.certificates:
                    for san in cert.subject_alternative_names:
                        if san not in [d.domain for d in result.domains]:
                            domain_obj = RelatedDomainInfo(
                                domain=san,
                                relationship_type="same_cert_email",
                                shared_attribute=email,
                                confidence=0.8,
                            )
                            result.domains.append(domain_obj)
            
            # Calculate statistics
            result.total_domains = len(result.domains)
            result.active_domains = sum(1 for d in result.domains if d.is_active)
            result.parked_domains = sum(1 for d in result.domains if d.is_parked)
            
            # Aggregate data
            for d in result.domains:
                if d.registrar and d.registrar not in result.registrars:
                    result.registrars.append(d.registrar)
                if d.registration_date and d.registration_date not in result.registration_dates:
                    result.registration_dates.append(d.registration_date)
            
            # Calculate risk
            result.total_risk_score = sum(d.risk_score for d in result.domains) // max(1, len(result.domains))
            result.high_risk_count = sum(1 for d in result.domains if d.risk_score >= 70)
            
        except Exception as e:
            logger.error(f"Email domain search failed: {e}")
        
        return result
    
    async def find_domains_by_company(
        self,
        company_name: str,
    ) -> DomainPortfolioResult:
        """
        Find all domains for a company.
        
        Args:
            company_name: Company name to search
            
        Returns:
            DomainPortfolioResult with company domains
        """
        logger.info(f"Finding domains for company {company_name}")
        
        result = DomainPortfolioResult(query=company_name, query_type="company")
        
        try:
            # Search via SecurityTrails using organization
            if self._securitytrails:
                # Search for domains with company in registrant org
                # Note: SecurityTrails doesn't directly support org search
                # This is a simplified version
                
                # Try common patterns
                company_domains = self._generate_company_domains(company_name)
                
                for domain in company_domains:
                    domain_info = await self._securitytrails.get_domain(domain)
                    
                    if domain_info and domain_info.registrant_organization:
                        # Check if company name is in organization
                        if company_name.lower() in domain_info.registrant_organization.lower():
                            domain_obj = RelatedDomainInfo(
                                domain=domain,
                                relationship_type="same_company",
                                shared_attribute=company_name,
                                confidence=1.0,
                                registration_date=domain_info.created_date,
                                registrar=domain_info.registrar,
                            )
                            result.domains.append(domain_obj)
            
            # Also search via WHOIS for same organization
            # This would require a WHOIS search by organization
            
        except Exception as e:
            logger.error(f"Company domain search failed: {e}")
        
        return result
    
    async def find_domain_variations(
        self,
        domain: str,
        check_existence: bool = True,
    ) -> DomainVariationsResult:
        """
        Generate and check domain variations.
        
        Args:
            domain: Original domain
            check_existence: Check if variations exist
            
        Returns:
            DomainVariationsResult with variations
        """
        logger.info(f"Finding variations for {domain}")
        
        result = DomainVariationsResult(original_domain=domain)
        
        try:
            # Generate variations
            variations = self._generate_variations(domain)
            
            if not check_existence:
                for var in variations:
                    result.variations.append(RelatedDomainInfo(
                        domain=var,
                        relationship_type="typosquatting_variation",
                        confidence=0.5,
                    ))
                return result
            
            # Check which variations exist
            for var in variations:
                domain_info = RelatedDomainInfo(
                    domain=var,
                    relationship_type="typosquatting_variation",
                    confidence=0.5,
                )
                
                # Check if domain exists
                if self._securitytrails:
                    st_domain = await self._securitytrails.get_domain(var)
                    
                    if st_domain:
                        domain_info.is_active = True
                        domain_info.registration_date = st_domain.created_date
                        domain_info.registrar = st_domain.registrar
                        domain_info.registrant_email = st_domain.registrant_email
                        
                        # Check for suspicious patterns
                        if self._is_suspicious(var):
                            domain_info.is_suspicious = True
                            domain_info.risk_score = 80
                
                result.variations.append(domain_info)
            
            # Check for potential takeovers
            result.takeovers = self._check_takeover_risk(variations)
            
        except Exception as e:
            logger.error(f"Variation search failed for {domain}: {e}")
        
        return result
    
    async def find_domains_by_nameserver(
        self,
        nameserver: str,
    ) -> List[RelatedDomainInfo]:
        """
        Find all domains using a specific nameserver.
        
        Args:
            nameserver: Nameserver domain
            
        Returns:
            List of RelatedDomainInfo objects
        """
        logger.info(f"Finding domains for nameserver {nameserver}")
        
        domains = []
        
        try:
            if self._securitytrails:
                domain_list = await self._securitytrails.search_domains_by_ns(nameserver)
                
                for domain in domain_list:
                    domains.append(RelatedDomainInfo(
                        domain=domain,
                        relationship_type="same_nameserver",
                        shared_attribute=nameserver,
                        confidence=0.9,
                    ))
            
        except Exception as e:
            logger.error(f"Nameserver search failed: {e}")
        
        return domains
    
    async def find_domains_by_asn(
        self,
        asn: str,
    ) -> List[RelatedDomainInfo]:
        """
        Find all domains on an ASN.
        
        Args:
            asn: ASN string (e.g., "AS15169")
            
        Returns:
            List of RelatedDomainInfo objects
        """
        logger.info(f"Finding domains for ASN {asn}")
        
        domains = []
        
        try:
            if self._censys:
                asn_decimal = 0
                if asn.startswith("AS"):
                    try:
                        asn_decimal = int(asn[2:])
                    except ValueError:
                        pass
                
                query = f"autonomous_system.asn: {asn_decimal}"
                search_result = await self._censys.search_hosts(query, per_page=100)
                
                for host in search_result.hosts:
                    for hostname in host.dns.get("reverse_dns", {}).get("names", []):
                        if hostname not in [d.domain for d in domains]:
                            domains.append(RelatedDomainInfo(
                                domain=hostname,
                                relationship_type="same_asn",
                                shared_attribute=asn,
                                confidence=0.8,
                            ))
            
        except Exception as e:
            logger.error(f"ASN search failed: {e}")
        
        return domains
    
    async def _find_by_email(
        self,
        email: str,
        exclude: Optional[List[str]] = None,
    ) -> List[RelatedDomainInfo]:
        """Find domains registered with same email."""
        domains = []
        
        if not self._securitytrails:
            return domains
        
        try:
            domain_list = await self._securitytrails.search_by_email(email)
            
            for domain in domain_list:
                if exclude and domain in exclude:
                    continue
                
                domain_info = await self._securitytrails.get_domain(domain)
                
                if domain_info:
                    domains.append(RelatedDomainInfo(
                        domain=domain,
                        relationship_type="same_registrant_email",
                        shared_attribute=email,
                        confidence=1.0,
                        registration_date=domain_info.created_date,
                        expiration_date=domain_info.expiration_date,
                        registrar=domain_info.registrar,
                    ))
                    
        except Exception as e:
            logger.warning(f"Email search failed: {e}")
        
        return domains
    
    async def _find_by_infrastructure(
        self,
        domain: str,
        ip_addresses: List[str],
    ) -> List[RelatedDomainInfo]:
        """Find domains on same IPs."""
        domains = []
        
        for ip in ip_addresses:
            # Use Censys
            if self._censys:
                ip_domains = await self._censys.search_domains_on_ip(ip)
                
                for d in ip_domains:
                    if d != domain:
                        domains.append(RelatedDomainInfo(
                            domain=d,
                            relationship_type="same_ip",
                            shared_attribute=ip,
                            confidence=0.9,
                        ))
            
            # Use Shodan
            # (would need shodan client)
        
        return domains
    
    async def _find_by_nameservers(
        self,
        domain: str,
        nameservers: List[str],
    ) -> List[RelatedDomainInfo]:
        """Find domains using same nameservers."""
        domains = []
        
        for ns in nameservers:
            ns_domains = await self.find_domains_by_nameserver(ns)
            
            for d in ns_domains:
                if d.domain != domain:
                    domains.append(d)
        
        return domains
    
    async def _find_by_certificate(
        self,
        domain: str,
    ) -> List[RelatedDomainInfo]:
        """Find domains with same certificate or issuer."""
        domains = []
        
        try:
            # Get certificate SANs
            ssl_result = await self._ssl.analyze(domain)
            
            if ssl_result.certificates:
                cert = ssl_result.certificates[0]
                
                # Search Censys by issuer
                if self._censys and cert.issuer_organization:
                    issuer_certs = await self._censys.search_by_issuer(cert.issuer_organization)
                    
                    for c in issuer_certs:
                        for san in c.subject_alternative_names:
                            if san != domain:
                                domains.append(RelatedDomainInfo(
                                    domain=san,
                                    relationship_type="same_certificate_issuer",
                                    shared_attribute=cert.issuer_organization,
                                    confidence=0.7,
                                ))
                
                # Search CT logs for same SANs
                if self._ct:
                    ct_result = await self._ct.search_certificates(domain)
                    
                    for ct_cert in ct_result.certificates:
                        for san in ct_cert.subject_alternative_names:
                            if san != domain:
                                domains.append(RelatedDomainInfo(
                                    domain=san,
                                    relationship_type="same_certificate",
                                    shared_attribute=ct_cert.fingerprint,
                                    confidence=0.9,
                                ))
                                
        except Exception as e:
            logger.warning(f"Certificate search failed: {e}")
        
        return domains
    
    def _generate_variations(self, domain: str) -> List[str]:
        """Generate domain variations for typosquatting detection."""
        import tldextract
        
        variations = set()
        
        # Extract domain parts
        extracted = tldextract.extract(domain)
        name = extracted.domain
        tld = extracted.suffix
        
        if not name:
            return []
        
        # Common typosquatting techniques
        # 1. Character omission
        for i in range(len(name)):
            variations.add(f"{name[:i]}{name[i+1:]}.{tld}")
        
        # 2. Character duplication
        for i in range(len(name)):
            variations.add(f"{name[:i]}{name[i]}{name[i:]}.{tld}")
        
        # 3. Adjacent key typos
        keyboard_adj = {
            "a": "sq", "b": "vn", "c": "xv", "d": "sf",
            "e": "wr", "f": "dg", "g": "fh", "h": "gj",
            "i": "uo", "j": "hk", "k": "jl", "l": "ko",
            "m": "n", "n": "bm", "o": "ip", "p": "ol",
            "q": "wa", "r": "et", "s": "ad", "t": "ry",
            "u": "yi", "v": "cb", "w": "qe", "x": "zc",
            "y": "tu", "z": "ax",
        }
        
        for i, char in enumerate(name):
            for adj in keyboard_adj.get(char, ""):
                variations.add(f"{name[:i]}{adj}{name[i+1:]}.{tld}")
        
        # 4. Dot insertion
        for i in range(len(name) + 1):
            variations.add(f"{name[:i]}.{name[i:]}.{tld}")
        
        # 5. Common TLD variations
        for tld in COMMON_TLDS:
            if tld != f".{extracted.suffix}":
                variations.add(f"{name}{tld}")
        
        # 6. Hyphenation
        for i in range(len(name) - 1):
            variations.add(f"{name[:i]}-{name[i+1:]}.{tld}")
        
        # Remove original
        variations.discard(domain)
        
        return list(variations)
    
    def _generate_company_domains(self, company_name: str) -> List[str]:
        """Generate possible domain names for a company."""
        # Clean company name
        name = re.sub(r'[^a-zA-Z0-9]', '', company_name).lower()
        
        domains = []
        
        # Common patterns
        patterns = [
            f"{name}.com",
            f"{name}.net",
            f"{name}.org",
            f"{name}.io",
            f"the{name}.com",
            f"{name}inc.com",
            f"{name}corp.com",
            f"{name}group.com",
            f"{name}global.com",
            f"{name}online.com",
        ]
        
        domains.extend(patterns)
        
        return domains
    
    def _is_parked(self, domain_info) -> bool:
        """Check if domain is parked."""
        # Check registrar parking
        registrar = (domain_info.registrar or "").lower()
        if "parking" in registrar or "sedo" in registrar:
            return True
        
        # Check nameservers
        nameservers = domain_info.nameservers or []
        for ns in nameservers:
            if "parking" in ns.lower() or "sedo" in ns.lower():
                return True
        
        # Check registrant info
        if not domain_info.registrant_name and not domain_info.registrant_email:
            return True
        
        return False
    
    def _is_suspicious(self, domain: str) -> bool:
        """Check if domain looks suspicious."""
        domain_lower = domain.lower()
        
        # Check for suspicious patterns
        for pattern in SUSPICIOUS_PATTERNS:
            if pattern in domain_lower:
                return True
        
        return False
    
    def _calculate_risk(self, domain_info: RelatedDomainInfo) -> int:
        """Calculate risk score for a domain."""
        score = 0
        
        # Suspicious patterns
        if domain_info.is_suspicious:
            score += 50
        
        # Parked domains have lower risk
        if domain_info.is_parked:
            score -= 20
        
        # New domains (less than 30 days) are slightly riskier
        if domain_info.registration_date:
            age = (datetime.utcnow() - domain_info.registration_date).days
            if age < 30:
                score += 10
        
        return min(100, max(0, score))
    
    def _check_takeover_risk(
        self,
        variations: List[str],
    ) -> List[Dict[str, Any]]:
        """Check for potential subdomain takeover risks."""
        takeovers = []
        
        # This would check for:
        # - CNAMEs pointing to non-existent services
        # - Unregistered subdomains with existing DNS records
        # - Abandoned cloud resources
        
        return takeovers
    
    async def close(self):
        """Close client connections."""
        await self._whois.close()
        await self._ct.close()
        if self._securitytrails:
            await self._securitytrails.close()
        if self._censys:
            await self._censys.close()
