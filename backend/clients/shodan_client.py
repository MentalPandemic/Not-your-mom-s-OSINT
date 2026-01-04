"""
Shodan Internet Search API Client

This module provides client functionality for accessing Shodan internet search engine
for IP addresses, services, banners, and infrastructure intelligence.
"""

import asyncio
import aiohttp
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ShodanClientError(Exception):
    """Custom exception for Shodan client failures."""
    pass


class ShodanAPIClient:
    """Shodan API client for internet-wide search and intelligence."""
    
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
    
    async def _make_request(self, endpoint: str, params: Dict = None, method: str = 'GET') -> Dict:
        """Make a request to Shodan API."""
        if not self.session:
            raise ShodanClientError("Client session not initialized. Use async context manager.")
        
        url = f"{self.base_url}{endpoint}"
        params = params or {}
        params['key'] = self.api_key
        
        try:
            if method == 'GET':
                async with self.session.get(url, params=params) as response:
                    if response.status == 200:
                        return await response.json()
                    elif response.status == 401:
                        raise ShodanClientError("Invalid Shodan API key")
                    elif response.status == 403:
                        raise ShodanClientError("Access forbidden - check API permissions")
                    elif response.status == 429:
                        raise ShodanClientError("Rate limit exceeded")
                    else:
                        error_text = await response.text()
                        raise ShodanClientError(f"Shodan API request failed: {response.status} - {error_text}")
                        
        except aiohttp.ClientError as e:
            raise ShodanClientError(f"Network error: {str(e)}")
    
    # Account Information
    async def get_api_info(self) -> Dict:
        """Get API usage information."""
        endpoint = "/api-info"
        return await self._make_request(endpoint)
    
    # Host Information
    async def get_host_info(self, ip_address: str, history: bool = False) -> Dict:
        """Get comprehensive information about a host."""
        params = {'history': history}
        endpoint = f"/shodan/host/{ip_address}"
        return await self._make_request(endpoint, params)
    
    async def get_host_count(self, query: str) -> int:
        """Get number of results for a query."""
        params = {'query': query}
        endpoint = "/shodan/host/count"
        response = await self._make_request(endpoint, params)
        return response.get('total', 0)
    
    # Search Functions
    async def search_hosts(self, query: str, page: int = 1, limit: int = 100,
                          minify: bool = False, facets: List[str] = None) -> Dict:
        """Search for hosts matching a query."""
        params = {
            'query': query,
            'page': page,
            'limit': limit,
            'minify': minify
        }
        
        if facets:
            params['facets'] = ','.join(facets)
        
        endpoint = "/shodan/host/search"
        return await self._make_request(endpoint, params)
    
    # DNS Functions
    async def dns_lookup(self, hostnames: List[str]) -> Dict:
        """Perform DNS lookup for hostnames."""
        params = {'hostnames': ','.join(hostnames)}
        endpoint = "/dns/lookup"
        return await self._make_request(endpoint, params)
    
    async def dns_reverse(self, ips: List[str]) -> Dict:
        """Perform reverse DNS lookup for IP addresses."""
        params = {'ips': ','.join(ips)}
        endpoint = "/dns/reverse"
        return await self._make_request(endpoint, params)
    
    # Network Alerts
    async def get_alerts(self) -> List[Dict]:
        """Get all network alerts."""
        endpoint = "/shodan/alerts"
        return await self._make_request(endpoint)
    
    async def create_alert(self, name: str, ip_range: str) -> Dict:
        """Create a network alert."""
        params = {'name': name, 'ip': ip_range}
        endpoint = "/shodan/alerts"
        return await self._make_request(endpoint, params, method='POST')
    
    # Data Exports
    async def create_export(self, type: str, query: str, filters: List[str] = None) -> Dict:
        """Create a data export."""
        params = {
            'type': type,
            'query': query
        }
        
        if filters:
            params['filters'] = ','.join(filters)
        
        endpoint = "/exports/create"
        return await self._make_request(endpoint, params, method='POST')
    
    async def get_export_info(self, export_id: str) -> Dict:
        """Get information about a data export."""
        endpoint = f"/exports/info/{export_id}"
        return await self._make_request(endpoint)
    
    # Security Scanner
    async def scan_network(self, ips: str) -> Dict:
        """Request Shodan to scan an IP or subnet."""
        params = {'ips': ips}
        endpoint = "/shodan/scan"
        return await self._make_request(endpoint, params, method='POST')
    
    async def get_scan_status(self, scan_id: str) -> Dict:
        """Get status of a scan request."""
        endpoint = f"/shodan/scan/{scan_id}"
        return await self._make_request(endpoint)
    
    # Helper Methods for Common Searches
    async def search_by_domain(self, domain: str) -> Dict:
        """Search for hosts related to a domain."""
        query = f'hostname:"{domain}"'
        return await self.search_hosts(query)
    
    async def search_by_organization(self, organization: str) -> Dict:
        """Search for hosts by organization."""
        query = f'org:"{organization}"'
        return await self.search_hosts(query)
    
    async def search_by_port(self, port: int) -> Dict:
        """Search for hosts with a specific port open."""
        query = f'port:{port}'
        return await self.search_hosts(query)
    
    async def search_by_product(self, product: str) -> Dict:
        """Search for hosts running specific software."""
        query = f'product:"{product}"'
        return await self.search_hosts(query)
    
    async def search_by_version(self, product: str, version: str) -> Dict:
        """Search for hosts running a specific version of software."""
        query = f'product:"{product}" version:"{version}"'
        return await self.search_hosts(query)
    
    async def search_by_os(self, operating_system: str) -> Dict:
        """Search for hosts by operating system."""
        query = f'os:"{operating_system}"'
        return await self.search_hosts(query)
    
    async def search_by_country(self, country_code: str) -> Dict:
        """Search for hosts in a specific country."""
        query = f'country:"{country_code}"'
        return await self.search_hosts(query)
    
    async def search_by_asn(self, asn: str) -> Dict:
        """Search for hosts in a specific ASN."""
        query = f'asn:{asn}'
        return await self.search_hosts(query)
    
    async def search_web_services(self) -> Dict:
        """Search for common web services."""
        query = 'http.title:"Apache" OR http.title:"nginx" OR http.title:"IIS" OR http.title:"lighttpd"'
        return await self.search_hosts(query)
    
    async def search_databases(self) -> Dict:
        """Search for exposed database services."""
        query = 'port:3306 OR port:5432 OR port:27017 OR port:6379 OR port:1521 OR port:1433'
        return await self.search_hosts(query)
    
    async def search_ftp_servers(self) -> Dict:
        """Search for FTP servers."""
        query = 'port:21'
        return await self.search_hosts(query)
    
    async def search_ssh_servers(self) -> Dict:
        """Search for SSH servers."""
        query = 'port:22'
        return await self.search_hosts(query)
    
    async def search_telnet_servers(self) -> Dict:
        """Search for Telnet servers."""
        query = 'port:23'
        return await self.search_hosts(query)
    
    async def search_voip_systems(self) -> Dict:
        """Search for VoIP systems."""
        query = 'port:5060 OR product:"Asterisk" OR product:"FreeSWITCH"'
        return await self.search_hosts(query)
    
    async def search_cameras(self) -> Dict:
        """Search for IP cameras and CCTV systems."""
        query = 'product:"DVR" OR product:"NVR" OR product:"IP Camera" OR "camera"'
        return await self.search_hosts(query)
    
    async def search_ics_scada(self) -> Dict:
        """Search for Industrial Control Systems and SCADA."""
        query = 'tag:ics OR tag:scada OR port:102 OR port:502 OR port:789 OR port:2404'
        return await self.search_hosts(query)
    
    async def search_iot_devices(self) -> Dict:
        """Search for Internet of Things devices."""
        query = 'tag:iot OR product:"RTSP" OR port:554 OR port:23'
        return await self.search_hosts(query)


