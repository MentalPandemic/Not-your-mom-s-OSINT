# Username Enumeration API Documentation

Comprehensive API documentation for username enumeration and identity relationship mapping.

## Overview

The Username Enumeration API provides endpoints for discovering and analyzing username presence across multiple social platforms and building identity relationship chains.

**Base URL**: `http://localhost:8000/api`

**Version**: 1.0.0

**Authentication**: None (public API with rate limiting)

---

## Authentication

Currently, the API does not require authentication. All endpoints are public but subject to rate limiting.

---

## Rate Limiting

The API implements per-IP rate limiting with different limits per endpoint:

- **Standard endpoints**: 10 requests/minute, 100 requests/hour
- **Search endpoints**: 5 requests/minute, 50 requests/hour
- **Fuzzy search**: 3 requests/minute, 30 requests/hour
- **Reverse lookup**: 2 requests/minute, 20 requests/hour

Rate limit information is included in response headers:

```
X-RateLimit-Limit-Minute: 10
X-RateLimit-Remaining-Minute: 8
X-RateLimit-Limit-Hour: 100
X-RateLimit-Remaining-Hour: 95
X-RateLimit-Reset: 2024-01-01T13:00:00Z
```

When rate limit is exceeded, the API returns `429 Too Many Requests`:

```http
HTTP/1.1 429 Too Many Requests
Retry-After: 60
X-RateLimit-Limit-Minute: 10
X-RateLimit-Remaining-Minute: 0
```

---

## Endpoints

### 1. Username Search

Search for username across all platforms using exact, fuzzy, and pattern matching.

```http
POST /api/search/username
```

#### Request Body

```json
{
  "username": "johndoe",
  "email": "john@example.com",
  "phone": "+1234567890"
}
```

**Parameters:**
- `username` (required): Username to search for
- `email` (optional): Email address for cross-referencing
- `phone` (optional): Phone number for cross-referencing

**Username Validation:**
- Must be 1-100 characters
- Can contain alphanumeric characters, underscores, hyphens, and dots
- Cannot be empty
- Automatically converted to lowercase

**Query Parameters:**
- `page` (optional): Page number for pagination (default: 1, min: 1)
- `page_size` (optional): Results per page (default: 20, min: 1, max: 100)

#### Response

```json
{
  "results": [
    {
      "platform": "GitHub",
      "profile_url": "https://github.com/johndoe",
      "confidence": 0.95,
      "match_type": "exact",
      "metadata": {
        "username": "johndoe",
        "platform": "GitHub",
        "email": "john@example.com",
        "created_date": "2023-01-15T08:30:00Z"
      },
      "discovered_at": "2024-01-01T12:00:00Z"
    },
    {
      "platform": "Twitter",
      "profile_url": "https://twitter.com/johndoe",
      "confidence": 0.88,
      "match_type": "exact",
      "metadata": {},
      "discovered_at": "2024-01-01T12:00:01Z"
    },
    {
      "platform": "Reddit",
      "profile_url": "https://reddit.com/user/john_doe",
      "confidence": 0.72,
      "match_type": "fuzzy",
      "metadata": {},
      "discovered_at": "2024-01-01T12:00:02Z"
    }
  ],
  "total_count": 15,
  "page": 1,
  "page_size": 20,
  "execution_time_ms": 2345,
  "cached": false
}
```

**Response Fields:**
- `results`: Array of platform results
  - `platform`: Platform name (e.g., "GitHub", "Twitter")
  - `profile_url`: Direct URL to the profile
  - `confidence`: Confidence score (0.0 to 1.0)
  - `match_type`: Type of match (exact, fuzzy, pattern, reverse)
  - `metadata`: Additional platform-specific data
  - `discovered_at`: Timestamp of discovery
- `total_count`: Total number of results
- `page`: Current page number
- `page_size`: Number of results per page
- `execution_time_ms`: Time taken to execute the search
- `cached`: Whether the result was served from cache

