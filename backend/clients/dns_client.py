"""
DNS API Client

This module provides DNS query functionality and integration with external DNS intelligence services.
"""

import asyncio
import dns.resolver
import dns.zone
import dns.query
import dns.rdatatype
import aiohttp
import json
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class DNSClientError(Exception):
    """Custom exception for DNS client failures."""
    pass


class DNSPythonClient:
    """DNS client using dnspython library."""
    
    def __init__(self, nameservers: List[str] = None, timeout: int = 10):
        self.resolver = dns.resolver.Resolver()
        self.resolver.timeout = timeout
        self.resolver.lifetime = timeout * 2
        
        if nameservers:
            self.resolver.nameservers = nameservers
        
        # Common public DNS servers
        self.public_dns_servers = {
            'google': ['8.8.8.8', '8.8.4.4'],
            'cloudflare': ['1.1.1.1', '1.0.0.1'],
            'quad9': ['9.9.9.9', '149.112.112.112'],
            'opendns': ['208.67.222.222', '208.67.220.220']
        }
    
    async def query(self, name: str, record_type: str, nameserver: str = None) -> List[Dict]:
        """Perform a DNS query."""
        try:
            if nameserver:
                # Use specific nameserver
                resolver = dns.resolver.Resolver()
                resolver.nameservers = [nameserver]
                resolver.timeout = self.resolver.timeout
            else:
                resolver = self.resolver
            
            answers = resolver.resolve(name, record_type)
            results = []
            
            for rdata in answers:
                result = {
                    'name': name,
                    'type': record_type,
                    'value': str(rdata),
                    'ttl': answers.rrset.ttl
                }
                
                # Add type-specific data
                if record_type == 'MX':
                    result['priority'] = rdata.preference
                    result['exchange'] = str(rdata.exchange)
                elif record_type == 'SRV':
                    result['priority'] = rdata.priority
                    result['weight'] = rdata.weight
                    result['port'] = rdata.port
                    result['target'] = str(rdata.target)
                elif record_type == 'TXT':
                    result['strings'] = [str(s) for s in rdata.strings]
                
                results.append(result)
            
            return results
            
        except dns.resolver.NXDOMAIN:
            logger.warning(f"Domain {name} does not exist")
            return []
        except dns.resolver.NoAnswer:
            logger.info(f"No {record_type} records found for {name}")
            return []
        except Exception as e:
            logger.error(f"DNS query failed for {name} {record_type}: {str(e)}")
            return []
    
    async def get_a_records(self, name: str, nameserver: str = None) -> List[Dict]:
        """Get A records."""
        return await self.query(name, 'A', nameserver)
    
    async def get_aaaa_records(self, name: str, nameserver: str = None) -> List[Dict]:
        """Get AAAA records."""
        return await self.query(name, 'AAAA', nameserver)
    
    async def get_mx_records(self, name: str, nameserver: str = None) -> List[Dict]:
        """Get MX records."""
        return await self.query(name, 'MX', nameserver)
    
    async def get_txt_records(self, name: str, nameserver: str = None) -> List[Dict]:
        """Get TXT records."""
        return await self.query(name, 'TXT', nameserver)
    
    async def get_cname_records(self, name: str, nameserver: str = None) -> List[Dict]:
        """Get CNAME records."""
        return await self.query(name, 'CNAME', nameserver)
    
    async def get_ns_records(self, name: str, nameserver: str = None) -> List[Dict]:
        """Get NS records."""
        return await self.query(name, 'NS', nameserver)
    
    async def get_srv_records(self, name: str, nameserver: str = None) -> List[Dict]:
        """Get SRV records."""
        return await self.query(name, 'SRV', nameserver)
    
    async def get_all_records(self, name: str, nameserver: str = None) -> Dict[str, List[Dict]]:
        """Get all common DNS records."""
        record_types = ['A', 'AAAA', 'MX', 'TXT', 'CNAME', 'NS', 'SRV']
        results = {}
        
        # Query all record types concurrently
        tasks = [self.query(name, record_type, nameserver) for record_type in record_types]
        answers = await asyncio.gather(*tasks, return_exceptions=True)
        
        for i, record_type in enumerate(record_types):
            if isinstance(answers[i], list):
                results[f"{record_type.lower()}_records"] = answers[i]
            else:
                results[f"{record_type.lower()}_records"] = []
        
        return results
    
    async def check_dns_propagation(self, domain: str) -> Dict:
        """Check DNS propagation across different resolvers."""
        propagation_results = {
            'domain': domain,
            'resolvers': {},
            'consistency': True,
            'different_results': []
        }
        
        # Test with different DNS servers
        for provider, servers in self.public_dns_servers.items():
            try:
                resolver = dns.resolver.Resolver()
                resolver.nameservers = servers
                resolver.timeout = 5
                
                answers = resolver.resolve(domain, 'A')
                ips = [str(rdata) for rdata in answers]
                
                propagation_results['resolvers'][provider] = {
                    'servers': servers,
                    'a_records': ips,
                    'consistent': True
                }
                
            except Exception as e:
                propagation_results['resolvers'][provider] = {
                    'servers': servers,
                    'error': str(e),
                    'consistent': False
                }
                propagation_results['consistency'] = False
        
        # Check if all resolvers return the same results
        all_results = []
        for provider_data in propagation_results['resolvers'].values():
            if 'a_records' in provider_data:
                all_results.append(tuple(sorted(provider_data['a_records'])))
        
        if len(set(all_results)) > 1:
            propagation_results['consistency'] = False
            propagation_results['different_results'] = list(set(all_results))
        
        return propagation_results
    
    async def zone_transfer(self, domain: str, nameserver: str = None) -> Dict:
        """Attempt zone transfer (AXFR)."""
        try:
            if not nameserver:
                # Get NS records first
                ns_records = await self.get_ns_records(domain)
                if not ns_records:
                    return {'success': False, 'error': 'No NS records found'}
                
                nameserver = ns_records[0]['value']
            
            # Attempt zone transfer
            zone = dns.zone.from_xfr(dns.query.xfr(nameserver, domain))
            
            records = []
            for name, node in zone.nodes.items():
                for rdataset in node.rdatasets:
                    for rdata in rdataset:
                        records.append({
                            'name': str(name),
                            'type': dns.rdatatype.to_text(rdataset.rdtype),
                            'value': str(rdata),
                            'ttl': rdataset.ttl
                        })
            
            return {
                'success': True,
                'nameserver': nameserver,
                'records': records,
                'record_count': len(records)
            }
            
        except Exception as e:
            return {
                'success': False,
                'nameserver': nameserver,
                'error': str(e)
            }


