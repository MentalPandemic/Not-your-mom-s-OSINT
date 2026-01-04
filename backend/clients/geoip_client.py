"""
GeoIP API Client

This module provides client functionality for IP geolocation services
including MaxMind GeoIP2 and other geolocation databases.
"""

import asyncio
import aiohttp
import json
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class GeoIPClientError(Exception):
    """Custom exception for GeoIP client failures."""
    pass


class MaxMindGeoIPClient:
    """MaxMind GeoIP2 API client."""
    
    def __init__(self, account_id: str, license_key: str):
        self.account_id = account_id
        self.license_key = license_key
        self.base_url = "https://geoip.maxmind.com/geoip/v2.1"
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def _make_request(self, endpoint: str, params: Dict = None) -> Dict:
        """Make a request to MaxMind GeoIP API."""
        if not self.session:
            raise GeoIPClientError("Client session not initialized. Use async context manager.")
        
        url = f"{self.base_url}{endpoint}"
        auth = aiohttp.BasicAuth(self.account_id, self.license_key)
        
        try:
            async with self.session.get(url, params=params, auth=auth) as response:
                if response.status == 200:
                    return await response.json()
                elif response.status == 401:
                    raise GeoIPClientError("Invalid MaxMind credentials")
                elif response.status == 403:
                    raise GeoIPClientError("Access forbidden - check API permissions")
                elif response.status == 429:
                    raise GeoIPClientError("Rate limit exceeded")
                else:
                    error_text = await response.text()
                    raise GeoIPClientError(f"MaxMind API request failed: {response.status} - {error_text}")
                    
        except aiohttp.ClientError as e:
            raise GeoIPClientError(f"Network error: {str(e)}")
    
    async def lookup_ip(self, ip_address: str) -> Dict:
        """Lookup geolocation information for an IP address."""
        endpoint = f"/city/{ip_address}"
        return await self._make_request(endpoint)
    
    async def lookup_ip_insights(self, ip_address: str) -> Dict:
        """Lookup detailed insights for an IP address."""
        endpoint = f"/insights/{ip_address}"
        return await self._make_request(endpoint)
    
    async def bulk_lookup(self, ip_addresses: List[str]) -> List[Dict]:
        """Perform bulk IP geolocation lookups."""
        results = []
        
        # MaxMind allows bulk lookups with comma-separated IPs
        ips_param = ','.join(ip_addresses)
        endpoint = f"/city/{ips_param}"
        
        try:
            response = await self._make_request(endpoint)
            # Convert single response to list format
            if isinstance(response, dict) and 'traits' in response:
                results.append(response)
            elif isinstance(response, list):
                results = response
        except Exception as e:
            logger.error(f"Bulk lookup failed: {str(e)}")
            # Fallback to individual lookups
            for ip in ip_addresses:
                try:
                    result = await self.lookup_ip(ip)
                    results.append(result)
                except Exception as e:
                    logger.warning(f"Failed to lookup {ip}: {str(e)}")
                    results.append({'ip': ip, 'error': str(e)})
        
        return results


