# Domain Intelligence API Tests

This directory contains tests for the domain intelligence module.

## Test Structure

- `unit/` - Unit tests for individual modules
- `integration/` - Integration tests for API endpoints
- `fixtures/` - Test fixtures and mock data
- `conftest.py` - Pytest configuration and fixtures

## Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-mock httpx

# Run all tests
pytest

# Run specific test file
pytest tests/unit/test_whois_lookup.py

# Run with coverage
pytest --cov=modules --cov=api --cov-report=html

# Run integration tests only
pytest tests/integration/
```

## Test Categories

### Unit Tests
- `test_whois_lookup.py` - WHOIS lookup functionality
- `test_dns_enumeration.py` - DNS enumeration and analysis
- `test_subdomain_discovery.py` - Subdomain discovery methods
- `test_ssl_analysis.py` - SSL certificate analysis
- `test_infrastructure_mapping.py` - Infrastructure mapping
- `test_related_domains.py` - Related domain discovery

### Integration Tests
- `test_api_endpoints.py` - API endpoint functionality
- `test_database_operations.py` - Database integration
- `test_external_apis.py` - External API integration

## Mock Data

Tests use mock data to avoid external API calls:

- WHOIS responses for test domains
- DNS record samples
- SSL certificate examples
- Certificate transparency log entries

## Test Fixtures

Common test fixtures are defined in `conftest.py`:

- `test_domain` - Sample domain for testing
- `test_ip` - Sample IP address
- `mock_whois_response` - Mock WHOIS API response
- `mock_dns_records` - Mock DNS records
- `mock_ssl_certificate` - Mock SSL certificate

## Test Configuration

Environment variables for testing:

```bash
# Use test database
POSTGRES_URL=postgresql+asyncpg://test_user:test_pass@localhost:5432/test_domain_intel
NEO4J_URI=bolt://localhost:7688

# Disable external API calls
DISABLE_EXTERNAL_APIS=true
MOCK_RESPONSES=true

# Test timeout
TEST_TIMEOUT=30
```