class SecurityTrailsDNSClient:
    """SecurityTrails DNS intelligence client."""
    
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
    
    async def _make_request(self, endpoint: str, params: Dict = None) -> Dict:
        """Make a request to SecurityTrails API."""
        if not self.session:
            raise DNSClientError("Client session not initialized. Use async context manager.")
        
        url = f"{self.base_url}{endpoint}"
        headers = {
            'Accept': 'application/json',
            'API-Key': self.api_key
        }
        
        try:
            async with self.session.get(url, params=params, headers=headers) as response:
                if response.status == 200:
                    return await response.json()
                elif response.status == 429:
                    raise DNSClientError("Rate limit exceeded")
                else:
                    error_text = await response.text()
                    raise DNSClientError(f"SecurityTrails API request failed: {response.status} - {error_text}")
                    
        except aiohttp.ClientError as e:
            raise DNSClientError(f"Network error: {str(e)}")
    
    async def get_dns_history(self, domain: str, record_type: str = 'A') -> List[Dict]:
        """Get DNS history for a domain."""
        endpoint = f"/domain/{domain}/dns/{record_type.lower()}"
        response = await self._make_request(endpoint)
        return response.get('records', [])
    
    async def get_subdomain_history(self, domain: str, subdomain: str) -> List[Dict]:
        """Get DNS history for a subdomain."""
        endpoint = f"/domain/{domain}/subdomains/{subdomain}/dns/a"
        response = await self._make_request(endpoint)
        return response.get('records', [])
    
    async def search_dns_by_ip(self, ip_address: str) -> List[str]:
        """Search for domains by IP address."""
        endpoint = f"/ips/{ip_address}/domains"
        response = await self._make_request(endpoint)
        return response.get('domains', [])
    
    async def get_dns_data_for_domain(self, domain: str) -> Dict:
        """Get complete DNS data for a domain."""
        # Get all record types
        record_types = ['A', 'AAAA', 'MX', 'TXT', 'CNAME', 'NS']
        dns_data = {'domain': domain, 'records': {}}
        
        for record_type in record_types:
            try:
                endpoint = f"/domain/{domain}/dns/{record_type.lower()}"
                response = await self._make_request(endpoint)
                dns_data['records'][record_type.lower()] = response.get('records', [])
            except Exception as e:
                logger.warning(f"Failed to get {record_type} records for {domain}: {str(e)}")
                dns_data['records'][record_type.lower()] = []
        
        return dns_data
    
    async def get_pdns_data(self, domain: str, record_type: str = 'A') -> List[Dict]:
        """Get passive DNS data."""
        endpoint = f"/domain/{domain}/pdns/{record_type.lower()}"
        response = await self._make_request(endpoint)
        return response.get('records', [])