**Match Type Definitions:**
- `exact`: Perfect username match on platform
- `fuzzy`: Similar username found (edit distance based)
- `pattern`: Username follows known pattern (firstname_lastname, etc.)
- `reverse`: Found through email/phone reverse lookup

#### Examples

**cURL:**
```bash
curl -X POST "http://localhost:8000/api/search/username" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "johndoe",
    "email": "john@example.com"
  }'
```

**Python:**
```python
import requests

response = requests.post(
    "http://localhost:8000/api/search/username",
    json={
        "username": "johndoe",
        "email": "john@example.com"
    }
)

data = response.json()
for result in data['results']:
    print(f"Found on {result['platform']}: {result['profile_url']}")
```

**JavaScript:**
```javascript
const response = await fetch('http://localhost:8000/api/search/username', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
    },
    body: JSON.stringify({
        username: 'johndoe',
        email: 'john@example.com'
    })
});

const data = await response.json();
console.log(`Found ${data.total_count} profiles`);
```

---

### 2. Reverse Lookup

Search by email or phone to find associated usernames.

```http
POST /api/search/reverse-lookup
```

#### Request Body

```json
{
  "email": "john@example.com"
}
```

or

```json
{
  "phone": "+1234567890"
}
```

**Parameters:**
- `email` (optional): Email address to search (must provide email or phone)
- `phone` (optional): Phone number to search (must provide email or phone)

**Validation:**
- At least one of `email` or `phone` must be provided
- Email must be valid format
- Phone must contain only digits, +, -, and spaces

#### Response

```json
{
  "usernames": [
    {
      "username": "johndoe",
      "platforms": ["GitHub", "LinkedIn", "Twitter"]
    },
    {
      "username": "john_doe_1990",
      "platforms": ["Instagram", "Reddit"]
    }
  ],
  "total_count": 3,
  "execution_time_ms": 1892
}
```

**Response Fields:**
- `usernames`: Array of found usernames and their platforms
- `total_count`: Total number of unique usernames found
- `execution_time_ms`: Time taken to execute the search

#### Examples

**cURL - Email:**
```bash
curl -X POST "http://localhost:8000/api/search/reverse-lookup" \
  -H "Content-Type: application/json" \
  -d '{"email": "john@example.com"}'
```

**cURL - Phone:**
```bash
curl -X POST "http://localhost:8000/api/search/reverse-lookup" \
  -H "Content-Type: application/json" \
  -d '{"phone": "+1234567890"}'
```

**Python:**
```python
response = requests.post(
    "http://localhost:8000/api/search/reverse-lookup",
    json={"email": "john@example.com"}
)

data = response.json()
for username_data in data['usernames']:
    print(f"Username: {username_data['username']}")
    print(f"Platforms: {', '.join(username_data['platforms'])}")
```

---

### 3. Fuzzy Match Search

Fuzzy search with configurable tolerance for similar usernames.

```http
POST /api/search/fuzzy-match
```

#### Request Body

```json
{
  "username": "johndoe",
  "tolerance_level": "medium"
}
```

**Parameters:**
- `username` (required): Username to search for variations
- `tolerance_level` (optional): Tolerance level - "low", "medium", or "high" (default: "medium")

**Tolerance Levels:**
- `low`: High similarity threshold (80%+), fewer but more accurate results
- `medium`: Moderate similarity threshold (70%+), balanced results (default)
- `high`: Lower similarity threshold (60%+), more results but potentially less accurate

#### Response

```json
{
  "original_username": "johndoe",
  "matches": [
    {
      "platform": "Twitter",
      "profile_url": "https://twitter.com/johndoe",
      "confidence": 0.95,
      "match_type": "exact",
      "metadata": {},
      "discovered_at": "2024-01-01T12:00:00Z"
    },
    {
      "platform": "Reddit",
      "profile_url": "https://reddit.com/user/john_doe",
      "confidence": 0.75,
      "match_type": "fuzzy",
      "metadata": {},
      "discovered_at": "2024-01-01T12:00:01Z"
    },
    {
      "platform": "GitHub",
      "profile_url": "https://github.com/johndoe123",
      "confidence": 0.65,
      "match_type": "fuzzy",
      "metadata": {},
      "discovered_at": "2024-01-01T12:00:02Z"
    }
  ],
  "total_count": 8,
  "execution_time_ms": 1567
}
```

