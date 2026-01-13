# Domain Intelligence Module Documentation

## Overview

The Domain Intelligence module provides comprehensive domain reconnaissance capabilities for OSINT (Open Source Intelligence) operations. It performs deep domain analysis including WHOIS lookups, DNS enumeration, subdomain discovery, SSL certificate analysis, and infrastructure mapping.

## Architecture

### Core Modules

1. **WHOIS Lookup Module** (`whois_lookup.py`)
   - Domain and IP WHOIS queries
   - Privacy protection detection
   - Registrant analysis

2. **DNS Enumeration Module** (`dns_enumeration.py`)
   - DNS record extraction (A, AAAA, MX, TXT, CNAME, NS, SRV)
   - DNS propagation analysis
   - Security configuration analysis

3. **Subdomain Discovery Module** (`subdomain_discovery.py`)
   - Brute force enumeration
   - Certificate transparency search
   - Subdomain analysis and service detection

4. **SSL/TLS Certificate Analysis** (`ssl_analysis.py`)
   - Certificate details extraction
   - Certificate chain analysis
   - Security assessment

5. **Infrastructure Mapping Module** (`infrastructure_mapping.py`)
   - IP-to-domain mapping
   - Service identification
   - ASN analysis

6. **Related Domain Discovery** (`related_domains.py`)
   - Domain variation generation
   - Typosquatting detection
   - Infrastructure relationship analysis

### API Clients

- **WHOIS Client** (`clients/whois_client.py`)
- **DNS Client** (`clients/dns_client.py`)
- **Certificate Transparency Client** (`clients/ct_client.py`)
- **Censys Client** (`clients/censys_client.py`)
- **Shodan Client** (`clients/shodan_client.py`)
- **SecurityTrails Client** (`clients/securitytrails_client.py`)
- **GeoIP Client** (`clients/geoip_client.py`)

### Database Integration

- **PostgreSQL**: Structured data storage
- **Neo4j**: Graph relationship modeling

## API Endpoints

### WHOIS Lookup

```http
POST /api/search/whois
Content-Type: application/json

{
    "target": "example.com",
    "include_analysis": true,
    "timeout": 30
}
```

**Response:**
```json
{
    "success": true,
    "data": {
        "domain": "example.com",
        "registrant_name": "Example Organization",
        "registrant_email": "admin@example.com",
        "registrar": "Example Registrar",
        "registration_date": "2020-01-01T00:00:00Z",
        "expiration_date": "2025-01-01T00:00:00Z",
        "name_servers": ["ns1.example.com", "ns2.example.com"],
        "analysis": {
            "uses_privacy": false,
            "risk_level": "low"
        }
    },
    "execution_time": 1.23
}
```

### DNS Enumeration

```http
POST /api/search/dns-records
Content-Type: application/json

{
    "domain": "example.com",
    "record_types": ["A", "MX", "TXT", "CNAME"],
    "include_propagation": true,
    "timeout": 30
}
```

**Response:**
```json
{
    "success": true,
    "domain": "example.com",
    "records": {
        "a_records": [
            {
                "name": "example.com",
                "type": "A",
                "value": "192.0.2.1",
                "ttl": 3600
            }
        ],
        "mx_records": [
            {
                "name": "example.com",
                "type": "MX",
                "value": "10 mail.example.com",
                "mail_server": "mail.example.com",
                "priority": 10
            }
        ],
        "txt_records": [
            {
                "name": "example.com",
                "type": "TXT",
                "value": "v=spf1 include:_spf.google.com ~all",
                "is_spf": true
            }
        ],
        "security_analysis": {
            "has_spf": true,
            "has_dkim": false,
            "has_dmarc": false,
            "security_score": 25
        }
    },
    "execution_time": 2.45
}
```

### Subdomain Discovery

```http
POST /api/search/subdomains
Content-Type: application/json

{
    "domain": "example.com",
    "use_extended_wordlist": true,
    "include_cert_transparency": true,
    "analyze_subdomains": true,
    "timeout": 300
}
```

