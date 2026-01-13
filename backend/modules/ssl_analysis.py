"""
SSL/TLS Certificate Analysis Module

This module provides comprehensive SSL/TLS certificate analysis including certificate details,
certificate chain analysis, certificate transparency logs, and historical certificate data.
"""

import asyncio
import ssl
import socket
import json
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple, Any
from urllib.parse import urlparse
import aiohttp
import OpenSSL
import logging

logger = logging.getLogger(__name__)


class SSLCertificateError(Exception):
    """Custom exception for SSL certificate analysis failures."""
    pass


class CertificateInfo:
    """SSL certificate information container."""
    
    def __init__(self):
        self.subject: Optional[str] = None
        self.common_name: Optional[str] = None
        self.organization: Optional[str] = None
        self.subject_alt_names: List[str] = []
        self.issuer: Optional[str] = None
        self.issuer_organization: Optional[str] = None
        self.serial_number: Optional[str] = None
        self.fingerprint_sha1: Optional[str] = None
        self.fingerprint_sha256: Optional[str] = None
        self.valid_from: Optional[datetime] = None
        self.valid_to: Optional[datetime] = None
        self.is_valid: bool = False
        self.days_until_expiry: Optional[int] = None
        self.version: Optional[int] = None
        self.signature_algorithm: Optional[str] = None
        self.key_size: Optional[int] = None
        self.is_ca: bool = False
        self.is_self_signed: bool = False
        self.certificate_chain: List[str] = []
        self.ct_log_entries: List[Dict] = []
        
    def to_dict(self) -> Dict:
        """Convert to dictionary format."""
        return {
            'subject': self.subject,
            'common_name': self.common_name,
            'organization': self.organization,
            'subject_alt_names': self.subject_alt_names,
            'issuer': self.issuer,
            'issuer_organization': self.issuer_organization,
            'serial_number': self.serial_number,
            'fingerprint_sha1': self.fingerprint_sha1,
            'fingerprint_sha256': self.fingerprint_sha256,
            'valid_from': self.valid_from.isoformat() if self.valid_from else None,
            'valid_to': self.valid_to.isoformat() if self.valid_to else None,
            'is_valid': self.is_valid,
            'days_until_expiry': self.days_until_expiry,
            'version': self.version,
            'signature_algorithm': self.signature_algorithm,
            'key_size': self.key_size,
            'is_ca': self.is_ca,
            'is_self_signed': self.is_self_signed,
            'certificate_chain': self.certificate_chain,
            'ct_log_entries': self.ct_log_entries
        }


class CTLogEntry:
    """Certificate Transparency log entry."""
    
    def __init__(self):
        self.log_name: Optional[str] = None
        self.timestamp: Optional[datetime] = None
        self.log_index: Optional[int] = None
        self.leaf_hash: Optional[str] = None
        self.domain: Optional[str] = None
        self.issuer: Optional[str] = None
        
    def to_dict(self) -> Dict:
        """Convert to dictionary format."""
        return {
            'log_name': self.log_name,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'log_index': self.log_index,
            'leaf_hash': self.leaf_hash,
            'domain': self.domain,
            'issuer': self.issuer
        }


