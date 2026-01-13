"""
WHOIS Lookup Module

This module provides comprehensive WHOIS lookup functionality for domains and IP addresses,
including privacy detection and email extraction capabilities.
"""

import asyncio
import re
import whois
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse
import ipaddress
import logging

logger = logging.getLogger(__name__)


class WHOISLookupError(Exception):
    """Custom exception for WHOIS lookup failures."""
    pass


class DomainWHOIS:
    """Domain WHOIS information container."""
    
    def __init__(self):
        self.domain: Optional[str] = None
        self.registrant_name: Optional[str] = None
        self.registrant_email: Optional[str] = None
        self.registrant_phone: Optional[str] = None
        self.registrant_address: Optional[str] = None
        self.registrar: Optional[str] = None
        self.registration_date: Optional[datetime] = None
        self.expiration_date: Optional[datetime] = None
        self.name_servers: List[str] = []
        self.dnssec_status: Optional[str] = None
        self.admin_email: Optional[str] = None
        self.tech_email: Optional[str] = None
        self.status: Optional[str] = None
        self.updated_date: Optional[datetime] = None
        
    def to_dict(self) -> Dict:
        """Convert to dictionary format."""
        return {
            'domain': self.domain,
            'registrant_name': self.registrant_name,
            'registrant_email': self.registrant_email,
            'registrant_phone': self.registrant_phone,
            'registrant_address': self.registrant_address,
            'registrar': self.registrar,
            'registration_date': self.registration_date.isoformat() if self.registration_date else None,
            'expiration_date': self.expiration_date.isoformat() if self.expiration_date else None,
            'name_servers': self.name_servers,
            'dnssec_status': self.dnssec_status,
            'admin_email': self.admin_email,
            'tech_email': self.tech_email,
            'status': self.status,
            'updated_date': self.updated_date.isoformat() if self.updated_date else None
        }


class IPWHOIS:
    """IP WHOIS information container."""
    
    def __init__(self):
        self.ip_address: Optional[str] = None
        self.isp: Optional[str] = None
        self.organization: Optional[str] = None
        self.asn: Optional[str] = None
        self.asn_description: Optional[str] = None
        self.country: Optional[str] = None
        self.city: Optional[str] = None
        self.netrange: Optional[str] = None
        self.netname: Optional[str] = None
        self.handle: Optional[str] = None
        
    def to_dict(self) -> Dict:
        """Convert to dictionary format."""
        return {
            'ip_address': self.ip_address,
            'isp': self.isp,
            'organization': self.organization,
            'asn': self.asn,
            'asn_description': self.asn_description,
            'country': self.country,
            'city': self.city,
            'netrange': self.netrange,
            'netname': self.netname,
            'handle': self.handle
        }


