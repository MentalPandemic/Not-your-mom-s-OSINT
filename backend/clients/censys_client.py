"""
Censys Internet Search API Client

This module provides client functionality for accessing Censys internet-wide scan data
for IP addresses, domains, certificates, and other internet infrastructure.
"""

import asyncio
import aiohttp
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class CensysClientError(Exception):
    """Custom exception for Censys client failures."""
    pass


class CensysAPIClient:
    """Censys API client for internet-wide intelligence."""
    
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
    
    async def _make_request(self, endpoint: str, params: Dict = None, method: str = 'GET') -> Dict:
        """Make a request to Censys API."""
        if not self.session:
            raise CensysClientError("Client session not initialized. Use async context manager.")
        
        url = f"{self.base_url}{endpoint}"
        auth = aiohttp.BasicAuth(self.api_id, self.api_secret)
        
        try:
            if method == 'GET':
                async with self.session.get(url, params=params, auth=auth) as response:
                    if response.status == 200:
                        return await response.json()
                    elif response.status == 401:
                        raise CensysClientError("Invalid Censys credentials")
                    elif response.status == 403:
                        raise CensysClientError("Access forbidden - check API permissions")
                    elif response.status == 429:
                        raise CensysClientError("Rate limit exceeded")
                    else:
                        error_text = await response.text()
                        raise CensysClientError(f"Censys API request failed: {response.status} - {error_text}")
                        
        except aiohttp.ClientError as e:
            raise CensysClientError(f"Network error: {str(e)}")
    
    # IP Address Methods
    async def get_ip_info(self, ip_address: str) -> Dict:
        """Get comprehensive information about an IP address."""
        endpoint = f"/ips/{ip_address}"
        return await self._make_request(endpoint)
    
    async def search_ips(self, query: str, page: int = 1, per_page: int = 100, 
                        fields: List[str] = None) -> Dict:
        """Search for IP addresses matching a query."""
        if fields is None:
            fields = ['ip', 'protocols', 'ports', 'hostnames', 'domain', 'organization', 'country']
        
        params = {
            'query': query,
            'page': page,
            'per_page': per_page,
            'fields': ','.join(fields)
        }
        
        endpoint = "/ips/search"
        return await self._make_request(endpoint, params)
    
    async def get_ip_protocols(self, ip_address: str) -> List[str]:
        """Get protocols available on an IP address."""
        endpoint = f"/ips/{ip_address}/protocols"
        response = await self._make_request(endpoint)
        return response.get('protocols', [])
    
    async def get_ip_domains(self, ip_address: str) -> List[str]:
        """Get domains hosted on an IP address."""
        endpoint = f"/ips/{ip_address}/domains"
        response = await self._make_request(endpoint)
        return response.get('domains', [])
    
    async def get_ip_certificates(self, ip_address: str) -> List[Dict]:
        """Get certificates associated with an IP address."""
        endpoint = f"/ips/{ip_address}/certificates"
        response = await self._make_request(endpoint)
        return response.get('certificates', [])
    
    # Certificate Methods
    async def search_certificates(self, query: str, page: int = 1, per_page: int = 100,
                                 fields: List[str] = None) -> Dict:
        """Search for SSL certificates."""
        if fields is None:
            fields = ['fingerprint_sha256', 'subject_dn', 'issuer_dn', 'serial_number',
                     'not_before', 'not_after', 'names', 'subject.common_name']
        
        params = {
            'query': query,
            'page': page,
            'per_page': per_page,
            'fields': ','.join(fields)
        }
        
        endpoint = "/certificates/search"
        return await self._make_request(endpoint, params)
    
    async def get_certificate(self, fingerprint_sha256: str) -> Dict:
        """Get detailed certificate information."""
        endpoint = f"/certificates/{fingerprint_sha256}"
        return await self._make_request(endpoint)
    
    async def search_certificates_by_domain(self, domain: str) -> Dict:
        """Search certificates by domain."""
        query = f'names: "{domain}" OR subject.common_name: "{domain}"'
        return await self.search_certificates(query)
    
    async def search_certificates_by_issuer(self, issuer: str) -> Dict:
        """Search certificates by issuer."""
        query = f'issuer.organization: "{issuer}" OR issuer_dn: "{issuer}"'
        return await self.search_certificates(query)
    
    async def search_certificates_by_organization(self, organization: str) -> Dict:
        """Search certificates by organization."""
        query = f'subject.organization: "{organization}" OR subject_dn: "{organization}"'
        return await self.search_certificates(query)
    
    # Website Methods
    async def search_websites(self, query: str, page: int = 1, per_page: int = 100,
                             fields: List[str] = None) -> Dict:
        """Search for websites."""
        if fields is None:
            fields = ['domain', 'ip', 'protocols', 'ports', 'cert', 'alexa_rank', 'http_status']
        
        params = {
            'query': query,
            'page': page,
            'per_page': per_page,
            'fields': ','.join(fields)
        }
        
        endpoint = "/websites/search"
        return await self._make_request(endpoint, params)
    
    async def get_website_info(self, domain: str) -> Dict:
        """Get comprehensive information about a website."""
        endpoint = f"/websites/{domain}"
        return await self._make_request(endpoint)
    
    async def search_websites_by_domain(self, domain: str) -> Dict:
        """Search for websites by domain."""
        query = f'domain: "{domain}" OR domain: "*.{domain}"'
        return await self.search_websites(query)
    
    async def search_websites_by_ip(self, ip_address: str) -> Dict:
        """Search for websites hosted on an IP address."""
        query = f'ip: "{ip_address}"'
        return await self.search_websites(query)
    
    # Domain Methods
    async def search_domains(self, query: str, page: int = 1, per_page: int = 100) -> Dict:
        """Search for domains."""
        params = {
            'query': query,
            'page': page,
            'per_page': per_page
        }
        
        endpoint = "/domains/search"
        return await self._make_request(endpoint, params)
    
    async def get_domain_info(self, domain: str) -> Dict:
        """Get detailed information about a domain."""
        endpoint = f"/domains/{domain}"
        return await self._make_request(endpoint)
    
    # Bulk Operations
    async def bulk_ip_lookup(self, ip_addresses: List[str]) -> Dict:
        """Perform bulk IP lookups."""
        ips_query = ' OR '.join([f'ip: "{ip}"' for ip in ip_addresses])
        return await self.search_ips(ips_query, per_page=len(ip_addresses))
    
    async def bulk_certificate_lookup(self, fingerprints: List[str]) -> Dict:
        """Perform bulk certificate lookups."""
        certs_query = ' OR '.join([f'fingerprint_sha256: "{fp}"' for fp in fingerprints])
        return await self.search_certificates(certs_query, per_page=len(fingerprints))
    
    # Advanced Search Methods
    async def search_by_technology(self, technology: str, version: str = None) -> Dict:
        """Search for services running specific technology."""
        query = f'services.product: "{technology}"'
        if version:
            query += f' AND services.version: "{version}"'
        return await self.search_ips(query)
    
    async def search_by_organization(self, organization: str) -> Dict:
        """Search for infrastructure by organization."""
        query = f'organization: "{organization}"'
        return await self.search_ips(query)
    
    async def search_by_country(self, country: str) -> Dict:
        """Search for infrastructure by country."""
        query = f'location.country: "{country}"'
        return await self.search_ips(query)
    
    async def search_by_asn(self, asn: str) -> Dict:
        """Search for infrastructure by ASN."""
        query = f'autonomous_system.asn: {asn}'
        return await self.search_ips(query)
    
    async def search_websites_by_ssl(self, ssl_issuer: str = None, ssl_algorithm: str = None) -> Dict:
        """Search for websites with specific SSL characteristics."""
        query = 'protocols: 443'
        
        if ssl_issuer:
            query += f' AND cert.issuer.organization: "{ssl_issuer}"'
        if ssl_algorithm:
            query += f' AND cert.signature.algorithm: "{ssl_algorithm}"'
        
        return await self.search_websites(query)


