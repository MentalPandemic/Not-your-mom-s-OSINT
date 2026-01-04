"""
WHOIS API Client

This module provides API client functionality for various WHOIS services and databases.
"""

import asyncio
import aiohttp
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class WHOISClientError(Exception):
    """Custom exception for WHOIS client failures."""
    pass


class WHOISAPIClient:
    """API client for WHOIS lookups and domain intelligence."""
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.api_key = api_key
        self.base_url = base_url or "https://api.whoisxml.com/v1"
        self.session = None
        
        # WHOIS API endpoints
        self.endpoints = {
            'domain_whois': '/domain/whois',
            'ip_whois': '/ip/whois',
            'bulk_whois': '/bulk/whois',
            'domain_search': '/domain/search',
            ' registrant_search': '/ registrant/search',
            'company_search': '/company/search'
        }
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def _make_request(self, endpoint: str, params: Dict = None) -> Dict:
        """Make a request to the WHOIS API."""
        if not self.session:
            raise WHOISClientError("Client session not initialized. Use async context manager.")
        
        url = f"{self.base_url}{endpoint}"
        headers = {'Accept': 'application/json'}
        
        if self.api_key:
            headers['X-API-Key'] = self.api_key
        
        try:
            async with self.session.get(url, params=params, headers=headers) as response:
                if response.status == 200:
                    return await response.json()
                elif response.status == 429:
                    raise WHOISClientError("Rate limit exceeded")
                else:
                    error_text = await response.text()
                    raise WHOISClientError(f"API request failed: {response.status} - {error_text}")
                    
        except aiohttp.ClientError as e:
            raise WHOISClientError(f"Network error: {str(e)}")
    
    async def get_domain_whois(self, domain: str) -> Dict:
        """Get WHOIS information for a domain."""
        params = {'domain': domain}
        return await self._make_request(self.endpoints['domain_whois'], params)
    
    async def get_ip_whois(self, ip_address: str) -> Dict:
        """Get WHOIS information for an IP address."""
        params = {'ip': ip_address}
        return await self._make_request(self.endpoints['ip_whois'], params)
    
    async def search_domains_by_registrant_email(self, email: str, limit: int = 100) -> List[Dict]:
        """Search for domains registered by a specific email."""
        params = {
            'email': email,
            'limit': limit
        }
        response = await self._make_request(self.endpoints[' registrant_search'], params)
        return response.get('domains', [])
    
    async def search_domains_by_registrant_name(self, name: str, limit: int = 100) -> List[Dict]:
        """Search for domains registered by a specific name."""
        params = {
            'name': name,
            'limit': limit
        }
        response = await self._make_request(self.endpoints[' registrant_search'], params)
        return response.get('domains', [])
    
    async def search_domains_by_company(self, company: str, limit: int = 100) -> List[Dict]:
        """Search for domains registered by a specific company."""
        params = {
            'company': company,
            'limit': limit
        }
        response = await self._make_request(self.endpoints['company_search'], params)
        return response.get('domains', [])
    
    async def bulk_whois_lookup(self, domains: List[str]) -> List[Dict]:
        """Perform bulk WHOIS lookups."""
        params = {
            'domains': ','.join(domains)
        }
        response = await self._make_request(self.endpoints['bulk_whois'], params)
        return response.get('results', [])
    
    async def search_domains_by_nameserver(self, nameserver: str, limit: int = 100) -> List[Dict]:
        """Search for domains using a specific nameserver."""
        params = {
            'nameserver': nameserver,
            'limit': limit
        }
        response = await self._make_request('/nameserver/search', params)
        return response.get('domains', [])