class IP2LocationClient:
    """IP2Location API client."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "http://api.ip2location.com/v2"
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def _make_request(self, ip: str, package: str = 'WS3') -> Dict:
        """Make a request to IP2Location API."""
        if not self.session:
            raise GeoIPClientError("Client session not initialized. Use async context manager.")
        
        url = f"{self.base_url}/"
        params = {
            'ip': ip,
            'key': self.api_key,
            'package': package,
            'format': 'json'
        }
        
        try:
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    return await response.json()
                elif response.status == 401:
                    raise GeoIPClientError("Invalid IP2Location API key")
                elif response.status == 429:
                    raise GeoIPClientError("Rate limit exceeded")
                else:
                    error_text = await response.text()
                    raise GeoIPClientError(f"IP2Location API request failed: {response.status} - {error_text}")
                    
        except aiohttp.ClientError as e:
            raise GeoIPClientError(f"Network error: {str(e)}")
    
    async def lookup_ip(self, ip_address: str, package: str = 'WS3') -> Dict:
        """Lookup geolocation information for an IP address."""
        return await self._make_request(ip_address, package)


class IPGeolocationClient:
    """Generic IP geolocation client using free APIs."""
    
    def __init__(self):
        self.session = None
        self.free_apis = [
            {
                'name': 'ip-api.com',
                'url': 'http://ip-api.com/json/{ip}',
                'fields': ['query', 'status', 'country', 'countryCode', 'region', 
                          'regionName', 'city', 'zip', 'lat', 'lon', 'timezone', 
                          'isp', 'org', 'as', 'proxy']
            },
            {
                'name': 'ipapi.co',
                'url': 'http://ipapi.co/{ip}/json/',
                'fields': ['ip', 'city', 'region', 'country', 'country_code', 
                          'latitude', 'longitude', 'timezone', 'org', 'asn']
            },
            {
                'name': 'ipinfo.io',
                'url': 'http://ipinfo.io/{ip}/json',
                'fields': ['ip', 'city', 'region', 'country', 'loc', 'org', 'postal']
            }
        ]
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def lookup_ip(self, ip_address: str, service: str = 'ip-api.com') -> Dict:
        """Lookup IP geolocation using specified service."""
        if not self.session:
            raise GeoIPClientError("Client session not initialized. Use async context manager.")
        
        # Find the service
        api_info = next((api for api in self.free_apis if api['name'] == service), None)
        if not api_info:
            raise GeoIPClientError(f"Unknown service: {service}")
        
        url = api_info['url'].format(ip=ip_address)
        
        try:
            async with self.session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._normalize_data(data, service)
                else:
                    raise GeoIPClientError(f"{service} API request failed: {response.status}")
                    
        except aiohttp.ClientError as e:
            raise GeoIPClientError(f"Network error with {service}: {str(e)}")
    
    def _normalize_data(self, data: Dict, service: str) -> Dict:
        """Normalize data from different services to common format."""
        normalized = {
            'ip': data.get('query') or data.get('ip'),
            'country': data.get('country'),
            'country_code': data.get('countryCode') or data.get('country_code'),
            'region': data.get('regionName') or data.get('region'),
            'city': data.get('city'),
            'postal_code': data.get('zip') or data.get('postal'),
            'latitude': data.get('lat') or data.get('latitude') or (float(data.get('loc', '0,0').split(',')[0]) if data.get('loc') else None),
            'longitude': data.get('lon') or data.get('longitude') or (float(data.get('loc', '0,0').split(',')[1]) if data.get('loc') else None),
            'timezone': data.get('timezone'),
            'isp': data.get('isp') or data.get('org'),
            'organization': data.get('org'),
            'asn': data.get('as', '').split()[0] if data.get('as') else None,
            'is_proxy': data.get('proxy', False),
            'source': service
        }
        
        return normalized
    
    async def lookup_ip_multiple_services(self, ip_address: str) -> List[Dict]:
        """Lookup IP geolocation using multiple services for verification."""
        results = []
        
        for api_info in self.free_apis:
            try:
                result = await self.lookup_ip(ip_address, api_info['name'])
                results.append(result)
            except Exception as e:
                logger.warning(f"Failed to get geolocation from {api_info['name']}: {str(e)}")
                continue
        
        return results


# Analysis and Intelligence Functions
def analyze_geolocation_data(geo_data_list: List[Dict]) -> Dict:
    """Analyze geolocation data from multiple sources."""
    if not geo_data_list:
        return {'error': 'No geolocation data to analyze'}
    
    analysis = {
        'consensus_location': None,
        'confidence': 0,
        'sources_agreeing': 0,
        'total_sources': len(geo_data_list),
        'location_variance': {},
        'isp_consensus': None,
        'proxy_detection': {}
    }
    
    # Extract location components
    countries = [data.get('country') for data in geo_data_list if data.get('country')]
    country_codes = [data.get('country_code') for data in geo_data_list if data.get('country_code')]
    cities = [data.get('city') for data in geo_data_list if data.get('city')]
    regions = [data.get('region') for data in geo_data_list if data.get('region')]
    
    isps = [data.get('isp') for data in geo_data_list if data.get('isp')]
    organizations = [data.get('organization') for data in geo_data_list if data.get('organization')]
    
    # Find consensus location
    if country_codes:
        country_consensus = max(set(country_codes), key=country_codes.count)
        country_votes = country_codes.count(country_consensus)
        analysis['consensus_location'] = {
            'country': next((data.get('country') for data in geo_data_list 
                           if data.get('country_code') == country_consensus), country_consensus),
            'country_code': country_consensus,
            'confidence': country_votes / len(country_codes)
        }
        analysis['sources_agreeing'] = country_votes
    
    # ISP consensus
    if isps or organizations:
        all_orgs = isps + organizations
        if all_orgs:
            org_consensus = max(set(all_orgs), key=all_orgs.count)
            org_votes = all_orgs.count(org_consensus)
            analysis['isp_consensus'] = {
                'organization': org_consensus,
                'confidence': org_votes / len(all_orgs)
            }
    
    # Location variance
    latitudes = [data.get('latitude') for data in geo_data_list if data.get('latitude')]
    longitudes = [data.get('longitude') for data in geo_data_list if data.get('longitude')]
    
    if latitudes and longitudes:
        lat_variance = max(latitudes) - min(latitudes) if len(latitudes) > 1 else 0
        lon_variance = max(longitudes) - min(longitudes) if len(longitudes) > 1 else 0
        
        analysis['location_variance'] = {
            'latitude_range': lat_variance,
            'longitude_range': lon_variance,
            'total_variance': lat_variance + lon_variance
        }
    
    # Proxy detection
    proxy_sources = [data for data in geo_data_list if data.get('is_proxy', False)]
    analysis['proxy_detection'] = {
        'proxy_detected': len(proxy_sources) > 0,
        'sources_detecting_proxy': len(proxy_sources),
        'total_sources': len(geo_data_list)
    }
    
    # Overall confidence calculation
    location_confidence = analysis['consensus_location']['confidence'] if analysis['consensus_location'] else 0
    proxy_penalty = 0.3 if analysis['proxy_detection']['proxy_detected'] else 0
    
    analysis['overall_confidence'] = max(0, location_confidence - proxy_penalty)
    
    return analysis


def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two coordinates using Haversine formula."""
    import math
    
    # Convert to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    # Earth's radius in kilometers
    r = 6371
    
    return c * r