# Analysis Functions
def analyze_host_security(host_info: Dict) -> Dict:
    """Analyze host security posture from Shodan data."""
    analysis = {
        'security_score': 100,
        'vulnerabilities': [],
        'open_ports': [],
        'services': [],
        'recommendations': []
    }
    
    # Extract data
    ip = host_info.get('ip')
    ports = host_info.get('ports', [])
    protocols = host_info.get('protocols', [])
    data = host_info.get('data', [])
    
    # Analyze open ports
    analysis['open_ports'] = ports
    
    # High-risk ports
    high_risk_ports = {
        21: 'FTP',
        23: 'Telnet', 
        135: 'RPC',
        139: 'NetBIOS',
        445: 'SMB',
        1433: 'MSSQL',
        3306: 'MySQL',
        3389: 'RDP',
        5432: 'PostgreSQL',
        5900: 'VNC'
    }
    
    for port in ports:
        if port in high_risk_ports:
            service_name = high_risk_ports[port]
            analysis['vulnerabilities'].append({
                'type': 'high_risk_port',
                'port': port,
                'service': service_name,
                'severity': 'high',
                'description': f'High-risk service {service_name} exposed on port {port}'
            })
            analysis['security_score'] -= 15
    
    # Analyze services
    for service_data in data:
        if isinstance(service_data, dict):
            service = service_data.get('service', {})
            product = service.get('product', '')
            version = service.get('version', '')
            port = service_data.get('port', 0)
            
            analysis['services'].append({
                'port': port,
                'product': product,
                'version': version,
                'banner': service_data.get('data', '')
            })
            
            # Check for outdated services
            if version:
                # Common outdated service patterns
                if 'OpenSSH_6.6' in version:
                    analysis['vulnerabilities'].append({
                        'type': 'outdated_service',
                        'service': 'OpenSSH',
                        'version': version,
                        'port': port,
                        'severity': 'medium',
                        'description': 'Outdated OpenSSH version detected'
                    })
                    analysis['security_score'] -= 10
    
    # Check for default credentials indicators
    for service_data in data:
        banner = service_data.get('data', '').lower()
        if any(indicator in banner for indicator in ['default', 'admin', 'root']):
            analysis['vulnerabilities'].append({
                'type': 'potential_default_credentials',
                'port': service_data.get('port'),
                'severity': 'medium',
                'description': 'Potential default credentials indicator detected'
            })
            analysis['security_score'] -= 5
    
    # Calculate final security score
    analysis['security_score'] = max(0, min(100, analysis['security_score']))
    
    # Determine security level
    if analysis['security_score'] >= 80:
        analysis['security_level'] = 'Low Risk'
    elif analysis['security_score'] >= 60:
        analysis['security_level'] = 'Medium Risk'
    else:
        analysis['security_level'] = 'High Risk'
    
    # Generate recommendations
    if len([v for v in analysis['vulnerabilities'] if v.get('severity') == 'high']) > 0:
        analysis['recommendations'].append('Immediately secure or disable high-risk services')
    
    if len(analysis['open_ports']) > 20:
        analysis['recommendations'].append('Reduce the number of open ports to minimize attack surface')
    
    if analysis['security_score'] < 60:
        analysis['recommendations'].append('Conduct comprehensive security assessment')
    
    return analysis