**Response:**
```json
{
    "success": true,
    "domain": "example.com",
    "results": {
        "subdomains": [
            {
                "name": "www.example.com",
                "ip_address": "192.0.2.1",
                "status": "active",
                "services": [
                    {
                        "url": "http://www.example.com",
                        "status_code": 200,
                        "protocol": "http"
                    }
                ],
                "technologies": ["Apache", "Ubuntu"],
                "ports": [80, 443]
            }
        ],
        "summary": {
            "total_found": 5,
            "active_subdomains": 4,
            "brute_force_found": 3,
            "cert_transparency_found": 2
        }
    },
    "execution_time": 45.67
}
```

### SSL Certificate Analysis

```http
POST /api/search/ssl-certificates
Content-Type: application/json

{
    "target": "example.com",
    "include_chain": true,
    "analyze_security": true,
    "timeout": 30
}
```

**Response:**
```json
{
    "success": true,
    "target": "example.com",
    "results": {
        "current_certificate": {
            "common_name": "example.com",
            "subject_alt_names": ["example.com", "www.example.com"],
            "issuer": "Let's Encrypt",
            "valid_from": "2023-01-01T00:00:00Z",
            "valid_to": "2024-01-01T00:00:00Z",
            "key_size": 2048,
            "is_valid": true
        },
        "security_analysis": {
            "security_score": 75,
            "security_rating": "Good",
            "issues": [],
            "recommendations": ["Add DMARC record"]
        },
        "related_domains": ["example.com", "www.example.com"]
    },
    "execution_time": 3.21
}
```

### Reverse IP Lookup

```http
POST /api/search/reverse-ip
Content-Type: application/json

{
    "ip_address": "192.0.2.1",
    "include_services": true,
    "timeout": 60
}
```

**Response:**
```json
{
    "success": true,
    "ip_address": "192.0.2.1",
    "results": {
        "domains": ["example.com", "www.example.com", "mail.example.com"],
        "ip_info": {
            "ip_address": "192.0.2.1",
            "isp": "Example ISP",
            "asn": "AS64512",
            "country": "US"
        },
        "services": [
            {
                "port": 80,
                "service_name": "HTTP",
                "is_open": true
            },
            {
                "port": 443,
                "service_name": "HTTPS",
                "is_open": true
            }
        ]
    },
    "execution_time": 8.94
}
```

### Related Domains Discovery

```http
POST /api/search/related-domains
Content-Type: application/json

{
    "target": "example.com",
    "search_types": ["variations", "registrant_links", "infrastructure_links"],
    "max_results": 100,
    "timeout": 120
}
```

**Response:**
```json
{
    "success": true,
    "target": "example.com",
    "results": {
        "domain_variations": [
            {
                "domain": "examplle.com",
                "variation_type": "typosquatting",
                "confidence": 0.7,
                "risk_level": "high",
                "status": "available"
            }
        ],
        "related_domains": [
            {
                "domain": "examplle.com",
                "relationship_type": "typosquatting",
                "confidence": 0.7,
                "status": "available"
            }
        ],
        "summary": {
            "total_variations_found": 1,
            "high_risk_variations": 1,
            "active_domains": 0
        }
    },
    "execution_time": 15.23
}
```

### Infrastructure Mapping

```http
GET /api/search/infrastructure/example.com
```

**Response:**
```json
{
    "success": true,
    "domain": "example.com",
    "results": {
        "ip_addresses": [
            {
                "ip_address": "192.0.2.1",
                "isp": "Example ISP",
                "asn": "AS64512",
                "country": "US"
            }
        ],
        "services": [
            {
                "port": 80,
                "service_name": "HTTP",
                "is_open": true
            }
        ],
        "cdn_info": {
            "uses_cdn": false,
            "cdn_providers": []
        },
        "infrastructure_summary": {
            "unique_ip_addresses": 1,
            "unique_asns": 1,
            "total_services": 1,
            "web_services": 1,
            "hosting_type": "Dedicated"
        }
    },
    "execution_time": 12.34
}
```

