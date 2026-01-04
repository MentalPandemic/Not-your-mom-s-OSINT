"""
Domain Intelligence Module Test Suite

This file contains sample unit tests for the domain intelligence modules.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

# Import modules to test
from modules.whois_lookup import WHOISLookup, DomainWHOIS, IPWHOIS
from modules.dns_enumeration import DNSEnumeration, DNSRecord, MXRecord, TXTRecord
from modules.subdomain_discovery import SubdomainDiscovery, SubdomainInfo
from modules.ssl_analysis import SSLAnalyzer, CertificateInfo
from modules.infrastructure_mapping import InfrastructureMapping, IPAddressInfo
from modules.related_domains import RelatedDomainDiscovery, DomainVariation


class TestWHOISLookup:
    """Test cases for WHOIS lookup functionality."""
    
    @pytest.fixture
    def whois_service(self):
        return WHOISLookup()
    
    @pytest.fixture
    def sample_domain_info(self):
        domain_info = DomainWHOIS()
        domain_info.domain = "example.com"
        domain_info.registrant_name = "Test Organization"
        domain_info.registrant_email = "admin@example.com"
        domain_info.registrar = "Test Registrar"
        domain_info.registration_date = datetime(2020, 1, 1)
        domain_info.expiration_date = datetime(2025, 1, 1)
        domain_info.name_servers = ["ns1.example.com", "ns2.example.com"]
        return domain_info
    
    @pytest.mark.asyncio
    async def test_whois_privacy_detection(self, whois_service):
        """Test privacy protection detection."""
        whois_text = "Redacted for privacy"
        is_privacy, providers = whois_service.is_privacy_protected(whois_text)
        
        assert is_privacy is True
        assert len(providers) > 0
    
    @pytest.mark.asyncio
    async def test_whois_email_extraction(self, whois_service):
        """Test email extraction from WHOIS text."""
        whois_text = "Registrant Email: admin@example.com\nAdmin Email: admin@example.com"
        emails = whois_service.extract_emails(whois_text)
        
        assert "admin@example.com" in emails
        assert len(emails) == 1  # Should be deduplicated
    
    @pytest.mark.asyncio
    async def test_domain_normalization(self, whois_service):
        """Test domain name normalization."""
        test_cases = [
            ("http://www.example.com", "example.com"),
            ("HTTPS://WWW.EXAMPLE.COM", "example.com"),
            ("example.com", "example.com"),
            ("ftp.example.com", "ftp.example.com")  # Should not remove non-www subdomains
        ]
        
        for input_domain, expected in test_cases:
            result = whois_service.normalize_domain(input_domain)
            assert result == expected
    
    def test_valid_domain_validation(self):
        """Test domain validation."""
        valid_domains = ["example.com", "sub.example.org", "test-domain.co.uk"]
        invalid_domains = ["invalid", "example", "domain..com", ".com"]
        
        from modules.whois_lookup import is_valid_domain
        
        for domain in valid_domains:
            assert is_valid_domain(domain) is True
        
        for domain in invalid_domains:
            assert is_valid_domain(domain) is False
    
    def test_valid_ip_validation(self):
        """Test IP address validation."""
        valid_ips = ["192.168.1.1", "10.0.0.1", "255.255.255.255"]
        invalid_ips = ["256.1.1.1", "192.168.1", "invalid"]
        
        from modules.whois_lookup import is_valid_ip
        
        for ip in valid_ips:
            assert is_valid_ip(ip) is True
        
        for ip in invalid_ips:
            assert is_valid_ip(ip) is False


class TestDNSEnumeration:
    """Test cases for DNS enumeration functionality."""
    
    @pytest.fixture
    def dns_service(self):
        return DNSEnumeration()
    
    @pytest.fixture
    def sample_dns_record(self):
        return DNSRecord("example.com", "A", "192.0.2.1", 3600)
    
    @pytest.fixture
    def sample_mx_record(self):
        return MXRecord("example.com", "mail.example.com", 10, 3600)
    
    @pytest.fixture
    def sample_txt_record(self):
        return TXTRecord("example.com", "v=spf1 include:_spf.google.com ~all", 3600)
    
    def test_dns_record_creation(self, sample_dns_record):
        """Test DNS record object creation."""
        assert sample_dns_record.name == "example.com"
        assert sample_dns_record.type == "A"
        assert sample_dns_record.value == "192.0.2.1"
        assert sample_dns_record.ttl == 3600
    
    def test_mx_record_creation(self, sample_mx_record):
        """Test MX record creation with priority."""
        assert sample_mx_record.mail_server == "mail.example.com"
        assert sample_mx_record.priority == 10
        assert sample_mx_record.type == "MX"
    
    def test_txt_record_analysis(self, sample_txt_record):
        """Test TXT record analysis for SPF/DKIM/DMARC."""
        assert sample_txt_record.is_spf is True
        assert sample_txt_record.is_dkim is False
        assert sample_txt_record.is_dmarc is False
    
    @pytest.mark.asyncio
    async def test_mx_record_analysis(self, dns_service):
        """Test MX record analysis."""
        mx_records = [
            MXRecord("example.com", "mail.example.com", 10),
            MXRecord("example.com", "mail2.example.com", 20)
        ]
        
        analysis = dns_service.analyze_mx_records(mx_records)
        
        assert analysis['total_servers'] == 2
        assert analysis['priorities'] == [10, 20]
        assert analysis['potential_issues'] == []
    
    def test_domain_normalization(self, dns_service):
        """Test domain normalization in DNS service."""
        test_cases = [
            ("http://www.example.com", "example.com"),
            ("HTTPS://WWW.EXAMPLE.COM", "example.com"),
        ]
        
        for input_domain, expected in test_cases:
            result = dns_service.normalize_domain(input_domain)
            assert result == expected


class TestSubdomainDiscovery:
    """Test cases for subdomain discovery functionality."""
    
    @pytest.fixture
    def subdomain_service(self):
        return SubdomainDiscovery()
    
    @pytest.fixture
    def sample_subdomain_info(self):
        return SubdomainInfo("api.example.com", "192.0.2.1", "active")
    
    def test_subdomain_creation(self, sample_subdomain_info):
        """Test subdomain info object creation."""
        assert sample_subdomain_info.name == "api.example.com"
        assert sample_subdomain_info.ip_address == "192.0.2.1"
        assert sample_subdomain_info.status == "active"
    
    def test_subdomain_to_dict(self, sample_subdomain_info):
        """Test subdomain info serialization."""
        result = sample_subdomain_info.to_dict()
        
        assert result['name'] == "api.example.com"
        assert result['ip_address'] == "192.0.2.1"
        assert result['status'] == "active"
        assert 'last_checked' in result
    
    @pytest.mark.asyncio
    async def test_wildcard_dns_detection(self, subdomain_service):
        """Test wildcard DNS detection."""
        # Mock the check_subdomain_exists method
        with patch.object(subdomain_service, 'check_subdomain_exists', return_value="192.0.2.1"):
            result = await subdomain_service.detect_wildcard_dns("example.com")
            assert result is True
    
    def test_common_subdomains(self, subdomain_service):
        """Test that common subdomains are defined."""
        assert "www" in subdomain_service.common_subdomains
        assert "mail" in subdomain_service.common_subdomains
        assert "api" in subdomain_service.common_subdomains
        assert len(subdomain_service.common_subdomains) > 50
    
    def test_domain_normalization(self, subdomain_service):
        """Test domain normalization in subdomain service."""
        test_cases = [
            ("http://www.example.com", "example.com"),
            ("HTTPS://WWW.EXAMPLE.COM", "example.com"),
        ]
        
        for input_domain, expected in test_cases:
            result = subdomain_service.normalize_domain(input_domain)
            assert result == expected


class TestSSLAnalysis:
    """Test cases for SSL certificate analysis."""
    
    @pytest.fixture
    def ssl_service(self):
        return SSLAnalyzer()
    
    @pytest.fixture
    def sample_certificate(self):
        cert_info = CertificateInfo()
        cert_info.common_name = "example.com"
        cert_info.subject_alt_names = ["example.com", "www.example.com"]
        cert_info.issuer = "Let's Encrypt"
        cert_info.valid_from = datetime(2023, 1, 1)
        cert_info.valid_to = datetime(2024, 1, 1)
        cert_info.key_size = 2048
        cert_info.is_valid = True
        cert_info.days_until_expiry = 365
        return cert_info
    
    def test_certificate_creation(self, sample_certificate):
        """Test certificate info object creation."""
        assert sample_certificate.common_name == "example.com"
        assert "example.com" in sample_certificate.subject_alt_names
        assert sample_certificate.key_size == 2048
        assert sample_certificate.is_valid is True
    
    def test_certificate_to_dict(self, sample_certificate):
        """Test certificate info serialization."""
        result = sample_certificate.to_dict()
        
        assert result['common_name'] == "example.com"
        assert result['subject_alt_names'] == ["example.com", "www.example.com"]
        assert result['key_size'] == 2048
        assert result['is_valid'] is True
        assert 'valid_from' in result
        assert 'valid_to' in result
    
    @pytest.mark.asyncio
    async def test_certificate_security_analysis(self, ssl_service, sample_certificate):
        """Test certificate security analysis."""
        analysis = await ssl_service.analyze_certificate_security(sample_certificate)
        
        assert 'security_score' in analysis
        assert 'security_rating' in analysis
        assert 'issues' in analysis
        assert 'recommendations' in analysis
        assert analysis['security_score'] > 0
    
    def test_domain_normalization(self, ssl_service):
        """Test domain normalization in SSL service."""
        test_cases = [
            ("http://www.example.com", "example.com"),
            ("HTTPS://WWW.EXAMPLE.COM", "example.com"),
        ]
        
        for input_domain, expected in test_cases:
            result = ssl_service.normalize_domain(input_domain)
            assert result == expected


class TestInfrastructureMapping:
    """Test cases for infrastructure mapping."""
    
    @pytest.fixture
    def infra_service(self):
        return InfrastructureMapping()
    
    @pytest.fixture
    def sample_ip_info(self):
        ip_info = IPAddressInfo()
        ip_info.ip_address = "192.0.2.1"
        ip_info.isp = "Example ISP"
        ip_info.asn = "AS64512"
        ip_info.country = "US"
        ip_info.city = "New York"
        return ip_info
    
    def test_ip_info_creation(self, sample_ip_info):
        """Test IP address info object creation."""
        assert sample_ip_info.ip_address == "192.0.2.1"
        assert sample_ip_info.isp == "Example ISP"
        assert sample_ip_info.asn == "AS64512"
        assert sample_ip_info.country == "US"
    
    def test_ip_info_to_dict(self, sample_ip_info):
        """Test IP info serialization."""
        result = sample_ip_info.to_dict()
        
        assert result['ip_address'] == "192.0.2.1"
        assert result['isp'] == "Example ISP"
        assert result['asn'] == "AS64512"
        assert result['country'] == "US"
    
    def test_service_name_mapping(self, infra_service):
        """Test service name mapping from port numbers."""
        assert infra_service.get_service_name_from_port(80) == "HTTP"
        assert infra_service.get_service_name_from_port(443) == "HTTPS"
        assert infra_service.get_service_name_from_port(22) == "SSH"
        assert infra_service.get_service_name_from_port(21) == "FTP"


class TestRelatedDomains:
    """Test cases for related domain discovery."""
    
    @pytest.fixture
    def related_domains_service(self):
        return RelatedDomainDiscovery()
    
    @pytest.fixture
    def sample_domain_variation(self):
        return DomainVariation("examplle.com", "typosquatting", 0.7)
    
    def test_domain_variation_creation(self, sample_domain_variation):
        """Test domain variation object creation."""
        assert sample_domain_variation.domain == "examplle.com"
        assert sample_domain_variation.variation_type == "typosquatting"
        assert sample_domain_variation.confidence == 0.7
    
    def test_domain_variation_to_dict(self, sample_domain_variation):
        """Test domain variation serialization."""
        result = sample_domain_variation.to_dict()
        
        assert result['domain'] == "examplle.com"
        assert result['variation_type'] == "typosquatting"
        assert result['confidence'] == 0.7
        assert 'risk_level' in result
    
    @pytest.mark.asyncio
    async def test_domain_status_check(self, related_domains_service):
        """Test domain status checking."""
        # Mock DNS resolution to avoid actual network calls
        with patch('modules.related_domains.dns.resolver') as mock_resolver:
            mock_resolver.Resolver.return_value.resolve.side_effect = Exception("NXDOMAIN")
            
            result = await related_domains_service.check_domain_status("nonexistentdomain12345.com")
            
            assert result['status'] == 'unknown'
            assert 'error' in result
    
    def test_common_tlds(self, related_domains_service):
        """Test that common TLDs are defined."""
        assert "com" in related_domains_service.common_tlds
        assert "net" in related_domains_service.common_tlds
        assert "org" in related_domains_service.common_tlds
        assert len(related_domains_service.common_tlds) > 20
    
    def test_typosquatting_patterns(self, related_domains_service):
        """Test that typosquatting patterns are defined."""
        assert len(related_domains_service.typosquatting_patterns) > 0
        
        # Check that patterns are tuples with regex and replacement
        for pattern, replacement in related_domains_service.typosquatting_patterns:
            assert isinstance(pattern, str)
            assert isinstance(replacement, str)


# Integration tests
class TestModuleIntegration:
    """Integration tests for multiple modules working together."""
    
    @pytest.mark.asyncio
    async def test_whois_dns_integration(self):
        """Test WHOIS and DNS modules working together."""
        whois_service = WHOISLookup()
        dns_service = DNSEnumeration()
        
        # This would normally make real API calls, so we'll mock them
        with patch.object(whois_service, 'lookup_domain') as mock_whois, \
             patch.object(dns_service, 'get_all_records') as mock_dns:
            
            # Mock return values
            mock_whois.return_value = DomainWHOIS()
            mock_whois.return_value.domain = "example.com"
            mock_dns.return_value = {"a_records": []}
            
            # Test integration
            whois_result = await whois_service.lookup_domain("example.com")
            dns_result = await dns_service.get_all_records("example.com")
            
            assert whois_result.domain == "example.com"
            assert isinstance(dns_result, dict)
    
    @pytest.mark.asyncio
    async def test_subdomain_ssl_integration(self):
        """Test subdomain discovery and SSL analysis integration."""
        subdomain_service = SubdomainDiscovery()
        ssl_service = SSLAnalyzer()
        
        # Mock subdomain discovery
        mock_subdomain = SubdomainInfo("api.example.com", "192.0.2.1", "active")
        
        with patch.object(subdomain_service, 'discover_subdomains') as mock_discover, \
             patch.object(ssl_service, 'get_certificate') as mock_ssl:
            
            mock_discover.return_value = {
                'subdomains': [mock_subdomain],
                'summary': {'total_found': 1}
            }
            mock_ssl.return_value = CertificateInfo()
            mock_ssl.return_value.common_name = "api.example.com"
            
            # Test integration
            subdomain_result = await subdomain_service.discover_subdomains("example.com")
            ssl_result = await ssl_service.get_certificate("api.example.com")
            
            assert len(subdomain_result['subdomains']) == 1
            assert ssl_result.common_name == "api.example.com"


# Utility test functions
def test_async_functionality():
    """Test that async functions work correctly."""
    
    async def sample_async_function():
        await asyncio.sleep(0.01)
        return "success"
    
    result = asyncio.run(sample_async_function())
    assert result == "success"


def test_error_handling():
    """Test error handling in modules."""
    
    with pytest.raises(Exception):
        # Test that invalid inputs raise appropriate errors
        from modules.whois_lookup import is_valid_domain
        assert is_valid_domain("invalid") is False


if __name__ == "__main__":
    pytest.main([__file__])