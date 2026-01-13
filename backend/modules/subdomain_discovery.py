"""
Subdomain Discovery Module

This module provides comprehensive subdomain discovery capabilities including brute force enumeration,
certificate transparency log analysis, and subdomain analysis.
"""

import asyncio
import aiohttp
import ssl
import socket
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple
from urllib.parse import urlparse
import re
import json
import logging
import dns.resolver

logger = logging.getLogger(__name__)


class SubdomainDiscoveryError(Exception):
    """Custom exception for subdomain discovery failures."""
    pass


class SubdomainInfo:
    """Subdomain information container."""
    
    def __init__(self, name: str, ip_address: Optional[str] = None, status: str = 'unknown'):
        self.name = name
        self.ip_address = ip_address
        self.status = status  # 'active', 'inactive', 'unknown', 'wildcard'
        self.services = []
        self.technologies = []
        self.ports = []
        self.response_time = None
        self.title = None
        self.server_header = None
        self.fingerprint = None
        self.last_checked = datetime.utcnow()
        
    def to_dict(self) -> Dict:
        """Convert to dictionary format."""
        return {
            'name': self.name,
            'ip_address': self.ip_address,
            'status': self.status,
            'services': self.services,
            'technologies': self.technologies,
            'ports': self.ports,
            'response_time': self.response_time,
            'title': self.title,
            'server_header': self.server_header,
            'fingerprint': self.fingerprint,
            'last_checked': self.last_checked.isoformat()
        }


