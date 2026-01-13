"""
Related Domain Discovery Module

This module discovers domains related to a target through various relationship types including
domain variations, registrant links, brand/company domains, and infrastructure connections.
"""

import asyncio
import re
import difflib
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple, Any
from urllib.parse import urlparse
import aiohttp
import logging

logger = logging.getLogger(__name__)


class RelatedDomainDiscoveryError(Exception):
    """Custom exception for related domain discovery failures."""
    pass


class DomainVariation:
    """Domain variation information container."""
    
    def __init__(self, domain: str, variation_type: str, confidence: float = 0.0):
        self.domain = domain
        self.variation_type = variation_type  # 'typosquatting', 'different_tld', 'subdomain', 'similar'
        self.confidence = confidence
        self.risk_level: str = 'unknown'  # 'low', 'medium', 'high'
        self.techniques: List[str] = []  # How the variation was created
        self.status: str = 'unknown'  # 'active', 'inactive', 'available', 'parked'
        self.registration_date: Optional[datetime] = None
        self.registrant_info: Optional[str] = None
        
    def to_dict(self) -> Dict:
        """Convert to dictionary format."""
        return {
            'domain': self.domain,
            'variation_type': self.variation_type,
            'confidence': self.confidence,
            'risk_level': self.risk_level,
            'techniques': self.techniques,
            'status': self.status,
            'registration_date': self.registration_date.isoformat() if self.registration_date else None,
            'registrant_info': self.registrant_info
        }


class RelatedDomainInfo:
    """Related domain information container."""
    
    def __init__(self, domain: str, relationship_type: str, confidence: float = 0.0):
        self.domain = domain
        self.relationship_type = relationship_type  # 'same_registrant', 'same_ns', 'same_ip', 'same_asn'
        self.confidence = confidence
        self.evidence: List[str] = []
        self.first_seen: Optional[datetime] = None
        self.last_seen: Optional[datetime] = None
        self.status: str = 'unknown'
        self.registrant_name: Optional[str] = None
        self.registrant_email: Optional[str] = None
        self.registrar: Optional[str] = None
        
    def to_dict(self) -> Dict:
        """Convert to dictionary format."""
        return {
            'domain': self.domain,
            'relationship_type': self.relationship_type,
            'confidence': self.confidence,
            'evidence': self.evidence,
            'first_seen': self.first_seen.isoformat() if self.first_seen else None,
            'last_seen': self.last_seen.isoformat() if self.last_seen else None,
            'status': self.status,
            'registrant_name': self.registrant_name,
            'registrant_email': self.registrant_email,
            'registrar': self.registrar
        }


