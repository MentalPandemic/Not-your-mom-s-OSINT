"""
Certificate Transparency API Client

This module provides client functionality for accessing Certificate Transparency logs
and certificate intelligence services.
"""

import asyncio
import aiohttp
import json
import ssl
import socket
from typing import Dict, List, Optional, Any
from datetime import datetime
import re
import logging

logger = logging.getLogger(__name__)


class CTClientError(Exception):
    """Custom exception for Certificate Transparency client failures."""
    pass


class CrtshClient:
    """crt.sh API client for Certificate Transparency logs."""
    
    def __init__(self):
        self.base_url = "https://crt.sh"
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def search_by_domain(self, domain: str, include_expired: bool = True) -> List[Dict]:
        """Search for certificates by domain."""
        try:
            params = {
                'q': f'%.{domain}',
                'output': 'json'
            }
            
            if not include_expired:
                params['exclude'] = 'expired'
            
            url = f"{self.base_url}/"
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._parse_ct_entries(data, domain)
                else:
                    logger.error(f"crt.sh search failed: {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error searching crt.sh for {domain}: {str(e)}")
            return []
    
    async def search_by_exact_domain(self, domain: str, include_expired: bool = True) -> List[Dict]:
        """Search for certificates by exact domain match."""
        try:
            params = {
                'q': domain,
                'output': 'json'
            }
            
            if not include_expired:
                params['exclude'] = 'expired'
            
            url = f"{self.base_url}/"
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._parse_ct_entries(data, domain, exact_match=True)
                else:
                    logger.error(f"crt.sh exact search failed: {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error in exact crt.sh search for {domain}: {str(e)}")
            return []
    
    async def search_by_email(self, email: str) -> List[Dict]:
        """Search for certificates by email address."""
        try:
            params = {
                'q': f'email:{email}',
                'output': 'json'
            }
            
            url = f"{self.base_url}/"
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._parse_ct_entries(data, email)
                else:
                    logger.error(f"crt.sh email search failed: {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error searching crt.sh for email {email}: {str(e)}")
            return []
    
    async def get_certificate_details(self, certificate_id: int) -> Dict:
        """Get detailed certificate information by ID."""
        try:
            params = {'id': certificate_id, 'output': 'json'}
            url = f"{self.base_url}/"
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return data[0] if data else {}
                else:
                    logger.error(f"crt.sh certificate details failed: {response.status}")
                    return {}
                    
        except Exception as e:
            logger.error(f"Error getting certificate details for ID {certificate_id}: {str(e)}")
            return {}
    
    def _parse_ct_entries(self, data: List[Dict], search_term: str, exact_match: bool = False) -> List[Dict]:
        """Parse Certificate Transparency log entries."""
        entries = []
        
        for entry in data:
            try:
                parsed_entry = {
                    'id': entry.get('id'),
                    'name_value': entry.get('name_value', ''),
                    'common_name': entry.get('common_name'),
                    'issuer_name': entry.get('issuer_name'),
                    'not_before': entry.get('not_before'),
                    'not_after': entry.get('not_after'),
                    'serial_number': entry.get('serial_number'),
                    'matching_identities': entry.get('matching_identities', []),
                    'entry_timestamp': entry.get('entry_timestamp'),
                    'search_term': search_term,
                    'exact_match': exact_match
                }
                
                # Parse name_value field which can contain multiple domains
                name_values = entry.get('name_value', '').split('\n')
                parsed_entry['domains'] = [
                    name.strip() for name in name_values if name.strip()
                ]
                
                entries.append(parsed_entry)
                
            except Exception as e:
                logger.debug(f"Error parsing CT entry: {str(e)}")
                continue
        
        return entries


