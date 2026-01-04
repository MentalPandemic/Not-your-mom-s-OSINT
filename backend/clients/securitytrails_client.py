"""
SecurityTrails Domain Intelligence API Client

This module provides client functionality for accessing SecurityTrails domain intelligence
API for DNS history, WHOIS data, subdomain discovery, and threat intelligence.
"""

import asyncio
import aiohttp
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class SecurityTrailsClientError(Exception):
    """Custom exception for SecurityTrails client failures."""
    pass


class SecurityTrailsAPIClient:
    """SecurityTrails API client for domain intelligence."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.securitytrails.com/v1"
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def _make_request(self, endpoint: str, params: Dict = None, method: str = 'GET') -> Dict:
        """Make a request to SecurityTrails API."""
        if not self.session:
            raise SecurityTrailsClientError("Client session not initialized. Use async context manager.")
        
        url = f"{self.base_url}{endpoint}"
        headers = {
            'Accept': 'application/json',
            'API-Key': self.api_key
        }
        
        try:
            if method == 'GET':
                async with self.session.get(url, params=params, headers=headers) as response:
                    if response.status == 200:
                        return await response.json()
                    elif response.status == 401:
                        raise SecurityTrailsClientError("Invalid SecurityTrails API key")
                    elif response.status == 403:
                        raise SecurityTrailsClientError("Access forbidden - check API permissions")
                    elif response.status == 429:
                        raise SecurityTrailsClientError("Rate limit exceeded")
                    else:
                        error_text = await response.text()
                        raise SecurityTrailsClientError(f"SecurityTrails API request failed: {response.status} - {error_text}")
                        
        except aiohttp.ClientError as e:
            raise SecurityTrailsClientError(f"Network error: {str(e)}")
    
    # Domain Information
    async def get_domain_info(self, domain: str) -> Dict:
        """Get comprehensive domain information."""
        endpoint = f"/domain/{domain}/info"
        return await self._make_request(endpoint)
    
    async def get_domain_stats(self, domain: str) -> Dict:
        """Get domain statistics."""
        endpoint = f"/domain/{domain}/stats"
        return await self._make_request(endpoint)
    
    async def get_domain_tags(self, domain: str) -> List[Dict]:
        """Get domain tags and classifications."""
        endpoint = f"/domain/{domain}/tags"
        response = await self._make_request(endpoint)
        return response.get('tags', [])
    
    # Subdomain Discovery
    async def get_domain_subdomains(self, domain: str, include_children: bool = False) -> Dict:
        """Get subdomains for a domain."""
        endpoint = f"/domain/{domain}/subdomains"
        params = {'children': 'true' if include_children else 'false'}
        return await self._make_request(endpoint, params)
    
    async def get_domain_all_subdomains(self, domain: str) -> List[str]:
        """Get all subdomains including children."""
        endpoint = f"/domain/{domain}/subdomains/all"
        response = await self._make_request(endpoint)
        return response.get('subdomains', [])
    
    # DNS History
    async def get_dns_history(self, domain: str, record_type: str = 'A', include_wildcards: bool = False) -> Dict:
        """Get DNS history for a domain."""
        endpoint = f"/domain/{domain}/dns/{record_type.lower()}"
        params = {'include_wildcards': 'true' if include_wildcards else 'false'}
        return await self._make_request(endpoint, params)
    
    async def get_all_dns_history(self, domain: str) -> Dict:
        """Get complete DNS history for all record types."""
        endpoint = f"/domain/{domain}/dns"
        return await self._make_request(endpoint)
    
    async def get_pdns(self, domain: str, record_type: str = 'A') -> List[Dict]:
        """Get passive DNS data."""
        endpoint = f"/domain/{domain}/pdns/{record_type.lower()}"
        response = await self._make_request(endpoint)
        return response.get('records', [])
    
    async def get_pdns_aggregate(self, domain: str, record_type: str = 'A') -> List[Dict]:
        """Get aggregated passive DNS data."""
        endpoint = f"/domain/{domain}/pdns/aggregate/{record_type.lower()}"
        response = await self._make_request(endpoint)
        return response.get('records', [])
    
    # WHOIS Data
    async def get_whois_history(self, domain: str) -> List[Dict]:
        """Get WHOIS history for a domain."""
        endpoint = f"/domain/{domain}/whois"
        response = await self._make_request(endpoint)
        return response.get('records', [])
    
    async def get_whois_current(self, domain: str) -> Dict:
        """Get current WHOIS data for a domain."""
        endpoint = f"/domain/{domain}/whois/current"
        return await self._make_request(endpoint)
    
    # IP Intelligence
    async def get_ip_info(self, ip_address: str) -> Dict:
        """Get information about an IP address."""
        endpoint = f"/ips/{ip_address}"
        return await self._make_request(endpoint)
    
    async def get_ip_domains(self, ip_address: str, page: int = 1, max_pages: int = None) -> List[str]:
        """Get domains hosted on an IP address."""
        all_domains = []
        current_page = page
        
        while True:
            endpoint = f"/ips/{ip_address}/domains"
            params = {'page': current_page}
            response = await self._make_request(endpoint, params)
            
            domains = response.get('domains', [])
            if not domains:
                break
                
            all_domains.extend(domains)
            
            # Check if we should continue paginating
            if max_pages and current_page >= max_pages:
                break
                
            current_page += 1
        
        return all_domains
    
    async def get_ip_neighbors(self, ip_address: str, limit: int = 100) -> Dict:
        """Get neighboring IP addresses."""
        endpoint = f"/ips/{ip_address}/neighbors"
        params = {'limit': limit}
        return await self._make_request(endpoint, params)
    
    # Search Functions
    async def search_domains(self, query: str, limit: int = 100, offset: int = 0) -> Dict:
        """Search for domains using a query."""
        endpoint = "/domains/search"
        params = {
            'q': query,
            'limit': limit,
            'offset': offset
        }
        return await self._make_request(endpoint, params)
    
    async def search_domains_by_field(self, field: str, value: str, limit: int = 100) -> Dict:
        """Search domains by specific field."""
        endpoint = "/domains/search"
        params = {
            'filter[field]': field,
            'filter[value]': value,
            'limit': limit
        }
        return await self._make_request(endpoint, params)
    
    async def search_domains_by_registrant_email(self, email: str) -> Dict:
        """Search for domains by registrant email."""
        return await self.search_domains_by_field('registrantEmail', email)
    
    async def search_domains_by_registrant_name(self, name: str) -> Dict:
        """Search for domains by registrant name."""
        return await self.search_domains_by_field('registrantName', name)
    
    async def search_domains_by_registrant_org(self, organization: str) -> Dict:
        """Search for domains by registrant organization."""
        return await self.search_domains_by_field('registrantOrganization', organization)
    
    async def search_domains_by_nameserver(self, nameserver: str) -> Dict:
        """Search for domains using a specific nameserver."""
        return await self.search_domains_by_field('ns', nameserver)
    
    async def search_domains_by_ip(self, ip_address: str) -> Dict:
        """Search for domains hosted on a specific IP."""
        return await self.search_domains_by_field('ipv4', ip_address)
    
    async def search_domains_by_asn(self, asn: str) -> Dict:
        """Search for domains in a specific ASN."""
        return await self.search_domains_by_field('asn', asn)
    
    async def search_domains_by_country(self, country: str) -> Dict:
        """Search for domains in a specific country."""
        return await self.search_domains_by_field('country', country)
    
    async def search_domains_by_creation_date(self, start_date: str, end_date: str) -> Dict:
        """Search for domains created between dates."""
        endpoint = "/domains/search"
        params = {
            'filter[field]': 'createdDate',
            'filter[startDate]': start_date,
            'filter[endDate]': end_date,
            'limit': 100
        }
        return await self._make_request(endpoint, params)
    
    async def search_domains_by_expiration_date(self, start_date: str, end_date: str) -> Dict:
        """Search for domains expiring between dates."""
        endpoint = "/domains/search"
        params = {
            'filter[field]': 'expiredDate',
            'filter[startDate]': start_date,
            'filter[endDate]': end_date,
            'limit': 100
        }
        return await self._make_request(endpoint, params)
    
    # Threat Intelligence
    async def get_domain_malware(self, domain: str) -> List[Dict]:
        """Get malware associated with a domain."""
        endpoint = f"/domain/{domain}/malware"
        response = await self._make_request(endpoint)
        return response.get('records', [])
    
    async def get_domain_dhcp(self, domain: str) -> List[Dict]:
        """Get DHCP information for a domain."""
        endpoint = f"/domain/{domain}/dhcp"
        response = await self._make_request(endpoint)
        return response.get('records', [])
    
    async def get_domain_ssl(self, domain: str) -> List[Dict]:
        """Get SSL certificate information for a domain."""
        endpoint = f"/domain/{domain}/ssl"
        response = await self._make_request(endpoint)
        return response.get('records', [])
    
    async def get_domain_related(self, domain: str) -> Dict:
        """Get related domains and entities."""
        endpoint = f"/domain/{domain}/related"
        return await self._make_request(endpoint)
    
    # Analytics
    async def get_domain_analysis(self, domain: str) -> Dict:
        """Get comprehensive domain analysis."""
        endpoint = f"/domain/{domain}/analysis"
        return await self._make_request(endpoint)
    
    async def get_domain_tracking(self, domain: str) -> Dict:
        """Get domain tracking information."""
        endpoint = f"/domain/{domain}/tracking"
        return await self._make_request(endpoint)
    
    async def get_domain_analytics(self, domain: str) -> Dict:
        """Get domain analytics data."""
        endpoint = f"/domain/{domain}/analytics"
        return await self._make_request(endpoint)
    
    # Bulk Operations
    async def bulk_domain_info(self, domains: List[str]) -> Dict:
        """Get information for multiple domains."""
        endpoint = "/domains/bulk"
        params = {'domains': ','.join(domains)}
        return await self._make_request(endpoint, params)
    
    async def bulk_dns_history(self, domains: List[str], record_type: str = 'A') -> Dict:
        """Get DNS history for multiple domains."""
        endpoint = "/domains/bulk/dns"
        params = {
            'domains': ','.join(domains),
            'type': record_type
        }
        return await self._make_request(endpoint, params)


# Analysis and Intelligence Functions
def analyze_domain_reputation(domain_data: Dict) -> Dict:
    """Analyze domain reputation based on SecurityTrails data."""
    analysis = {
        'reputation_score': 50,  # Neutral starting point
        'risk_indicators': [],
        'trust_indicators': [],
        'threat_intelligence': [],
        'age_score': 0,
        'registration_quality': 0
    }
    
    # Analyze domain age and registration quality
    created_date = domain_data.get('createdDate')
    if created_date:
        try:
            created = datetime.fromisoformat(created_date.replace('Z', '+00:00'))
            age_days = (datetime.utcnow() - created).days
            
            # Older domains are generally more trustworthy
            if age_days > 365 * 5:  # 5+ years
                analysis['age_score'] = 25
                analysis['trust_indicators'].append('Domain age > 5 years')
            elif age_days > 365 * 2:  # 2+ years
                analysis['age_score'] = 15
                analysis['trust_indicators'].append('Domain age > 2 years')
            elif age_days > 365:  # 1+ year
                analysis['age_score'] = 5
            else:
                analysis['age_score'] = -10
                analysis['risk_indicators'].append('New domain (< 1 year)')
                
        except:
            pass
    
    # Analyze nameservers
    ns_records = domain_data.get('nserver', [])
    if len(ns_records) > 1:
        analysis['registration_quality'] += 10
        analysis['trust_indicators'].append('Multiple nameservers')
    
    # Analyze domain classification
    domain_tags = domain_data.get('domain_tags', [])
    for tag in domain_tags:
        if tag.get('name') == 'parked':
            analysis['risk_indicators'].append('Parked domain')
            analysis['reputation_score'] -= 20
        elif tag.get('name') == 'phishing':
            analysis['threat_intelligence'].append('Associated with phishing')
            analysis['reputation_score'] -= 30
        elif tag.get('name') == 'malware':
            analysis['threat_intelligence'].append('Associated with malware')
            analysis['reputation_score'] -= 40
    
    # Analyze WHOIS privacy
    whois_data = domain_data.get('whois', {})
    if whois_data:
        registrant_email = whois_data.get('registrantEmail', '').lower()
        if 'privacy' in registrant_email or 'redacted' in registrant_email:
            analysis['risk_indicators'].append('Privacy protection enabled')
            analysis['reputation_score'] -= 5
    
    # Calculate final reputation score
    total_score = (
        analysis['reputation_score'] + 
        analysis['age_score'] + 
        analysis['registration_quality']
    )
    analysis['final_score'] = max(0, min(100, total_score))
    
    # Determine risk level
    if analysis['final_score'] >= 80:
        analysis['risk_level'] = 'Low'
    elif analysis['final_score'] >= 60:
        analysis['risk_level'] = 'Medium'
    elif analysis['final_score'] >= 40:
        analysis['risk_level'] = 'High'
    else:
        analysis['risk_level'] = 'Critical'
    
    return analysis


def extract_domain_relationships(domain_data: Dict, ip_data: Dict = None) -> List[Dict]:
    """Extract relationships from domain data."""
    relationships = []
    
    # Domain to nameserver relationships
    ns_records = domain_data.get('nserver', [])
    for ns in ns_records:
        relationships.append({
            'type': 'uses_nameserver',
            'source': domain_data.get('domain'),
            'target': ns,
            'confidence': 0.9,
            'source_type': 'domain',
            'target_type': 'nameserver'
        })
    
    # Domain to IP relationships
    a_records = domain_data.get('a', [])
    for ip in a_records:
        relationships.append({
            'type': 'resolves_to',
            'source': domain_data.get('domain'),
            'target': ip,
            'confidence': 0.8,
            'source_type': 'domain',
            'target_type': 'ip'
        })
    
    # Domain to registrant relationships
    whois_data = domain_data.get('whois', {})
    if whois_data:
        registrant_email = whois_data.get('registrantEmail')
        if registrant_email:
            relationships.append({
                'type': 'registered_by',
                'source': domain_data.get('domain'),
                'target': registrant_email,
                'confidence': 0.9,
                'source_type': 'domain',
                'target_type': 'person'
            })
        
        registrant_org = whois_data.get('registrantOrganization')
        if registrant_org:
            relationships.append({
                'type': 'owned_by',
                'source': domain_data.get('domain'),
                'target': registrant_org,
                'confidence': 0.8,
                'source_type': 'domain',
                'target_type': 'organization'
            })
    
    return relationships


def identify_infrastructure_changes(dns_history: Dict) -> List[Dict]:
    """Identify infrastructure changes from DNS history."""
    changes = []
    
    # Analyze A record changes
    a_records = dns_history.get('a', [])
    if len(a_records) > 1:
        # Sort by date
        sorted_records = sorted(a_records, key=lambda x: x.get('first_seen', ''))
        
        for i in range(1, len(sorted_records)):
            current = sorted_records[i]
            previous = sorted_records[i-1]
            
            current_ips = set(current.get('values', []))
            previous_ips = set(previous.get('values', []))
            
            # Detect IP changes
            if current_ips != previous_ips:
                added_ips = current_ips - previous_ips
                removed_ips = previous_ips - current_ips
                
                if added_ips:
                    changes.append({
                        'type': 'ip_added',
                        'date': current.get('first_seen'),
                        'ips': list(added_ips),
                        'severity': 'medium'
                    })
                
                if removed_ips:
                    changes.append({
                        'type': 'ip_removed',
                        'date': current.get('first_seen'),
                        'ips': list(removed_ips),
                        'severity': 'low'
                    })
    
    # Analyze NS record changes
    ns_records = dns_history.get('ns', [])
    if len(ns_records) > 1:
        sorted_ns = sorted(ns_records, key=lambda x: x.get('first_seen', ''))
        
        for i in range(1, len(sorted_ns)):
            current = sorted_ns[i]
            previous = sorted_ns[i-1]
            
            current_ns = set(current.get('values', []))
            previous_ns = set(previous.get('values', []))
            
            if current_ns != previous_ns:
                added_ns = current_ns - previous_ns
                removed_ns = previous_ns - current_ns
                
                if added_ns:
                    changes.append({
                        'type': 'nameserver_added',
                        'date': current.get('first_seen'),
                        'nameservers': list(added_ns),
                        'severity': 'high'
                    })
                
                if removed_ns:
                    changes.append({
                        'type': 'nameserver_removed',
                        'date': current.get('first_seen'),
                        'nameservers': list(removed_ns),
                        'severity': 'medium'
                    })
    
    return changes