class WHOISLookup:
    """Main WHOIS lookup service."""
    
    def __init__(self):
        self.privacy_patterns = [
            r'Redacted for privacy',
            r'Privacy protection',
            r'Registrant Privacy',
            r'Domain Privacy Service',
            r'WhoisGuard',
            r'Privacy Protection',
            r'Privacy service',
            r'Domain ID Shield',
            r'Redacted',
            r'Private registration',
            r'WHOIS privacy',
            r'Registrant: Domain Privacy',
            r'Domain Privacy Shield'
        ]
        
        self.privacy_providers = [
            'whoisguard',
            'privacyprotection',
            'whoisproxy',
            'domainprivacy',
            'namecheap',
            'godaddy',
            'domainsbyproxy',
            'privacy guardian',
            'whois.com',
            'privacy service',
            'domain id shield',
            'privacy protection service',
            'redacted for privacy'
        ]
        
    def is_privacy_protected(self, whois_text: str) -> Tuple[bool, List[str]]:
        """Detect if domain uses privacy protection."""
        detected_providers = []
        
        for pattern in self.privacy_patterns:
            if re.search(pattern, whois_text, re.IGNORECASE):
                detected_providers.append(pattern)
                
        for provider in self.privacy_providers:
            if provider.lower() in whois_text.lower():
                detected_providers.append(provider)
                
        return len(detected_providers) > 0, detected_providers
    
    def extract_emails(self, whois_text: str) -> List[str]:
        """Extract all email addresses from WHOIS text."""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, whois_text, re.IGNORECASE)
        return list(set(emails))  # Remove duplicates
    
    def extract_phones(self, whois_text: str) -> List[str]:
        """Extract phone numbers from WHOIS text."""
        phone_patterns = [
            r'\+?1?[-.\s]?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}',  # US format
            r'\+[0-9]{1,3}[-.\s]?[0-9]{1,14}',  # International format
            r'\b[0-9]{3}[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b'  # Simple format
        ]
        
        phones = []
        for pattern in phone_patterns:
            phones.extend(re.findall(pattern, whois_text))
            
        return list(set(phones))
    
    def normalize_domain(self, domain: str) -> str:
        """Normalize domain name for lookup."""
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
    
    async def lookup_domain(self, domain: str) -> DomainWHOIS:
        """Perform WHOIS lookup for a domain."""
        normalized_domain = self.normalize_domain(domain)
        
        try:
            # Perform WHOIS lookup
            whois_data = whois.whois(normalized_domain)
            
            domain_info = DomainWHOIS()
            domain_info.domain = normalized_domain
            
            # Extract registrant information
            if whois_data.get('name'):
                domain_info.registrant_name = whois_data.get('name')
            elif whois_data.get('org'):
                domain_info.registrant_name = whois_data.get('org')
            elif whois_data.get('organization'):
                domain_info.registrant_name = whois_data.get('organization')
                
            domain_info.registrant_email = whois_data.get('email')
            domain_info.registrant_phone = whois_data.get('phone')
            domain_info.registrant_address = whois_data.get('address')
            
            # Extract registrar information
            domain_info.registrar = whois_data.get('registrar')
            domain_info.status = whois_data.get('status')
            
            # Extract dates
            if whois_data.get('creation_date'):
                if isinstance(whois_data['creation_date'], list):
                    domain_info.registration_date = whois_data['creation_date'][0]
                else:
                    domain_info.registration_date = whois_data['creation_date']
                    
            if whois_data.get('expiration_date'):
                if isinstance(whois_data['expiration_date'], list):
                    domain_info.expiration_date = whois_data['expiration_date'][0]
                else:
                    domain_info.expiration_date = whois_data['expiration_date']
                    
            if whois_data.get('updated_date'):
                if isinstance(whois_data['updated_date'], list):
                    domain_info.updated_date = whois_data['updated_date'][0]
                else:
                    domain_info.updated_date = whois_data['updated_date']
            
            # Extract name servers
            if whois_data.get('name_servers'):
                if isinstance(whois_data['name_servers'], list):
                    domain_info.name_servers = whois_data['name_servers']
                else:
                    domain_info.name_servers = [whois_data['name_servers']]
            
            # Check for privacy protection
            whois_text = str(whois_data).lower()
            is_privacy, providers = self.is_privacy_protected(whois_text)
            
            # Extract admin and tech emails
            emails = self.extract_emails(str(whois_data))
            for email in emails:
                if any(keyword in str(whois_data).lower() for keyword in ['admin', 'administrative']):
                    domain_info.admin_email = email
                elif any(keyword in str(whois_data).lower() for keyword in ['tech', 'technical']):
                    domain_info.tech_email = email
                    
            return domain_info
            
        except Exception as e:
            logger.error(f"WHOIS lookup failed for domain {normalized_domain}: {str(e)}")
            raise WHOISLookupError(f"WHOIS lookup failed for {normalized_domain}: {str(e)}")
    
    async def lookup_ip(self, ip_address: str) -> IPWHOIS:
        """Perform WHOIS lookup for an IP address."""
        try:
            # Validate IP address
            ipaddress.ip_address(ip_address)
            
            # Perform WHOIS lookup
            whois_data = whois.whois(ip_address)
            
            ip_info = IPWHOIS()
            ip_info.ip_address = ip_address
            
            # Extract ISP/organization information
            if whois_data.get('org'):
                ip_info.organization = whois_data.get('org')
            elif whois_data.get('organization'):
                ip_info.organization = whois_data.get('organization')
            elif whois_data.get('netname'):
                ip_info.netname = whois_data.get('netname')
                
            # Extract ASN information
            if whois_data.get('asn'):
                ip_info.asn = whois_data.get('asn')
            elif whois_data.get('asn_org'):
                ip_info.asn = whois_data.get('asn_org')
                
            # Extract description
            if whois_data.get('descr'):
                ip_info.asn_description = whois_data.get('descr')
            elif whois_data.get('asn_description'):
                ip_info.asn_description = whois_data.get('asn_description')
                
            # Extract location information
            if whois_data.get('country'):
                ip_info.country = whois_data.get('country')
            elif whois_data.get('cc'):
                ip_info.country = whois_data.get('cc')
                
            if whois_data.get('city'):
                ip_info.city = whois_data.get('city')
                
            # Extract network range
            if whois_data.get('cidr'):
                ip_info.netrange = whois_data.get('cidr')
            elif whois_data.get('netrange'):
                ip_info.netrange = whois_data.get('netrange')
                
            # Handle (like NET-XXX-XXX-XXX-XXX)
            if whois_data.get('handle'):
                ip_info.handle = whois_data.get('handle')
            elif whois_data.get('net_handle'):
                ip_info.handle = whois_data.get('net_handle')
                
            # Try to determine ISP from organization
            if ip_info.organization:
                ip_info.isp = ip_info.organization
                
            return ip_info
            
        except ValueError as e:
            logger.error(f"Invalid IP address: {ip_address}")
            raise WHOISLookupError(f"Invalid IP address: {ip_address}")
        except Exception as e:
            logger.error(f"IP WHOIS lookup failed for {ip_address}: {str(e)}")
            raise WHOISLookupError(f"IP WHOIS lookup failed for {ip_address}: {str(e)}")
    
    async def find_domains_by_email(self, email: str) -> List[str]:
        """Find other domains registered by the same email (simulated)."""
        # This would typically use APIs like SecurityTrails, RiskIQ, etc.
        # For now, return empty list as it requires external API integration
        logger.info(f"Finding domains registered by email {email} (requires external API)")
        return []
    
    async def analyze_registrant(self, domain_info: DomainWHOIS) -> Dict:
        """Analyze registrant information for patterns and risks."""
        analysis = {
            'uses_privacy': False,
            'privacy_providers': [],
            'email_variations': [],
            'suspicious_patterns': [],
            'risk_score': 0
        }
        
        if domain_info.registrant_email:
            # Check for privacy protection
            whois_text = str(domain_info.to_dict()).lower()
            is_privacy, providers = self.is_privacy_protected(whois_text)
            analysis['uses_privacy'] = is_privacy
            analysis['privacy_providers'] = providers
            
            # Generate email variations
            base_email = domain_info.registrant_email
            local_part = base_email.split('@')[0]
            domain_part = base_email.split('@')[1]
            
            variations = [
                f"{local_part}@{domain_part}",
                f"{local_part.replace('.', '')}@{domain_part}",
                f"{local_part.replace('-', '')}@{domain_part}",
                f"{local_part.replace('_', '')}@{domain_part}",
            ]
            
            analysis['email_variations'] = list(set(variations))
        
        # Check for suspicious patterns
        if domain_info.registrant_name:
            name = domain_info.registrant_name.lower()
            if any(suspicious in name for suspicious in ['privacy', 'redacted', 'protected', 'anonymous']):
                analysis['suspicious_patterns'].append('generic_privacy_name')
                analysis['risk_score'] += 20
        
        if analysis['uses_privacy']:
            analysis['risk_score'] += 30
            
        if analysis['risk_score'] > 50:
            analysis['risk_level'] = 'high'
        elif analysis['risk_score'] > 25:
            analysis['risk_level'] = 'medium'
        else:
            analysis['risk_level'] = 'low'
            
        return analysis


# Utility functions
def is_valid_domain(domain: str) -> bool:
    """Check if string is a valid domain name."""
    domain_pattern = re.compile(
        r'^([a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$'
    )
    return bool(domain_pattern.match(domain))


def is_valid_ip(ip: str) -> bool:
    """Check if string is a valid IP address."""
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False