class CertSpotterClient:
    """CertSpotter API client."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.certspotter.com/v1"
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def _make_request(self, endpoint: str, params: Dict = None) -> List[Dict]:
        """Make a request to CertSpotter API."""
        if not self.session:
            raise CTClientError("Client session not initialized. Use async context manager.")
        
        url = f"{self.base_url}{endpoint}"
        headers = {'Authorization': f'Bearer {self.api_key}'}
        
        try:
            async with self.session.get(url, params=params, headers=headers) as response:
                if response.status == 200:
                    return await response.json()
                elif response.status == 401:
                    raise CTClientError("Invalid API key")
                elif response.status == 429:
                    raise CTClientError("Rate limit exceeded")
                else:
                    error_text = await response.text()
                    raise CTClientError(f"CertSpotter API request failed: {response.status} - {error_text}")
                    
        except aiohttp.ClientError as e:
            raise CTClientError(f"Network error: {str(e)}")
    
    async def get_issuances(self, domain: str, include_subdomains: bool = True, 
                           match_wildcards: bool = False, expired: bool = True) -> List[Dict]:
        """Get certificate issuances for a domain."""
        params = {
            'domain': domain,
            'include_subdomains': include_subdomains,
            'match_wildcards': match_wildcards,
            'expired': expired
        }
        
        endpoint = "/issuances"
        return await self._make_request(endpoint, params)
    
    async def get_issuances_by_email(self, email: str) -> List[Dict]:
        """Get certificate issuances by email."""
        params = {'email': email}
        endpoint = "/issuances"
        return await self._make_request(endpoint, params)
    
    async def get_certificate_details(self, issuance_id: str) -> Dict:
        """Get detailed certificate information."""
        endpoint = f"/issuances/{issuance_id}"
        return await self._make_request(endpoint)


class CensysCertificatesClient:
    """Censys certificate search client."""
    
    def __init__(self, api_id: str, api_secret: str):
        self.api_id = api_id
        self.api_secret = api_secret
        self.base_url = "https://censys.io/api/v1"
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def _make_request(self, endpoint: str, params: Dict = None) -> Dict:
        """Make a request to Censys API."""
        if not self.session:
            raise CTClientError("Client session not initialized. Use async context manager.")
        
        url = f"{self.base_url}{endpoint}"
        auth = aiohttp.BasicAuth(self.api_id, self.api_secret)
        
        try:
            async with self.session.get(url, params=params, auth=auth) as response:
                if response.status == 200:
                    return await response.json()
                elif response.status == 401:
                    raise CTClientError("Invalid Censys credentials")
                elif response.status == 429:
                    raise CTClientError("Rate limit exceeded")
                else:
                    error_text = await response.text()
                    raise CTClientError(f"Censys API request failed: {response.status} - {error_text}")
                    
        except aiohttp.ClientError as e:
            raise CTClientError(f"Network error: {str(e)}")
    
    async def search_certificates(self, query: str, fields: List[str] = None, 
                                 page: int = 1, per_page: int = 100) -> Dict:
        """Search certificates by query."""
        if fields is None:
            fields = ['fingerprint_sha256', 'subject_dn', 'issuer_dn', 'serial_number', 
                     'not_before', 'not_after', 'names']
        
        params = {
            'query': query,
            'page': page,
            'per_page': per_page,
            'fields': ','.join(fields)
        }
        
        endpoint = "/certificates/search"
        return await self._make_request(endpoint, params)
    
    async def get_certificate(self, fingerprint_sha256: str) -> Dict:
        """Get certificate by SHA256 fingerprint."""
        endpoint = f"/certificates/{fingerprint_sha256}"
        return await self._make_request(endpoint)
    
    async def search_by_domain(self, domain: str) -> Dict:
        """Search certificates by domain."""
        query = f'names: "{domain}" OR subject_dn: "{domain}"'
        return await self.search_certificates(query)
    
    async def search_by_organization(self, organization: str) -> Dict:
        """Search certificates by organization."""
        query = f'organization: "{organization}" OR subject.organization: "{organization}"'
        return await self.search_certificates(query)
    
    async def search_by_issuer(self, issuer: str) -> Dict:
        """Search certificates by issuer."""
        query = f'issuer.organization: "{issuer}" OR issuer_dn: "{issuer}"'
        return await self.search_certificates(query)


# Utility functions for Certificate Transparency analysis
def analyze_certificate_issuance_patterns(ct_entries: List[Dict]) -> Dict:
    """Analyze patterns in certificate issuance."""
    if not ct_entries:
        return {'error': 'No certificate entries to analyze'}
    
    analysis = {
        'total_certificates': len(ct_entries),
        'unique_domains': set(),
        'issuers': {},
        'issuance_timeline': {},
        'certificate_types': {},
        'wildcard_certificates': 0,
        'self_signed_certificates': 0
    }
    
    for entry in ct_entries:
        # Count domains
        domains = entry.get('domains', [])
        analysis['unique_domains'].update(domains)
        
        # Count issuers
        issuer = entry.get('issuer_name', 'Unknown')
        analysis['issuers'][issuer] = analysis['issuers'].get(issuer, 0) + 1
        
        # Timeline analysis
        if entry.get('not_before'):
            try:
                date = datetime.fromisoformat(entry['not_before'].replace('Z', '+00:00'))
                year = date.year
                analysis['issuance_timeline'][year] = analysis['issuance_timeline'].get(year, 0) + 1
            except:
                pass
        
        # Check for wildcard certificates
        if any('*' in domain for domain in domains):
            analysis['wildcard_certificates'] += 1
        
        # Analyze certificate types based on domain patterns
        if domains:
            for domain in domains:
                if domain.startswith('www.'):
                    analysis['certificate_types']['www_subdomain'] = analysis['certificate_types'].get('www_subdomain', 0) + 1
                elif domain.startswith('mail.'):
                    analysis['certificate_types']['mail_subdomain'] = analysis['certificate_types'].get('mail_subdomain', 0) + 1
                elif domain.startswith('api.'):
                    analysis['certificate_types']['api_subdomain'] = analysis['certificate_types'].get('api_subdomain', 0) + 1
                else:
                    analysis['certificate_types']['root_domain'] = analysis['certificate_types'].get('root_domain', 0) + 1
    
    # Convert sets to lists for JSON serialization
    analysis['unique_domains'] = list(analysis['unique_domains'])
    
    return analysis


def detect_suspicious_certificate_patterns(ct_entries: List[Dict]) -> List[Dict]:
    """Detect suspicious patterns in certificate data."""
    suspicious = []
    
    for entry in ct_entries:
        domains = entry.get('domains', [])
        issuer = entry.get('issuer_name', '')
        
        # Check for suspicious issuer patterns
        if any(suspicious_word in issuer.lower() for suspicious_word in ['test', 'fake', 'self', 'invalid']):
            suspicious.append({
                'type': 'suspicious_issuer',
                'certificate_id': entry.get('id'),
                'issuer': issuer,
                'domains': domains,
                'severity': 'medium',
                'description': f'Certificate issued by potentially suspicious CA: {issuer}'
            })
        
        # Check for short validity periods
        if entry.get('not_before') and entry.get('not_after'):
            try:
                start = datetime.fromisoformat(entry['not_before'].replace('Z', '+00:00'))
                end = datetime.fromisoformat(entry['not_after'].replace('Z', '+00:00'))
                validity_days = (end - start).days
                
                if validity_days < 30:
                    suspicious.append({
                        'type': 'short_validity',
                        'certificate_id': entry.get('id'),
                        'domains': domains,
                        'validity_days': validity_days,
                        'severity': 'high',
                        'description': f'Certificate has very short validity period: {validity_days} days'
                    })
            except:
                pass
        
        # Check for unusual domain patterns
        for domain in domains:
            # Check for homograph-like patterns
            if re.search(r'[а-я]', domain):  # Cyrillic characters
                suspicious.append({
                    'type': 'homograph_risk',
                    'certificate_id': entry.get('id'),
                    'domain': domain,
                    'severity': 'high',
                    'description': f'Potential homograph attack detected: {domain}'
                })
            
            # Check for excessive subdomains
            subdomain_count = domain.count('.')
            if subdomain_count > 3:
                suspicious.append({
                    'type': 'excessive_subdomains',
                    'certificate_id': entry.get('id'),
                    'domain': domain,
                    'subdomain_count': subdomain_count,
                    'severity': 'low',
                    'description': f'Domain has excessive subdomains: {subdomain_count} levels'
                })
    
    return suspicious


def extract_domains_from_certificates(ct_entries: List[Dict]) -> List[str]:
    """Extract all domains from certificate transparency entries."""
    domains = []
    
    for entry in ct_entries:
        # Add domains from name_value field
        name_values = entry.get('name_value', '').split('\n')
        for name in name_values:
            clean_name = name.strip()
            if clean_name and not clean_name.startswith('*.'):
                domains.append(clean_name)
        
        # Add common name if not already included
        common_name = entry.get('common_name')
        if common_name and common_name not in domains:
            domains.append(common_name)
    
    # Remove duplicates and return sorted list
    return sorted(list(set(domains)))