# Analysis and Intelligence Functions
def analyze_ip_reputation(ip_info: Dict) -> Dict:
    """Analyze IP address reputation and characteristics."""
    analysis = {
        'reputation_score': 0,
        'risk_indicators': [],
        'trust_indicators': [],
        'geographic_distribution': [],
        'services': [],
        'threat_indicators': []
    }
    
    # Extract IP information
    ip = ip_info.get('ip')
    protocols = ip_info.get('protocols', [])
    ports = ip_info.get('ports', [])
    organization = ip_info.get('organization', '')
    country = ip_info.get('location', {}).get('country', '')
    
    # Analyze services
    if 22 in ports:
        analysis['services'].append('SSH')
        if any('SSH-2.0-OpenSSH' in proto for proto in protocols):
            analysis['trust_indicators'].append('Standard SSH')
    
    if 80 in ports:
        analysis['services'].append('HTTP')
        analysis['trust_indicators'].append('Web Server')
    
    if 443 in ports:
        analysis['services'].append('HTTPS')
        analysis['trust_indicators'].append('SSL/TLS')
    
    # Analyze organization
    if organization:
        known_providers = ['Amazon', 'Google', 'Microsoft', 'Cloudflare', 'Akamai']
        if any(provider.lower() in organization.lower() for provider in known_providers):
            analysis['trust_indicators'].append(f'Reputable provider: {organization}')
            analysis['reputation_score'] += 20
    
    # Geographic analysis
    if country:
        analysis['geographic_distribution'].append(country)
        
        # Some countries have higher risk scores
        high_risk_countries = ['CN', 'RU', 'KP']
        if country in high_risk_countries:
            analysis['risk_indicators'].append(f'High-risk geography: {country}')
            analysis['reputation_score'] -= 10
    
    # Calculate final reputation score
    analysis['reputation_score'] = max(0, min(100, analysis['reputation_score']))
    
    # Determine risk level
    if analysis['reputation_score'] >= 80:
        analysis['risk_level'] = 'Low'
    elif analysis['reputation_score'] >= 60:
        analysis['risk_level'] = 'Medium'
    else:
        analysis['risk_level'] = 'High'
    
    return analysis