def detect_suspicious_geolocation_patterns(geo_data_list: List[Dict], ip_info: Dict = None) -> List[Dict]:
    """Detect suspicious patterns in geolocation data."""
    suspicious_patterns = []
    
    if not geo_data_list:
        return suspicious_patterns
    
    # Check for conflicting geolocation data
    latitudes = [data.get('latitude') for data in geo_data_list if data.get('latitude')]
    longitudes = [data.get('longitude') for data in geo_data_list if data.get('longitude')]
    
    if len(latitudes) > 1 and len(longitudes) > 1:
        lat_range = max(latitudes) - min(latitudes)
        lon_range = max(longitudes) - min(longitudes)
        
        # Large discrepancies suggest VPN/proxy usage
        if lat_range > 10 or lon_range > 10:  # More than ~1000km difference
            suspicious_patterns.append({
                'type': 'geolocation_inconsistency',
                'severity': 'medium',
                'description': 'Large geolocation discrepancies detected',
                'evidence': {
                    'latitude_range': lat_range,
                    'longitude_range': lon_range
                }
            })
    
    # Check for high-risk countries
    high_risk_countries = ['CN', 'RU', 'KP', 'IR', 'SY']
    countries = [data.get('country_code') for data in geo_data_list if data.get('country_code')]
    
    for country in countries:
        if country in high_risk_countries:
            suspicious_patterns.append({
                'type': 'high_risk_country',
                'severity': 'low',
                'country': country,
                'description': f'IP located in high-risk country: {country}'
            })
    
    # Check for data center IP ranges
    if ip_info:
        org = ip_info.get('organization', '').lower()
        isp = ip_info.get('isp', '').lower()
        
        data_center_indicators = [
            'amazon', 'aws', 'google', 'microsoft', 'azure', 'cloudflare',
            'digitalocean', 'linode', 'vultr', 'contabo', 'ovh', 'hetzner'
        ]
        
        for indicator in data_center_indicators:
            if indicator in org or indicator in isp:
                suspicious_patterns.append({
                    'type': 'data_center_ip',
                    'severity': 'low',
                    'provider': indicator,
                    'description': f'IP appears to be from data center: {indicator}'
                })
                break
    
    # Check for proxy/VPN indicators
    proxy_sources = [data for data in geo_data_list if data.get('is_proxy', False)]
    if proxy_sources:
        suspicious_patterns.append({
            'type': 'proxy_detected',
            'severity': 'high',
            'sources_detecting_proxy': len(proxy_sources),
            'description': 'Proxy/VPN usage detected by multiple sources'
        })
    
    return suspicious_patterns


def create_geolocation_fingerprint(ip_address: str, geo_data_list: List[Dict]) -> Dict:
    """Create a geolocation fingerprint for an IP address."""
    if not geo_data_list:
        return {'ip': ip_address, 'error': 'No geolocation data available'}
    
    # Calculate consensus data
    countries = [data.get('country') for data in geo_data_list if data.get('country')]
    country_codes = [data.get('country_code') for data in geo_data_list if data.get('country_code')]
    cities = [data.get('city') for data in geo_data_list if data.get('city')]
    regions = [data.get('region') for data in geo_data_list if data.get('region')]
    
    isps = [data.get('isp') for data in geo_data_list if data.get('isp')]
    organizations = [data.get('organization') for data in geo_data_list if data.get('organization')]
    
    # Calculate consensus values
    country = max(set(countries), key=countries.count) if countries else None
    country_code = max(set(country_codes), key=country_codes.count) if country_codes else None
    city = max(set(cities), key=cities.count) if cities else None
    region = max(set(regions), key=regions.count) if regions else None
    
    # Calculate average coordinates
    latitudes = [data.get('latitude') for data in geo_data_list if data.get('latitude')]
    longitudes = [data.get('longitude') for data in geo_data_list if data.get('longitude')]
    
    avg_lat = sum(latitudes) / len(latitudes) if latitudes else None
    avg_lon = sum(longitudes) / len(longitudes) if longitudes else None
    
    # Most common ISP/Organization
    all_orgs = isps + organizations
    main_org = max(set(all_orgs), key=all_orgs.count) if all_orgs else None
    
    return {
        'ip': ip_address,
        'location': {
            'country': country,
            'country_code': country_code,
            'region': region,
            'city': city,
            'latitude': avg_lat,
            'longitude': avg_lon
        },
        'organization': main_org,
        'data_sources': [data.get('source') for data in geo_data_list],
        'confidence': len(geo_data_list),
        'last_updated': datetime.utcnow().isoformat(),
        'raw_data': geo_data_list
    }