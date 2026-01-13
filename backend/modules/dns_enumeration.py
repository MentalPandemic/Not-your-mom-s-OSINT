"""
DNS Enumeration Module

This module provides comprehensive DNS record enumeration, DNS history analysis,
and DNS propagation checking capabilities.
"""

import asyncio
import dns.resolver
import dns.zone
import dns.query
import dns.rdatatype
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple, Any
from urllib.parse import urlparse
import ipaddress
import logging

logger = logging.getLogger(__name__)


class DNSEnumerationError(Exception):
    """Custom exception for DNS enumeration failures."""
    pass


class DNSRecord:
    """DNS record container."""
    
    def __init__(self, name: str, record_type: str, value: str, ttl: int = None):
        self.name = name
        self.type = record_type
        self.value = value
        self.ttl = ttl
        self.timestamp = datetime.utcnow()
        
    def to_dict(self) -> Dict:
        """Convert to dictionary format."""
        return {
            'name': self.name,
            'type': self.type,
            'value': self.value,
            'ttl': self.ttl,
            'timestamp': self.timestamp.isoformat()
        }


class MXRecord(DNSRecord):
    """MX record with priority."""
    
    def __init__(self, name: str, mail_server: str, priority: int, ttl: int = None):
        super().__init__(name, 'MX', f"{priority} {mail_server}", ttl)
        self.mail_server = mail_server
        self.priority = priority
        
    def to_dict(self) -> Dict:
        base_dict = super().to_dict()
        base_dict['mail_server'] = self.mail_server
        base_dict['priority'] = self.priority
        return base_dict


class TXTRecord(DNSRecord):
    """TXT record with analysis."""
    
    def __init__(self, name: str, value: str, ttl: int = None):
        super().__init__(name, 'TXT', value, ttl)
        self.is_spf = 'v=spf1' in value.lower()
        self.is_dkim = 'dkim' in value.lower()
        self.is_dmarc = 'dmarc' in value.lower()
        self.has_verification = any(keyword in value.lower() for keyword in [
            'verification', 'verify', 'token', 'confirm'
        ])
        
    def to_dict(self) -> Dict:
        base_dict = super().to_dict()
        base_dict['is_spf'] = self.is_spf
        base_dict['is_dkim'] = self.is_dkim
        base_dict['is_dmarc'] = self.is_dmarc
        base_dict['has_verification'] = self.has_verification
        return base_dict


