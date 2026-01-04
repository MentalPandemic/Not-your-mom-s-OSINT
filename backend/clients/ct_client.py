"""
Certificate Transparency (CT) Log Client.

Uses crt.sh API to search for certificates and subdomains.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from urllib.parse import quote_plus

import httpx

logger = logging.getLogger(__name__)


@dataclass
class CertificateInfo:
    """Certificate information from CT logs."""
    id: str
    entry_timestamp: datetime
    not_before: datetime
    not_after: datetime
    common_name: str
    subject_alternative_names: List[str] = field(default_factory=list)
    issuer_name: str = ""
    issuer_organization: str = ""
    serial_number: str = ""
    algorithm: str = ""
    public_key_size: int = 0
    signature_algorithm: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "entry_timestamp": self.entry_timestamp.isoformat(),
            "not_before": self.not_before.isoformat(),
            "not_after": self.not_after.isoformat(),
            "common_name": self.common_name,
            "subject_alternative_names": self.subject_alternative_names,
            "issuer_name": self.issuer_name,
            "issuer_organization": self.issuer_organization,
            "serial_number": self.serial_number,
            "algorithm": self.algorithm,
            "public_key_size": self.public_key_size,
            "signature_algorithm": self.signature_algorithm,
        }


@dataclass
class CtSearchResult:
    """Result from CT log search."""
    domain: str
    certificates: List[CertificateInfo] = field(default_factory=list)
    subdomains: List[str] = field(default_factory=list)
    total_results: int = 0
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "domain": self.domain,
            "certificates": [c.to_dict() for c in self.certificates],
            "subdomains": self.subdomains,
            "total_results": self.total_results,
            "error": self.error,
        }


class CtClient:
    """
    Client for querying Certificate Transparency logs.
    
    Uses the crt.sh public API to search for certificates and extract
    subdomains from certificate SANs.
    
    API Documentation: https://crt.sh/...
    """
    
    BASE_URL = "https://crt.sh"
    DEFAULT_TIMEOUT = 30.0
    MAX_CONCURRENT_REQUESTS = 5
    RATE_LIMIT_DELAY = 1.0  # seconds between requests
    
    def __init__(
        self,
        timeout: float = DEFAULT_TIMEOUT,
        max_concurrent: int = MAX_CONCURRENT_REQUESTS,
        rate_limit_delay: float = RATE_LIMIT_DELAY,
    ):
        self.timeout = timeout
        self.max_concurrent = max_concurrent
        self.rate_limit_delay = rate_limit_delay
        self._client: Optional[httpx.Client] = None
        self._semaphore = asyncio.Semaphore(max_concurrent)
        
    @property
    def client(self) -> httpx.Client:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.Client(
                timeout=self.timeout,
                follow_redirects=True,
                headers={
                    "User-Agent": "DomainIntelligence/1.0 (OSINT Research)",
                },
            )
        return self._client
    
    async def search_certificates(
        self,
        domain: str,
        include_subdomains: bool = True,
    ) -> CtSearchResult:
        """
        Search for certificates in CT logs for a domain.
        
        Args:
            domain: Domain to search certificates for
            include_subdomains: Whether to extract subdomains from SANs
            
        Returns:
            CtSearchResult with certificates and subdomains
        """
        try:
            # Use crt.sh JSON API
            encoded_domain = quote_plus(domain)
            url = f"{self.BASE_URL}/?q={encoded_domain}&output=json"
            
            logger.info(f"Searching CT logs for {domain}")
            
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.get(url, timeout=self.timeout),
            )
            
            response.raise_for_status()
            data = response.json()
            
            certificates = []
            seen_cns = set()
            
            for entry in data:
                cert = self._parse_certificate_entry(entry)
                
                # Avoid duplicates
                if cert.common_name in seen_cns:
                    continue
                seen_cns.add(cert.common_name)
                
                certificates.append(cert)
            
            subdomains = set()
            if include_subdomains:
                for cert in certificates:
                    for san in cert.subject_alternative_names:
                        if san.endswith(domain):
                            subdomain = san.replace(f".{domain}", "").split(".")[0]
                            if subdomain and subdomain != "*":
                                subdomains.add(san)
            
            return CtSearchResult(
                domain=domain,
                certificates=certificates,
                subdomains=list(subdomains),
                total_results=len(data),
            )
            
        except httpx.HTTPStatusError as e:
            logger.error(f"CT API HTTP error: {e}")
            return CtSearchResult(domain=domain, error=f"HTTP error: {e}")
        except Exception as e:
            logger.error(f"CT log search failed: {e}")
            return CtSearchResult(domain=domain, error=str(e))
    
    async def get_certificate_details(
        self,
        cert_id: str,
    ) -> Optional[CertificateInfo]:
        """
        Get detailed information for a specific certificate.
        
        Args:
            cert_id: Certificate ID from crt.sh
            
        Returns:
            CertificateInfo or None if not found
        """
        try:
            url = f"{self.BASE_URL}/?id={cert_id}&output=json"
            
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.get(url, timeout=self.timeout),
            )
            
            response.raise_for_status()
            data = response.json()
            
            if data:
                return self._parse_certificate_entry(data[0])
            return None
            
        except Exception as e:
            logger.error(f"Failed to get certificate details: {e}")
            return None
    
    async def search_by_issuer(
        self,
        issuer: str,
        limit: int = 100,
    ) -> List[CertificateInfo]:
        """
        Search for certificates by issuer organization.
        
        Args:
            issuer: Issuer organization name
            limit: Maximum number of results
            
        Returns:
            List of CertificateInfo objects
        """
        try:
            encoded_issuer = quote_plus(f'issuer:"{issuer}"')
            url = f"{self.BASE_URL}/?q={encoded_issuer}&output=json&limit={limit}"
            
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.get(url, timeout=self.timeout),
            )
            
            response.raise_for_status()
            data = response.json()
            
            certificates = []
            for entry in data[:limit]:
                cert = self._parse_certificate_entry(entry)
                certificates.append(cert)
            
            return certificates
            
        except Exception as e:
            logger.error(f"Issuer search failed: {e}")
            return []
    
    async def search_multiple_domains(
        self,
        domains: List[str],
        include_subdomains: bool = True,
    ) -> Dict[str, CtSearchResult]:
        """
        Search for certificates for multiple domains.
        
        Args:
            domains: List of domains to search
            include_subdomains: Whether to extract subdomains
            
        Returns:
            Dictionary mapping domain to CtSearchResult
        """
        results = {}
        
        for domain in domains:
            async with self._semaphore:
                result = await self.search_certificates(domain, include_subdomains)
                results[domain] = result
                await asyncio.sleep(self.rate_limit_delay)
        
        return results
    
    def _parse_certificate_entry(self, entry: Dict[str, Any]) -> CertificateInfo:
        """Parse a certificate entry from crt.sh response."""
        # Parse common name
        common_name = entry.get("common_name", "") or ""
        
        # Parse SANs
        sans = []
        san_string = entry.get("subject_alternative_name", "")
        if san_string:
            sans = [s.strip() for s in san_string.split(",")]
        
        # Parse issuer
        issuer_name = entry.get("issuer_name", "") or ""
        issuer_org = ""
        if "O=" in issuer_name:
            issuer_org = issuer_name.split("O=")[1].split(",")[0].strip('"')
        elif "O=" in entry.get("issuer_organization", ""):
            issuer_org = entry.get("issuer_organization", "")
        
        # Parse dates
        not_before = datetime.fromisoformat(
            entry.get("not_before", "").replace("Z", "+00:00")
        )
        not_after = datetime.fromisoformat(
            entry.get("not_after", "").replace("Z", "+00:00")
        )
        
        entry_timestamp = datetime.fromisoformat(
            entry.get("entry_timestamp", "").replace("Z", "+00:00")
        )
        
        return CertificateInfo(
            id=str(entry.get("id", "")),
            entry_timestamp=entry_timestamp,
            not_before=not_before,
            not_after=not_after,
            common_name=common_name,
            subject_alternative_names=sans,
            issuer_name=issuer_name,
            issuer_organization=issuer_org,
            serial_number=entry.get("serial_number", ""),
            algorithm=entry.get("algorithm", ""),
            public_key_size=entry.get("public_key_size", 0),
            signature_algorithm=entry.get("signature_algorithm", ""),
        )
    
    async def close(self):
        """Close the HTTP client."""
        if self._client:
            self._client.close()
            self._client = None
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
