"""
Pytest configuration and fixtures for domain intelligence tests.
"""

import asyncio
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_dns_client():
    """Mock DNS client for testing."""
    from clients.dns_client import DnsResult, DnsRecord
    
    mock_client = MagicMock()
    mock_client.resolve = AsyncMock(return_value=DnsResult(
        domain="example.com",
        record_type="A",
        records=[
            DnsRecord(value="93.184.216.34", ttl=3600),
            DnsRecord(value="93.184.216.35", ttl=3600),
        ],
        found=True,
    ))
    return mock_client


@pytest.fixture
def mock_whois_lookup():
    """Mock WHOIS lookup for testing."""
    from modules.whois_lookup import DomainWhoisResult, RegistrantInfo
    
    mock = MagicMock()
    mock.lookup_domain = AsyncMock(return_value=DomainWhoisResult(
        domain="example.com",
        registrant=RegistrantInfo(
            name="John Doe",
            email="john@example.com",
            organization="Example Corp",
            country="US",
        ),
        registrar="GoDaddy.com",
        nameservers=["ns1.example.com", "ns2.example.com"],
    ))
    return mock


@pytest.fixture
def mock_securitytrails():
    """Mock SecurityTrails client for testing."""
    mock = MagicMock()
    mock.get_domain = AsyncMock(return_value=MagicMock(
        hostname="example.com",
        created_date=None,
        updated_date=None,
        registrar="GoDaddy.com",
        registrant_name="John Doe",
        registrant_email="john@example.com",
        registrant_organization="Example Corp",
        registrant_country="US",
        nameservers=["ns1.example.com", "ns2.example.com"],
        dnssec=False,
    ))
    mock.get_subdomains = AsyncMock(return_value=[])
    mock.search_by_email = AsyncMock(return_value=[])
    mock.get_dns_history = AsyncMock(return_value=MagicMock(
        hostname="example.com",
        a_records=[],
        aaaa_records=[],
        mx_records=[],
        ns_records=[],
        txt_records=[],
        soa_records=[],
    ))
    mock.get_associated_domains = AsyncMock(return_value={
        "registrant": [],
        "ip": [],
        "nameserver": [],
    })
    mock.close = AsyncMock()
    return mock


@pytest.fixture
def mock_geoip():
    """Mock GeoIP client for testing."""
    from clients.geoip_client import GeoIpResult, GeoLocation, AsnInfo
    
    mock = MagicMock()
    mock.lookup = MagicMock(return_value=GeoIpResult(
        ip_address="8.8.8.8",
        location=GeoLocation(
            ip_address="8.8.8.8",
            country_code="US",
            country_name="United States",
            city="Mountain View",
            latitude=37.3861,
            longitude=-122.0839,
            timezone="America/Los_Angeles",
        ),
        isp="Google LLC",
        asn=AsnInfo(
            asn="AS15169",
            asn_decimal=15169,
            organization="Google LLC",
        ),
        is_bogon=False,
    ))
    mock.close = MagicMock()
    return mock


@pytest.fixture
def mock_censys():
    """Mock Censys client for testing."""
    mock = MagicMock()
    mock.search_hosts = AsyncMock(return_value=MagicMock(
        hosts=[],
        total=0,
    ))
    mock.search_certificates = AsyncMock(return_value=MagicMock(
        certificates=[],
        total=0,
    ))
    mock.search_domains_on_ip = AsyncMock(return_value=[])
    mock.search_by_issuer = AsyncMock(return_value=[])
    mock.close = AsyncMock()
    return mock


@pytest.fixture
def mock_shodan():
    """Mock Shodan client for testing."""
    mock = MagicMock()
    mock.host = AsyncMock(return_value=MagicMock(
        ip="8.8.8.8",
        ports=[80, 443],
        services={},
        hostnames=[],
        domains=[],
    ))
    mock.search = AsyncMock(return_value=MagicMock(
        hosts=[],
        total=0,
    ))
    mock.search_domains_on_ip = AsyncMock(return_value=[])
    mock.close = AsyncMock()
    return mock


@pytest.fixture
def mock_ct_client():
    """Mock Certificate Transparency client for testing."""
    mock = MagicMock()
    mock.search_certificates = AsyncMock(return_value=MagicMock(
        domain="example.com",
        certificates=[],
        subdomains=[],
        total_results=0,
    ))
    mock.close = AsyncMock()
    return mock


@pytest.fixture
def sample_domain_data():
    """Sample domain data for testing."""
    return {
        "domain": "example.com",
        "registrant": {
            "name": "John Doe",
            "email": "john@example.com",
            "organization": "Example Corp",
            "country": "US",
            "phone": "+1.5551234567",
        },
        "registrar": {
            "name": "GoDaddy.com",
            "url": "https://www.godaddy.com",
            "iana_id": "146",
        },
        "nameservers": [
            "ns1.example.com",
            "ns2.example.com",
            "ns3.example.com",
        ],
        "dates": {
            "registered": "2020-01-01T00:00:00Z",
            "expires": "2030-01-01T00:00:00Z",
            "updated": "2023-06-01T00:00:00Z",
        },
    }


@pytest.fixture
def sample_dns_records():
    """Sample DNS records for testing."""
    return {
        "a": [
            {"value": "93.184.216.34", "ttl": 3600},
            {"value": "93.184.216.35", "ttl": 3600},
        ],
        "aaaa": [
            {"value": "::1", "ttl": 3600},
        ],
        "mx": [
            {"target": "mail.example.com", "priority": 10, "ttl": 3600},
        ],
        "txt": [
            {"value": "v=spf1 include:_spf.example.com ~all", "ttl": 3600},
            {"value": "google-site-verification=abc123", "ttl": 3600},
        ],
        "cname": [
            {"value": "www.example.com", "ttl": 3600},
        ],
        "ns": [
            {"value": "ns1.example.com", "ttl": 3600},
            {"value": "ns2.example.com", "ttl": 3600},
        ],
    }


@pytest.fixture
def sample_subdomains():
    """Sample subdomains for testing."""
    return [
        "api.example.com",
        "admin.example.com",
        "cdn.example.com",
        "dev.example.com",
        "mail.example.com",
        "staging.example.com",
        "test.example.com",
        "www.example.com",
    ]


@pytest.fixture
def sample_certificate():
    """Sample certificate details for testing."""
    from datetime import datetime, timedelta
    
    return {
        "subject": {
            "common_name": "example.com",
            "organization": "Example Corp",
            "country": "US",
        },
        "sans": [
            "example.com",
            "*.example.com",
            "www.example.com",
            "api.example.com",
        ],
        "issuer": {
            "common_name": "Let's Encrypt",
            "organization": "Let's Encrypt",
            "country": "US",
        },
        "validity": {
            "not_before": datetime.utcnow() - timedelta(days=30),
            "not_after": datetime.utcnow() + timedelta(days=60),
        },
        "technical": {
            "signature_algorithm": "sha256WithRSAEncryption",
            "public_key_algorithm": "RSA",
            "public_key_size": 2048,
        },
        "fingerprints": {
            "sha256": "a1b2c3d4e5f6...",
            "sha1": "a1b2c3d4e5f6...",
        },
    }
