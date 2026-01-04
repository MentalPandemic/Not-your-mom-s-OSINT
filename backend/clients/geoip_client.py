"""
IP Geolocation Client using MaxMind GeoIP2.

Provides IP geolocation data including country, city, ISP, and ASN information.
"""

import asyncio
import logging
import os
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

import geoip2.database
import geoip2.errors

logger = logging.getLogger(__name__)


@dataclass
class GeoLocation:
    """Geolocation information for an IP address."""
    ip_address: str
    country_code: Optional[str] = None
    country_name: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    state_code: Optional[str] = None
    postal_code: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    timezone: Optional[str] = None
    is_in_european_union: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "ip_address": self.ip_address,
            "country_code": self.country_code,
            "country_name": self.country_name,
            "city": self.city,
            "state": self.state,
            "state_code": self.state_code,
            "postal_code": self.postal_code,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "timezone": self.timezone,
            "is_in_european_union": self.is_in_european_union,
        }


@dataclass
class AsnInfo:
    """ASN (Autonomous System Number) information."""
    asn: Optional[str] = None
    asn_decimal: Optional[int] = None
    organization: Optional[str] = None
    network: Optional[str] = None
    name: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "asn": self.asn,
            "asn_decimal": self.asn_decimal,
            "organization": self.organization,
            "network": self.network,
            "name": self.name,
        }


@dataclass
class GeoIpResult:
    """Complete geolocation result for an IP address."""
    ip_address: str
    location: Optional[GeoLocation] = None
    isp: Optional[str] = None
    connection_type: Optional[str] = None
    asn: Optional[AsnInfo] = None
    is_bogon: bool = False
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "ip_address": self.ip_address,
            "location": self.location.to_dict() if self.location else None,
            "isp": self.isp,
            "connection_type": self.connection_type,
            "asn": self.asn.to_dict() if self.asn else None,
            "is_bogon": self.is_bogon,
            "error": self.error,
        }