class DNSEnumeration:
    """Main DNS enumeration service."""
    
    def __init__(self):
        self.resolver = dns.resolver.Resolver()
        self.resolver.timeout = 10
        self.resolver.lifetime = 15
        
        # Common subdomain wordlist
        self.common_subdomains = [
            'www', 'mail', 'ftp', 'localhost', 'webmail', 'smtp', 'pop', 'ns1', 'webdisk',
            'ns2', 'cpanel', 'whm', 'autodiscover', 'autoconfig', 'm', 'imap', 'test',
            'ns', 'blog', 'pop3', 'dev', 'www2', 'admin', 'forum', 'news', 'vpn',
            'ns3', 'mail2', 'new', 'mysql', 'old', 'www1', 'staging', 'secure',
            'demo', 'cp', 'calendar', 'ftp2', 'mx', 'static', 'docs', 'beta',
            'www0', 'email', 'en', 'mail1', 'www3', 'www4', 'support', 'mobile',
            'msoid', 'web', 'www5', 'www6', 'm1', 'wap', 'st', 'app', 'www7',
            'ns4', 'www8', 'www9', 'www10', 'shop', 'sql', 'secure2', 'secure3',
            'email2', 'email3', 'web2', 'web3', 'web4', 'www11', 'www12', 'mail3',
            'mail4', 'mail5', 'ns5', 'ns6', 'ns7', 'ns8', 'ns9', 'ns10', 'poker',
            'www13', 'www14', 'www15', 'm2', 'm3', 'm4', 'm5', 'www16', 'www17',
            'www18', 'www19', 'www20'
        ]
        
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
    
    async def get_a_records(self, domain: str) -> List[DNSRecord]:
        """Get A records (IPv4 addresses)."""
        domain = self.normalize_domain(domain)
        records = []
        
        try:
            answers = self.resolver.resolve(domain, 'A')
            for rdata in answers:
                record = DNSRecord(domain, 'A', str(rdata), answers.rrset.ttl)
                records.append(record)
        except dns.resolver.NXDOMAIN:
            logger.warning(f"Domain {domain} does not exist")
        except dns.resolver.NoAnswer:
            logger.info(f"No A records found for {domain}")
        except Exception as e:
            logger.error(f"Error getting A records for {domain}: {str(e)}")
            
        return records
    
    async def get_aaaa_records(self, domain: str) -> List[DNSRecord]:
        """Get AAAA records (IPv6 addresses)."""
        domain = self.normalize_domain(domain)
        records = []
        
        try:
            answers = self.resolver.resolve(domain, 'AAAA')
            for rdata in answers:
                record = DNSRecord(domain, 'AAAA', str(rdata), answers.rrset.ttl)
                records.append(record)
        except dns.resolver.NXDOMAIN:
            logger.warning(f"Domain {domain} does not exist")
        except dns.resolver.NoAnswer:
            logger.info(f"No AAAA records found for {domain}")
        except Exception as e:
            logger.error(f"Error getting AAAA records for {domain}: {str(e)}")
            
        return records
    
    async def get_mx_records(self, domain: str) -> List[MXRecord]:
        """Get MX records (mail servers)."""
        domain = self.normalize_domain(domain)
        records = []
        
        try:
            answers = self.resolver.resolve(domain, 'MX')
            for rdata in answers:
                record = MXRecord(domain, str(rdata.exchange), rdata.preference, answers.rrset.ttl)
                records.append(record)
        except dns.resolver.NXDOMAIN:
            logger.warning(f"Domain {domain} does not exist")
        except dns.resolver.NoAnswer:
            logger.info(f"No MX records found for {domain}")
        except Exception as e:
            logger.error(f"Error getting MX records for {domain}: {str(e)}")
            
        return records
    
    async def get_txt_records(self, domain: str) -> List[TXTRecord]:
        """Get TXT records."""
        domain = self.normalize_domain(domain)
        records = []
        
        try:
            answers = self.resolver.resolve(domain, 'TXT')
            for rdata in answers:
                # Join all strings in the TXT record
                txt_value = ''.join(str(s) for s in rdata.strings)
                record = TXTRecord(domain, txt_value, answers.rrset.ttl)
                records.append(record)
        except dns.resolver.NXDOMAIN:
            logger.warning(f"Domain {domain} does not exist")
        except dns.resolver.NoAnswer:
            logger.info(f"No TXT records found for {domain}")
        except Exception as e:
            logger.error(f"Error getting TXT records for {domain}: {str(e)}")
            
        return records
    
    async def get_cname_records(self, domain: str) -> List[DNSRecord]:
        """Get CNAME records."""
        domain = self.normalize_domain(domain)
        records = []
        
        try:
            answers = self.resolver.resolve(domain, 'CNAME')
            for rdata in answers:
                record = DNSRecord(domain, 'CNAME', str(rdata.target), answers.rrset.ttl)
                records.append(record)
        except dns.resolver.NXDOMAIN:
            logger.warning(f"Domain {domain} does not exist")
        except dns.resolver.NoAnswer:
            logger.info(f"No CNAME records found for {domain}")
        except Exception as e:
            logger.error(f"Error getting CNAME records for {domain}: {str(e)}")
            
        return records
    
    async def get_ns_records(self, domain: str) -> List[DNSRecord]:
        """Get NS records (name servers)."""
        domain = self.normalize_domain(domain)
        records = []
        
        try:
            answers = self.resolver.resolve(domain, 'NS')
            for rdata in answers:
                record = DNSRecord(domain, 'NS', str(rdata.target), answers.rrset.ttl)
                records.append(record)
        except dns.resolver.NXDOMAIN:
            logger.warning(f"Domain {domain} does not exist")
        except dns.resolver.NoAnswer:
            logger.info(f"No NS records found for {domain}")
        except Exception as e:
            logger.error(f"Error getting NS records for {domain}: {str(e)}")
            
        return records
    
    async def get_srv_records(self, domain: str) -> List[DNSRecord]:
        """Get SRV records."""
        domain = self.normalize_domain(domain)
        records = []
        
        try:
            answers = self.resolver.resolve(domain, 'SRV')
            for rdata in answers:
                srv_value = f"{rdata.priority} {rdata.weight} {rdata.port} {rdata.target}"
                record = DNSRecord(domain, 'SRV', srv_value, answers.rrset.ttl)
                records.append(record)
        except dns.resolver.NXDOMAIN:
            logger.warning(f"Domain {domain} does not exist")
        except dns.resolver.NoAnswer:
            logger.info(f"No SRV records found for {domain}")
        except Exception as e:
            logger.error(f"Error getting SRV records for {domain}: {str(e)}")
            
        return records
    
    async def get_all_records(self, domain: str) -> Dict[str, List[DNSRecord]]:
        """Get all DNS records for a domain."""
        domain = self.normalize_domain(domain)
        
        results = {
            'a_records': await self.get_a_records(domain),
            'aaaa_records': await self.get_aaaa_records(domain),
            'mx_records': await self.get_mx_records(domain),
            'txt_records': await self.get_txt_records(domain),
            'cname_records': await self.get_cname_records(domain),
            'ns_records': await self.get_ns_records(domain),
            'srv_records': await self.get_srv_records(domain)
        }
        
        return results
    
    def analyze_mx_records(self, mx_records: List[MXRecord]) -> Dict:
        """Analyze MX records for email services and potential issues."""
        analysis = {
            'total_servers': len(mx_records),
            'priorities': [],
            'mail_services': [],
            'potential_issues': [],
            'email_providers': []
        }
        
        if not mx_records:
            analysis['potential_issues'].append('no_mx_records')
            return analysis
        
        # Extract priorities
        for record in mx_records:
            analysis['priorities'].append(record.priority)
        
        # Sort by priority
        analysis['priorities'].sort()
        
        # Analyze mail servers
        for record in mx_records:
            mail_server = record.mail_server.lower()
            
            # Identify email providers
            if 'google' in mail_server or 'gmail' in mail_server:
                analysis['email_providers'].append('google')
            elif 'outlook' in mail_server or 'microsoft' in mail_server:
                analysis['email_providers'].append('microsoft')
            elif 'yahoo' in mail_server:
                analysis['email_providers'].append('yahoo')
            elif 'zoho' in mail_server:
                analysis['email_providers'].append('zoho')
            elif 'protonmail' in mail_server:
                analysis['email_providers'].append('protonmail')
            elif 'amazonaws' in mail_server or 'amazon' in mail_server:
                analysis['email_providers'].append('amazon')
            elif 'sendgrid' in mail_server:
                analysis['email_providers'].append('sendgrid')
            elif 'mailgun' in mail_server:
                analysis['email_providers'].append('mailgun')
            else:
                analysis['mail_services'].append(record.mail_server)
        
        # Check for potential issues
        priorities = analysis['priorities']
        if len(set(priorities)) == 1 and len(priorities) > 1:
            analysis['potential_issues'].append('duplicate_priorities')
        
        if min(priorities) != 10:
            analysis['potential_issues'].append('unusual_primary_priority')
        
        if max(priorities) > 50:
            analysis['potential_issues'].append('high_priority_numbers')
        
        # Remove duplicates from providers
        analysis['email_providers'] = list(set(analysis['email_providers']))
        
        return analysis
    
    def analyze_txt_records(self, txt_records: List[TXTRecord]) -> Dict:
        """Analyze TXT records for security configurations."""
        analysis = {
            'has_spf': False,
            'has_dkim': False,
            'has_dmarc': False,
            'verification_tokens': [],
            'security_policies': [],
            'service_identifiers': []
        }
        
        for record in txt_records:
            value_lower = record.value.lower()
            
            # Check for SPF
            if record.is_spf:
                analysis['has_spf'] = True
                analysis['security_policies'].append(f"SPF: {record.value}")
            
            # Check for DKIM
            if record.is_dkim:
                analysis['has_dkim'] = True
                # Extract selector
                if 'selector1' in value_lower:
                    analysis['service_identifiers'].append('google_dkim')
                elif 'selector2' in value_lower:
                    analysis['service_identifiers'].append('google_dkim')
                elif 'amazonses' in value_lower:
                    analysis['service_identifiers'].append('amazon_ses')
                elif 'sendgrid' in value_lower:
                    analysis['service_identifiers'].append('sendgrid')
                else:
                    analysis['service_identifiers'].append('dkim')
            
            # Check for DMARC
            if record.is_dmarc:
                analysis['has_dmarc'] = True
                analysis['security_policies'].append(f"DMARC: {record.value}")
            
            # Check for verification tokens
            if record.has_verification:
                analysis['verification_tokens'].append(record.value)
            
            # Look for other service identifiers
            if 'v=spf1' in value_lower and 'include:' in value_lower:
                includes = re.findall(r'include:([^\s]+)', value_lower)
                for include in includes:
                    analysis['service_identifiers'].append(f"spf_include_{include}")
            
            # Look for domain verification
            if 'domainkey' in value_lower or 'dkim' in value_lower:
                if 'google' in value_lower:
                    analysis['service_identifiers'].append('google_workspace')
                elif 'outlook' in value_lower:
                    analysis['service_identifiers'].append('microsoft_365')
        
        # Remove duplicates
        analysis['service_identifiers'] = list(set(analysis['service_identifiers']))
        analysis['security_policies'] = list(set(analysis['security_policies']))
        
        return analysis
    
    async def attempt_zone_transfer(self, domain: str) -> Dict:
        """Attempt zone transfer (AXFR) on domain name servers."""
        domain = self.normalize_domain(domain)
        results = {
            'zone_transfer_successful': False,
            'nameservers': [],
            'records': [],
            'error': None
        }
        
        try:
            # Get NS records first
            ns_records = await self.get_ns_records(domain)
            
            for ns_record in ns_records:
                nameserver = ns_record.value
                try:
                    # Attempt zone transfer
                    zone = dns.zone.from_xfr(dns.query.xfr(nameserver, domain))
                    
                    results['zone_transfer_successful'] = True
                    results['nameservers'].append(nameserver)
                    
                    # Extract all records
                    for name, node in zone.nodes.items():
                        for rdataset in node.rdatasets:
                            for rdata in rdataset:
                                record = {
                                    'name': str(name),
                                    'type': dns.rdatatype.to_text(rdataset.rdtype),
                                    'value': str(rdata),
                                    'ttl': rdataset.ttl
                                }
                                results['records'].append(record)
                    
                except Exception as e:
                    logger.info(f"Zone transfer failed from {nameserver}: {str(e)}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error attempting zone transfer for {domain}: {str(e)}")
            results['error'] = str(e)
            
        return results
    
    async def check_dns_propagation(self, domain: str) -> Dict:
        """Check DNS propagation across different resolvers."""
        domain = self.normalize_domain(domain)
        
        # Use multiple public resolvers
        resolvers = [
            '8.8.8.8',        # Google
            '1.1.1.1',        # Cloudflare
            '9.9.9.9',        # Quad9
            '208.67.222.222', # OpenDNS
            '8.8.4.4'         # Google secondary
        ]
        
        propagation_results = {
            'domain': domain,
            'resolvers': {},
            'inconsistencies': [],
            'total_propagated': 0
        }
        
        for resolver_ip in resolvers:
            try:
                resolver = dns.resolver.Resolver()
                resolver.nameservers = [resolver_ip]
                resolver.timeout = 5
                
                # Check A record
                answers = resolver.resolve(domain, 'A')
                ips = [str(rdata) for rdata in answers]
                
                propagation_results['resolvers'][resolver_ip] = {
                    'reachable': True,
                    'a_records': ips,
                    'record_count': len(ips)
                }
                propagation_results['total_propagated'] += 1
                
            except Exception as e:
                propagation_results['resolvers'][resolver_ip] = {
                    'reachable': False,
                    'error': str(e)
                }
        
        # Check for inconsistencies
        all_ips = set()
        resolver_results = {}
        
        for resolver_ip, result in propagation_results['resolvers'].items():
            if result['reachable']:
                ips = tuple(sorted(result['a_records']))
                resolver_results[resolver_ip] = ips
                all_ips.update(result['a_records'])
        
        # Find inconsistencies
        if len(set(resolver_results.values())) > 1:
            propagation_results['inconsistencies'] = [
                'Different A records returned by different resolvers'
            ]
        
        # Check if all resolvers agree
        if resolver_results:
            unique_results = set(resolver_results.values())
            if len(unique_results) == 1:
                propagation_results['all_resolvers_agree'] = True
                propagation_results['consistent_records'] = list(unique_results)[0]
            else:
                propagation_results['all_resolvers_agree'] = False
        
        return propagation_results
    
    async def analyze_dns_security(self, domain: str) -> Dict:
        """Analyze DNS security configuration."""
        domain = self.normalize_domain(domain)
        
        security_analysis = {
            'has_spf': False,
            'has_dkim': False,
            'has_dmarc': False,
            'has_dnssec': False,
            'security_score': 0,
            'recommendations': []
        }
        
        try:
            # Check TXT records for SPF, DKIM, DMARC
            txt_records = await self.get_txt_records(domain)
            txt_analysis = self.analyze_txt_records(txt_records)
            
            security_analysis['has_spf'] = txt_analysis['has_spf']
            security_analysis['has_dkim'] = txt_analysis['has_dkim']
            security_analysis['has_dmarc'] = txt_analysis['has_dmarc']
            
            # Check DNSSEC
            try:
                self.resolver.resolve(domain, 'DNSKEY')
                security_analysis['has_dnssec'] = True
            except:
                pass
            
            # Calculate security score
            if security_analysis['has_spf']:
                security_analysis['security_score'] += 25
            else:
                security_analysis['recommendations'].append('Add SPF record')
            
            if security_analysis['has_dkim']:
                security_analysis['security_score'] += 25
            else:
                security_analysis['recommendations'].append('Add DKIM record')
            
            if security_analysis['has_dmarc']:
                security_analysis['security_score'] += 25
            else:
                security_analysis['recommendations'].append('Add DMARC record')
            
            if security_analysis['has_dnssec']:
                security_analysis['security_score'] += 25
            else:
                security_analysis['recommendations'].append('Enable DNSSEC')
        
        except Exception as e:
            logger.error(f"Error analyzing DNS security for {domain}: {str(e)}")
            security_analysis['error'] = str(e)
        
        return security_analysis