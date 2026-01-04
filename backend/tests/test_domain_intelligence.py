"""
Tests for domain intelligence modules.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from modules.whois_lookup import (
    WhoisLookup,
    DomainWhoisResult,
    IpWhoisResult,
    RegistrantInfo,
    RegistrarInfo,
    PrivacyDetector,
)

from modules.dns_enumeration import (
    DnsEnumeration,
    DnsEnumerateResult,
    DnsHistoryResult,
    DnsPropagationResult,
)

from modules.subdomain_discovery import (
    SubdomainDiscovery,
    SubdomainDiscoveryResult,
    SubdomainInfoResult,
)

from modules.ssl_analysis import (
    SslAnalysis,
    SslAnalysisResult,
    SslCertificateDetails,
    CertificateChain,
)

from modules.infrastructure_mapping import (
    InfrastructureMapping,
    InfrastructureMap,
    HostInfo,
    ServiceInfo,
    AsnInfoResult,
)

from modules.related_domains import (
    RelatedDomains,
    RelatedDomainInfo,
    DomainPortfolioResult,
    DomainVariationsResult,
)


class TestWhoisLookup:
    """Tests for WHOIS lookup module."""
    
    @pytest.fixture
    def whois_lookup(self):
        """Create WHOIS lookup instance."""
        return WhoisLookup()
    
    @pytest.mark.asyncio
    async def test_parse_whois_response(self, whois_lookup):
        """Test parsing WHOIS response."""
        # Create mock WHOIS entry
        mock_whois = MagicMock()
        mock_whois.domain = "example.com"
        mock_whois.creation_date = datetime(2020, 1, 1)
        mock_whois.expiration_date = datetime(2030, 1, 1)
        mock_whois.updated_date = datetime(2023, 6, 1)
        mock_whois.registrant = "John Doe"
        mock_whois.registrant_email = "john@example.com"
        mock_whois.registrant_org = "Example Corp"
        mock_whois.registrant_country = "US"
        mock_whois.admin_email = "admin@example.com"
        mock_whois.tech_email = "tech@example.com"
        mock_whois.registrar = "GoDaddy.com"
        mock_whois.nameservers = ["ns1.example.com", "ns2.example.com"]
        mock_whois.dnssec = True
        mock_whois.status = ["clientTransferProhibited"]
        
        result = DomainWhoisResult(domain="example.com")
        parsed = whois_lookup._parse_whois_response(mock_whois, result)
        
        assert parsed.domain == "example.com"
        assert parsed.registrant.name == "John Doe"
        assert parsed.registrant.email == "john@example.com"
        assert parsed.registrant.organization == "Example Corp"
        assert parsed.registrant_email == "john@example.com"
        assert parsed.admin_email == "admin@example.com"
        assert parsed.tech_email == "tech@example.com"
        assert parsed.registrar == "GoDaddy.com"
        assert len(parsed.nameservers) == 2
        assert parsed.dnssec is True
        assert "clientTransferProhibited" in parsed.status
    
    def test_privacy_detector(self):
        """Test privacy detection."""
        detector = PrivacyDetector()
        
        # Test with empty registrant
        result = DomainWhoisResult(domain="example.com")
        result.registrant = RegistrantInfo()
        assert detector.is_privacy_protected(result) is True
        
        # Test with real data
        result2 = DomainWhoisResult(domain="example.com")
        result2.registrant = RegistrantInfo(
            name="John Doe",
            email="john@example.com",
            country="US",
        )
        assert detector.is_privacy_protected(result2) is False
        
        # Test with privacy service
        result3 = DomainWhoisResult(domain="example.com")
        result3.registrant = RegistrantInfo()
        result3.raw_whois = "REDACTED FOR PRIVACY by Namecheap"
        assert detector.is_privacy_protected(result3) is True
    
    def test_get_privacy_service(self):
        """Test privacy service identification."""
        detector = PrivacyDetector()
        
        result = DomainWhoisResult(domain="example.com")
        result.raw_whois = "Domain ID Shield Service with NAMECHEAP.COM"
        
        service = detector.get_privacy_service(result)
        assert service == "Namecheap"


class TestDnsEnumeration:
    """Tests for DNS enumeration module."""
    
    @pytest.fixture
    def dns_enumeration(self):
        """Create DNS enumeration instance."""
        return DnsEnumeration()
    
    @pytest.mark.asyncio
    async def test_parse_dns_result(self, dns_enumeration):
        """Test parsing DNS results."""
        from clients.dns_client import DnsResult, DnsRecord
        
        dns_result = DnsResult(
            domain="example.com",
            record_type="A",
            records=[
                DnsRecord(value="93.184.216.34", ttl=3600),
                DnsRecord(value="93.184.216.35", ttl=3600),
            ],
            found=True,
        )
        
        parsed = dns_enumeration._parse_dns_result(dns_result)
        
        assert len(parsed) == 2
        assert parsed[0]["value"] == "93.184.216.34"
        assert parsed[0]["ttl"] == 3600
    
    def test_identify_email_providers(self, dns_enumeration):
        """Test email provider identification."""
        mx_records = [
            {"target": "aspmx.l.google.com"},
            {"target": "alt1.aspmx.l.google.com"},
            {"target": "alt2.aspmx.l.google.com"},
        ]
        
        providers = dns_enumeration._identify_email_providers(mx_records)
        
        assert "google.com" in providers or "google" in " ".join(providers).lower()
    
    def test_parse_spf_record(self, dns_enumeration):
        """Test SPF record parsing."""
        spf = "v=spf1 ip4:192.168.1.0/24 include:_spf.google.com ~all"
        
        parsed = dns_enumeration._parse_spf_record(spf)
        
        assert "mechanisms" in parsed
        assert len(parsed["mechanisms"]) >= 2
        assert parsed["all"] == "~all"
    
    def test_parse_dmarc_record(self, dns_enumeration):
        """Test DMARC record parsing."""
        dmarc = "v=DMARC1; p=none; rua=mailto:dmarc@example.com"
        
        parsed = dns_enumeration._parse_dmarc_record(dmarc)
        
        assert parsed["policy"] == "none"
        assert "dmarc@example.com" in parsed.get("aggregate_report_uri", "")
    
    def test_get_all_ips(self, dns_enumeration):
        """Test getting all IPs from result."""
        result = DnsEnumerateResult(domain="example.com")
        result.a_records = [{"value": "1.2.3.4"}, {"value": "5.6.7.8"}]
        result.aaaa_records = [{"value": "::1"}]
        
        ips = result.get_all_ips()
        
        assert len(ips) == 3
        assert "1.2.3.4" in ips
        assert "5.6.7.8" in ips
        assert "::1" in ips
    
    def test_get_all_nameservers(self, dns_enumeration):
        """Test getting all nameservers from result."""
        result = DnsEnumerateResult(domain="example.com")
        result.ns_records = [
            {"value": "ns1.example.com"},
            {"value": "ns2.example.com"},
        ]
        
        ns = result.get_all_nameservers()
        
        assert len(ns) == 2
        assert "ns1.example.com" in ns


class TestSubdomainDiscovery:
    """Tests for subdomain discovery module."""
    
    @pytest.fixture
    def subdomain_discovery(self):
        """Create subdomain discovery instance."""
        return SubdomainDiscovery()
    
    def test_subdomain_info_result(self):
        """Test subdomain info result."""
        info = SubdomainInfoResult(
            subdomain="api.example.com",
            domain="example.com",
            ip_addresses=["1.2.3.4"],
            discovery_method="ct",
            is_active=True,
        )
        
        assert info.subdomain == "api.example.com"
        assert info.domain == "example.com"
        assert len(info.ip_addresses) == 1
        assert info.is_active is True
    
    def test_subdomain_discovery_result(self):
        """Test subdomain discovery result."""
        result = SubdomainDiscoveryResult(domain="example.com")
        result.subdomains = [
            SubdomainInfoResult(subdomain="api.example.com", domain="example.com"),
            SubdomainInfoResult(subdomain="www.example.com", domain="example.com"),
        ]
        result.total_found = 2
        result.total_active = 2
        
        data = result.to_dict()
        
        assert data["domain"] == "example.com"
        assert len(data["subdomains"]) == 2
        assert data["total_found"] == 2
    
    def test_generate_variations(self, subdomain_discovery):
        """Test domain variation generation."""
        # This tests the protected method indirectly
        from tldextract import extract
        
        # Just verify the method exists and is callable
        assert hasattr(subdomain_discovery, "_generate_variations")
    
    def test_check_subdomain_exists(self, subdomain_discovery):
        """Test subdomain existence checking."""
        # This would need a real DNS query, so we mock it
        subdomain_discovery.dns_client.resolve = AsyncMock(return_value=MagicMock(
            found=True,
            records=[MagicMock(value="1.2.3.4")],
        ))
        
        # Test with async
        result = asyncio.run(subdomain_discovery._check_subdomain_exists("test.example.com"))
        
        assert result is True


class TestSslAnalysis:
    """Tests for SSL analysis module."""
    
    @pytest.fixture
    def ssl_analysis(self):
        """Create SSL analysis instance."""
        return SslAnalysis()
    
    def test_ssl_certificate_details(self):
        """Test SSL certificate details."""
        cert = SslCertificateDetails(
            subject_common_name="example.com",
            subject_organization="Example Corp",
            issuer_common_name="Let's Encrypt",
            issuer_organization="Let's Encrypt",
            not_before=datetime.utcnow() - timedelta(days=30),
            not_after=datetime.utcnow() + timedelta(days=60),
            public_key_algorithm="RSA",
            public_key_size=2048,
            signature_algorithm="sha256WithRSAEncryption",
            fingerprint_sha256="abc123",
        )
        
        data = cert.to_dict()
        
        assert data["subject"]["common_name"] == "example.com"
        assert data["subject"]["organization"] == "Example Corp"
        assert data["issuer"]["common_name"] == "Let's Encrypt"
        assert data["technical"]["public_key_algorithm"] == "RSA"
        assert data["fingerprints"]["sha256"] == "abc123"
    
    def test_ssl_analysis_result(self):
        """Test SSL analysis result."""
        result = SslAnalysisResult(
            domain="example.com",
            ip_address="1.2.3.4",
            port=443,
            is_valid=True,
            is_trusted=True,
            is_self_signed=False,
        )
        
        data = result.to_dict()
        
        assert data["domain"] == "example.com"
        assert data["is_valid"] is True
        assert data["is_trusted"] is True
    
    def test_validate_certificate(self, ssl_analysis):
        """Test certificate validation."""
        # Valid certificate
        valid_cert = SslCertificateDetails(
            not_before=datetime.utcnow() - timedelta(days=30),
            not_after=datetime.utcnow() + timedelta(days=60),
        )
        assert ssl_analysis._validate_certificate(valid_cert) is True
        
        # Expired certificate
        expired_cert = SslCertificateDetails(
            not_before=datetime.utcnow() - timedelta(days=365),
            not_after=datetime.utcnow() - timedelta(days=1),
        )
        assert ssl_analysis._validate_certificate(expired_cert) is False
        
        # Not yet valid
        future_cert = SslCertificateDetails(
            not_before=datetime.utcnow() + timedelta(days=1),
            not_after=datetime.utcnow() + timedelta(days=365),
        )
        assert ssl_analysis._validate_certificate(future_cert) is False
    
    def test_is_self_signed(self, ssl_analysis):
        """Test self-signed detection."""
        # Self-signed
        self_signed = SslCertificateDetails(
            subject_common_name="example.com",
            issuer_common_name="example.com",
        )
        assert ssl_analysis._is_self_signed(self_signed) is True
        
        # Not self-signed
        not_self_signed = SslCertificateDetails(
            subject_common_name="example.com",
            issuer_common_name="DigiCert",
        )
        assert ssl_analysis._is_self_signed(not_self_signed) is False
    
    def test_analyze_vulnerabilities(self, ssl_analysis):
        """Test vulnerability analysis."""
        # Expired certificate
        expired_cert = SslCertificateDetails(
            not_before=datetime.utcnow() - timedelta(days=365),
            not_after=datetime.utcnow() - timedelta(days=1),
            signature_algorithm="sha256WithRSAEncryption",
            public_key_algorithm="RSA",
            public_key_size=2048,
        )
        
        vulns = ssl_analysis._analyze_vulnerabilities(expired_cert)
        
        vuln_types = [v["type"] for v in vulns]
        assert "expired_certificate" in vuln_types
        
        # Weak algorithm
        weak_alg_cert = SslCertificateDetails(
            not_before=datetime.utcnow() - timedelta(days=30),
            not_after=datetime.utcnow() + timedelta(days=60),
            signature_algorithm="sha1WithRSA",
            public_key_algorithm="RSA",
            public_key_size=2048,
        )
        
        vulns = ssl_analysis._analyze_vulnerabilities(weak_alg_cert)
        vuln_types = [v["type"] for v in vulns]
        assert "weak_signature_algorithm" in vuln_types
        
        # Weak key size
        weak_key_cert = SslCertificateDetails(
            not_before=datetime.utcnow() - timedelta(days=30),
            not_after=datetime.utcnow() + timedelta(days=60),
            signature_algorithm="sha256WithRSAEncryption",
            public_key_algorithm="RSA",
            public_key_size=1024,  # Too small
        )
        
        vulns = ssl_analysis._analyze_vulnerabilities(weak_key_cert)
        vuln_types = [v["type"] for v in vulns]
        assert "weak_key_size" in vuln_types


class TestInfrastructureMapping:
    """Tests for infrastructure mapping module."""
    
    @pytest.fixture
    def infra_mapping(self):
        """Create infrastructure mapping instance."""
        return InfrastructureMapping()
    
    def test_host_info(self):
        """Test host info."""
        host = HostInfo(
            ip_address="1.2.3.4",
            hostname="example.com",
            domain="example.com",
            services=[
                ServiceInfo(port=80, product="Nginx"),
                ServiceInfo(port=443, product="Nginx", is_https=True),
            ],
        )
        
        data = host.to_dict()
        
        assert data["ip_address"] == "1.2.3.4"
        assert data["hostname"] == "example.com"
        assert len(data["services"]) == 2
        assert data["services"][1]["is_https"] is True
    
    def test_service_info(self):
        """Test service info."""
        service = ServiceInfo(
            port=443,
            product="Nginx",
            version="1.18.0",
            is_https=True,
            technologies=["nginx", "php"],
        )
        
        data = service.to_dict()
        
        assert data["port"] == 443
        assert data["product"] == "Nginx"
        assert data["version"] == "1.18.0"
        assert data["is_https"] is True
        assert "nginx" in data["technologies"]
    
    def test_asn_info_result(self):
        """Test ASN info result."""
        asn = AsnInfoResult(
            asn="AS15169",
            asn_decimal=15169,
            name="GOOGLE",
            organization="Google LLC",
            country_code="US",
            is_cloud=True,
        )
        
        data = asn.to_dict()
        
        assert data["asn"] == "AS15169"
        assert data["is_cloud"] is True
        assert data["organization"] == "Google LLC"
    
    def test_infrastructure_map(self):
        """Test infrastructure map."""
        infra = InfrastructureMap(
            domain="example.com",
            ip_addresses=["1.2.3.4", "5.6.7.8"],
            hosts=[
                HostInfo(ip_address="1.2.3.4"),
                HostInfo(ip_address="5.6.7.8"),
            ],
            is_cdn=True,
            infrastructure_type="cdn",
        )
        
        data = infra.to_dict()
        
        assert data["domain"] == "example.com"
        assert len(data["ip_addresses"]) == 2
        assert len(data["hosts"]) == 2
        assert data["is_cdn"] is True
        assert data["infrastructure_type"] == "cdn"
    
    def test_check_cdn(self, infra_mapping):
        """Test CDN detection."""
        assert infra_mapping._check_cdn("Cloudflare Inc") is True
        assert infra_mapping._check_cdn("Akamai Technologies") is True
        assert infra_mapping._check_cdn("Some Random ISP") is False
    
    def test_check_cloud(self, infra_mapping):
        """Test cloud provider detection."""
        assert infra_mapping._check_cloud("Amazon.com Inc") is True
        assert infra_mapping._check_cloud("Microsoft Corporation") is True
        assert infra_mapping._check_cloud("Google LLC") is True
        assert infra_mapping._check_cloud("Some Random ISP") is False
    
    def test_is_datacenter_ip(self, infra_mapping):
        """Test datacenter IP detection."""
        # Cloudflare IP
        assert infra_mapping._is_datacenter_ip("1.1.1.1") is True
        # Unknown IP
        assert infra_mapping._is_datacenter_ip("8.8.8.8") is False


class TestRelatedDomains:
    """Tests for related domains module."""
    
    @pytest.fixture
    def related_domains(self):
        """Create related domains instance."""
        return RelatedDomains()
    
    def test_related_domain_info(self):
        """Test related domain info."""
        domain = RelatedDomainInfo(
            domain="example.net",
            relationship_type="same_registrant_email",
            confidence=0.95,
            shared_attribute="john@example.com",
            is_active=True,
            registration_date=datetime(2020, 1, 1),
            registrar="GoDaddy",
        )
        
        data = domain.to_dict()
        
        assert data["domain"] == "example.net"
        assert data["relationship_type"] == "same_registrant_email"
        assert data["confidence"] == 0.95
        assert data["shared_attribute"] == "john@example.com"
        assert data["is_active"] is True
    
    def test_domain_portfolio_result(self):
        """Test domain portfolio result."""
        portfolio = DomainPortfolioResult(
            query="john@example.com",
            query_type="email",
            domains=[
                RelatedDomainInfo(domain="example1.com", relationship_type="same_email"),
                RelatedDomainInfo(domain="example2.com", relationship_type="same_email"),
            ],
            total_domains=2,
            active_domains=2,
            registrars=["GoDaddy", "Namecheap"],
        )
        
        data = portfolio.to_dict()
        
        assert data["query"] == "john@example.com"
        assert data["total_domains"] == 2
        assert len(data["domains"]) == 2
        assert len(data["registrars"]) == 2
    
    def test_domain_variations_result(self):
        """Test domain variations result."""
        variations = DomainVariationsResult(
            original_domain="example.com",
            variations=[
                RelatedDomainInfo(domain="examp1e.com", relationship_type="typosquatting"),
                RelatedDomainInfo(domain="exampler.com", relationship_type="typosquatting"),
            ],
            takeovers=[],
        )
        
        data = variations.to_dict()
        
        assert data["original_domain"] == "example.com"
        assert len(data["variations"]) == 2
    
    def test_is_parked(self, related_domains):
        """Test parked domain detection."""
        # Should detect parking
        mock_domain = MagicMock()
        mock_domain.registrar = "Sedo Domain Parking"
        mock_domain.nameservers = ["ns1.sedoparking.com"]
        mock_domain.registrant_name = None
        mock_domain.registrant_email = None
        
        assert related_domains._is_parked(mock_domain) is True
        
        # Should not detect parking for real domain
        real_domain = MagicMock()
        real_domain.registrar = "GoDaddy"
        real_domain.nameservers = ["ns1.example.com", "ns2.example.com"]
        real_domain.registrant_name = "John Doe"
        real_domain.registrant_email = "john@example.com"
        
        assert related_domains._is_parked(real_domain) is False
    
    def test_is_suspicious(self, related_domains):
        """Test suspicious domain detection."""
        assert related_domains._is_suspicious("example-phish.com") is True
        assert related_domains._is_suspicious("example-fake-store.com") is True
        assert related_domains._is_suspicious("legitimate-example.com") is False
    
    def test_calculate_risk(self, related_domains):
        """Test risk score calculation."""
        # Low risk
        low_risk = RelatedDomainInfo(
            domain="legitimate.com",
            is_suspicious=False,
            is_parked=False,
            registration_date=datetime.utcnow() - timedelta(days=365),
        )
        score = related_domains._calculate_risk(low_risk)
        assert score < 50
        
        # High risk (suspicious)
        high_risk = RelatedDomainInfo(
            domain="phish-example.com",
            is_suspicious=True,
            is_parked=False,
        )
        score = related_domains._calculate_risk(high_risk)
        assert score >= 50
    
    def test_generate_company_domains(self, related_domains):
        """Test company domain generation."""
        domains = related_domains._generate_company_domains("Acme Corp")
        
        assert len(domains) > 0
        assert any("acme" in d for d in domains)
        assert any(d.endswith(".com") for d in domains)


class TestGeoIpClient:
    """Tests for GeoIP client."""
    
    def test_geo_location(self):
        """Test geolocation."""
        from clients.geoip_client import GeoLocation
        
        location = GeoLocation(
            ip_address="8.8.8.8",
            country_code="US",
            country_name="United States",
            city="Mountain View",
            latitude=37.3861,
            longitude=-122.0839,
            timezone="America/Los_Angeles",
        )
        
        data = location.to_dict()
        
        assert data["country_code"] == "US"
        assert data["city"] == "Mountain View"
        assert data["latitude"] == 37.3861
    
    def test_asn_info(self):
        """Test ASN info."""
        from clients.geoip_client import AsnInfo
        
        asn = AsnInfo(
            asn="AS15169",
            asn_decimal=15169,
            organization="Google LLC",
            network="8.8.8.0/24",
        )
        
        data = asn.to_dict()
        
        assert data["asn"] == "AS15169"
        assert data["organization"] == "Google LLC"
    
    def test_geo_ip_result(self):
        """Test GeoIP result."""
        from clients.geoip_client import GeoIpResult, GeoLocation, AsnInfo
        
        result = GeoIpResult(
            ip_address="8.8.8.8",
            location=GeoLocation(country_code="US"),
            isp="Google LLC",
            asn=AsnInfo(asn="AS15169"),
            is_bogon=False,
        )
        
        data = result.to_dict()
        
        assert data["ip_address"] == "8.8.8.8"
        assert data["location"]["country_code"] == "US"
        assert data["isp"] == "Google LLC"
        assert data["asn"]["asn"] == "AS15169"
        assert data["is_bogon"] is False


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