def extract_domain_relationships(censys_data: Dict) -> List[Dict]:
    """Extract domain relationships from Censys data."""
    relationships = []
    
    # Get domains from IP data
    ip_info = censys_data.get('ip_info', {})
    domains = ip_info.get('domains', [])
    ip = ip_info.get('ip')
    
    # Create domain-to-IP relationships
    for domain in domains:
        relationships.append({
            'type': 'hosted_on',
            'source': domain,
            'target': ip,
            'confidence': 0.9,
            'source_type': 'domain',
            'target_type': 'ip'
        })
    
    # Get certificates and create relationships
    certificates = ip_info.get('certificates', [])
    for cert in certificates:
        cert_fp = cert.get('fingerprint_sha256')
        if cert_fp:
            relationships.append({
                'type': 'secured_by',
                'source': ip,
                'target': cert_fp,
                'confidence': 0.8,
                'source_type': 'ip',
                'target_type': 'certificate'
            })
    
    return relationships


def identify_infrastructure_clusters(ip_data_list: List[Dict]) -> List[Dict]:
    """Identify clusters of related infrastructure."""
    clusters = []
    
    # Group by organization
    org_groups = {}
    for ip_data in ip_data_list:
        org = ip_data.get('organization', 'Unknown')
        if org not in org_groups:
            org_groups[org] = []
        org_groups[org].append(ip_data)
    
    # Create clusters for organizations with multiple IPs
    for org, ip_list in org_groups.items():
        if len(ip_list) > 1:
            clusters.append({
                'type': 'organization_infrastructure',
                'name': f"{org} Infrastructure",
                'members': [ip.get('ip') for ip in ip_list],
                'organization': org,
                'confidence': 0.8,
                'size': len(ip_list)
            })
    
    # Group by ASN
    asn_groups = {}
    for ip_data in ip_data_list:
        asn_info = ip_data.get('autonomous_system', {})
        asn = asn_info.get('asn')
        if asn:
            if asn not in asn_groups:
                asn_groups[asn] = []
            asn_groups[asn].append(ip_data)
    
    # Create clusters for ASNs with multiple IPs
    for asn, ip_list in asn_groups.items():
        if len(ip_list) > 1:
            clusters.append({
                'type': 'asn_infrastructure',
                'name': f"ASN {asn}",
                'members': [ip.get('ip') for ip in ip_list],
                'asn': asn,
                'confidence': 0.7,
                'size': len(ip_list)
            })
    
    return clusters