# Domain Intelligence Module Documentation

## Overview

The Domain Intelligence module provides comprehensive WHOIS, DNS, and domain intelligence capabilities for the OSINT aggregation platform. It enables deep domain reconnaissance including WHOIS lookups, DNS enumeration, subdomain discovery, SSL certificate analysis, and infrastructure mapping.

## Architecture

```
backend/
├── modules/
│   ├── whois_lookup.py         # WHOIS lookup for domains and IPs
│   ├── dns_enumeration.py      # DNS record enumeration
│   ├── subdomain_discovery.py  # Subdomain enumeration
│   ├── ssl_analysis.py         # SSL/TLS certificate analysis
│   ├── infrastructure_mapping.py # IP-to-domain mapping and ASN analysis
│   └── related_domains.py      # Related domain discovery
├── clients/
│   ├── whois_client.py         # WHOIS API client
│   ├── dns_client.py           # DNS query client (dnspython)
│   ├── ct_client.py            # Certificate Transparency client (crt.sh)
│   ├── censys_client.py        # Censys IP search API
│   ├── shodan_client.py        # Shodan internet search API
│   ├── securitytrails_client.py # SecurityTrails domain intelligence
│   └── geoip_client.py         # IP geolocation client (MaxMind)
├── database/
│   ├── models.py               # SQLAlchemy models
│   ├── connection.py           # Database connection management
│   └── neo4j_schema.py         # Neo4j graph schema
├── routes/
│   └── domain_intelligence.py  # API endpoints
└── tests/
    └── test_domain_intelligence.py # Unit tests
```

## Capabilities

### 1. WHOIS Lookup

The WHOIS module provides comprehensive domain and IP WHOIS lookups.

**Features:**
- Domain registration information (registrant, admin, tech contacts)
- Registrar details and IANA ID
- Registration and expiration dates
- Name servers
- DNSSEC status
- IP WHOIS with ASN and geolocation
- Privacy protection detection
- Email extraction and alternative domain discovery

**Usage:**
```python
from modules.whois_lookup import WhoisLookup

whois = WhoisLookup(securitytrails_api_key="your-key")
result = await whois.lookup_domain("example.com")

print(result.registrant_name)
print(result.registrar)
print(result.nameservers)
print(result.expiration_date)
print(result.privacy_protected)
```

### 2. DNS Enumeration

The DNS module enumerates all DNS record types with support for historical data.

**Features:**
- All record types: A, AAAA, MX, TXT, CNAME, NS, SOA, SRV, CAA
- Email provider identification from MX records
- Nameserver IP resolution
- SPF, DKIM, DMARC record parsing
- Historical DNS records via SecurityTrails
- DNS propagation checking
- DNS takeover vulnerability detection

**Usage:**
```python
from modules.dns_enumeration import DnsEnumeration

dns = DnsEnumeration(securitytrails_api_key="your-key")
result = await dns.enumerate_all("example.com")

print(result.a_records)
print(result.aaaa_records)
print(result.mx_records)
print(result.txt_records)
print(result.email_providers)
print(result.nameserver_ips)

# Get historical DNS
history = await dns.get_historical_dns("example.com")
print(history.ip_changes)
```

### 3. Subdomain Discovery

The subdomain module discovers subdomains using multiple techniques.

**Features:**
- Certificate Transparency log search (crt.sh)
- Brute force with common subdomain wordlists
- SecurityTrails subdomain enumeration
- Zone transfer attempts
- Wildcard DNS detection
- Service detection on discovered subdomains

**Usage:**
```python
from modules.subdomain_discovery import SubdomainDiscovery

subdomain = SubdomainDiscovery(securitytrails_api_key="your-key")
result = await subdomain.discover("example.com", methods=["ct", "bruteforce"])

print(f"Found {result.total_found} subdomains")
print(f"Active: {result.total_active}")
print(f"Wildcard: {result.total_wildcard}")

for sub in result.subdomains:
    print(f"{sub.subdomain}: {sub.ip_addresses}")

# Find high-value targets
high_value = await subdomain.find_high_value_targets("example.com")
```