class SSLAnalyzer:
    """Main SSL/TLS certificate analysis service."""
    
    def __init__(self):
        # Certificate Transparency APIs
        self.ct_log_apis = [
            "https://crt.sh/?q=%.{domain}&output=json",
            "https://certspotter.com/api/v1/issuances?domain={domain}&include_subdomains=true&match_wildcards=false&expired=true&include_expired=true",
            "https://api.certdb.com/v1/certificates/search?domain={domain}"
        ]
        
        # Certificate validation timeouts
        self.timeout = 10
        
    def normalize_domain(self, domain: str) -> str:
        """Normalize domain name."""
        if not domain:
            return domain
            
        # Remove protocol and path if present
        if '://' in domain:
            domain = urlparse(domain).netloc
            
        # Remove www prefix
        domain = domain.lower().strip()
        if domain.startswith('www.'):
            domain = domain[4:]
            
        return domain
    
    async def get_certificate(self, host: str, port: int = 443) -> Optional[CertificateInfo]:
        """Get SSL certificate from a host."""
        try:
            # Create SSL context
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            
            # Connect and get certificate
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(host, port),
                timeout=self.timeout
            )
            
            # Perform SSL handshake
            ssl_object = context.wrap_socket(
                reader, 
                do_handshake_on_connect=True,
                server_hostname=host if port == 443 else None
            )
            
            # Get certificate
            cert_der = ssl_object.getpeercert(binary_form=True)
            
            # Close connection
            writer.close()
            await writer.wait_closed()
            
            if cert_der:
                return self.parse_certificate(cert_der, host)
            
        except asyncio.TimeoutError:
            logger.error(f"Timeout connecting to {host}:{port}")
        except Exception as e:
            logger.error(f"Error getting certificate from {host}:{port}: {str(e)}")
        
        return None
    
    def parse_certificate(self, cert_der: bytes, host: str) -> CertificateInfo:
        """Parse SSL certificate from DER format."""
        try:
            # Convert DER to X509 certificate
            cert = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_ASN1, cert_der)
            
            cert_info = CertificateInfo()
            
            # Extract subject information
            subject = cert.get_subject()
            cert_info.subject = str(subject)
            cert_info.common_name = subject.CN if hasattr(subject, 'CN') else None
            cert_info.organization = subject.O if hasattr(subject, 'O') else None
            
            # Extract issuer information
            issuer = cert.get_issuer()
            cert_info.issuer = str(issuer)
            cert_info.issuer_organization = issuer.O if hasattr(issuer, 'O') else None
            
            # Extract subject alternative names
            try:
                san_ext = cert.get_extension(8)  # 8 is the OID for SAN
                if san_ext.get_data():
                    # Parse SAN extension
                    san_data = san_ext.get_data()
                    # This is a simplified parsing - in practice you'd need more robust parsing
                    cert_info.subject_alt_names = self.parse_san_extension(san_data)
            except:
                pass
            
            # Extract validity dates
            not_before = cert.get_notBefore()
            not_after = cert.get_notAfter()
            
            if not_before:
                cert_info.valid_from = datetime.strptime(not_before.decode(), '%Y%m%d%H%M%SZ')
            if not_after:
                cert_info.valid_to = datetime.strptime(not_after.decode(), '%Y%m%d%H%M%SZ')
            
            # Check if certificate is currently valid
            now = datetime.utcnow()
            cert_info.is_valid = (
                cert_info.valid_from and 
                cert_info.valid_to and 
                cert_info.valid_from <= now <= cert_info.valid_to
            )
            
            # Calculate days until expiry
            if cert_info.valid_to:
                cert_info.days_until_expiry = (cert_info.valid_to - now).days
            
            # Extract other certificate details
            cert_info.serial_number = cert.get_serial_number()
            cert_info.version = cert.get_version()
            cert_info.signature_algorithm = cert.get_signature_algorithm().decode()
            
            # Extract fingerprints
            cert_info.fingerprint_sha1 = cert.digest('sha1').decode()
            cert_info.fingerprint_sha256 = cert.digest('sha256').decode()
            
            # Extract public key information
            try:
                public_key = cert.get_pubkey()
                if public_key:
                    cert_info.key_size = public_key.bits()
            except:
                pass
            
            # Check if it's a CA certificate
            try:
                basic_constraints = cert.get_extension(0)  # 0 is the OID for Basic Constraints
                cert_info.is_ca = basic_constraints.get_critical()
            except:
                cert_info.is_ca = False
            
            # Check if it's self-signed
            cert_info.is_self_signed = (cert_info.subject == cert_info.issuer)
            
            return cert_info
            
        except Exception as e:
            logger.error(f"Error parsing certificate: {str(e)}")
            raise SSLCertificateError(f"Failed to parse certificate: {str(e)}")
    
    def parse_san_extension(self, san_data: bytes) -> List[str]:
        """Parse Subject Alternative Name extension data."""
        san_names = []
        
        try:
            # Simplified SAN parsing - in practice this would be more complex
            # This is a basic implementation that looks for common patterns
            
            # Look for DNS names in the SAN data
            dns_pattern = rb'\x82\x04([^\x00]+)'
            matches = re.findall(dns_pattern, san_data)
            
            for match in matches:
                try:
                    # Decode the DNS name
                    dns_name = match.decode('utf-8', errors='ignore')
                    san_names.append(dns_name)
                except:
                    continue
            
            # Also look for IP addresses
            ip_pattern = rb'\x87\x04([^\x00]+)'
            ip_matches = re.findall(ip_pattern, san_data)
            
            for match in ip_matches:
                try:
                    # Decode the IP address
                    ip_addr = '.'.join(str(b) for b in match)
                    san_names.append(ip_addr)
                except:
                    continue
        
        except Exception as e:
            logger.debug(f"Error parsing SAN extension: {str(e)}")
        
        return san_names
    
    async def get_certificate_chain(self, host: str, port: int = 443) -> List[CertificateInfo]:
        """Get the full certificate chain."""
        certificates = []
        
        try:
            # Get the leaf certificate
            leaf_cert = await self.get_certificate(host, port)
            if leaf_cert:
                certificates.append(leaf_cert)
                
                # Note: Getting the full certificate chain would require more complex SSL handling
                # This is a simplified implementation that focuses on the leaf certificate
                # In practice, you'd want to get the intermediate certificates as well
                
        except Exception as e:
            logger.error(f"Error getting certificate chain for {host}:{port}: {str(e)}")
        
        return certificates
    
    async def search_certificate_transparency(self, domain: str) -> List[CTLogEntry]:
        """Search certificate transparency logs for domain."""
        domain = self.normalize_domain(domain)
        ct_entries = []
        
        try:
            # Use crt.sh API
            url = f"https://crt.sh/?q=%.{domain}&output=json"
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        for entry in data:
                            ct_entry = CTLogEntry()
                            
                            # Extract information from CT log entry
                            ct_entry.domain = entry.get('name_value', '').split('\n')[0] if entry.get('name_value') else None
                            ct_entry.issuer = entry.get('issuer_ca_id', '')
                            ct_entry.timestamp = None  # crt.sh doesn't provide timestamp in this format
                            
                            if ct_entry.domain:
                                ct_entries.append(ct_entry)
                    
                    else:
                        logger.warning(f"Certificate transparency search failed with status {response.status}")
        
        except Exception as e:
            logger.error(f"Error searching certificate transparency logs: {str(e)}")
        
        return ct_entries
    
    async def analyze_certificate_security(self, cert_info: CertificateInfo) -> Dict:
        """Analyze certificate security properties."""
        analysis = {
            'security_score': 0,
            'issues': [],
            'recommendations': [],
            'strengths': []
        }
        
        # Check certificate validity
        if not cert_info.is_valid:
            analysis['issues'].append('certificate_not_valid')
            analysis['recommendations'].append('Use a valid SSL certificate')
        else:
            analysis['security_score'] += 20
            analysis['strengths'].append('certificate_is_valid')
        
        # Check expiration
        if cert_info.days_until_expiry is not None:
            if cert_info.days_until_expiry < 0:
                analysis['issues'].append('certificate_expired')
                analysis['recommendations'].append('Renew expired certificate immediately')
            elif cert_info.days_until_expiry < 30:
                analysis['issues'].append('certificate_expires_soon')
                analysis['recommendations'].append('Renew certificate before it expires')
            elif cert_info.days_until_expiry > 365:
                analysis['strengths'].append('long_validity_period')
                analysis['security_score'] += 10
            else:
                analysis['security_score'] += 15
        
        # Check key size
        if cert_info.key_size:
            if cert_info.key_size >= 2048:
                analysis['security_score'] += 20
                analysis['strengths'].append('strong_key_size')
            elif cert_info.key_size >= 1024:
                analysis['issues'].append('weak_key_size')
                analysis['recommendations'].append('Upgrade to 2048-bit or stronger key')
            else:
                analysis['issues'].append('very_weak_key_size')
                analysis['recommendations'].append('Use at least 2048-bit key')
        
        # Check for self-signed certificates
        if cert_info.is_self_signed:
            analysis['issues'].append('self_signed_certificate')
            analysis['recommendations'].append('Use a certificate from a trusted CA')
        else:
            analysis['security_score'] += 15
        
        # Check signature algorithm
        if cert_info.signature_algorithm:
            if 'sha256' in cert_info.signature_algorithm.lower() or 'sha384' in cert_info.signature_algorithm.lower():
                analysis['security_score'] += 10
                analysis['strengths'].append('strong_signature_algorithm')
            elif 'sha1' in cert_info.signature_algorithm.lower():
                analysis['issues'].append('weak_signature_algorithm')
                analysis['recommendations'].append('Upgrade to SHA-256 or stronger signature algorithm')
            elif 'md5' in cert_info.signature_algorithm.lower():
                analysis['issues'].append('very_weak_signature_algorithm')
                analysis['recommendations'].append('Use SHA-256 or stronger signature algorithm')
        
        # Check for Subject Alternative Names
        if cert_info.subject_alt_names:
            analysis['strengths'].append('has_san_extension')
            analysis['security_score'] += 5
        
        # Calculate overall security rating
        if analysis['security_score'] >= 80:
            analysis['security_rating'] = 'Excellent'
        elif analysis['security_score'] >= 60:
            analysis['security_rating'] = 'Good'
        elif analysis['security_score'] >= 40:
            analysis['security_rating'] = 'Fair'
        elif analysis['security_score'] >= 20:
            analysis['security_rating'] = 'Poor'
        else:
            analysis['security_rating'] = 'Very Poor'
        
        return analysis
    
    async def find_certificates_by_ip(self, ip_address: str) -> List[CertificateInfo]:
        """Find certificates associated with an IP address."""
        # This would typically require APIs like Censys, Shodan, etc.
        # For now, return empty list as it requires external API integration
        logger.info(f"Finding certificates for IP {ip_address} (requires external API)")
        return []
    
    async def find_domains_on_same_certificate(self, cert_info: CertificateInfo) -> List[str]:
        """Find all domains using the same certificate."""
        domains = []
        
        # Add common name
        if cert_info.common_name:
            domains.append(cert_info.common_name)
        
        # Add all subject alternative names
        domains.extend(cert_info.subject_alt_names)
        
        # Remove duplicates and clean up
        unique_domains = []
        for domain in domains:
            # Clean up domain (remove wildcards, etc.)
            clean_domain = domain.replace('*.', '').replace('*', '')
            if clean_domain and clean_domain not in unique_domains:
                unique_domains.append(clean_domain)
        
        return unique_domains
    
    async def analyze_certificate_history(self, domain: str) -> Dict:
        """Analyze historical certificate data for a domain."""
        domain = self.normalize_domain(domain)
        
        history = {
            'domain': domain,
            'current_certificate': None,
            'historical_certificates': [],
            'certificate_changes': [],
            'analysis_summary': {}
        }
        
        try:
            # Get current certificate
            current_cert = await self.get_certificate(domain)
            if current_cert:
                history['current_certificate'] = current_cert.to_dict()
            
            # Search for historical certificates via CT logs
            ct_entries = await self.search_certificate_transparency(domain)
            history['historical_certificates'] = [entry.to_dict() for entry in ct_entries]
            
            # Analyze certificate changes
            if len(history['historical_certificates']) > 1:
                history['analysis_summary']['certificate_changes_detected'] = True
                history['analysis_summary']['total_certificates_found'] = len(history['historical_certificates'])
            else:
                history['analysis_summary']['certificate_changes_detected'] = False
            
            # Check for certificate renewal patterns
            if current_cert and current_cert.valid_to:
                days_until_expiry = current_cert.days_until_expiry
                if days_until_expiry is not None:
                    if days_until_expiry > 365:
                        history['analysis_summary']['renewal_strategy'] = 'long_term'
                    elif days_until_expiry > 30:
                        history['analysis_summary']['renewal_strategy'] = 'standard'
                    else:
                        history['analysis_summary']['renewal_strategy'] = 'last_minute'
            
        except Exception as e:
            logger.error(f"Error analyzing certificate history for {domain}: {str(e)}")
            history['error'] = str(e)
        
        return history
    
    async def get_certificate_for_ip(self, ip_address: str) -> Optional[CertificateInfo]:
        """Get SSL certificate for an IP address (SNI required)."""
        try:
            # IP addresses require SNI to get the correct certificate
            # This is a simplified implementation - in practice you'd need the hostname
            return None
        except Exception as e:
            logger.error(f"Error getting certificate for IP {ip_address}: {str(e)}")
            return None