# Username Enumeration API - Integration Guide

This guide explains how to integrate the username enumeration API into the core platform.

## Core Platform Integration Points

### 1. Main Search Endpoint Integration

Update the main `/api/search` endpoint to include username enumeration results:

```python
from backend.routes.username_enum import search_username

@router.post("/api/search")
async def unified_search(search_request: UnifiedSearchRequest):
    results = {}
    
    # If username is provided, include enum results
    if search_request.username:
        username_results = await search_username(
            request,
            UsernameSearchRequest(
                username=search_request.username,
                email=search_request.email,
                phone=search_request.phone
            )
        )
        results['username_enum'] = username_results
    
    # Include other search types...
    return results
```

### 2. Results Endpoint Integration

Update the main results endpoint to include username data:

```python
@router.get("/api/results/{identity_id}")
async def get_results(identity_id: str):
    # Get existing identity data
    identity_data = await get_identity_from_db(identity_id)
    
    # Augment with username enumeration data
    if identity_data.get('username'):
        username_data = await get_username_results(
            request,
            identity_data['username']
        )
        identity_data['username_profiles'] = username_data
    
    return identity_data
```

### 3. Neo4j Graph Integration

The username enumeration service automatically creates Neo4j relationships:
- Links discovered profiles to usernames
- Creates email/phone connections
- Builds identity chains

Access graph data through:
```python
# Get identity chain
GET /api/results/identity-chain/{username}

# Get related identities
# Query Neo4j directly or use the graph endpoints
```

### 4. Export Functionality Integration

Update CSV/JSON export to include username data:

```python
@router.get("/api/export/{format}")
async def export_data(format: str, identity_id: str):
    # Get base data
    data = await get_identity_data(identity_id)
    
    # Include username enumeration results
    if data.get('username'):
        username_results = await search_username(
            UsernameSearchRequest(username=data['username'])
        )
        data['discovered_profiles'] = username_results.results
    
    # Export to requested format
    return export_to_format(data, format)
```

## Frontend Integration

### API Client Setup

```javascript
const USERNAME_API_BASE = '/api/search';

class UsernameEnumClient {
    async searchUsername(username, email = null, phone = null) {
        const response = await fetch(`${USERNAME_API_BASE}/username`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ username, email, phone })
        });
        
        if (response.status === 429) {
            throw new Error('Rate limit exceeded');
        }
        
        return response.json();
    }
    
    async getIdentityChain(username) {
        const response = await fetch(`/api/results/identity-chain/${username}`);
        return response.json();
    }
}
```

### UI Components

#### Username Profile Display
```javascript
function UsernameProfileCard({ profile }) {
    const confidenceColor = profile.confidence > 0.7 ? 'green' : 
                           profile.confidence > 0.5 ? 'yellow' : 'red';
    
    return (
        <div className="profile-card">
            <h4>{profile.platform}</h4>
            <a href={profile.profile_url} target="_blank" rel="noopener noreferrer">
                View Profile
            </a>
            <div className={`confidence-${confidenceColor}`}>
                Confidence: {Math.round(profile.confidence * 100)}%
            </div>
            <span className="match-type">{profile.match_type}</span>
        </div>
    );
}
```

#### Identity Chain Visualization
```javascript
function IdentityChain({ chain }) {
    return (
        <div className="identity-chain">
            {chain.nodes?.map(node => (
                <div key={node.id} className={`node ${node.type}`}>
                    <strong>{node.type}:</strong> {node.value}
                    {node.platform && <span>({node.platform})</span>}
                </div>
            ))}
        </div>
    );
}
```

### Rate Limiting Headers

The API includes rate limit headers in all responses:

```javascript
async function handleRateLimiting(response) {
    const limit = response.headers.get('X-RateLimit-Limit-Minute');
    const remaining = response.headers.get('X-RateLimit-Remaining-Minute');
    
    console.log(`Requests: ${remaining}/${limit} remaining`);
    
    if (remaining === '0') {
        // Show rate limit warning to user
        showWarning('Rate limit approaching');
    }
}
```

## Data Flow

### Search Flow

1. User initiates search with username
2. Frontend calls `/api/search/username`
3. API performs enumeration across all platforms
4. Results cached for 1 hour
5. Results stored in PostgreSQL and Neo4j
6. Response returned with confidence scores

### Reverse Lookup Flow

1. User provides email/phone
2. Frontend calls `/api/search/reverse-lookup`
3. API extracts patterns and searches for usernames
4. Returns associated usernames and platforms
5. Data logged to databases

### Identity Chain Flow

1. User requests identity chain for username
2. Frontend calls `/api/results/identity-chain/{username}`
3. API queries Neo4j for relationships
4. If no data, dynamically builds chain
5. Returns nodes and relationships

## Performance Considerations

### Caching Strategy

- User searches cached for 1 hour
- Platform metadata cached indefinitely
- Cache keys based on search parameters
- Redis preferred, in-memory fallback

### Batch Processing

For multiple searches, use batch endpoint:

```python
@router.post("/api/search/batch")
async def batch_search(search_requests: List[UsernameSearchRequest]):
    results = await asyncio.gather(*[
        search_username(req) for req in search_requests
    ])
    return results
```

### Connection Pooling

Database connections are pooled automatically:
- PostgreSQL: 2-10 connections
- Neo4j: Managed by driver

## Error Handling

### Common Errors

```javascript
// Rate limit exceeded (429)
if (response.status === 429) {
    const retryAfter = response.headers.get('Retry-After');
    showError(`Rate limit exceeded. Try again in ${retryAfter} seconds.`);
}

// Invalid input (400)
if (response.status === 400) {
    const error = await response.json();
    showError(`Invalid input: ${error.message}`);
}

// Server error (500)
if (response.status >= 500) {
    showError('Server error. Please try again later.');
}
```

### Validation

Input validation is performed automatically:
- Username format validation
- Email format validation
- Phone format validation
- Tolerance level validation

## Monitoring

### Metrics Available

- Request count by endpoint
- Average response times
- Cache hit rates
- Rate limit hits
- Platform discovery rates
- Confidence score distributions

Access metrics through:
```python
GET /api/search/stats?days=7
```

### Logging

All searches are logged with:
- Search parameters
- Results count
- Execution time
- IP address
- User agent
- Timestamp

## Security Considerations

### Rate Limiting

- Per-IP rate limits enforced
- Configurable limits per endpoint
- Graceful handling of exceeded limits
- Block suspicious IPs automatically

### Input Sanitization

- All inputs validated with Pydantic
- SQL injection prevention
- XSS prevention
- Special character handling

### Data Privacy

- IP addresses stored for analytics
- Optional user agent logging
- GDPR-compliant data handling
- Data retention policies configurable

## Deployment

### Environment Variables

Required environment variables:
- `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`
- `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`
- `REDIS_HOST` (optional, for caching)
- `RATE_LIMIT_*` (optional, for rate limiting)

### Docker Configuration

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "-m", "backend.main"]
```

### Scaling

For high traffic:
- Use Redis for distributed caching
- Scale PostgreSQL read replicas
- Neo4j cluster mode
- Load balancer with sticky sessions