def extract_host_fingerprint(host_info: Dict) -> Dict:
    """Extract a unique fingerprint for a host."""
    fingerprint = {
        'ip': host_info.get('ip'),
        'ports': set(host_info.get('ports', [])),
        'protocols': set(host_info.get('protocols', [])),
        'services': {},
        'certificates': [],
        'banners': []
    }
    
    # Extract service information
    data = host_info.get('data', [])
    for service_data in data:
        if isinstance(service_data, dict):
            port = service_data.get('port')
            service = service_data.get('service', {})
            product = service.get('product', '')
            version = service.get('version', '')
            
            if product:
                service_key = f"{product}{' ' + version if version else ''}"
                if service_key not in fingerprint['services']:
                    fingerprint['services'][service_key] = []
                fingerprint['services'][service_key].append(port)
            
            # Extract banners
            banner = service_data.get('data', '')
            if banner:
                fingerprint['banners'].append(banner[:200])  # Limit banner length
            
            # Extract certificates
            ssl_info = service_data.get('ssl', {})
            if ssl_info:
                cert_info = {
                    'issuer': ssl_info.get('issuer', []),
                    'subject': ssl_info.get('subject', []),
                    'version': ssl_info.get('version')
                }
                fingerprint['certificates'].append(cert_info)
    
    # Convert sets to lists for JSON serialization
    fingerprint['ports'] = list(fingerprint['ports'])
    fingerprint['protocols'] = list(fingerprint['protocols'])
    
    return fingerprint