### 4. SSL Certificate Analysis

The SSL module analyzes certificates for security and related domains.

**Features:**
- Complete certificate details (subject, issuer, validity)
- Subject Alternative Names (SANs) extraction
- Certificate chain validation
- Fingerprint generation (SHA256, SHA1, MD5)
- Weak algorithm and key size detection
- Historical certificates via Censys
- Related domain discovery via CT logs

**Usage:**
```python
from modules.ssl_analysis import SslAnalysis

ssl = SslAnalysis(
    censys_api_id="your-id",
    censys_api_secret="your-secret",
)
result = await ssl.analyze("example.com")

print(result.certificates[0].subject_common_name)
print(result.certificates[0].sans)
print(result.certificates[0].issuer_organization)
print(result.certificates[0].validity_days_remaining)
print(result.vulnerabilities)

# Get historical certificates
history = await ssl.get_historical_certificates("example.com")
```

### 5. Infrastructure Mapping

The infrastructure module maps domain infrastructure including IPs, ASNs, and services.

**Features:**
- IP-to-domain mapping (reverse IP)
- ASN analysis and classification
- Service detection and port scanning
- IP geolocation
- CDN and cloud provider detection
- Virtual hosting identification
- Infrastructure type classification (shared, dedicated, cloud, CDN)

**Usage:**
```python
from modules.infrastructure_mapping import InfrastructureMapping

infra = InfrastructureMapping(
    censys_api_id="your-id",
    censys_api_secret="your-secret",
    shodan_api_key="your-key",
)
result = await infra.map_infrastructure("example.com")

print(f"IP addresses: {result.ip_addresses}")
print(f"Infrastructure type: {result.infrastructure_type}")
print(f"Is CDN: {result.is_cdn}")
print(f"Countries: {result.countries}")

for host in result.hosts:
    print(f"{host.ip_address}: {host.ports}")

# Reverse IP lookup
reverse = await infra.reverse_ip_lookup("1.2.3.4")
print(f"Domains on IP: {reverse.domains}")
```

### 6. Related Domain Discovery

The related domains module finds connections between domains.

**Features:**
- Same registrant via WHOIS email
- Same infrastructure (IP, ASN, nameservers)
- Same certificate issuer
- Typosquatting and variation detection
- Brand domain discovery
- Domain portfolio analysis

**Usage:**
```python
from modules.related_domains import RelatedDomains

related = RelatedDomains(
    securitytrails_api_key="your-key",
    censys_api_id="your-id",
    censys_api_secret="your-secret",
)

# Find related domains
result = await related.find_related_domains("example.com")
for domain in result:
    print(f"{domain.domain} ({domain.relationship_type})")

# Find all domains by email
portfolio = await related.find_domains_by_email("john@example.com")
print(f"Total domains: {portfolio.total_domains}")

# Domain variations
variations = await related.find_domain_variations("example.com")
for var in variations.variations:
    print(f"{var.domain}: {var.confidence}")
```

## API Endpoints

### POST /api/search/whois
WHOIS lookup for domain or IP.

**Request:**
```json
{
    "domain": "example.com",
    "include_raw": false
}
```

**Response:**
```json
{
    "success": true,
    "result": {
        "domain": "example.com",
        "registrant": {...},
        "registrar": "GoDaddy.com",
        "registration_date": "2020-01-01T00:00:00",
        "expiration_date": "2030-01-01T00:00:00",
        "nameservers": ["ns1.example.com", "ns2.example.com"],
        "dnssec": true,
        "privacy_protected": false
    }
}
```

### POST /api/search/dns-records
DNS enumeration for a domain.

### POST /api/search/subdomains
Subdomain discovery for a domain.

### POST /api/search/ssl-certificates
SSL certificate analysis.

### POST /api/search/reverse-ip
Reverse IP lookup.

### POST /api/search/related-domains
Find related domains.

### GET /api/search/infrastructure/{domain}
Get full infrastructure map.