### Domain Portfolio Analysis

```http
POST /api/search/domain-portfolio
Content-Type: application/json

{
    "identifier": "admin@example.com",
    "identifier_type": "email",
    "include_analysis": true,
    "timeout": 60
}
```

**Response:**
```json
{
    "success": true,
    "identifier": "admin@example.com",
    "identifier_type": "email",
    "results": {
        "registrant_domains": ["example.com", "example.org"],
        "analysis": [
            {
                "domain": "example.com",
                "whois_info": {
                    "domain": "example.com",
                    "registrant_email": "admin@example.com",
                    "registrar": "Example Registrar"
                }
            }
        ]
    },
    "execution_time": 8.76
}
```

## Configuration

### Environment Variables

```bash
# PostgreSQL
POSTGRES_URL=postgresql+asyncpg://user:password@localhost:5432/domain_intel
POSTGRES_ECHO=false
POSTGRES_POOL_SIZE=10
POSTGRES_MAX_OVERFLOW=20

# Neo4j
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password
NEO4J_DATABASE=neo4j

# External API Keys
WHOISXML_API_KEY=your_whoisxml_api_key
SECURITYTRAILS_API_KEY=your_securitytrails_api_key
CENSYS_API_ID=your_censys_api_id
CENSYS_API_SECRET=your_censys_api_secret
SHODAN_API_KEY=your_shodan_api_key
MAXMIND_ACCOUNT_ID=your_maxmind_account_id
MAXMIND_LICENSE_KEY=your_maxmind_license_key
```

### Database Setup

1. **PostgreSQL Setup:**
   ```sql
   CREATE DATABASE domain_intel;
   CREATE USER domain_user WITH PASSWORD 'secure_password';
   GRANT ALL PRIVILEGES ON DATABASE domain_intel TO domain_user;
   ```

2. **Neo4j Setup:**
   ```bash
   # Install Neo4j
   wget -O - https://debian.neo4j.com/neotechnology.gpg.key | sudo apt-key add -
   echo 'deb https://debian.neo4j.com stable 4.4' | sudo tee -a /etc/apt/sources.list.d/neo4j.list
   sudo apt-get update
   sudo apt-get install neo4j
   
   # Start Neo4j
   sudo systemctl start neo4j
   sudo systemctl enable neo4j
   ```

### Installation

1. **Clone and Setup:**
   ```bash
   cd /home/engine/project/backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Database Initialization:**
   ```python
   from database.config import initialize_databases
   
   # Initialize databases
   asyncio.run(initialize_databases())
   ```

3. **Run the API:**
   ```bash
   uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
   ```

## Usage Examples

### Python Client Usage

```python
import asyncio
import aiohttp

async def analyze_domain(domain):
    async with aiohttp.ClientSession() as session:
        # WHOIS lookup
        whois_data = await perform_whois_lookup(session, domain)
        print(f"Registrant: {whois_data['data']['registrant_name']}")
        
        # DNS enumeration
        dns_data = await enumerate_dns_records(session, domain)
        print(f"A records: {dns_data['records']['a_records']}")
        
        # Subdomain discovery
        subdomains = await discover_subdomains(session, domain)
        print(f"Found {len(subdomains['results']['subdomains'])} subdomains")

async def main():
    await analyze_domain("example.com")

if __name__ == "__main__":
    asyncio.run(main())
```

### Bulk Domain Analysis

```python
import asyncio
from modules.whois_lookup import WHOISLookup
from modules.dns_enumeration import DNSEnumeration
from modules.subdomain_discovery import SubdomainDiscovery