**Response Fields:**
- `original_username`: The username that was searched
- `matches`: Array of matching platform results
- `total_count`: Total number of matches found
- `execution_time_ms`: Time taken to execute the search

#### Examples

**cURL:**
```bash
curl -X POST "http://localhost:8000/api/search/fuzzy-match" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "johndoe",
    "tolerance_level": "high"
  }'
```

**Python:**
```python
response = requests.post(
    "http://localhost:8000/api/search/fuzzy-match",
    json={
        "username": "johndoe",
        "tolerance_level": "high"
    }
)

data = response.json()
for match in data['matches']:
    print(f"{match['platform']}: {match['profile_url']} (confidence: {match['confidence']:.2f})")
```

---

### 4. Get Username Results

Get detailed information about a username across all platforms.

```http
GET /api/results/username/{username}
```

#### Path Parameters

- `username` (required): Username to get results for

#### Query Parameters

- `include_metadata` (optional): Include platform metadata in response (default: true)

#### Response

```json
{
  "username": "johndoe",
  "results_count": 8,
  "platforms": {
    "GitHub": [
      {
        "profile_url": "https://github.com/johndoe",
        "confidence": 0.95,
        "match_type": "exact",
        "discovered_at": "2024-01-01T12:00:00Z",
        "metadata": {
          "email": "john@example.com",
          "bio": "Software developer",
          "created_date": "2020-03-15T10:30:00Z"
        }
      }
    ],
    "Twitter": [
      {
        "profile_url": "https://twitter.com/johndoe",
        "confidence": 0.88,
        "match_type": "exact",
        "discovered_at": "2024-01-01T12:00:01Z"
      }
    ],
    "LinkedIn": [
      {
        "profile_url": "https://www.linkedin.com/in/johndoe",
        "confidence": 0.92,
        "match_type": "exact",
        "discovered_at": "2024-01-01T12:00:02Z"
      }
    ]
  },
  "identity_data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "primary_username": "johndoe",
    "email": "john@example.com",
    "phone": "+1234567890",
    "confidence": 0.95,
    "first_seen": "2024-01-01T10:00:00Z",
    "last_updated": "2024-01-01T12:00:00Z"
  },
  "execution_time_ms": 982
}
```

**Response Fields:**
- `username`: The requested username
- `results_count`: Total number of results found
- `platforms`: Results grouped by platform
- `identity_data`: Consolidated identity information (if available)
- `execution_time_ms`: Time taken to execute the search

---

### 5. Get Identity Chain

Get identity connection chains showing relationships between different identities.

```http
GET /api/results/identity-chain/{username}
```

#### Path Parameters

- `username` (required): Username to get identity chain for

#### Query Parameters

- `max_depth` (optional): Maximum depth of relationship chain (default: 3, min: 1, max: 5)

#### Response

```json
{
  "nodes": [
    {
      "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "type": "username",
      "value": "johndoe",
      "platform": null,
      "confidence": 1.0
    },
    {
      "id": "b2c3d4e5-f6a7-8901-bcde-f23456789012",
      "type": "profile",
      "value": "https://github.com/johndoe",
      "platform": "GitHub",
      "confidence": 0.95
    },
    {
      "id": "c3d4e5f6-a7b8-9012-cdef-345678901234",
      "type": "email",
      "value": "john@example.com",
      "platform": "GitHub",
      "confidence": 0.9
    },
    {
      "id": "d4e5f6a7-b8c9-0123-defg-456789012345",
      "type": "phone",
      "value": "+1234567890",
      "platform": "Twitter",
      "confidence": 0.85
    }
  ],
  "relationships": [
    {
      "source_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "target_id": "b2c3d4e5-f6a7-8901-bcde-f23456789012",
      "relationship_type": "found_on",
      "confidence": 0.95,
      "discovered_at": "2024-01-01T12:00:00Z"
    },
    {
      "source_id": "b2c3d4e5-f6a7-8901-bcde-f23456789012",
      "target_id": "c3d4e5f6-a7b8-9012-cdef-345678901234",
      "relationship_type": "linked_to",
      "confidence": 0.9,
      "discovered_at": "2024-01-01T12:00:01Z"
    }
  ],
  "chain_length": 3,
  "execution_time_ms": 1234
}
```