def identify_similar_hosts(host_list: List[Dict]) -> List[Dict]:
    """Identify hosts with similar configurations."""
    similarities = []
    
    # Group hosts by similar port sets
    port_groups = {}
    for host in host_list:
        ports = frozenset(host.get('ports', []))
        if ports not in port_groups:
            port_groups[ports] = []
        port_groups[ports].append(host)
    
    # Create similarity groups for hosts with similar port patterns
    for ports, hosts in port_groups.items():
        if len(hosts) > 1:
            similarities.append({
                'type': 'similar_ports',
                'members': [host.get('ip') for host in hosts],
                'common_ports': list(ports),
                'count': len(hosts),
                'confidence': min(0.9, len(hosts) / 10)  # Higher confidence for more similar hosts
            })
    
    # Group by organization
    org_groups = {}
    for host in host_list:
        org = host.get('org', 'Unknown')
        if org not in org_groups:
            org_groups[org] = []
        org_groups[org].append(host)
    
    for org, hosts in org_groups.items():
        if len(hosts) > 1 and org != 'Unknown':
            similarities.append({
                'type': 'same_organization',
                'members': [host.get('ip') for host in hosts],
                'organization': org,
                'count': len(hosts),
                'confidence': 0.8
            })
    
    return similarities


def calculate_host_risk_score(host_info: Dict) -> Dict:
    """Calculate comprehensive risk score for a host."""
    risk_analysis = {
        'overall_score': 0,
        'risk_factors': [],
        'risk_level': 'Unknown',
        'threat_indicators': []
    }
    
    # Initialize score at 100 (lowest risk)
    score = 100
    
    # Analyze port exposure
    ports = host_info.get('ports', [])
    risky_ports = [21, 23, 135, 139, 445, 1433, 3306, 3389, 5432, 5900, 8080]
    
    exposed_risky_ports = set(ports) & set(risky_ports)
    if exposed_risky_ports:
        score -= len(exposed_risky_ports) * 10
        risk_analysis['risk_factors'].append({
            'type': 'risky_ports',
            'ports': list(exposed_risky_ports),
            'impact': 'medium'
        })
    
    # Analyze service types
    data = host_info.get('data', [])
    for service_data in data:
        if isinstance(service_data, dict):
            service = service_data.get('service', {})
            product = service.get('product', '').lower()
            
            # High-risk services
            if 'telnet' in product:
                score -= 20
                risk_analysis['risk_factors'].append({
                    'type': 'telnet_service',
                    'product': product,
                    'impact': 'high'
                })
            elif 'ftp' in product and 'sftp' not in product:
                score -= 15
                risk_analysis['risk_factors'].append({
                    'type': 'ftp_service',
                    'product': product,
                    'impact': 'medium'
                })
            elif 'rdp' in product:
                score -= 10
                risk_analysis['risk_factors'].append({
                    'type': 'rdp_service',
                    'product': product,
                    'impact': 'medium'
                })
            elif 'vnc' in product:
                score -= 15
                risk_analysis['risk_factors'].append({
                    'type': 'vnc_service',
                    'product': product,
                    'impact': 'medium'
                })
    
    # Analyze banner information
    for service_data in data:
        banner = service_data.get('data', '').lower()
        if 'default' in banner or 'admin' in banner:
            score -= 10
            risk_analysis['risk_factors'].append({
                'type': 'default_credentials_indicator',
                'impact': 'high'
            })
    
    # Geographic risk (example - would need geo database)
    # This is a simplified example
    country = host_info.get('location', {}).get('country_name', '')
    high_risk_countries = ['China', 'Russia', 'North Korea']
    if country in high_risk_countries:
        score -= 5
        risk_analysis['risk_factors'].append({
            'type': 'high_risk_geography',
            'country': country,
            'impact': 'low'
        })
    
    # Final scoring
    risk_analysis['overall_score'] = max(0, min(100, score))
    
    # Determine risk level
    if risk_analysis['overall_score'] >= 80:
        risk_analysis['risk_level'] = 'Low'
    elif risk_analysis['overall_score'] >= 60:
        risk_analysis['risk_level'] = 'Medium'
    elif risk_analysis['overall_score'] >= 40:
        risk_analysis['risk_level'] = 'High'
    else:
        risk_analysis['risk_level'] = 'Critical'
    
    return risk_analysis