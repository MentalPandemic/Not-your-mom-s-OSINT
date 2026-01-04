"""
Infrastructure Mapping Module

This module provides comprehensive infrastructure mapping capabilities including IP-to-domain mapping,
service identification, ASN analysis, and geolocation services.
"""

import asyncio
import socket
import ipaddress
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple, Any
from urllib.parse import urlparse
import aiohttp
import logging
import dns.resolver

logger = logging.getLogger(__name__)


class InfrastructureMappingError(Exception):
    """Custom exception for infrastructure mapping failures."""
    pass


class IPAddressInfo:
    """IP address information container."""
    
    def __init__(self):
        self.ip_address: Optional[str] = None
        self.isp: Optional[str] = None
        self.organization: Optional[str] = None
        self.asn: Optional[str] = None
        self.asn_description: Optional[str] = None
        self.country: Optional[str] = None
        self.city: Optional[str] = None
        self.region: Optional[str] = None
        self.latitude: Optional[float] = None
        self.longitude: Optional[float] = None
        self.netrange: Optional[str] = None
        self.netmask: Optional[str] = None
        self.is_public: Optional[bool] = None
        self.is_private: Optional[bool] = None
        self.is_reserved: Optional[bool] = None
        self.hosting_provider: Optional[str] = None
        self.reverse_dns: Optional[str] = None
        
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
            'region': self.region,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'netrange': self.netrange,
            'netmask': self.netmask,
            'is_public': self.is_public,
            'is_private': self.is_private,
            'is_reserved': self.is_reserved,
            'hosting_provider': self.hosting_provider,
            'reverse_dns': self.reverse_dns
        }


class ServiceInfo:
    """Service information container."""
    
    def __init__(self):
        self.host: Optional[str] = None
        self.port: Optional[int] = None
        self.protocol: Optional[str] = None
        self.service_name: Optional[str] = None
        self.version: Optional[str] = None
        self.banner: Optional[str] = None
        self.is_open: Optional[bool] = None
        self.response_time: Optional[float] = None
        self.technologies: List[str] = []
        
    def to_dict(self) -> Dict:
        """Convert to dictionary format."""
        return {
            'host': self.host,
            'port': self.port,
            'protocol': self.protocol,
            'service_name': self.service_name,
            'version': self.version,
            'banner': self.banner,
            'is_open': self.is_open,
            'response_time': self.response_time,
            'technologies': self.technologies
        }


class ASNInfo:
    """Autonomous System Number information container."""
    
    def __init__(self):
        self.asn: Optional[str] = None
        self.name: Optional[str] = None
        self.description: Optional[str] = None
        self.country: Optional[str] = None
        self.rir: Optional[str] = None
        self.allocation_date: Optional[datetime] = None
        self.ip_ranges: List[str] = []
        self.organization: Optional[str] = None
        self.isp: Optional[str] = None
        self.is_peering_db: bool = False
        
    def to_dict(self) -> Dict:
        """Convert to dictionary format."""
        return {
            'asn': self.asn,
            'name': self.name,
            'description': self.description,
            'country': self.country,
            'rir': self.rir,
            'allocation_date': self.allocation_date.isoformat() if self.allocation_date else None,
            'ip_ranges': self.ip_ranges,
            'organization': self.organization,
            'isp': self.isp,
            'is_peering_db': self.is_peering_db
        }