### POST /api/search/domain-portfolio
Find all domains for person/company.

## Database Schema

### PostgreSQL Tables

#### domains
Stores domain registration and WHOIS information.

#### dns_records
Stores DNS records for domains.

#### subdomains
Stores discovered subdomains.

#### ssl_certificates
Stores SSL certificate details.

#### ip_addresses
Stores IP address information with geolocation.

#### related_domains
Stores related domain relationships.

### Neo4j Graph Nodes

- **Domain**: Domain name and registration info
- **IP**: IP address with geolocation
- **Person**: Person linked to registrant email
- **Nameserver**: Nameserver domains
- **Certificate**: SSL certificates
- **ASN**: Autonomous System Numbers

### Neo4j Relationships

- `REGISTERED_TO`: Domain to registrant person
- `POINTS_TO`: Domain to IP address
- `HOSTED_ON`: IP to ASN
- `USES_NAMESERVER`: Domain to nameserver
- `RELATED_TO`: Related domains
- `CERTIFICATE_FOR`: Certificate to domain

## Rate Limiting

| Service | Rate Limit |
|---------|------------|
| WHOIS | 30 requests/minute |
| DNS | 100 requests/second |
| Certificate Transparency | 30 requests/second |
| Censys | 120 requests/second |
| Shodan | 1 request/second |
| SecurityTrails | 50 requests/second |
| GeoIP | 1000 requests/second |

## Privacy Detection

The module automatically detects privacy protection services:

- **Namecheap**: Namecheap Privacy, ID Protection
- **GoDaddy**: Domains by Proxy
- **eNom**: Privacy service
- **MarkMonitor**: Brand protection
- **Generic**: REDACTED FOR PRIVACY

## Integration with Other Phases

### Phase 2.3/2.4 Integration
Receives domains, emails, and company names from earlier phases for investigation.

### Phase 2.6 GitHub Intelligence
Cross-references domain infrastructure with GitHub organization data.

### Phase 2.7 Graph Correlation
Creates graph relationships between:
- Domains and their registrants
- IPs and ASNs
- Shared infrastructure
- Certificate chains

### Phase 3 Frontend Dashboard
Provides data for:
- Domain intelligence views
- Infrastructure visualization
- Attack surface mapping
- Timeline of domain registrations

## Configuration

### Environment Variables

```bash
# API Keys
SECURITYTRAILS_API_KEY=your-key
CENSYS_API_ID=your-id
CENSYS_API_SECRET=your-secret
SHODAN_API_KEY=your-key

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/domain_intel
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password

# GeoIP
GEOIP_CITY_DB=/usr/share/GeoIP/GeoLite2-City.mmdb
GEOIP_ASN_DB=/usr/share/GeoIP/GeoLite2-ASN.mmdb
```

### FastAPI Configuration

```python
from app import config, set_api_key

# Set API keys
set_api_key("securitytrails", "your-api-key")
set_api_key("censys", "your-id:your-secret")
set_api_key("shodan", "your-api-key")

# Configure database
config.database_url = "postgresql+asyncpg://..."
```

## Testing

Run tests with pytest:

```bash
pytest backend/tests/test_domain_intelligence.py -v
```

Tests cover:
- WHOIS parsing and privacy detection
- DNS record parsing and email provider identification
- Subdomain discovery methods
- SSL certificate analysis and vulnerability detection
- Infrastructure mapping and classification
- Related domain discovery algorithms
- Database model operations
- API endpoint functionality

## Error Handling

All modules include comprehensive error handling:

- Timeout handling for slow queries
- Rate limit detection and backoff
- Graceful degradation when services are unavailable
- Logging of all operations for monitoring

## Performance Considerations

- Async/await for concurrent operations
- Connection pooling for database access
- Caching of DNS and geolocation results
- Rate limiting to prevent API blocks
- Batch processing for multiple domains

## Logging

All operations are logged with:
- Timestamp
- Query target
- Duration
- Success/failure
- Rate limit status
- Error details

```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
```