class ShodanDNSClient:
    """Shodan DNS intelligence client."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.shodan.io"
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def _make_request(self, endpoint: str, params: Dict = None) -> Dict:
        """Make a request to Shodan API."""
        if not self.session:
            raise DNSClientError("Client session not initialized. Use async context manager.")
        
        url = f"{self.base_url}{endpoint}"
        params = params or {}
        params['key'] = self.api_key
        
        try:
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    return await response.json()
                elif response.status == 429:
                    raise DNSClientError("Rate limit exceeded")
                else:
                    error_text = await response.text()
                    raise DNSClientError(f"Shodan API request failed: {response.status} - {error_text}")
                    
        except aiohttp.ClientError as e:
            raise DNSClientError(f"Network error: {str(e)}")
    
    async def dns_lookup(self, domain: str) -> Dict:
        """Perform DNS lookup via Shodan."""
        endpoint = "/dns/lookup"
        params = {'hostnames': domain}
        return await self._make_request(endpoint, params)
    
    async def reverse_dns(self, ip_address: str) -> List[str]:
        """Perform reverse DNS lookup."""
        endpoint = "/dns/reverse"
        params = {'ips': ip_address}
        response = await self._make_request(endpoint, params)
        return response.get('hostnames', [])
    
    async def search_by_dns(self, query: str) -> Dict:
        """Search for hosts by DNS query."""
        endpoint = "/shodan/host/search"
        params = {'query': query}
        return await self._make_request(endpoint, params)


# Utility functions for DNS analysis
def analyze_dns_security(dns_data: Dict) -> Dict:
    """Analyze DNS configuration for security issues."""
    analysis = {
        'has_spf': False,
        'has_dkim': False,
        'has_dmarc': False,
        'has_dnssec': False,
        'security_score': 0,
        'issues': [],
        'recommendations': []
    }
    
    # Check TXT records for SPF, DKIM, DMARC
    txt_records = dns_data.get('records', {}).get('txt', [])
    for record in txt_records:
        value = record.get('value', '').lower()
        if 'v=spf1' in value:
            analysis['has_spf'] = True
            analysis['security_score'] += 25
        if 'dkim' in value:
            analysis['has_dkim'] = True
            analysis['security_score'] += 25
        if 'dmarc' in value:
            analysis['has_dmarc'] = True
            analysis['security_score'] += 25
    
    # Check NS records for DNSSEC
    ns_records = dns_data.get('records', {}).get('ns', [])
    if len(ns_records) > 1:
        analysis['security_score'] += 10  # Multiple nameservers is good
    
    # Generate recommendations
    if not analysis['has_spf']:
        analysis['recommendations'].append('Add SPF record')
    if not analysis['has_dkim']:
        analysis['recommendations'].append('Add DKIM record')
    if not analysis['has_dmarc']:
        analysis['recommendations'].append('Add DMARC record')
    
    # Calculate final security rating
    if analysis['security_score'] >= 75:
        analysis['security_rating'] = 'Excellent'
    elif analysis['security_score'] >= 50:
        analysis['security_rating'] = 'Good'
    elif analysis['security_score'] >= 25:
        analysis['security_rating'] = 'Fair'
    else:
        analysis['security_rating'] = 'Poor'
    
    return analysis


def detect_dns_takeover_risks(dns_data: Dict) -> List[Dict]:
    """Detect potential DNS takeover risks."""
    risks = []
    
    # Check CNAME records
    cname_records = dns_data.get('records', {}).get('cname', [])
    for record in cname_records:
        target = record.get('value', '').lower()
        name = record.get('name', '')
        
        # Check for common takeover patterns
        takeover_patterns = [
            'github.io', 'herokuapp.com', 'amazonaws.com', 'cloudfront.net',
            'azure.com', 'googleusercontent.com', 'wordpress.com', 'tumblr.com'
        ]
        
        for pattern in takeover_patterns:
            if pattern in target:
                risks.append({
                    'type': 'cname_takeover_risk',
                    'name': name,
                    'target': target,
                    'pattern': pattern,
                    'severity': 'medium',
                    'description': f'CNAME points to {pattern} - potential takeover target'
                })
                break
    
    return risks