class SubdomainDiscovery:
    """Main subdomain discovery service."""
    
    def __init__(self):
        # Comprehensive subdomain wordlists
        self.common_subdomains = [
            # Common services
            'www', 'mail', 'ftp', 'localhost', 'webmail', 'smtp', 'pop', 'ns1', 'webdisk',
            'ns2', 'cpanel', 'whm', 'autodiscover', 'autoconfig', 'm', 'imap', 'test',
            'ns', 'blog', 'pop3', 'dev', 'www2', 'admin', 'forum', 'news', 'vpn',
            'ns3', 'mail2', 'new', 'mysql', 'old', 'www1', 'staging', 'secure',
            'demo', 'cp', 'calendar', 'ftp2', 'mx', 'static', 'docs', 'beta',
            'www0', 'email', 'en', 'mail1', 'www3', 'www4', 'support', 'mobile',
            'msoid', 'web', 'www5', 'www6', 'm1', 'wap', 'st', 'app', 'www7',
            
            # Tech-specific
            'api', 'api1', 'api2', 'rest', 'graphql', 'soap', 'rpc', 'json',
            'cdn', 'static', 'assets', 'images', 'img', 'css', 'js', 'media',
            'download', 'files', 'uploads', 'content', 'media', 'assets',
            
            # Development
            'dev', 'development', 'test', 'testing', 'staging', 'stage', 'qa',
            'sandbox', 'ci', 'cd', 'build', 'deploy', 'preview', 'demo',
            'backoffice', 'intranet', 'internal', 'private', 'secret',
            
            # E-commerce
            'shop', 'store', 'cart', 'checkout', 'order', 'orders', 'payment',
            'payments', 'billing', 'account', 'accounts', 'user', 'users',
            'customer', 'customers', 'client', 'clients',
            
            # Monitoring/Analytics
            'monitor', 'monitoring', 'metrics', 'stats', 'statistics', 'analytics',
            'tracking', 'logs', 'logging', 'alerts', 'health', 'status',
            
            # Services
            'service', 'services', 'service1', 'service2', 'microservice',
            'gateway', 'proxy', 'loadbalancer', 'lb',
            
            # Database
            'db', 'database', 'sql', 'mysql', 'postgresql', 'postgres', 'mongo',
            'redis', 'cache', 'elasticsearch', 'elastic',
            
            # Cloud/Infra
            'cloud', 'compute', 'instance', 'server', 'host', 'node',
            'cluster', 'k8s', 'kubernetes', 'docker',
            
            # Security
            'security', 'auth', 'authentication', 'login', 'logout', 'sso',
            'oauth', 'openid', 'ldap', 'directory', 'firewall', 'waf',
            
            # Email services
            'email', 'emails', 'newsletter', 'newsletters', 'mailing', 'lists',
            'list', 'subscribe', 'unsubscribe', 'marketing',
            
            # Search
            'search', 'find', 'lookup', 'query', 'suggest', 'autocomplete',
            
            # Mobile
            'mobile', 'm', 'iphone', 'android', 'app', 'apps',
            
            # Misc
            'community', 'support', 'help', 'wiki', 'docs', 'documentation',
            'blog', 'blogs', 'forum', 'forums', 'chat', 'social', 'media'
        ]
        
        # Extended wordlist for deeper enumeration
        self.extended_subdomains = [
            'backup', 'backups', 'mirror', 'mirrors', 'archive', 'archives',
            'old', 'new', 'www-old', 'www-new', 'v1', 'v2', 'v3', 'version1',
            'alpha', 'beta', 'gamma', 'delta', 'epsilon', 'zeta', 'eta',
            'theta', 'iota', 'kappa', 'lambda', 'mu', 'nu', 'xi', 'omicron',
            'pi', 'rho', 'sigma', 'tau', 'upsilon', 'phi', 'chi', 'psi', 'omega',
            'production', 'prod', 'preproduction', 'pre-prod', 'staging',
            'staging1', 'staging2', 'development', 'dev1', 'dev2', 'test1',
            'test2', 'testing', 'qa1', 'qa2', 'demo1', 'demo2', 'pilot',
            'sandbox1', 'sandbox2', 'int', 'integration', 'perf', 'performance',
            'load', 'stress', 'stress-test', 'security', 'sec', 'pentest',
            'red', 'blue', 'green', 'yellow', 'orange', 'purple', 'pink',
            'black', 'white', 'gray', 'grey', 'red-team', 'blue-team'
        ]
        
        # CT log APIs
        self.ct_log_apis = [
            "https://crt.sh/?q=%.{domain}&output=json",
            "https://certificate-transparency.org/api/v1/entry/{}"
        ]
        
        # Common ports to check
        self.common_ports = [21, 22, 23, 25, 53, 80, 110, 143, 443, 993, 995, 8080, 8443]
        
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
    
    async def check_subdomain_exists(self, subdomain: str, domain: str, timeout: int = 5) -> Optional[str]:
        """Check if a subdomain exists and return its IP."""
        full_domain = f"{subdomain}.{domain}"
        
        try:
            # Set up socket with timeout
            socket.setdefaulttimeout(timeout)
            
            # Resolve IP
            ip = socket.gethostbyname(full_domain)
            return ip
            
        except socket.gaierror:
            return None
        except Exception as e:
            logger.debug(f"Error checking subdomain {full_domain}: {str(e)}")
            return None
    
    async def brute_force_subdomains(self, domain: str, use_extended: bool = False) -> List[SubdomainInfo]:
        """Brute force common subdomains."""
        domain = self.normalize_domain(domain)
        subdomains = []
        
        wordlist = self.common_subdomains + self.extended_subdomains if use_extended else self.common_subdomains
        
        logger.info(f"Starting brute force subdomain enumeration for {domain}")
        logger.info(f"Using wordlist of {len(wordlist)} subdomains")
        
        # Use semaphore to limit concurrent requests
        semaphore = asyncio.Semaphore(100)
        
        async def check_single_subdomain(subdomain: str) -> Optional[SubdomainInfo]:
            async with semaphore:
                try:
                    ip = await self.check_subdomain_exists(subdomain, domain)
                    if ip:
                        subdomain_info = SubdomainInfo(
                            name=f"{subdomain}.{domain}",
                            ip_address=ip,
                            status='active'
                        )
                        logger.debug(f"Found active subdomain: {subdomain_info.name} -> {ip}")
                        return subdomain_info
                except Exception as e:
                    logger.debug(f"Error checking subdomain {subdomain}: {str(e)}")
                return None
        
        # Create tasks for all subdomains
        tasks = [check_single_subdomain(subdomain) for subdomain in wordlist]
        
        # Execute all tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter successful results
        for result in results:
            if isinstance(result, SubdomainInfo):
                subdomains.append(result)
        
        logger.info(f"Brute force enumeration found {len(subdomains)} active subdomains")
        return subdomains
    
    async def search_certificate_transparency(self, domain: str) -> List[SubdomainInfo]:
        """Search certificate transparency logs for subdomains."""
        domain = self.normalize_domain(domain)
        subdomains = []
        
        try:
            # Use crt.sh API
            url = f"https://crt.sh/?q=%.{domain}&output=json"
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        for entry in data:
                            # Extract subdomain from common_name or name_value
                            subdomains_found = set()
                            
                            if entry.get('common_name'):
                                cn = entry['common_name']
                                if self.is_valid_subdomain_for_domain(cn, domain):
                                    subdomains_found.add(cn)
                            
                            if entry.get('name_value'):
                                # name_value can contain multiple domains separated by \n
                                domains = entry['name_value'].split('\n')
                                for domain_name in domains:
                                    if self.is_valid_subdomain_for_domain(domain_name, domain):
                                        subdomains_found.add(domain_name)
                            
                            # Add found subdomains
                            for subdomain in subdomains_found:
                                # Clean up subdomain (remove wildcards, etc.)
                                clean_subdomain = subdomain.replace('*.', '').replace('*.', '')
                                if clean_subdomain != domain:
                                    subdomain_info = SubdomainInfo(
                                        name=clean_subdomain,
                                        status='from_certificate'
                                    )
                                    subdomains.append(subdomain_info)
                    
                    else:
                        logger.warning(f"Certificate transparency search failed with status {response.status}")
        
        except Exception as e:
            logger.error(f"Error searching certificate transparency logs: {str(e)}")
        
        # Remove duplicates
        unique_subdomains = []
        seen_names = set()
        
        for subdomain in subdomains:
            if subdomain.name not in seen_names:
                unique_subdomains.append(subdomain)
                seen_names.add(subdomain.name)
        
        logger.info(f"Certificate transparency search found {len(unique_subdomains)} unique subdomains")
        return unique_subdomains
    
    def is_valid_subdomain_for_domain(self, subdomain: str, domain: str) -> bool:
        """Check if subdomain belongs to the target domain."""
        subdomain = subdomain.lower().strip()
        domain = domain.lower().strip()
        
        # Remove wildcards
        subdomain = subdomain.replace('*.', '')
        
        # Check if subdomain ends with the domain
        return subdomain.endswith('.' + domain) or subdomain == domain
    
    async def analyze_subdomain(self, subdomain_info: SubdomainInfo) -> SubdomainInfo:
        """Analyze a subdomain for services and technologies."""
        try:
            # Try to resolve IP if not already known
            if not subdomain_info.ip_address:
                ip = await self.check_subdomain_exists(subdomain_info.name, subdomain_info.name)
                if ip:
                    subdomain_info.ip_address = ip
                    subdomain_info.status = 'active'
            
            # If we have an IP, do additional analysis
            if subdomain_info.ip_address:
                await self.analyze_web_services(subdomain_info)
                await self.analyze_ports(subdomain_info)
            
        except Exception as e:
            logger.debug(f"Error analyzing subdomain {subdomain_info.name}: {str(e)}")
        
        return subdomain_info
    
    async def analyze_web_services(self, subdomain_info: SubdomainInfo):
        """Analyze web services on a subdomain."""
        try:
            # Try HTTP and HTTPS
            for protocol in ['http', 'https']:
                try:
                    url = f"{protocol}://{subdomain_info.name}"
                    
                    timeout = aiohttp.ClientTimeout(total=10)
                    async with aiohttp.ClientSession(timeout=timeout) as session:
                        start_time = asyncio.get_event_loop().time()
                        async with session.get(url, allow_redirects=True) as response:
                            end_time = asyncio.get_event_loop().time()
                            subdomain_info.response_time = round((end_time - start_time) * 1000, 2)
                            
                            # Check server header
                            server_header = response.headers.get('Server')
                            if server_header:
                                subdomain_info.server_header = server_header
                                subdomain_info.technologies.append(f"Server: {server_header}")
                            
                            # Get page title if HTML
                            content_type = response.headers.get('Content-Type', '')
                            if 'text/html' in content_type:
                                content = await response.text()
                                title_match = re.search(r'<title[^>]*>([^<]+)</title>', content, re.IGNORECASE)
                                if title_match:
                                    subdomain_info.title = title_match.group(1).strip()
                            
                            # Add service information
                            service_info = {
                                'url': url,
                                'status_code': response.status,
                                'protocol': protocol,
                                'content_type': content_type
                            }
                            subdomain_info.services.append(service_info)
                            
                            # Identify technologies from headers
                            self.identify_technologies(subdomain_info, response.headers)
                            
                            break  # If HTTP succeeds, don't try HTTPS
                            
                except Exception as e:
                    logger.debug(f"Error analyzing {url}: {str(e)}")
                    continue
        
        except Exception as e:
            logger.debug(f"Error in web service analysis for {subdomain_info.name}: {str(e)}")
    
    def identify_technologies(self, subdomain_info: SubdomainInfo, headers: dict):
        """Identify technologies from HTTP headers."""
        headers_lower = {k.lower(): v.lower() for k, v in headers.items()}
        
        # Server header analysis
        server = headers_lower.get('server', '')
        if server:
            if 'nginx' in server:
                subdomain_info.technologies.append('Nginx')
            elif 'apache' in server:
                subdomain_info.technologies.append('Apache')
            elif 'iis' in server:
                subdomain_info.technologies.append('IIS')
            elif 'cloudflare' in server:
                subdomain_info.technologies.append('Cloudflare')
            elif 'aws' in server or 'amazon' in server:
                subdomain_info.technologies.append('AWS')
        
        # Other headers
        powered_by = headers_lower.get('x-powered-by', '')
        if powered_by:
            subdomain_info.technologies.append(f"X-Powered-By: {powered_by}")
        
        # Framework detection
        via = headers_lower.get('via', '')
        if via:
            subdomain_info.technologies.append(f"Via: {via}")
        
        # CDN detection
        cf_ray = headers_lower.get('cf-ray', '')
        if cf_ray:
            subdomain_info.technologies.append('Cloudflare')
        
        # Security headers
        if headers_lower.get('strict-transport-security'):
            subdomain_info.technologies.append('HSTS')
        
        if headers_lower.get('content-security-policy'):
            subdomain_info.technologies.append('CSP')
    
    async def analyze_ports(self, subdomain_info: SubdomainInfo):
        """Analyze common ports on a subdomain."""
        if not subdomain_info.ip_address:
            return
        
        open_ports = []
        
        async def check_port(port: int):
            try:
                reader, writer = await asyncio.wait_for(
                    asyncio.open_connection(subdomain_info.ip_address, port),
                    timeout=2.0
                )
                writer.close()
                await writer.wait_closed()
                return port
            except:
                return None
        
        # Check common ports concurrently
        semaphore = asyncio.Semaphore(50)
        
        async def check_port_limited(port: int):
            async with semaphore:
                return await check_port(port)
        
        tasks = [check_port_limited(port) for port in self.common_ports]
        results = await asyncio.gather(*tasks)
        
        open_ports = [port for port in results if port is not None]
        subdomain_info.ports = open_ports
        
        # Add port-based services
        for port in open_ports:
            if port == 80:
                subdomain_info.services.append({'port': port, 'service': 'HTTP'})
            elif port == 443:
                subdomain_info.services.append({'port': port, 'service': 'HTTPS'})
            elif port == 22:
                subdomain_info.services.append({'port': port, 'service': 'SSH'})
            elif port == 21:
                subdomain_info.services.append({'port': port, 'service': 'FTP'})
            elif port == 25:
                subdomain_info.services.append({'port': port, 'service': 'SMTP'})
            elif port == 3306:
                subdomain_info.services.append({'port': port, 'service': 'MySQL'})
            elif port == 5432:
                subdomain_info.services.append({'port': port, 'service': 'PostgreSQL'})
            elif port == 8080:
                subdomain_info.services.append({'port': port, 'service': 'HTTP-Alt'})
    
    async def detect_wildcard_dns(self, domain: str) -> bool:
        """Detect if domain uses wildcard DNS."""
        try:
            # Try to resolve a random subdomain
            test_subdomain = f"random-test-{datetime.now().strftime('%Y%m%d%H%M%S')}.{domain}"
            ip = await self.check_subdomain_exists(test_subdomain, domain)
            return ip is not None
        except:
            return False
    
    async def discover_subdomains(self, domain: str, use_extended: bool = False, 
                                  include_cert_transparency: bool = True,
                                  analyze_subdomains: bool = True) -> Dict:
        """Comprehensive subdomain discovery."""
        domain = self.normalize_domain(domain)
        
        logger.info(f"Starting comprehensive subdomain discovery for {domain}")
        
        results = {
            'domain': domain,
            'subdomains': [],
            'summary': {
                'total_found': 0,
                'active_subdomains': 0,
                'inactive_subdomains': 0,
                'cert_transparency_found': 0,
                'brute_force_found': 0,
                'wildcard_dns': False
            }
        }
        
        try:
            # Check for wildcard DNS first
            results['summary']['wildcard_dns'] = await self.detect_wildcard_dns(domain)
            
            all_subdomains = []
            
            # Brute force enumeration
            brute_force_subdomains = await self.brute_force_subdomains(domain, use_extended)
            for sub in brute_force_subdomains:
                sub.source = 'brute_force'
            all_subdomains.extend(brute_force_subdomains)
            
            # Certificate transparency search
            if include_cert_transparency:
                ct_subdomains = await self.search_certificate_transparency(domain)
                for sub in ct_subdomains:
                    sub.source = 'certificate_transparency'
                all_subdomains.extend(ct_subdomains)
            
            # Remove duplicates and filter
            unique_subdomains = []
            seen_names = set()
            
            for subdomain in all_subdomains:
                if subdomain.name not in seen_names:
                    seen_names.add(subdomain.name)
                    unique_subdomains.append(subdomain)
            
            # Analyze subdomains if requested
            if analyze_subdomains:
                semaphore = asyncio.Semaphore(20)
                
                async def analyze_with_semaphore(subdomain):
                    async with semaphore:
                        return await self.analyze_subdomain(subdomain)
                
                tasks = [analyze_with_semaphore(subdomain) for subdomain in unique_subdomains]
                analyzed_subdomains = await asyncio.gather(*tasks, return_exceptions=True)
                
                for subdomain in analyzed_subdomains:
                    if isinstance(subdomain, SubdomainInfo):
                        results['subdomains'].append(subdomain)
            else:
                results['subdomains'] = unique_subdomains
            
            # Generate summary
            results['summary']['total_found'] = len(results['subdomains'])
            results['summary']['active_subdomains'] = len([s for s in results['subdomains'] if s.status == 'active'])
            results['summary']['inactive_subdomains'] = len([s for s in results['subdomains'] if s.status != 'active'])
            results['summary']['brute_force_found'] = len([s for s in results['subdomains'] if getattr(s, 'source', '') == 'brute_force'])
            results['summary']['cert_transparency_found'] = len([s for s in results['subdomains'] if getattr(s, 'source', '') == 'certificate_transparency'])
            
            logger.info(f"Subdomain discovery completed: {results['summary']['total_found']} total subdomains found")
            
        except Exception as e:
            logger.error(f"Error in subdomain discovery for {domain}: {str(e)}")
            results['error'] = str(e)
        
        return results