class GeoIpClient:
    """
    Client for IP geolocation using MaxMind GeoIP2.
    
    Requires GeoIP2 database files:
    - GeoLite2-City.mmdb (city-level geolocation)
    - GeoLite2-ASN.mmdb (ASN information)
    
    Databases can be downloaded from:
    https://dev.maxmind.com/geoip/geolite2-free-geolocation-data
    """
    
    DEFAULT_CITY_DB = "/usr/share/GeoIP/GeoLite2-City.mmdb"
    DEFAULT_ASN_DB = "/usr/share/GeoIP/GeoLite2-ASN.mmdb"
    
    def __init__(
        self,
        city_db_path: Optional[str] = None,
        asn_db_path: Optional[str] = None,
        cache_size: int = 1000,
    ):
        self.city_db_path = city_db_path or os.environ.get(
            "GEOIP_CITY_DB",
            self.DEFAULT_CITY_DB,
        )
        self.asn_db_path = asn_db_path or os.environ.get(
            "GEOIP_ASN_DB",
            self.DEFAULT_ASN_DB,
        )
        self._city_reader = None
        self._asn_reader = None
        self._cache: Dict[str, GeoIpResult] = {}
        self._cache_size = cache_size
        
    @property
    def city_reader(self):
        """Get or create city database reader."""
        if self._city_reader is None:
            if os.path.exists(self.city_db_path):
                self._city_reader = geoip2.database.Reader(self.city_db_path)
            else:
                logger.warning(f"City database not found at {self.city_db_path}")
        return self._city_reader
    
    @property
    def asn_reader(self):
        """Get or create ASN database reader."""
        if self._asn_reader is None:
            if os.path.exists(self.asn_db_path):
                self._asn_reader = geoip2.database.Reader(self.asn_db_path)
            else:
                logger.warning(f"ASN database not found at {self.asn_db_path}")
        return self._asn_reader
    
    def lookup(
        self,
        ip_address: str,
        use_cache: bool = True,
    ) -> GeoIpResult:
        """
        Look up geolocation for an IP address.
        
        Args:
            ip_address: IP address to look up
            use_cache: Whether to use cached results
            
        Returns:
            GeoIpResult with location and ISP information
        """
        # Check cache
        if use_cache and ip_address in self._cache:
            return self._cache[ip_address]
        
        result = GeoIpResult(ip_address=ip_address)
        
        try:
            # Check if bogon IP
            if self._is_bogon(ip_address):
                result.is_bogon = True
                return result
            
            # Get city-level geolocation
            if self.city_reader:
                try:
                    city_response = self.city_reader.city(ip_address)
                    location = GeoLocation(
                        ip_address=ip_address,
                        country_code=city_response.country.iso_code,
                        country_name=city_response.country.name,
                        city=city_response.city.name,
                        state=city_response.subdivisions.most_specific.name if city_response.subdivisions else None,
                        state_code=city_response.subdivisions.most_specific.iso_code if city_response.subdivisions else None,
                        postal_code=city_response.postal.code,
                        latitude=city_response.location.latitude,
                        longitude=city_response.location.longitude,
                        timezone=city_response.location.time_zone,
                        is_in_european_union=city_response.country.is_in_european_union,
                    )
                    result.location = location
                    result.isp = city_response.traits.isp
                    result.connection_type = city_response.traits.connection_type
                except geoip2.errors.AddressNotFoundError:
                    logger.debug(f"IP not found in city database: {ip_address}")
                except Exception as e:
                    logger.error(f"City lookup error for {ip_address}: {e}")
            
            # Get ASN information
            if self.asn_reader:
                try:
                    asn_response = self.asn_reader.asn(ip_address)
                    result.asn = AsnInfo(
                        asn=f"AS{asn_response.autonomous_system_number}",
                        asn_decimal=asn_response.autonomous_system_number,
                        organization=asn_response.autonomous_system_organization,
                    )
                except geoip2.errors.AddressNotFoundError:
                    logger.debug(f"IP not found in ASN database: {ip_address}")
                except Exception as e:
                    logger.error(f"ASN lookup error for {ip_address}: {e}")
                    
        except Exception as e:
            logger.error(f"Geolocation lookup failed for {ip_address}: {e}")
            result.error = str(e)
        
        # Cache result
        if use_cache:
            if len(self._cache) >= self._cache_size:
                # Remove oldest entry
                oldest_key = next(iter(self._cache))
                del self._cache[oldest_key]
            self._cache[ip_address] = result
        
        return result
    
    async def lookup_async(
        self,
        ip_address: str,
        use_cache: bool = True,
    ) -> GeoIpResult:
        """Async wrapper for lookup."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.lookup(ip_address, use_cache),
        )
    
    async def lookup_multiple(
        self,
        ip_addresses: list[str],
        use_cache: bool = True,
    ) -> Dict[str, GeoIpResult]:
        """
        Look up geolocation for multiple IP addresses.
        
        Args:
            ip_addresses: List of IP addresses
            use_cache: Whether to use cached results
            
        Returns:
            Dictionary mapping IP to GeoIpResult
        """
        loop = asyncio.get_event_loop()
        
        results = await loop.run_in_executor(
            None,
            lambda: {ip: self.lookup(ip, use_cache) for ip in ip_addresses},
        )
        
        return results
    
    def lookup_asn(
        self,
        ip_address: str,
    ) -> Optional[AsnInfo]:
        """
        Look up ASN information for an IP address.
        
        Args:
            ip_address: IP address to look up
            
        Returns:
            AsnInfo or None if not found
        """
        if not self.asn_reader:
            return None
        
        try:
            asn_response = self.asn_reader.asn(ip_address)
            return AsnInfo(
                asn=f"AS{asn_response.autonomous_system_number}",
                asn_decimal=asn_response.autonomous_system_number,
                organization=asn_response.autonomous_system_organization,
            )
        except geoip2.errors.AddressNotFoundError:
            return None
        except Exception as e:
            logger.error(f"ASN lookup error for {ip_address}: {e}")
            return None
    
    def lookup_location(
        self,
        ip_address: str,
    ) -> Optional[GeoLocation]:
        """
        Look up location information for an IP address.
        
        Args:
            ip_address: IP address to look up
            
        Returns:
            GeoLocation or None if not found
        """
        if not self.city_reader:
            return None
        
        try:
            city_response = self.city_reader.city(ip_address)
            return GeoLocation(
                ip_address=ip_address,
                country_code=city_response.country.iso_code,
                country_name=city_response.country.name,
                city=city_response.city.name,
                state=city_response.subdivisions.most_specific.name if city_response.subdivisions else None,
                state_code=city_response.subdivisions.most_specific.iso_code if city_response.subdivisions else None,
                postal_code=city_response.postal.code,
                latitude=city_response.location.latitude,
                longitude=city_response.location.longitude,
                timezone=city_response.location.time_zone,
                is_in_european_union=city_response.country.is_in_european_union,
            )
        except geoip2.errors.AddressNotFoundError:
            return None
        except Exception as e:
            logger.error(f"Location lookup error for {ip_address}: {e}")
            return None
    
    def _is_bogon(self, ip_address: str) -> bool:
        """Check if IP address is a bogon (non-routable) address."""
        # RFC 1918 private addresses
        private_ranges = [
            ("10.0.0.0", "10.255.255.255"),
            ("172.16.0.0", "172.31.255.255"),
            ("192.168.0.0", "192.168.255.255"),
        ]
        
        # Loopback
        if ip_address.startswith("127."):
            return True
        
        # Link-local
        if ip_address.startswith("169.254."):
            return True
        
        # Check private ranges
        import ipaddress
        try:
            ip = ipaddress.ip_address(ip_address)
            for start, end in private_ranges:
                start_ip = ipaddress.ip_address(start)
                end_ip = ipaddress.ip_address(end)
                if start_ip <= ip <= end_ip:
                    return True
        except ValueError:
            pass
        
        return False
    
    def clear_cache(self):
        """Clear the geolocation cache."""
        self._cache.clear()
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            "size": len(self._cache),
            "max_size": self._cache_size,
        }
    
    def close(self):
        """Close database readers."""
        if self._city_reader:
            self._city_reader.close()
            self._city_reader = None
        if self._asn_reader:
            self._asn_reader.close()
            self._asn_reader = None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