**Response Fields:**
- `nodes`: Array of identity nodes
  - `id`: Unique node identifier
  - `type`: Node type (username, email, phone, profile)
  - `value`: Node value (username, email address, etc.)
  - `platform`: Associated platform (for profiles)
  - `confidence`: Confidence score for this node
- `relationships`: Array of relationships between nodes
  - `source_id`: Source node ID
  - `target_id`: Target node ID
  - `relationship_type`: Type of relationship
  - `confidence`: Confidence in this relationship
  - `discovered_at`: When this relationship was discovered
- `chain_length`: Number of relationships in the chain
- `execution_time_ms`: Time taken to execute

**Relationship Types:**
- `found_on`: Username found on platform profile
- `linked_to`: Profile linked to email/phone
- `uses`: Username uses email/phone
- `similar_to`: Similar usernames patterns

#### Examples

**cURL:**
```bash
curl "http://localhost:8000/api/results/identity-chain/johndoe?max_depth=3"
```

**Python:**
```python
response = requests.get(
    "http://localhost:8000/api/results/identity-chain/johndoe",
    params={"max_depth": 3}
)

data = response.json()
print(f"Chain has {data['chain_length']} relationships")
print(f"Found {len(data['nodes'])} identity nodes")
```

---

### 6. Search Statistics

Get search and platform statistics for analytics.

```http
GET /api/search/stats
```

#### Query Parameters

- `days` (optional): Number of days to analyze (default: 7, min: 1, max: 90)

#### Response

```json
{
  "analytics": [
    {
      "search_type": "username_search",
      "total_requests": 1523,
      "avg_response_time": 2.34,
      "total_success": 1456,
      "total_errors": 67,
      "avg_cache_hit_rate": 0.65
    },
    {
      "search_type": "reverse_lookup",
      "total_requests": 234,
      "avg_response_time": 1.89,
      "total_success": 228,
      "total_errors": 6,
      "avg_cache_hit_rate": 0.42
    }
  ],
  "platform_statistics": [
    {
      "platform": "GitHub",
      "total_profiles": 856,
      "avg_confidence": 0.88,
      "unique_usernames": 623
    },
    {
      "platform": "Twitter",
      "total_profiles": 723,
      "avg_confidence": 0.82,
      "unique_usernames": 534
    }
  ]
}
```

**Response Fields:**
- `analytics`: Search performance metrics by type
- `platform_statistics`: Platform discovery statistics

---

### 7. Health Check

Check API and service health status.

```http
GET /health
```

#### Response

```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00Z",
  "services": {
    "postgresql": "connected",
    "neo4j": "connected"
  }
}
```

**Status Values:**
- `healthy`: All services operational
- `degraded`: Some services unavailable
- `unhealthy`: Critical services down

---

### 8. API Root

Get API information and available endpoints.

```http
GET /
```

#### Response

```json
{
  "message": "Username Enumeration API",
  "version": "1.0.0",
  "endpoints": {
    "username_search": "/api/search/username",
    "reverse_lookup": "/api/search/reverse-lookup",
    "fuzzy_match": "/api/search/fuzzy-match",
    "username_results": "/api/results/username/{username}",
    "identity_chain": "/api/results/identity-chain/{username}",
    "health_check": "/health",
    "docs": "/docs"
  }
}
```