class RelatedDomainDiscovery:
    """Main related domain discovery service."""
    
    def __init__(self):
        # Common TLDs to check
        self.common_tlds = [
            'com', 'net', 'org', 'info', 'biz', 'name', 'pro', 'museum', 'coop',
            'aero', 'travel', 'jobs', 'mobi', 'cat', 'tel', 'asia', 'us', 'uk',
            'de', 'fr', 'it', 'es', 'nl', 'ch', 'at', 'be', 'se', 'no', 'dk',
            'fi', 'pl', 'cz', 'hu', 'pt', 'gr', 'bg', 'ro', 'hr', 'sk', 'si',
            'lt', 'lv', 'ee', 'mt', 'cy', 'lu', 'ie', 'eu', 'co', 'me', 'tk',
            'ml', 'ga', 'cf', 'gq', 'nu', 'cc', 'tv', 'ws', 'fm', 'im', 'ly'
        ]
        
        # Typosquatting patterns
        self.typosquatting_patterns = [
            # Character substitution
            (r'([a-z])n([a-z])', r'\1m\2'),  # m/n substitution
            (r'([a-z])rn([a-z])', r'\1m\2'), # rn/m substitution
            (r'([a-z])l([a-z])', r'\1i\2'),  # l/i substitution
            (r'([a-z])o([a-z])', r'\1a\2'),  # o/a substitution
            (r'([a-z])c([a-z])', r'\1k\2'),  # c/k substitution
            (r'([a-z])p([a-z])', r'\1b\2'),  # p/b substitution
            (r'([a-z])d([a-z])', r'\1cl\2'), # d/cl substitution
            (r'([a-z])s([a-z])', r'\1z\2'),  # s/z substitution
            (r'([a-z])t([a-z])', r'\1f\2'),  # t/f substitution
            (r'([a-z])g([a-z])', r'\1q\2'),  # g/q substitution
            (r'([a-z])v([a-z])', r'\1w\2'),  # v/w substitution
            (r'([a-z])x([a-z])', r'\1z\2'),  # x/z substitution
            
            # Character omission
            (r'(.)\1+', r'\1'),              # Repeated characters
            (r'(.{2,})[aeiou]', r'\1'),      # Vowel omission
            (r'(.)\1(.)', r'\1\2'),          # Double letter to single
            
            # Character addition
            (r'(.)', r'\1\1'),               # Character duplication
            (r'(.{2,})', r'\1s'),            # Add 's'
            (r'(.{2,})', r'\1y'),            # Add 'y'
            (r'(.{2,})', r'\1ing'),          # Add 'ing'
            
            # Character transposition
            (r'(.)(.)', r'\2\1'),            # Swap adjacent characters
            
            # Homograph attacks (basic)
            (r'a', 'а'),                     # Latin 'a' to Cyrillic 'а'
            (r'e', 'е'),                     # Latin 'e' to Cyrillic 'е'
            (r'o', 'о'),                     # Latin 'o' to Cyrillic 'о'
            (r'p', 'р'),                     # Latin 'p' to Cyrillic 'р'
            (r'c', 'с'),                     # Latin 'c' to Cyrillic 'с'
            (r'y', 'у'),                     # Latin 'y' to Cyrillic 'у'
            (r'x', 'х'),                     # Latin 'x' to Cyrillic 'х'
        ]
        
        # Brand/company domain patterns
        self.brand_patterns = [
            # Add/remove prefixes
            r'get(.+)', r'\1app', r'join(.+)', r'(.+)team', r'(.+)hq',
            
            # Add/remove suffixes
            r'(.+)online', r'(.+)web', r'(.+)site', r'(.+)net', r'(.+)direct',
            r'(.+)official', r'(.+)support', r'(.+)help', r'(.+)docs', r'(.+)blog',
            
            # Security-focused
            r'(.+)security', r'(.+)secure', r'(.+)protect', r'(.+)defend', r'(.+)guard',
            
            # Location-based
            r'(.+)usa', r'(.+)uk', r'(.+)eu', r'(.+)asia', r'(.+)global',
            
            # Mobile-focused
            r'(.+)mobile', r'(.+)app', r'(.+)mobi', r'(.+)phone', r'(.+)smart',
            
            # Corporate
            r'(.+)corp', r'(.+)inc', r'(.+)llc', r'(.+)ltd', r'(.+)co',
        ]
        
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
    
    def generate_domain_variations(self, domain: str) -> List[DomainVariation]:
        """Generate domain variations using various techniques."""
        domain = self.normalize_domain(domain)
        root_domain, tld = self.extract_root_and_tld(domain)
        
        variations = []
        
        # 1. Different TLD variations
        for new_tld in self.common_tlds:
            if new_tld != tld:
                new_domain = f"{root_domain}.{new_tld}"
                variation = DomainVariation(new_domain, 'different_tld', 0.8)
                variation.techniques.append('tld_replacement')
                variations.append(variation)
        
        # 2. Typosquatting variations
        typosquatting_variations = self.generate_typosquatting_variations(root_domain)
        for var_domain, confidence, techniques in typosquatting_variations:
            variation = DomainVariation(f"{var_domain}.{tld}", 'typosquatting', confidence)
            variation.techniques = techniques
            variations.append(variation)
        
        # 3. Subdomain variations
        subdomain_variations = self.generate_subdomain_variations(domain)
        for var_domain, confidence, techniques in subdomain_variations:
            variation = DomainVariation(var_domain, 'subdomain', confidence)
            variation.techniques = techniques
            variations.append(variation)
        
        # 4. Similar domain variations
        similar_variations = self.generate_similar_variations(root_domain)
        for var_domain, confidence, techniques in similar_variations:
            variation = DomainVariation(f"{var_domain}.{tld}", 'similar', confidence)
            variation.techniques = techniques
            variations.append(variation)
        
        return variations
    
    def generate_typosquatting_variations(self, root_domain: str) -> List[Tuple[str, float, List[str]]]:
        """Generate typosquatting variations."""
        variations = []
        
        # Character substitution
        for pattern, replacement in self.typosquatting_patterns:
            try:
                new_domain = re.sub(pattern, replacement, root_domain, flags=re.IGNORECASE)
                if new_domain != root_domain:
                    variations.append((new_domain, 0.7, ['character_substitution']))
            except:
                continue
        
        # Common typos
        common_typos = {
            'facebook': ['facebok', 'faceboook', 'facebbook', 'faceboko'],
            'google': ['googel', 'gogle', 'googl', 'googlee'],
            'amazon': ['amamzon', 'amaozn', 'amzon', 'amazn'],
            'microsoft': ['microsft', 'micosoft', 'microsof', 'msoft'],
            'apple': ['aple', 'appl', 'applee', 'applel'],
            'twitter': ['twiter', 'twitte', 'twiter', 'twittre'],
            'instagram': ['instgram', 'instgaram', 'instagram', 'instagrm'],
            'linkedin': ['linkdin', 'linkedn', 'linkedin', 'linkdn'],
        }
        
        for brand, typos in common_typos.items():
            if brand in root_domain.lower():
                for typo in typos:
                    if typo != root_domain.lower():
                        variations.append((typo, 0.6, ['common_typo']))
        
        return [(var, conf, techs) for var, conf, techs in variations]
    
    def generate_subdomain_variations(self, domain: str) -> List[Tuple[str, float, List[str]]]:
        """Generate subdomain variations."""
        variations = []
        root_domain, tld = self.extract_root_and_tld(domain)
        
        common_subdomains = [
            'www', 'mail', 'ftp', 'api', 'admin', 'blog', 'forum', 'shop',
            'support', 'help', 'docs', 'wiki', 'dev', 'test', 'staging',
            'cdn', 'static', 'assets', 'img', 'images', 'css', 'js',
            'mobile', 'm', 'app', 'login', 'auth', 'secure', 'pay',
            'checkout', 'cart', 'orders', 'account', 'profile', 'user'
        ]
        
        for subdomain in common_subdomains:
            new_domain = f"{subdomain}.{domain}"
            variations.append((new_domain, 0.9, ['common_subdomain']))
        
        # Add subdomain variations of root domain
        for subdomain in common_subdomains:
            new_domain = f"{subdomain}.{root_domain}.{tld}"
            variations.append((new_domain, 0.7, ['subdomain_variation']))
        
        return variations
    
    def generate_similar_variations(self, root_domain: str) -> List[Tuple[str, float, List[str]]]:
        """Generate similar domain variations."""
        variations = []
        
        # Add common prefixes
        prefixes = ['get', 'my', 'the', 'go', 'try', 'use', 'join', 'meet']
        for prefix in prefixes:
            new_domain = f"{prefix}{root_domain}"
            if new_domain != root_domain:
                variations.append((new_domain, 0.5, ['prefix_addition']))
        
        # Add common suffixes
        suffixes = ['app', 'web', 'site', 'online', 'hub', 'zone', 'spot', 'plus']
        for suffix in suffixes:
            new_domain = f"{root_domain}{suffix}"
            if new_domain != root_domain:
                variations.append((new_domain, 0.5, ['suffix_addition']))
        
        # Word combinations
        if len(root_domain.split()) > 1:
            words = root_domain.split()
            # Reverse words
            reversed_domain = ' '.join(reversed(words))
            variations.append((reversed_domain.replace(' ', ''), 0.6, ['word_reversal']))
            
            # Remove spaces
            no_space = root_domain.replace(' ', '')
            if no_space != root_domain:
                variations.append((no_space, 0.7, ['space_removal']))
        
        return variations
    
    def extract_root_and_tld(self, domain: str) -> Tuple[str, str]:
        """Extract root domain and TLD."""
        parts = domain.split('.')
        if len(parts) >= 2:
            return '.'.join(parts[:-1]), parts[-1]
        return domain, ''
    
    def calculate_similarity_score(self, domain1: str, domain2: str) -> float:
        """Calculate similarity score between two domains."""
        # Use sequence matcher for similarity
        return difflib.SequenceMatcher(None, domain1.lower(), domain2.lower()).ratio()
    
    def assess_variation_risk(self, variation: DomainVariation) -> str:
        """Assess risk level of a domain variation."""
        risk_score = 0
        
        # High confidence typosquatting patterns
        if variation.variation_type == 'typosquatting':
            risk_score += 40
            
            # Check for specific high-risk techniques
            for technique in variation.techniques:
                if technique in ['character_substitution', 'homograph_attack']:
                    risk_score += 20
                elif technique == 'common_typo':
                    risk_score += 15
        
        # Different TLDs with common brands
        if variation.variation_type == 'different_tld':
            risk_score += 20
        
        # Subdomain variations are generally lower risk
        if variation.variation_type == 'subdomain':
            risk_score += 10
        
        # Similar domains
        if variation.variation_type == 'similar':
            risk_score += 15
        
        # Adjust based on confidence
        risk_score += int(variation.confidence * 10)
        
        # Determine risk level
        if risk_score >= 60:
            return 'high'
        elif risk_score >= 30:
            return 'medium'
        else:
            return 'low'
    
    async def check_domain_status(self, domain: str) -> Dict:
        """Check if a domain is active, inactive, or available."""
        try:
            import dns.resolver
            
            resolver = dns.resolver.Resolver()
            resolver.timeout = 5
            
            # Try to resolve A record
            try:
                answers = resolver.resolve(domain, 'A')
                return {'status': 'active', 'a_records': [str(rdata) for rdata in answers]}
            except dns.resolver.NXDOMAIN:
                return {'status': 'available'}
            except dns.resolver.NoAnswer:
                return {'status': 'inactive'}
            except Exception:
                return {'status': 'unknown', 'error': 'DNS resolution failed'}
                
        except ImportError:
            logger.warning("dnspython not available for domain status checking")
            return {'status': 'unknown', 'error': 'DNS library not available'}
        except Exception as e:
            logger.error(f"Error checking domain status for {domain}: {str(e)}")
            return {'status': 'unknown', 'error': str(e)}
    
    async def discover_related_domains(self, target_domain: str, search_types: List[str] = None) -> Dict:
        """Discover domains related to the target domain."""
        target_domain = self.normalize_domain(target_domain)
        
        if search_types is None:
            search_types = ['variations', 'registrant_links', 'infrastructure_links']
        
        results = {
            'target_domain': target_domain,
            'domain_variations': [],
            'related_domains': [],
            'registrant_links': [],
            'infrastructure_links': [],
            'summary': {
                'total_variations_found': 0,
                'total_related_found': 0,
                'high_risk_variations': 0,
                'active_domains': 0
            }
        }
        
        try:
            # 1. Generate domain variations
            if 'variations' in search_types:
                logger.info(f"Generating domain variations for {target_domain}")
                variations = self.generate_domain_variations(target_domain)
                
                # Check status of variations
                semaphore = asyncio.Semaphore(20)
                
                async def check_variation_status(variation):
                    async with semaphore:
                        try:
                            status_info = await self.check_domain_status(variation.domain)
                            variation.status = status_info['status']
                            
                            # Assess risk level
                            variation.risk_level = self.assess_variation_risk(variation)
                            
                            return variation
                        except Exception as e:
                            logger.debug(f"Error checking variation {variation.domain}: {str(e)}")
                            return variation
                
                # Check status for all variations concurrently
                tasks = [check_variation_status(variation) for variation in variations]
                checked_variations = await asyncio.gather(*tasks, return_exceptions=True)
                
                results['domain_variations'] = [
                    var.to_dict() for var in checked_variations 
                    if isinstance(var, DomainVariation)
                ]
                
                results['summary']['total_variations_found'] = len(results['domain_variations'])
                results['summary']['high_risk_variations'] = len([
                    var for var in results['domain_variations'] 
                    if var.get('risk_level') == 'high'
                ])
                results['summary']['active_domains'] = len([
                    var for var in results['domain_variations'] 
                    if var.get('status') == 'active'
                ])
            
            # 2. Search for registrant links (would require WHOIS databases)
            if 'registrant_links' in search_types:
                logger.info(f"Searching for registrant links for {target_domain} (requires external API)")
                # This would typically use WHOIS databases, SecurityTrails, etc.
                results['registrant_links'] = []
            
            # 3. Search for infrastructure links (same IP, ASN, nameservers)
            if 'infrastructure_links' in search_types:
                logger.info(f"Searching for infrastructure links for {target_domain} (requires external API)")
                # This would typically use reverse IP lookups, ASN databases, etc.
                results['infrastructure_links'] = []
            
            # 4. Combine all related domains
            all_related = []
            
            # Add variations as related domains
            for variation in results['domain_variations']:
                related = RelatedDomainInfo(
                    domain=variation['domain'],
                    relationship_type=variation['variation_type'],
                    confidence=variation['confidence']
                )
                related.evidence = [f"Generated as {variation['variation_type']} variation"]
                related.status = variation['status']
                all_related.append(related)
            
            # Add registrant links
            for link in results['registrant_links']:
                all_related.append(link)
            
            # Add infrastructure links
            for link in results['infrastructure_links']:
                all_related.append(link)
            
            results['related_domains'] = [domain.to_dict() for domain in all_related]
            results['summary']['total_related_found'] = len(results['related_domains'])
            
            logger.info(f"Related domain discovery completed for {target_domain}")
            
        except Exception as e:
            logger.error(f"Error in related domain discovery for {target_domain}: {str(e)}")
            results['error'] = str(e)
        
        return results
    
    async def search_domains_by_registrant(self, email: str = None, name: str = None) -> List[RelatedDomainInfo]:
        """Search for domains registered by the same person or organization."""
        related_domains = []
        
        try:
            # This would typically use WHOIS databases, SecurityTrails, etc.
            # For now, return empty results as it requires external API integration
            
            logger.info(f"Searching for domains by registrant: {email or name} (requires external API)")
            
        except Exception as e:
            logger.error(f"Error searching domains by registrant: {str(e)}")
        
        return related_domains
    
    async def search_domains_by_nameserver(self, nameserver: str) -> List[RelatedDomainInfo]:
        """Search for domains using the same nameserver."""
        related_domains = []
        
        try:
            # This would typically use DNS databases or WHOIS records
            # For now, return empty results as it requires external API integration
            
            logger.info(f"Searching for domains using nameserver: {nameserver} (requires external API)")
            
        except Exception as e:
            logger.error(f"Error searching domains by nameserver: {str(e)}")
        
        return related_domains
    
    async def search_domains_by_ip(self, ip_address: str) -> List[RelatedDomainInfo]:
        """Search for domains hosted on the same IP address."""
        related_domains = []
        
        try:
            # This would typically use reverse IP lookup APIs
            # For now, return empty results as it requires external API integration
            
            logger.info(f"Searching for domains on IP: {ip_address} (requires external API)")
            
        except Exception as e:
            logger.error(f"Error searching domains by IP: {str(e)}")
        
        return related_domains