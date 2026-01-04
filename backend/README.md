# Domain Intelligence Module - Backend

This module provides comprehensive WHOIS, DNS, and domain intelligence capabilities for the OSINT aggregation platform.

## Architecture Overview

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
│   ├── censys_client.py        # Censys API client
│   ├── shodan_client.py        # Shodan API client
│   ├── securitytrails_client.py # SecurityTrails API client
│   └── geoip_client.py         # IP geolocation client (MaxMind)
├── database/
│   ├── models.py               # SQLAlchemy models
│   └── neo4j_schema.py         # Neo4j graph schema
├── routes/
│   └── domain_intelligence.py  # API endpoints
└── docs/
    └── DOMAIN_INTELLIGENCE.md  # Module documentation
```

## Dependencies

```txt
dnspython>=2.4.0
whois>=0.9.13
geoip2>=4.7.0
aiohttp>=3.8.0
sqlalchemy[asyncio]>=2.0.0
neo4j>=5.0.0
python-dateutil>=2.8.0
tldextract>=3.4.0
censys>=2.1.0
shodan>=1.28.0
requests>=2.31.0
```

## Usage

### WHOIS Lookup
```python
from modules.whois_lookup import WhoisLookup

whois = WhoisLookup()
result = await whois.lookup_domain("example.com")
print(result.registrant_name)
print(result.registrar)
print(result.nameservers)
```

### DNS Enumeration
```python
from modules.dns_enumeration import DnsEnumeration

dns = DnsEnumeration()
records = await dns.enumerate_records("example.com")
print(records.a_records)
print(records.mx_records)
print(records.txt_records)
```

### Subdomain Discovery
```python
from modules.subdomain_discovery import SubdomainDiscovery

subdomain_finder = SubdomainDiscovery()
subdomains = await subdomain_finder.discover("example.com")
for sub in subdomains:
    print(f"{sub.name}: {sub.ip_address}")
```

### SSL Certificate Analysis
```python
from modules.ssl_analysis import SslAnalysis

ssl = SslAnalysis()
cert = await ssl.analyze_certificate("example.com")
print(cert.subject)
print(cert.sans)
print(cert.issuer)
```

## API Endpoints

All endpoints are available under `/api/search/` and `/api/results/`.

### POST /api/search/whois
WHOIS lookup for domain or IP.

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

### GET /api/results/infrastructure/{domain}
Get full infrastructure map.

### POST /api/search/domain-portfolio
Find all domains for person/company.

## Rate Limiting

Each external API client implements rate limiting to prevent blocking:

- WHOIS: 30 requests/minute
- DNS: 100 requests/second
- Certificate Transparency: 30 requests/second
- Censys: 120 requests/second
- Shodan: 1 request/second
- SecurityTrails: 50 requests/second
- GeoIP: 1000 requests/second

## Logging

All queries are logged with:
- Timestamp
- Query target
- Response time
- Success/failure status
- Rate limit status
