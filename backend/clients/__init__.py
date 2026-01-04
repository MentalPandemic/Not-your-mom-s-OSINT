"""
API Clients for Domain Intelligence Module.

This package provides clients for various external APIs used in domain intelligence:
- WHOIS lookups
- DNS resolution
- Certificate Transparency (CT) logs
- Censys (certificates and hosts)
- Shodan (devices and vulnerabilities)
- SecurityTrails (historical DNS and WHOIS)
- IP Geolocation (MaxMind GeoIP2)
"""

from .dns_client import DnsClient, DnsLookupFailed
from .dns_client_base import BaseDnsClient, DnsRecord, DnsResult
from .ct_client import CtClient, CtSearchResult, CertificateInfo
from .censys_client import (
    CensysClient,
    CensysHost,
    CensysCertificate,
    CensysSearchResult,
)
from .shodan_client import (
    ShodanClient,
    ShodanHost,
    ShodanService,
    ShodanSearchResult,
    ShodanExploit,
)
from .securitytrails_client import (
    SecurityTrailsClient,
    SecurityTrailsDomain,
    SecurityTrailsHistory,
    SubdomainInfo,
    HistoricalRecord,
)
from .geoip_client import (
    GeoIpClient,
    GeoIpResult,
    GeoLocation,
    AsnInfo,
)

__all__ = [
    # DNS
    "DnsClient",
    "DnsLookupFailed",
    "BaseDnsClient",
    "DnsRecord",
    "DnsResult",
    # Certificate Transparency
    "CtClient",
    "CtSearchResult",
    "CertificateInfo",
    # Censys
    "CensysClient",
    "CensysHost",
    "CensysCertificate",
    "CensysSearchResult",
    # Shodan
    "ShodanClient",
    "ShodanHost",
    "ShodanService",
    "ShodanSearchResult",
    "ShodanExploit",
    # SecurityTrails
    "SecurityTrailsClient",
    "SecurityTrailsDomain",
    "SecurityTrailsHistory",
    "SubdomainInfo",
    "HistoricalRecord",
    # GeoIP
    "GeoIpClient",
    "GeoIpResult",
    "GeoLocation",
    "AsnInfo",
]