async def bulk_analyze_domains(domains):
    whois_service = WHOISLookup()
    dns_service = DNSEnumeration()
    subdomain_service = SubdomainDiscovery()
    
    results = {}
    
    for domain in domains:
        try:
            # Perform all analyses in parallel
            whois_task = whois_service.lookup_domain(domain)
            dns_task = dns_service.get_all_records(domain)
            subdomain_task = subdomain_service.discover_subdomains(domain)
            
            whois_data, dns_data, subdomain_data = await asyncio.gather(
                whois_task, dns_task, subdomain_task
            )
            
            results[domain] = {
                'whois': whois_data.to_dict() if whois_data else None,
                'dns': dns_data,
                'subdomains': subdomain_data
            }
            
        except Exception as e:
            print(f"Error analyzing {domain}: {e}")
            results[domain] = {'error': str(e)}
    
    return results

# Usage
domains = ['example.com', 'google.com', 'github.com']
results = asyncio.run(bulk_analyze_domains(domains))
```

## Security Considerations

### Rate Limiting

- Implement rate limiting to avoid overwhelming external services
- Use exponential backoff for failed requests
- Cache results to reduce API calls

### Data Privacy

- WHOIS data may contain personal information
- Follow GDPR and other privacy regulations
- Implement data retention policies

### API Key Security

- Store API keys in environment variables
- Rotate keys regularly
- Monitor API usage for anomalies

## Performance Optimization

### Caching Strategy

```python
from functools import lru_cache
import redis

class CachedDomainIntelligence:
    def __init__(self):
        self.redis_client = redis.Redis(host='localhost', port=6379, db=0)
        self.cache_ttl = 3600  # 1 hour
    
    async def get_whois_data(self, domain):
        cache_key = f"whois:{domain}"
        
        # Check cache first
        cached_data = self.redis_client.get(cache_key)
        if cached_data:
            return json.loads(cached_data)
        
        # Perform WHOIS lookup
        whois_data = await self.whois_service.lookup_domain(domain)
        
        # Cache result
        self.redis_client.setex(
            cache_key, 
            self.cache_ttl, 
            json.dumps(whois_data.to_dict())
        )
        
        return whois_data.to_dict()
```

### Async Processing

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

class AsyncDomainAnalyzer:
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=10)
    
    async def analyze_domain_batch(self, domains):
        # Use asyncio.gather for concurrent processing
        tasks = [
            self.analyze_single_domain(domain) 
            for domain in domains
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        return {
            domain: result for domain, result 
            in zip(domains, results)
        }
    
    async def analyze_single_domain(self, domain):
        # Use thread pool for blocking operations
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor, 
            self.perform_blocking_analysis, 
            domain
        )
```

## Integration with Other Modules

### Phase 2.3/2.4 Integration

The domain intelligence module integrates with earlier phases:

1. **Email Intelligence**: Cross-reference domains found via email searches
2. **People Search**: Match WHOIS registrant data with people intelligence
3. **Company Intelligence**: Associate domains with organization data

### Phase 2.6/2.7 Integration

1. **GitHub Intelligence**: Match domains with GitHub usernames and repositories
2. **Graph Correlation**: Create Neo4j relationships between all discovered entities

### Frontend Integration

```javascript
// Example React component for domain intelligence
import React, { useState } from 'react';

const DomainAnalyzer = () => {
    const [domain, setDomain] = useState('');
    const [results, setResults] = useState(null);
    const [loading, setLoading] = useState(false);

    const analyzeDomain = async () => {
        setLoading(true);
        try {
            const response = await fetch('/api/search/whois', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    target: domain, 
                    include_analysis: true 
                })
            });
            const data = await response.json();
            setResults(data);
        } catch (error) {
            console.error('Analysis failed:', error);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div>
            <input 
                type="text" 
                value={domain} 
                onChange={(e) => setDomain(e.target.value)}
                placeholder="Enter domain"
            />
            <button onClick={analyzeDomain} disabled={loading}>
                {loading ? 'Analyzing...' : 'Analyze Domain'}
            </button>
            
            {results && (
                <div className="results">
                    <h3>WHOIS Information</h3>
                    <p>Registrant: {results.data?.registrant_name}</p>
                    <p>Email: {results.data?.registrant_email}</p>
                    <p>Registrar: {results.data?.registrar}</p>
                </div>
            )}
        </div>
    );
};
```