class SecurityTrailsClient:
    """SecurityTrails API client for domain intelligence."""
    
    def __init__(self, api_key: Optional[str] = None):
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
            raise WHOISClientError("Client session not initialized. Use async context manager.")
        
        url = f"{self.base_url}{endpoint}"
        headers = {'Accept': 'application/json'}
        
        if self.api_key:
            headers['API-Key'] = self.api_key
        
        try:
            async with self.session.get(url, params=params, headers=headers) as response:
                if response.status == 200:
                    return await response.json()
                elif response.status == 429:
                    raise WHOISClientError("Rate limit exceeded")
                else:
                    error_text = await response.text()
                    raise WHOISClientError(f"SecurityTrails API request failed: {response.status} - {error_text}")
                    
        except aiohttp.ClientError as e:
            raise WHOISClientError(f"Network error: {str(e)}")
    
    async def get_domain_info(self, domain: str) -> Dict:
        """Get comprehensive domain information."""
        return await self._make_request(f"/domain/{domain}/info")
    
    async def get_domain_subdomains(self, domain: str) -> List[str]:
        """Get subdomains for a domain."""
        response = await self._make_request(f"/domain/{domain}/subdomains")
        return response.get('subdomains', [])
    
    async def get_domain_dns(self, domain: str) -> Dict:
        """Get DNS history for a domain."""
        return await self._make_request(f"/domain/{domain}/dns")
    
    async def get_domain_whois(self, domain: str) -> Dict:
        """Get WHOIS history for a domain."""
        return await self._make_request(f"/domain/{domain}/whois")
    
    async def search_domains_by_email(self, email: str) -> List[Dict]:
        """Search for domains by registrant email."""
        params = {'email': email}
        response = await self._make_request("/domains/search", params)
        return response.get('domains', [])
    
    async def search_domains_by_name(self, name: str) -> List[Dict]:
        """Search for domains by registrant name."""
        params = {'name': name}
        response = await self._make_request("/domains/search", params)
        return response.get('domains', [])
    
    async def get_ip_info(self, ip_address: str) -> Dict:
        """Get information about an IP address."""
        return await self._make_request(f"/ips/{ip_address}")
    
    async def get_associated_domains(self, ip_address: str) -> List[str]:
        """Get domains associated with an IP address."""
        response = await self._make_request(f"/ips/{ip_address}/domains")
        return response.get('domains', [])
    
    async def get_hosting_history(self, domain: str) -> List[Dict]:
        """Get hosting history for a domain."""
        response = await self._make_request(f"/domain/{domain}/hosting")
        return response.get('hosting', [])


class WhoisXMLClient(WHOISAPIClient):
    """WhoisXML API client (extends base WHOIS client)."""
    
    def __init__(self, api_key: str):
        super().__init__(api_key, "https://domainwhoisdatabase.com/api/v1")
    
    async def get_domain_analysis(self, domain: str) -> Dict:
        """Get comprehensive domain analysis."""
        return await self._make_request("/domain/analysis", {'domain': domain})
    
    async def get_registrant_info(self, email: str) -> Dict:
        """Get registrant information by email."""
        return await self._make_request("/registrant/info", {'email': email})


# Rate limiting and caching decorators
class RateLimiter:
    """Simple rate limiter for API calls."""
    
    def __init__(self, max_calls: int, time_window: int):
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls = []
    
    async def wait_if_needed(self):
        """Wait if rate limit would be exceeded."""
        now = datetime.now().timestamp()
        
        # Remove old calls outside time window
        self.calls = [call_time for call_time in self.calls if now - call_time < self.time_window]
        
        if len(self.calls) >= self.max_calls:
            # Calculate wait time
            oldest_call = min(self.calls)
            wait_time = self.time_window - (now - oldest_call)
            if wait_time > 0:
                logger.info(f"Rate limit reached, waiting {wait_time:.2f} seconds")
                await asyncio.sleep(wait_time)
        
        # Add current call
        self.calls.append(now)


def rate_limited(calls_per_minute: int = 60):
    """Decorator to rate limit API calls."""
    def decorator(func):
        limiter = RateLimiter(calls_per_minute, 60)
        
        async def wrapper(*args, **kwargs):
            await limiter.wait_if_needed()
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


# Utility functions
def format_whois_data(whois_data: Dict) -> Dict:
    """Format WHOIS data from API responses."""
    formatted = {
        'domain': whois_data.get('domainName', whois_data.get('domain')),
        'registrant_name': whois_data.get('registrantName', whois_data.get('name')),
        'registrant_email': whois_data.get('registrantEmail', whois_data.get('email')),
        'registrant_phone': whois_data.get('registrantTelephone', whois_data.get('phone')),
        'registrar': whois_data.get('registrarName', whois_data.get('registrar')),
        'registration_date': whois_data.get('creationDate'),
        'expiration_date': whois_data.get('expirationDate'),
        'name_servers': whois_data.get('nameServers', whois_data.get('nserver', [])),
        'status': whois_data.get('domainStatus', whois_data.get('status'))
    }
    
    # Convert dates to ISO format if present
    for date_field in ['registration_date', 'expiration_date']:
        if formatted[date_field]:
            try:
                if isinstance(formatted[date_field], str):
                    # Try to parse common date formats
                    from dateutil import parser
                    formatted[date_field] = parser.parse(formatted[date_field]).isoformat()
            except:
                pass
    
    return formatted