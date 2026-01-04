"""
SSL/TLS Certificate Analysis Module for domain intelligence.

Provides comprehensive SSL certificate analysis including:
- Certificate details extraction
- Subject Alternative Names (SANs) analysis
- Certificate chain validation
- Historical certificate data
- Certificate Transparency log search
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

import ssl
import socket
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa, ec, dsa, ed25519
from cryptography.x509.oid import NameOID, ExtendedKeyUsageOID

from clients.censys_client import CensysClient, CensysCertificate
from clients.ct_client import CtClient, CertificateInfo
from clients.shodan_client import ShodanClient, ShodanHost

logger = logging.getLogger(__name__)


@dataclass
class SslCertificateDetails:
    """Detailed SSL certificate information."""
    # Subject
    subject_common_name: Optional[str] = None
    subject_organization: Optional[str] = None
    subject_organizational_unit: Optional[str] = None
    subject_country: Optional[str] = None
    subject_state: Optional[str] = None
    subject_locality: Optional[str] = None
    
    # Alternative Names
    sans: List[str] = field(default_factory=list)
    dns_names: List[str] = field(default_factory=list)
    ip_addresses: List[str] = field(default_factory=list)
    email_addresses: List[str] = field(default_factory=list)
    uris: List[str] = field(default_factory=list)
    
    # Issuer
    issuer_common_name: Optional[str] = None
    issuer_organization: Optional[str] = None
    issuer_country: Optional[str] = None
    
    # Validity
    not_before: Optional[datetime] = None
    not_after: Optional[datetime] = None
    validity_days: int = 0
    validity_days_remaining: int = 0
    is_expired: bool = False
    is_not_yet_valid: bool = False
    
    # Technical Details
    signature_algorithm: Optional[str] = None
    public_key_algorithm: Optional[str] = None
    public_key_size: int = 0
    public_key_curve: Optional[str] = None
    serial_number: Optional[str] = None
    version: int = 0
    
    # Fingerprints
    fingerprint_sha256: Optional[str] = None
    fingerprint_sha1: Optional[str] = None
    fingerprint_md5: Optional[str] = None
    
    # Extensions
    key_usage: Dict[str, bool] = field(default_factory=dict)
    extended_key_usage: List[str] = field(default_factory=list)
    basic_constraints: Dict[str, Any] = field(default_factory=dict)
    authority_info_access: Dict[str, str] = field(default_factory=dict)
    certificate_policies: List[str] = field(default_factory=list)
    crl_distribution_points: List[str] = field(default_factory=list)
    
    # Transparency
    ct_log_entries: List[Dict[str, Any]] = field(default_factory=list)
    is_sct_verified: bool = False
    
    # Raw
    raw_pem: Optional[str] = None
    pem: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "subject": {
                "common_name": self.subject_common_name,
                "organization": self.subject_organization,
                "organizational_unit": self.subject_organizational_unit,
                "country": self.subject_country,
                "state": self.subject_state,
                "locality": self.subject_locality,
            },
            "alternative_names": {
                "sans": self.sans,
                "dns_names": self.dns_names,
                "ip_addresses": self.ip_addresses,
                "email_addresses": self.email_addresses,
                "uris": self.uris,
            },
            "issuer": {
                "common_name": self.issuer_common_name,
                "organization": self.issuer_organization,
                "country": self.issuer_country,
            },
            "validity": {
                "not_before": self.not_before.isoformat() if self.not_before else None,
                "not_after": self.not_after.isoformat() if self.not_after else None,
                "validity_days": self.validity_days,
                "validity_days_remaining": self.validity_days_remaining,
                "is_expired": self.is_expired,
                "is_not_yet_valid": self.is_not_yet_valid,
            },
            "technical": {
                "signature_algorithm": self.signature_algorithm,
                "public_key_algorithm": self.public_key_algorithm,
                "public_key_size": self.public_key_size,
                "public_key_curve": self.public_key_curve,
                "serial_number": self.serial_number,
                "version": self.version,
            },
            "fingerprints": {
                "sha256": self.fingerprint_sha256,
                "sha1": self.fingerprint_sha1,
                "md5": self.fingerprint_md5,
            },
            "extensions": {
                "key_usage": self.key_usage,
                "extended_key_usage": self.extended_key_usage,
                "basic_constraints": self.basic_constraints,
                "authority_info_access": self.authority_info_access,
                "certificate_policies": self.certificate_policies,
                "crl_distribution_points": self.crl_distribution_points,
            },
            "transparency": {
                "ct_log_entries": self.ct_log_entries,
                "is_sct_verified": self.is_sct_verified,
            },
            "raw_pem": self.raw_pem,
        }


@dataclass
class CertificateChain:
    """SSL certificate chain."""
    certificate: SslCertificateDetails
    issuer: Optional[SslCertificateDetails] = None
    root: Optional[SslCertificateDetails] = None
    is_valid: bool = False
    validation_error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "certificate": self.certificate.to_dict(),
            "issuer": self.issuer.to_dict() if self.issuer else None,
            "root": self.root.to_dict() if self.root else None,
            "is_valid": self.is_valid,
            "validation_error": self.validation_error,
        }


@dataclass
class SslAnalysisResult:
    """Complete SSL analysis result for a domain."""
    domain: str
    ip_address: Optional[str] = None
    port: int = 443
    
    # Certificates
    certificates: List[SslCertificateDetails] = field(default_factory=list)
    certificate_chain: Optional[CertificateChain] = None
    
    # Analysis
    is_valid: bool = False
    is_trusted: bool = False
    is_self_signed: bool = False
    is_expired: bool = False
    
    # Vulnerabilities
    vulnerabilities: List[Dict[str, Any]] = field(default_factory=list)
    
    # Related domains
    related_domains: List[str] = field(default_factory=list)
    
    # Metadata
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "domain": self.domain,
            "ip_address": self.ip_address,
            "port": self.port,
            "certificates": [c.to_dict() for c in self.certificates],
            "certificate_chain": self.certificate_chain.to_dict() if self.certificate_chain else None,
            "is_valid": self.is_valid,
            "is_trusted": self.is_trusted,
            "is_self_signed": self.is_self_signed,
            "is_expired": self.is_expired,
            "vulnerabilities": self.vulnerabilities,
            "related_domains": self.related_domains,
            "error": self.error,
        }


@dataclass
class SslHistoryResult:
    """Historical SSL certificate data."""
    domain: str
    certificates: List[Dict[str, Any]] = field(default_factory=list)
    ip_history: List[Dict[str, Any]] = field(default_factory=list)
    related_domains: List[str] = field(default_factory=list)
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "domain": self.domain,
            "certificates": self.certificates,
            "ip_history": self.ip_history,
            "related_domains": self.related_domains,
            "error": self.error,
        }


class SslAnalysis:
    """
    SSL/TLS certificate analysis module.
    
    Provides:
    - Certificate details extraction
    - SANs analysis
    - Certificate chain validation
    - Historical certificate data
    - Vulnerability detection
    - Related domain discovery via CT logs
    """
    
    DEFAULT_TIMEOUT = 10.0
    
    # Weak signature algorithms
    WEAK_ALGORITHMS = [
        "md5",
        "sha1",
        "mdc2",
        "md4",
    ]
    
    # Weak key sizes
    WEAK_KEY_SIZES = {
        "RSA": 2048,  # Minimum acceptable
        "DSA": 2048,
        "EC": 224,  # Minimum acceptable
    }
    
    # Expired certificate thresholds
    EXPIRED_WARNING_DAYS = 30
    EXPIRED_CRITICAL_DAYS = 0
    
    def __init__(
        self,
        censys_api_id: Optional[str] = None,
        censys_api_secret: Optional[str] = None,
        shodan_api_key: Optional[str] = None,
        timeout: float = DEFAULT_TIMEOUT,
    ):
        """
        Initialize SSL analysis module.
        
        Args:
            censys_api_id: Censys API ID
            censys_api_secret: Censys API secret
            shodan_api_key: Shodan API key
            timeout: Connection timeout
        """
        self.timeout = timeout
        self._censys: Optional[CensysClient] = None
        self._shodan: Optional[ShodanClient] = None
        
        if censys_api_id and censys_api_secret:
            self._censys = CensysClient(censys_api_id, censys_api_secret)
        if shodan_api_key:
            self._shodan = ShodanClient(shodan_api_key)
    
    async def analyze(
        self,
        domain: str,
        port: int = 443,
        include_chain: bool = True,
    ) -> SslAnalysisResult:
        """
        Analyze SSL certificate for a domain.
        
        Args:
            domain: Domain to analyze
            port: SSL port
            include_chain: Include certificate chain
            
        Returns:
            SslAnalysisResult with certificate analysis
        """
        logger.info(f"Analyzing SSL certificate for {domain}:{port}")
        
        result = SslAnalysisResult(domain=domain, port=port)
        
        try:
            # Get certificate from socket
            cert_details = await self._fetch_certificate(domain, port)
            
            if not cert_details:
                result.error = "Failed to fetch certificate"
                return result
            
            result.certificates = [cert_details]
            
            # Check if certificate is valid
            result.is_valid = self._validate_certificate(cert_details)
            result.is_expired = cert_details.is_expired
            result.is_self_signed = self._is_self_signed(cert_details)
            
            # Get certificate chain if requested
            if include_chain:
                result.certificate_chain = await self._get_certificate_chain(domain, port)
                result.is_trusted = result.certificate_chain.is_valid if result.certificate_chain else False
            
            # Analyze for vulnerabilities
            result.vulnerabilities = self._analyze_vulnerabilities(cert_details)
            
            # Find related domains via SANs
            result.related_domains = cert_details.dns_names.copy()
            
            # Get related domains from CT logs
            ct_related = await self._find_related_domains(domain)
            result.related_domains.extend(ct_related)
            result.related_domains = list(set(result.related_domains))
            
        except Exception as e:
            logger.error(f"SSL analysis failed for {domain}: {e}")
            result.error = str(e)
        
        return result
    
    async def analyze_ip(
        self,
        ip_address: str,
        port: int = 443,
    ) -> SslAnalysisResult:
        """
        Analyze SSL certificate for an IP address.
        
        Args:
            ip_address: IP address to analyze
            port: SSL port
            
        Returns:
            SslAnalysisResult with certificate analysis
        """
        logger.info(f"Analyzing SSL certificate for {ip_address}:{port}")
        
        result = SslAnalysisResult(domain=ip_address, ip_address=ip_address, port=port)
        
        try:
            # Get certificate from socket
            cert_details = await self._fetch_certificate(ip_address, port, is_ip=True)
            
            if not cert_details:
                result.error = "Failed to fetch certificate"
                return result
            
            result.certificates = [cert_details]
            result.is_valid = self._validate_certificate(cert_details)
            
        except Exception as e:
            logger.error(f"SSL analysis failed for {ip_address}: {e}")
            result.error = str(e)
        
        return result
    
    async def get_certificate_chain(
        self,
        domain: str,
        port: int = 443,
    ) -> Optional[CertificateChain]:
        """
        Get the full certificate chain.
        
        Args:
            domain: Domain name
            port: SSL port
            
        Returns:
            CertificateChain or None
        """
        try:
            # Get leaf certificate
            leaf = await self._fetch_certificate(domain, port)
            
            if not leaf:
                return None
            
            chain = CertificateChain(certificate=leaf)
            
            # Create SSL context to get chain
            import ssl
            
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            
            with socket.create_connection((domain, port), timeout=self.timeout) as sock:
                with context.wrap_socket(sock, server_hostname=domain) as ssock:
                    cert_chain = ssock.getpeercert_chain()
            
            # Parse chain certificates
            if len(cert_chain) > 1:
                # First is leaf (we already have it)
                # Parse intermediate
                for cert_der in cert_chain[1:]:
                    cert = self._parse_certificate_der(cert_der)
                    if cert:
                        if not chain.issuer:
                            chain.issuer = cert
                        elif not chain.root:
                            chain.root = cert
            
            chain.is_valid = True
            
            return chain
            
        except Exception as e:
            logger.error(f"Failed to get certificate chain: {e}")
            return None
    
    async def search_by_issuer(
        self,
        issuer: str,
        limit: int = 100,
    ) -> List[SslCertificateDetails]:
        """
        Search for certificates by issuer.
        
        Args:
            issuer: Issuer organization name
            limit: Maximum results
            
        Returns:
            List of certificate details
        """
        if not self._censys:
            logger.warning("Censys not configured, cannot search by issuer")
            return []
        
        try:
            certs = await self._censys.search_by_issuer(issuer, limit)
            
            results = []
            for censys_cert in certs:
                details = self._parse_censys_certificate(censys_cert)
                results.append(details)
            
            return results
            
        except Exception as e:
            logger.error(f"Issuer search failed: {e}")
            return []
    
    async def search_by_common_name(
        self,
        common_name: str,
        limit: int = 100,
    ) -> List[SslCertificateDetails]:
        """
        Search for certificates by common name.
        
        Args:
            common_name: Certificate common name
            limit: Maximum results
            
        Returns:
            List of certificate details
        """
        if not self._censys:
            logger.warning("Censys not configured, cannot search by common name")
            return []
        
        try:
            certs = await self._censys.search_by_common_name(common_name, limit)
            
            results = []
            for censys_cert in certs:
                details = self._parse_censys_certificate(censys_cert)
                results.append(details)
            
            return results
            
        except Exception as e:
            logger.error(f"Common name search failed: {e}")
            return []
    
    async def get_historical_certificates(
        self,
        domain: str,
    ) -> SslHistoryResult:
        """
        Get historical certificates for a domain.
        
        Args:
            domain: Domain name
            
        Returns:
            SslHistoryResult with historical data
        """
        logger.info(f"Getting historical certificates for {domain}")
        
        result = SslHistoryResult(domain=domain)
        
        if not self._censys:
            result.error = "Censys not configured"
            return result
        
        try:
            # Search for all certificates matching domain
            query = f'names: "{domain}"'
            search_result = await self._censys.search_certificates(query, per_page=100)
            
            for cert in search_result.certificates:
                result.certificates.append({
                    "fingerprint": cert.fingerprint,
                    "common_name": cert.common_name,
                    "sans": cert.subject_alternative_names,
                    "issuer": cert.issuer.get("organization"),
                    "not_before": cert.validity.get("not_before").isoformat() if cert.validity.get("not_before") else None,
                    "not_after": cert.validity.get("not_after").isoformat() if cert.validity.get("not_after") else None,
                })
            
            # Get related domains
            result.related_domains = list(set(
                san.split(".")[0] for cert in search_result.certificates
                for san in cert.subject_alternative_names
                if san.endswith(domain)
            ))
            
        except Exception as e:
            logger.error(f"Historical certificate search failed: {e}")
            result.error = str(e)
        
        return result
    
    async def find_domains_on_same_ip(
        self,
        ip_address: str,
        port: int = 443,
    ) -> List[str]:
        """
        Find all domains on the same IP (virtual hosting).
        
        Args:
            ip_address: IP address
            port: SSL port
            
        Returns:
            List of domain names
        """
        # Get certificate SANs
        result = await self.analyze_ip(ip_address, port)
        
        if result.certificates:
            return result.certificates[0].dns_names
        
        return []
    
    async def _fetch_certificate(
        self,
        host: str,
        port: int,
        is_ip: bool = False,
    ) -> Optional[SslCertificateDetails]:
        """Fetch and parse SSL certificate from host."""
        
        def _fetch():
            import ssl
            
            context = ssl.create_default_context()
            
            if is_ip:
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
            
            with socket.create_connection((host, port), timeout=self.timeout) as sock:
                with context.wrap_socket(sock, server_hostname=host if not is_ip else None) as ssock:
                    cert_der = ssock.getpeercert(binary_form=True)
                    chain = ssock.getpeercert_chain()
                    
                    return cert_der, chain
        
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, _fetch)
        
        if result:
            cert_der, chain = result
            return self._parse_certificate_der(cert_der)
        
        return None
    
    def _parse_certificate_der(self, cert_der: bytes) -> Optional[SslCertificateDetails]:
        """Parse DER-encoded certificate."""
        try:
            cert = x509.load_der_x509_certificate(cert_der, default_backend())
            return self._parse_x509_certificate(cert)
        except Exception as e:
            logger.error(f"Failed to parse certificate: {e}")
            return None
    
    def _parse_x509_certificate(self, cert: x509.Certificate) -> SslCertificateDetails:
        """Parse x509 Certificate object."""
        details = SslCertificateDetails()
        
        # Subject
        subject = cert.subject
        for attr in subject:
            if attr.oid == NameOID.COMMON_NAME:
                details.subject_common_name = attr.value
            elif attr.oid == NameOID.ORGANIZATION_NAME:
                details.subject_organization = attr.value
            elif attr.oid == NameOID.ORGANIZATIONAL_UNIT_NAME:
                details.subject_organizational_unit = attr.value
            elif attr.oid == NameOID.COUNTRY_NAME:
                details.subject_country = attr.value
            elif attr.oid == NameOID.STATE_OR_PROVINCE_NAME:
                details.subject_state = attr.value
            elif attr.oid == NameOID.LOCALITY_NAME:
                details.subject_locality = attr.value
        
        # Issuer
        issuer = cert.issuer
        for attr in issuer:
            if attr.oid == NameOID.COMMON_NAME:
                details.issuer_common_name = attr.value
            elif attr.oid == NameOID.ORGANIZATION_NAME:
                details.issuer_organization = attr.value
            elif attr.oid == NameOID.COUNTRY_NAME:
                details.issuer_country = attr.value
        
        # Validity
        details.not_before = cert.not_valid_before_utc
        details.not_after = cert.not_valid_after_utc
        now = datetime.utcnow()
        details.validity_days = (details.not_after - details.not_before).days
        details.validity_days_remaining = (details.not_after - now).days
        details.is_expired = now > details.not_after
        details.is_not_yet_valid = now < details.not_before
        
        # Signature algorithm
        details.signature_algorithm = cert.signature_algorithm_oid._name
        
        # Public key
        public_key = cert.public_key()
        if isinstance(public_key, rsa.RSAPublicKey):
            details.public_key_algorithm = "RSA"
            details.public_key_size = public_key.key_size
        elif isinstance(public_key, ec.EllipticCurvePublicKey):
            details.public_key_algorithm = "EC"
            details.public_key_curve = public_key.curve.name
        elif isinstance(public_key, dsa.DSAPublicKey):
            details.public_key_algorithm = "DSA"
            details.public_key_size = public_key.key_size
        elif isinstance(public_key, ed25519.Ed25519PublicKey):
            details.public_key_algorithm = "Ed25519"
        
        # Serial number
        details.serial_number = format(cert.serial_number, "x")
        
        # Version
        details.version = cert.version
        
        # Extensions
        try:
            san_ext = cert.extensions.get_extension_for_class(x509.SubjectAlternativeName)
            details.sans = san_ext.value.get_values_for_type(x509.DNSName)
            details.dns_names = san_ext.value.get_values_for_type(x509.DNSName)
            details.ip_addresses = [str(ip) for ip in san_ext.value.get_values_for_type(x509.IPAddress)]
            details.email_addresses = san_ext.value.get_values_for_type(x509.RFC822Name)
            details.uris = san_ext.value.get_values_for_type(x509.UniformResourceIdentifier)
        except x509.ExtensionNotFound:
            pass
        
        try:
            key_usage = cert.extensions.get_extension_for_class(x509.KeyUsage)
            details.key_usage = {
                "digital_signature": key_usage.value.digital_signature,
                "content_commitment": key_usage.value.content_commitment,
                "key_encipherment": key_usage.value.key_encipherment,
                "data_encipherment": key_usage.value.data_encipherment,
                "key_agreement": key_usage.value.key_agreement,
                "key_cert_sign": key_usage.value.key_cert_sign,
                "crl_sign": key_usage.value.crl_sign,
                "encipher_only": key_usage.value.encipher_only,
                "decipher_only": key_usage.value.decipher_only,
            }
        except x509.ExtensionNotFound:
            pass
        
        try:
            ext_key_usage = cert.extensions.get_extension_for_class(x509.ExtendedKeyUsage)
            details.extended_key_usage = [
                oid._name for oid in ext_key_usage.value
            ]
        except x509.ExtensionNotFound:
            pass
        
        try:
            basic_constraints = cert.extensions.get_extension_for_class(x509.BasicConstraints)
            details.basic_constraints = {
                "is_ca": basic_constraints.value.ca,
                "path_length": basic_constraints.value.path_length,
            }
        except x509.ExtensionNotFound:
            pass
        
        # Fingerprints
        details.fingerprint_sha256 = cert.fingerprint(hashes.SHA256()).hex()
        details.fingerprint_sha1 = cert.fingerprint(hashes.SHA1()).hex()
        details.fingerprint_md5 = cert.fingerprint(hashes.MD5()).hex()
        
        return details
    
    def _parse_censys_certificate(self, cert) -> SslCertificateDetails:
        """Parse Censys certificate data."""
        details = SslCertificateDetails()
        
        details.subject_common_name = cert.common_name
        details.sans = cert.subject_alternative_names
        details.dns_names = cert.subject_alternative_names
        
        validity = cert.validity
        if validity:
            details.not_before = validity.get("not_before")
            details.not_after = validity.get("not_after")
            if details.not_after:
                now = datetime.utcnow()
                details.validity_days_remaining = (details.not_after - now).days
                details.is_expired = now > details.not_after
        
        issuer = cert.issuer
        if issuer:
            details.issuer_organization = issuer.get("organization")
            details.issuer_common_name = issuer.get("common_name")
        
        public_key = cert.public_key
        if public_key:
            details.public_key_algorithm = public_key.get("algorithm")
            details.public_key_size = public_key.get("key_size")
        
        details.signature_algorithm = cert.signature_algorithm
        details.fingerprint_sha256 = cert.fingerprint
        
        return details
    
    def _validate_certificate(self, cert: SslCertificateDetails) -> bool:
        """Validate certificate is not expired and properly signed."""
        if cert.is_expired:
            return False
        if cert.is_not_yet_valid:
            return False
        return True
    
    def _is_self_signed(self, cert: SslCertificateDetails) -> bool:
        """Check if certificate is self-signed."""
        if cert.issuer_common_name == cert.subject_common_name:
            if cert.issuer_organization == cert.issuer_organization:
                return True
        return False
    
    def _analyze_vulnerabilities(
        self,
        cert: SslCertificateDetails,
    ) -> List[Dict[str, Any]]:
        """Analyze certificate for vulnerabilities."""
        vulnerabilities = []
        
        # Check for expired certificate
        if cert.is_expired:
            vulnerabilities.append({
                "type": "expired_certificate",
                "severity": "critical",
                "description": "Certificate has expired",
                "not_after": cert.not_after.isoformat() if cert.not_after else None,
            })
        
        # Check for expiring soon
        if cert.validity_days_remaining < self.EXPIRED_WARNING_DAYS and not cert.is_expired:
            vulnerabilities.append({
                "type": "expiring_certificate",
                "severity": "warning",
                "description": f"Certificate expires in {cert.validity_days_remaining} days",
                "not_after": cert.not_after.isoformat() if cert.not_after else None,
            })
        
        # Check for weak signature algorithm
        if cert.signature_algorithm:
            algorithm = cert.signature_algorithm.lower()
            for weak in self.WEAK_ALGORITHMS:
                if weak in algorithm:
                    vulnerabilities.append({
                        "type": "weak_signature_algorithm",
                        "severity": "high",
                        "description": f"Certificate uses weak signature algorithm: {cert.signature_algorithm}",
                    })
                    break
        
        # Check for weak key size
        if cert.public_key_algorithm == "RSA" and cert.public_key_size < self.WEAK_KEY_SIZES["RSA"]:
            vulnerabilities.append({
                "type": "weak_key_size",
                "severity": "high",
                "description": f"RSA key size {cert.public_key_size} is below minimum {self.WEAK_KEY_SIZES['RSA']}",
            })
        elif cert.public_key_algorithm == "EC" and cert.public_key_curve:
            if cert.public_key_curve == "secp160k1" or "160" in cert.public_key_curve:
                vulnerabilities.append({
                    "type": "weak_ec_curve",
                    "severity": "high",
                    "description": f"EC curve {cert.public_key_curve} may be weak",
                })
        
        # Check for self-signed certificate
        if self._is_self_signed(cert):
            vulnerabilities.append({
                "type": "self_signed_certificate",
                "severity": "medium",
                "description": "Certificate is self-signed",
            })
        
        # Check for missing SANs
        if not cert.sans:
            vulnerabilities.append({
                "type": "missing_sans",
                "severity": "low",
                "description": "Certificate has no Subject Alternative Names",
            })
        
        return vulnerabilities
    
    async def _find_related_domains(self, domain: str) -> List[str]:
        """Find related domains via CT logs."""
        try:
            from clients.ct_client import CtClient
            
            async with CtClient() as ct_client:
                result = await ct_client.search_certificates(domain)
                
                if result.certificates:
                    related = set()
                    for cert in result.certificates:
                        for san in cert.subject_alternative_names:
                            if san != domain and san.endswith(domain):
                                related.add(san)
                            elif san.endswith(domain):
                                related.add(san)
                    
                    return list(related)
                    
        except Exception as e:
            logger.debug(f"Failed to find related domains: {e}")
        
        return []
    
    async def close(self):
        """Close client connections."""
        if self._censys:
            await self._censys.close()
        if self._shodan:
            await self._shodan.close()