## Testing

### Unit Tests

```python
import pytest
import asyncio
from modules.whois_lookup import WHOISLookup

@pytest.mark.asyncio
async def test_whois_lookup():
    whois_service = WHOISLookup()
    result = await whois_service.lookup_domain("example.com")
    
    assert result is not None
    assert result.domain == "example.com"
    assert result.registrar is not None

@pytest.mark.asyncio
async def test_dns_enumeration():
    dns_service = DNSEnumeration()
    records = await dns_service.get_a_records("google.com")
    
    assert len(records) > 0
    assert records[0].type == "A"
    assert records[0].value is not None
```

### Integration Tests

```python
import pytest
from api.main import app
from fastapi.testclient import TestClient

client = TestClient(app)

def test_whois_api():
    response = client.post("/api/search/whois", json={
        "target": "example.com",
        "include_analysis": True
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "data" in data
    assert "execution_time" in data

def test_dns_api():
    response = client.post("/api/search/dns-records", json={
        "domain": "example.com",
        "record_types": ["A", "MX"]
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "records" in data
```

## Monitoring and Logging

### Logging Configuration

```python
import logging
from logging.handlers import RotatingFileHandler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler('domain_intel.log', maxBytes=10*1024*1024, backupCount=5),
        logging.StreamHandler()
    ]
)

# Module-specific loggers
whois_logger = logging.getLogger('domain_intel.whois')
dns_logger = logging.getLogger('domain_intel.dns')
subdomain_logger = logging.getLogger('domain_intel.subdomain')
```

### Metrics Collection

```python
from prometheus_client import Counter, Histogram, Gauge

# Define metrics
whois_queries_total = Counter('whois_queries_total', 'Total WHOIS queries', ['status'])
dns_query_duration = Histogram('dns_query_duration_seconds', 'DNS query duration')
active_domains = Gauge('active_domains_total', 'Total active domains being monitored')

# Usage in code
def track_whois_query(success=True):
    whois_queries_total.labels(status='success' if success else 'failure').inc()

def track_dns_duration(duration):
    dns_query_duration.observe(duration)
```

## Troubleshooting

### Common Issues

1. **WHOIS Lookup Failures:**
   - Check rate limits on WHOIS services
   - Verify domain format
   - Handle timeout gracefully

2. **DNS Resolution Issues:**
   - Check DNS server connectivity
   - Verify domain exists
   - Handle different DNS record types

3. **Subdomain Discovery Timeouts:**
   - Adjust timeout values
   - Use smaller wordlists for testing
   - Implement progress tracking

4. **Database Connection Issues:**
   - Verify PostgreSQL and Neo4j are running
   - Check connection strings
   - Monitor connection pool usage

### Debug Mode

```python
import logging

# Enable debug logging
logging.getLogger('domain_intel').setLevel(logging.DEBUG)

# Add debug output to specific modules
whois_service = WHOISLookup()
whois_service.debug = True
```

## Future Enhancements

### Planned Features

1. **Machine Learning Integration:**
   - Automated domain classification
   - Malicious domain detection
   - Anomaly detection in DNS patterns

2. **Additional Data Sources:**
   - Passive DNS feeds
   - Threat intelligence feeds
   - Certificate transparency monitoring

3. **Advanced Analytics:**
   - Domain reputation scoring
   - Infrastructure fingerprinting
   - Attack surface mapping

4. **Performance Improvements:**
   - Distributed processing
   - Advanced caching strategies
   - Optimized database queries

### API Versioning

```python
# Version 2.0 enhancements
@router.post("/v2/whois")
async def perform_enhanced_whois_lookup(request: EnhancedWHOISRequest):
    # Enhanced features:
    # - Multiple data source aggregation
    # - Historical WHOIS data
    # - Automated analysis
    pass
```

This comprehensive documentation provides a complete guide for implementing, deploying, and using the domain intelligence module for OSINT operations.