---

## Core Platform Integration

### 1. General Search

Unified search endpoint that delegates to specific modules.

```http
POST /api/search
```

#### Request Body
```json
{
  "query": "johndoe",
  "search_type": "all"
}
```

### 2. General Results

Get aggregated results for a specific query from all modules.

```http
GET /api/results?query=johndoe
```

---

## Error Responses

### Error Response Format

All errors follow this format:

```json
{
  "error": "Error type",
  "message": "Human-readable error description",
  "timestamp": "2024-01-01T12:00:00Z",
  "request_id": "http://localhost:8000/api/search/username"
}
```

### HTTP Status Codes

- `200 OK`: Successful request
- `400 Bad Request`: Invalid input parameters
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error
- `503 Service Unavailable`: Service temporarily unavailable

### Common Errors

#### Rate Limit Exceeded (429)

```http
HTTP/1.1 429 Too Many Requests
Content-Type: application/json
Retry-After: 60

{
  "error": "Rate limit exceeded",
  "message": "Too many requests. Please try again later.",
  "timestamp": "2024-01-01T12:00:00Z",
  "retry_after": "60",
  "rate_limit_info": {
    "minute_limit": "10",
    "minute_remaining": "0",
    "hour_limit": "100",
    "hour_remaining": "45"
  }
}
```

#### Invalid Input (400)

```http
HTTP/1.1 400 Bad Request
Content-Type: application/json

{
  "error": "Validation error",
  "message": "Username contains invalid characters",
  "timestamp": "2024-01-01T12:00:00Z",
  "request_id": "http://localhost:8000/api/search/username"
}
```

#### Server Error (500)

```http
HTTP/1.1 500 Internal Server Error
Content-Type: application/json

{
  "error": "Search failed",
  "message": "Database connection timeout",
  "timestamp": "2024-01-01T12:00:00Z",
  "request_id": "http://localhost:8000/api/search/username"
}
```

---

## Confidence Scoring

Confidence scores (0.0 - 1.0) indicate matching accuracy:

- **0.90 - 1.00**: Very High Confidence - Strong evidence of correct match
- **0.70 - 0.89**: High Confidence - Likely correct match
- **0.50 - 0.69**: Medium Confidence - Possible match, verify with additional data
- **0.30 - 0.49**: Low Confidence - Weak match, requires verification
- **0.00 - 0.29**: Very Low Confidence - Unlikely to be correct

### Confidence Factors

- **Platform reliability** (20% weight): How reliable the platform data is
- **Match type** (25% weight): Exact matches score higher than fuzzy matches
- **Pattern analysis** (15% weight): Usable patterns in username
- **Metadata quality** (20% weight): Rich profile data increases confidence
- **Temporal factors** (10% weight): Account age and activity
- **String similarity** (10% weight): Similarity to search query

---

## Pattern Recognition

The API recognizes common username patterns:

### Name Patterns
- `firstname_lastname` (e.g., "john_doe", "jane-smith")
- `firstname_initial_lastname` (e.g., "jdoe", "jsmith")
- `firstname.lastname` (e.g., "john.doe", "jane.smith")

### Number Patterns
- `name_number` (e.g., "johndoe123", "user_456")
- `year_suffix` (e.g., "johndoe1990", "jane2000")

### Common Patterns
- `common_name`: Common first names with suffixes
- `repeated_pattern`: Repeated character patterns
- `keyboard_pattern`: QWERTY-based patterns

---

## Supported Platforms

The API supports 19 major platforms:

| Platform | Exact Match | Fuzzy Match | API Available | Auth Required |
|----------|-------------|-------------|---------------|---------------|
| GitHub | ✅ | ✅ | ✅ | ❌ |
| Twitter | ✅ | ✅ | ✅ | ❌ |
| LinkedIn | ✅ | ❌ | ✅ | ✅ |
| Instagram | ✅ | ❌ | ✅ | ❌ |
| Facebook | ✅ | ❌ | ✅ | ❌ |
| Reddit | ✅ | ✅ | ✅ | ❌ |
| YouTube | ✅ | ❌ | ✅ | ❌ |
| TikTok | ✅ | ❌ | ✅ | ❌ |
| Pinterest | ✅ | ✅ | ✅ | ❌ |
| Medium | ✅ | ❌ | ✅ | ❌ |
| StackOverflow | ✅ | ❌ | ✅ | ❌ |
| Discord | ❌ | ❌ | ❌ | ✅ |
| Twitch | ✅ | ✅ | ✅ | ❌ |
| Snapchat | ✅ | ❌ | ✅ | ❌ |
| Telegram | ✅ | ❌ | ✅ | ❌ |
| Keybase | ✅ | ✅ | ✅ | ❌ |
| GitLab | ✅ | ✅ | ✅ | ❌ |

---

## Caching

Results are cached for improved performance:
- **Username searches**: 1 hour cache
- **Platform metadata**: 24 hours cache
- **Search statistics**: 5 minutes cache

Cache hits are indicated in the response:
```json
{
  "cached": true,
  "results": [...]
}
```

---

## Pagination

All search endpoints support pagination:

```http
GET /api/search/username?username=johndoe&page=2&page_size=20
```

**Pagination Parameters:**
- `page`: Page number to retrieve (starts at 1)
- `page_size`: Number of results per page (max 100)

**Response:**
```json
{
  "results": [...],
  "total_count": 156,
  "page": 2,
  "page_size": 20
}
```

---

## Monitoring

### Performance Metrics

Track API performance through:
- `X-Response-Time` header in responses
- `/api/search/stats` endpoint for analytics
- Database logs in PostgreSQL

### Logging

All searches are logged with:
- Search parameters
- Results count
- Execution time
- IP address (for rate limiting)
- Timestamp

Access logs:
```sql
SELECT * FROM search_queries ORDER BY created_at DESC;
SELECT * FROM search_results ORDER BY discovered_at DESC;
```

---

## Security Notes

### Input Validation

- All inputs validated using Pydantic models
- SQL injection protection via parameterized queries
- XSS prevention through proper output encoding
- Special character handling and sanitization

### Data Privacy

- IP addresses stored for rate limiting and security
- User-agent logging for analytics (optional)
- GDPR-compliant data handling
- Configurable data retention policies

### Best Practices

- Always validate user inputs before sending to API
- Handle rate limit responses gracefully
- Don't expose API error details to end users
- Use HTTPS in production
- Implement proper authentication for sensitive data

---

## Performance Considerations

### Response Times

Typical response times:
- **Username search**: 1-3 seconds (depending on platforms)
- **Reverse lookup**: 1-2 seconds
- **Fuzzy search**: 2-4 seconds
- **Identity chain**: 1-2 seconds
- **Cached results**: <100ms

### Optimization Tips

1. **Use specific searches**: Provide email/phone when available
2. **Enable caching**: Configured by default
3. **Use pagination**: For results > 100
4. **Monitor rate limits**: Implement retry logic
5. **Batch processing**: For multiple searches, use async patterns

### Connection Pooling

Database connections are automatically pooled:
- PostgreSQL: 2-10 connections per instance
- Neo4j: Managed by official driver
- Redis: Single connection with pipelining

---

## Support

For issues and questions:
1. Check this documentation and examples
2. Review server logs for error details
3. Test with the `/health` endpoint
4. Verify database connections
5. Check rate limit status

---

## Changelog

### Version 1.0.0 (Current)

- Initial API release
- Username search across 19 platforms
- Reverse lookup functionality
- Fuzzy matching with configurable tolerance
- Identity chain generation
- Rate limiting and caching
- PostgreSQL and Neo4j integration
- Comprehensive statistics
- Full documentation

---

## License

This API is part of the Not-Your-Mom's-OSINT platform.