class InfrastructureMapping:
    """Main infrastructure mapping service."""
    
    def __init__(self):
        # Common ports to scan
        self.common_ports = [21, 22, 23, 25, 53, 80, 110, 135, 139, 143, 443, 445, 993, 995, 1723, 3306, 3389, 5432, 5900, 8080, 8443]
        
        # Service detection signatures
        self.service_signatures = {
            21: {
                'pattern': r'^220.*FTP',
                'service': 'FTP',
                'default_version': 'Unknown'
            },
            22: {
                'pattern': r'^SSH-.*',
                'service': 'SSH',
                'default_version': 'OpenSSH'
            },
            23: {
                'pattern': r'.*',
                'service': 'Telnet',
                'default_version': 'Unknown'
            },
            25: {
                'pattern': r'^220.*ESMTP|^220.*SMTP',
                'service': 'SMTP',
                'default_version': 'Unknown'
            },
            53: {
                'pattern': r'.*',
                'service': 'DNS',
                'default_version': 'Unknown'
            },
            80: {
                'pattern': r'HTTP.*|Server:.*',
                'service': 'HTTP',
                'default_version': 'Unknown'
            },
            110: {
                'pattern': r'^\+OK.*POP3',
                'service': 'POP3',
                'default_version': 'Unknown'
            },
            135: {
                'pattern': r'.*',
                'service': 'Microsoft RPC',
                'default_version': 'Unknown'
            },
            139: {
                'pattern': r'.*',
                'service': 'NetBIOS Session Service',
                'default_version': 'Unknown'
            },
            443: {
                'pattern': r'HTTP.*|Server:.*',
                'service': 'HTTPS',
                'default_version': 'Unknown'
            },
            445: {
                'pattern': r'.*',
                'service': 'Microsoft Directory Services',
                'default_version': 'Unknown'
            },
            993: {
                'pattern':'.*',
                'service': 'IMAPS',
                'default_version': 'Unknown'
            },
            995: {
                'pattern': r'^\+OK.*POP3S',
                'service': 'POP3S',
                'default_version': 'Unknown'
            },
            3306: {
                'pattern': r'.*mysql.*',
                'service': 'MySQL',
                'default_version': 'MySQL'
            },
            3389: {
                'pattern': r'.*',
                'service': 'Remote Desktop Protocol',
                'default_version': 'RDP'
            },
            5432: {
                'pattern': r'.*PostgreSQL.*',
                'service': 'PostgreSQL',
                'default_version': 'PostgreSQL'
            },
            8080: {
                'pattern': r'HTTP.*|Server:.*',
                'service': 'HTTP-Alt',
                'default_version': 'Unknown'
            },
            8443: {
                'pattern': r'HTTP.*|Server:.*',
                'service': 'HTTPS-Alt',
                'default_version': 'Unknown'
            }
        }
        
        # CDN detection patterns
        self.cdn_patterns = {
            'Cloudflare': {
                'headers': ['cf-ray', 'cf-cache-status', 'cf-h2-upstream'],
                'server_header': 'cloudflare'
            },
            'Akamai': {
                'headers': ['x-akamai-request-id', 'x-akamai-cache-status'],
                'server_header': 'akamai'
            },
            'AWS CloudFront': {
                'headers': ['x-amz-cf-id', 'x-amz-cf-pop'],
                'server_header': 'cloudfront'
            },
            'Fastly': {
                'headers': ['fastly-debug', 'x-served-by'],
                'server_header': 'fastly'
            },
            'MaxCDN': {
                'headers': ['x-served-by', 'x-cache'],
                'server_header': 'NetDNA'
            }
        }
    
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
    
    async def get_ip_info(self, ip_address: str) -> IPAddressInfo:
        """Get detailed information about an IP address."""
        try:
            # Validate IP address
            ip = ipaddress.ip_address(ip_address)
            
            ip_info = IPAddressInfo()
            ip_info.ip_address = str(ip)
            ip_info.is_public = ip.is_global
            ip_info.is_private = ip.is_private
            ip_info.is_reserved = ip.is_reserved
            
            # Try reverse DNS lookup
            try:
                hostname, _, _ = await asyncio.get_event_loop().run_in_executor(
                    None, socket.gethostbyaddr, ip_address
                )
                ip_info.reverse_dns = hostname
            except:
                pass
            
            # Get network information
            if hasattr(ip, 'packed'):
                # For IPv4, get network info
                if ip.version == 4:
                    network = ipaddress.ip_network(f"{ip_address}/24", strict=False)
                    ip_info.netrange = str(network)
                    ip_info.netmask = str(network.netmask)
            
            # This would typically use APIs like IPinfo, MaxMind, etc.
            # For now, return basic information
            logger.info(f"Getting IP info for {ip_address} (requires external API for full details)")
            
            return ip_info
            
        except ValueError as e:
            logger.error(f"Invalid IP address: {ip_address}")
            raise InfrastructureMappingError(f"Invalid IP address: {ip_address}")
        except Exception as e:
            logger.error(f"Error getting IP info for {ip_address}: {str(e)}")
            raise InfrastructureMappingError(f"Failed to get IP info: {str(e)}")
    
    async def port_scan(self, host: str, ports: List[int] = None, timeout: float = 2.0) -> List[ServiceInfo]:
        """Perform port scanning on a host."""
        if ports is None:
            ports = self.common_ports
        
        services = []
        
        async def scan_port(port: int) -> Optional[ServiceInfo]:
            try:
                start_time = asyncio.get_event_loop().time()
                
                # Try to connect to the port
                reader, writer = await asyncio.wait_for(
                    asyncio.open_connection(host, port),
                    timeout=timeout
                )
                
                end_time = asyncio.get_event_loop().time()
                response_time = (end_time - start_time) * 1000  # Convert to milliseconds
                
                # Create service info
                service_info = ServiceInfo()
                service_info.host = host
                service_info.port = port
                service_info.protocol = 'tcp'
                service_info.is_open = True
                service_info.response_time = round(response_time, 2)
                
                # Try to get service banner
                try:
                    banner = await asyncio.wait_for(reader.read(1024), timeout=1.0)
                    if banner:
                        service_info.banner = banner.decode('utf-8', errors='ignore').strip()
                        
                        # Try to identify service
                        service_info.service_name, service_info.version = self.identify_service(port, service_info.banner)
                except:
                    pass
                
                # If no banner identification, use default
                if not service_info.service_name:
                    service_info.service_name, service_info.version = self.get_default_service(port)
                
                writer.close()
                await writer.wait_closed()
                
                return service_info
                
            except asyncio.TimeoutError:
                return None
            except ConnectionRefusedError:
                return None
            except Exception as e:
                logger.debug(f"Error scanning port {port} on {host}: {str(e)}")
                return None
        
        # Scan ports concurrently
        semaphore = asyncio.Semaphore(50)
        
        async def scan_port_limited(port: int):
            async with semaphore:
                return await scan_port(port)
        
        tasks = [scan_port_limited(port) for port in ports]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter successful results
        for result in results:
            if isinstance(result, ServiceInfo):
                services.append(result)
        
        return services
    
    def identify_service(self, port: int, banner: str) -> Tuple[str, Optional[str]]:
        """Identify service from banner."""
        if port in self.service_signatures:
            signature = self.service_signatures[port]
            if re.search(signature['pattern'], banner, re.IGNORECASE):
                return signature['service'], signature['default_version']
        
        # Try to extract version information
        version_match = re.search(r'(v(?:ersion)?\s*[\d\.]+)', banner, re.IGNORECASE)
        if version_match:
            return self.get_service_name_from_port(port), version_match.group(1)
        
        return self.get_service_name_from_port(port), None
    
    def get_default_service(self, port: int) -> Tuple[str, Optional[str]]:
        """Get default service name for port."""
        if port in self.service_signatures:
            signature = self.service_signatures[port]
            return signature['service'], signature['default_version']
        
        return f"Unknown-{port}", None
    
    def get_service_name_from_port(self, port: int) -> str:
        """Get service name from port number."""
        service_names = {
            21: "FTP", 22: "SSH", 23: "Telnet", 25: "SMTP", 53: "DNS",
            80: "HTTP", 110: "POP3", 135: "Microsoft RPC", 139: "NetBIOS",
            143: "IMAP", 443: "HTTPS", 445: "Microsoft Directory Services",
            993: "IMAPS", 995: "POP3S", 1723: "PPTP", 3306: "MySQL",
            3389: "RDP", 5432: "PostgreSQL", 5900: "VNC", 8080: "HTTP-Alt",
            8443: "HTTPS-Alt"
        }
        return service_names.get(port, f"Unknown-{port}")
    
    async def detect_cdn(self, host: str) -> Dict:
        """Detect CDN usage for a host."""
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                async with session.get(f"http://{host}") as response:
                    headers = {k.lower(): v.lower() for k, v in response.headers.items()}
                    
                    detected_cdns = []
                    for cdn_name, patterns in self.cdn_patterns.items():
                        # Check headers
                        for header in patterns['headers']:
                            if header in headers:
                                detected_cdns.append(cdn_name)
                                break
                        
                        # Check server header
                        server_header = headers.get('server', '')
                        if patterns['server_header'] in server_header:
                            if cdn_name not in detected_cdns:
                                detected_cdns.append(cdn_name)
                    
                    return {
                        'uses_cdn': len(detected_cdns) > 0,
                        'cdn_providers': detected_cdns,
                        'headers': dict(headers)
                    }
                    
        except Exception as e:
            logger.debug(f"Error detecting CDN for {host}: {str(e)}")
            return {'uses_cdn': False, 'cdn_providers': [], 'error': str(e)}
    
    async def get_asn_info(self, ip_address: str) -> ASNInfo:
        """Get ASN information for an IP address."""
        try:
            # This would typically use APIs like IPinfo, BGPView, etc.
            # For now, return basic information
            
            asn_info = ASNInfo()
            
            # Basic ASN lookup would go here
            logger.info(f"Getting ASN info for {ip_address} (requires external API)")
            
            return asn_info
            
        except Exception as e:
            logger.error(f"Error getting ASN info for {ip_address}: {str(e)}")
            raise InfrastructureMappingError(f"Failed to get ASN info: {str(e)}")
    
    async def reverse_ip_lookup(self, ip_address: str) -> List[str]:
        """Find domains hosted on the same IP address."""
        try:
            # This would typically use APIs like SecurityTrails, Shodan, etc.
            # For now, return empty list as it requires external API integration
            
            logger.info(f"Reverse IP lookup for {ip_address} (requires external API)")
            return []
            
        except Exception as e:
            logger.error(f"Error in reverse IP lookup for {ip_address}: {str(e)}")
            raise InfrastructureMappingError(f"Failed to perform reverse IP lookup: {str(e)}")
    
    async def map_domain_infrastructure(self, domain: str) -> Dict:
        """Map complete infrastructure for a domain."""
        domain = self.normalize_domain(domain)
        
        mapping = {
            'domain': domain,
            'ip_addresses': [],
            'services': [],
            'cdn_info': {},
            'asn_info': {},
            'infrastructure_summary': {},
            'potential_issues': []
        }
        
        try:
            # Resolve domain to IP addresses
            resolver = dns.resolver.Resolver()
            resolver.timeout = 10
            
            try:
                answers = resolver.resolve(domain, 'A')
                ip_addresses = [str(rdata) for rdata in answers]
            except:
                ip_addresses = []
            
            if not ip_addresses:
                mapping['potential_issues'].append('no_ip_addresses_found')
                return mapping
            
            # Get information for each IP address
            for ip in ip_addresses:
                ip_info = await self.get_ip_info(ip)
                mapping['ip_addresses'].append(ip_info.to_dict())
                
                # Get ASN info
                asn_info = await self.get_asn_info(ip)
                mapping['asn_info'][ip] = asn_info.to_dict()
                
                # Perform port scanning
                services = await self.port_scan(ip)
                for service in services:
                    mapping['services'].append(service.to_dict())
            
            # Detect CDN usage
            mapping['cdn_info'] = await self.detect_cdn(domain)
            
            # Generate infrastructure summary
            unique_ips = len(set(ip['ip_address'] for ip in mapping['ip_addresses']))
            unique_asns = set(asn_info.get('asn') for asn_info in mapping['asn_info'].values())
            open_ports = len(mapping['services'])
            web_ports = len([s for s in mapping['services'] if s.get('port') in [80, 443, 8080, 8443]])
            mail_ports = len([s for s in mapping['services'] if s.get('port') in [25, 587, 465, 993, 995]])
            db_ports = len([s for s in mapping['services'] if s.get('port') in [3306, 5432, 27017, 6379]])
            
            mapping['infrastructure_summary'] = {
                'unique_ip_addresses': unique_ips,
                'unique_asns': len([asn for asn in unique_asns if asn]),
                'total_services': open_ports,
                'web_services': web_ports,
                'mail_services': mail_ports,
                'database_services': db_ports,
                'uses_cdn': mapping['cdn_info'].get('uses_cdn', False),
                'hosting_type': 'Dedicated' if unique_ips == 1 else 'Shared/Virtual Hosting'
            }
            
            # Identify potential issues
            if unique_ips == 0:
                mapping['potential_issues'].append('no_dns_resolution')
            elif unique_ips > 10:
                mapping['potential_issues'].append('high_number_of_ips')
            
            if open_ports > 50:
                mapping['potential_issues'].append('excessive_open_ports')
            
            if not any(s.get('port') in [80, 443, 8080, 8443] for s in mapping['services']):
                mapping['potential_issues'].append('no_web_services')
            
            if mapping['cdn_info'].get('uses_cdn'):
                mapping['potential_issues'].append('uses_cdn')
            
        except Exception as e:
            logger.error(f"Error mapping infrastructure for {domain}: {str(e)}")
            mapping['error'] = str(e)
        
        return mapping
    
    async def find_similar_infrastructure(self, domain: str) -> Dict:
        """Find domains with similar infrastructure patterns."""
        domain = self.normalize_domain(domain)
        
        # First, get the infrastructure for the target domain
        target_infrastructure = await self.map_domain_infrastructure(domain)
        
        similar_infrastructure = {
            'target_domain': domain,
            'target_infrastructure': target_infrastructure,
            'similar_domains': [],
            'analysis': {}
        }
        
        try:
            # Extract infrastructure patterns
            ip_addresses = [ip_info['ip_address'] for ip_info in target_infrastructure['ip_addresses']]
            asns = [asn_info.get('asn') for asn_info in target_infrastructure['asn_info'].values() if asn_info.get('asn')]
            
            # This would typically search for domains sharing the same infrastructure
            # For now, return empty results as it requires external API integration
            logger.info(f"Finding similar infrastructure for {domain} (requires external API)")
            
            # Analyze the target infrastructure
            similar_infrastructure['analysis'] = {
                'infrastructure_fingerprint': {
                    'ip_count': len(ip_addresses),
                    'asn_count': len(set(asns)),
                    'service_fingerprint': self.create_service_fingerprint(target_infrastructure['services'])
                },
                'potential_issues': target_infrastructure.get('potential_issues', [])
            }
            
        except Exception as e:
            logger.error(f"Error finding similar infrastructure for {domain}: {str(e)}")
            similar_infrastructure['error'] = str(e)
        
        return similar_infrastructure
    
    def create_service_fingerprint(self, services: List[ServiceInfo]) -> str:
        """Create a fingerprint of services for comparison."""
        # Extract key services and their ports
        key_services = set()
        for service in services:
            if service.get('is_open'):
                key_services.add(f"{service.get('port', 'unknown')}:{service.get('service_name', 'unknown')}")
        
        # Sort and create fingerprint
        return '-'.join(sorted(key_services))