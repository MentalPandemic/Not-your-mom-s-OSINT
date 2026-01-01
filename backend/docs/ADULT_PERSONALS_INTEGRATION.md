# Adult/Personals Sites Integration

This document describes the integration of adult/NSFW platforms and personals/classified sites into the Not-your-mom's-OSINT platform.

## Overview

The adult/personals integration provides comprehensive enumeration and scraping capabilities for:

1. **Adult/NSFW Platforms**: Pornography sites, adult social networks, and adult forums
2. **Personals/Classified Sites**: Skipthegames, Bedpage, Craigslist, Doublelist, and similar platforms

## Architecture

### Module Structure

```
backend/
├── modules/
│   ├── adult_sites.py          # Adult platform enumeration
│   └── personals_sites.py      # Personals/classified scraping
├── routes/
│   └── adult_personals.py      # API endpoints
├── config/
│   └── adult_personals_sources.json  # Configuration
├── models/
│   └── database.py             # Database models
└── utils/
    └── scraping_utils.py        # Scraping utilities
```

### Data Flow

1. **API Request** → FastAPI endpoint
2. **Scraping Module** → Async scraping with rate limiting
3. **Data Extraction** → BeautifulSoup parsing, regex extraction
4. **Database Storage** → PostgreSQL + Neo4j
5. **API Response** → JSON results

## Supported Platforms

### Adult/NSFW Sites

| Platform | Type | Features |
|----------|------|----------|
| Pornhub | Pornography | Profile search, username enumeration, linked accounts |
| xHamster | Pornography | Profile search, content enumeration |
| Motherless | Pornography | Profile search, user enumeration |
| RedTube | Pornography | Profile search |
| Xvideos | Pornography | Profile search, content enumeration |
| Fetlife | Adult Social | Profile enumeration, linked social media |
| OnlyFans | Adult Social | Creator profiles, linked social media |

### Personals/Classified Sites

| Platform | Type | Features |
|----------|------|----------|
| Skipthegames | Personals | Profile/post enumeration, contact info extraction |
| Bedpage | Classifieds | Profile/post enumeration, service descriptions |
| Craigslist | Classifieds | Personals categories, location-based search |
| Doublelist | Personals | Profile/post enumeration, contact info |

## Data Extraction

### Adult Platforms

- **Username**: Exact match and partial match detection
- **Profile URL**: Full profile link
- **Bio/Description**: User profile information
- **Join Date**: Account creation date
- **Profile Image**: Avatar/image URL
- **Linked Accounts**: Social media and other platform links
- **Confidence Score**: Match probability (0.0-1.0)

### Personals Sites

- **Post Title**: Advertisement title
- **Post Content**: Full post description
- **Phone Number**: Normalized contact number
- **Email**: Normalized email address
- **Location**: Raw location text and parsed coordinates
- **Post Date**: Publication timestamp
- **Images**: Post image URLs
- **Confidence Score**: Match probability (0.0-1.0)

## Confidence Scoring

### Adult Platforms

- **Exact username match**: +1.0 point
- **Partial username match**: +0.5 points
- **Target in bio**: +0.5 points
- **Target in profile URL**: +0.5 points
- **Exact match bonus**: ×1.2 multiplier

### Personals Sites

- **Target in title**: +1.0 point
- **Target in content**: +1.0 point
- **Exact phone match**: +1.0 point
- **Exact email match**: +1.0 point
- **Target in location**: +0.5 points
- **Exact contact match bonus**: ×1.3 multiplier

## Database Schema

### PostgreSQL Tables

#### `adult_profiles`
```sql
CREATE TABLE adult_profiles (
    id SERIAL PRIMARY KEY,
    identity_id INTEGER,
    platform VARCHAR(50),
    username VARCHAR(100),
    profile_url VARCHAR(500),
    bio TEXT,
    join_date TIMESTAMP,
    profile_image_url VARCHAR(500),
    linked_accounts JSON,
    confidence_score FLOAT,
    scraped_at TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    metadata JSON
);
```

#### `personals_posts`
```sql
CREATE TABLE personals_posts (
    id SERIAL PRIMARY KEY,
    identity_id INTEGER,
    site VARCHAR(50),
    post_id VARCHAR(100),
    post_title VARCHAR(255),
    post_content TEXT,
    phone_number VARCHAR(20),
    email VARCHAR(255),
    location VARCHAR(255),
    latitude FLOAT,
    longitude FLOAT,
    post_date TIMESTAMP,
    scraped_at TIMESTAMP,
    confidence_score FLOAT,
    image_urls JSON,
    is_active BOOLEAN DEFAULT TRUE,
    metadata JSON
);
```

#### `content`
```sql
CREATE TABLE content (
    id SERIAL PRIMARY KEY,
    identity_id INTEGER,
    source_site VARCHAR(100),
    post_id VARCHAR(100),
    contact_info JSON,
    location_data JSON,
    post_content TEXT,
    image_urls JSON,
    posted_date TIMESTAMP,
    scraped_date TIMESTAMP,
    confidence_score FLOAT,
    is_active BOOLEAN DEFAULT TRUE,
    metadata JSON
);
```

### Neo4j Graph Structure

- **Nodes**: `AdultProfile`, `PersonalsPost`, `Identity`
- **Relationships**: `POSTED_ON`, `LINKED_TO`, `MENTIONED_IN`
- **Properties**: Platform, username, confidence scores, timestamps

## API Endpoints

### Adult Sites Search

**POST** `/api/search/adult-sites`

Request:
```json
{
    "target": "username_or_keyword",
    "platforms": ["pornhub", "xhamster"]
}
```

Response:
```json
{
    "success": true,
    "target": "username_or_keyword",
    "results": [
        {
            "platform": "pornhub",
            "username": "target_user",
            "profile_url": "https://...",
            "bio": "User description",
            "join_date": "2023-01-01T00:00:00Z",
            "profile_image_url": "https://...",
            "linked_accounts": ["twitter.com/user"],
            "confidence_score": 0.95,
            "scraped_at": "2023-10-01T12:00:00Z"
        }
    ],
    "count": 1
}
```

### Personals Sites Search

**POST** `/api/search/personals-sites`

Request:
```json
{
    "target": "phone_or_email_or_keyword",
    "sites": ["skipthegames", "bedpage"]
}
```

Response:
```json
{
    "success": true,
    "target": "phone_or_email_or_keyword",
    "results": [
        {
            "site": "skipthegames",
            "post_id": "abc123",
            "post_title": "Looking for...",
            "post_content": "Full post text",
            "phone_number": "+1234567890",
            "email": "user@example.com",
            "location": "City, State",
            "post_date": "2023-01-01T00:00:00Z",
            "image_urls": ["https://..."],
            "confidence_score": 0.85,
            "scraped_at": "2023-10-01T12:00:00Z"
        }
    ],
    "count": 1
}
```

### Contact Info Search

**POST** `/api/search/contact-info`

Request:
```json
{
    "contact_info": "phone_or_email"
}
```

Response:
```json
{
    "success": true,
    "contact_info": "phone_or_email",
    "adult_profiles": [...],
    "personals_posts": [...],
    "total_results": 5
}
```

## Technical Implementation

### Async Scraping

- **aiohttp**: Async HTTP requests
- **Concurrent requests**: Configurable max concurrent connections
- **Rate limiting**: Respectful scraping with delays
- **User-agent rotation**: Avoid blocking
- **Retry logic**: Exponential backoff for failed requests

### Data Processing

- **BeautifulSoup**: HTML parsing
- **Regex extraction**: Phone numbers, emails, locations
- **Normalization**: Consistent data formats
- **Confidence scoring**: Match probability calculation

### Database Operations

- **SQLAlchemy Async**: Async PostgreSQL operations
- **Neo4j Python Driver**: Graph database integration
- **Batch processing**: Efficient data storage
- **Error handling**: Transaction rollback on failure

## Configuration

### Environment Variables

```env
# Database
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=osint_db
POSTGRES_USER=osint_user
POSTGRES_PASSWORD=secure_password

# Neo4j
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=neo4j_password

# Scraping
MAX_CONCURRENT_REQUESTS=10
REQUEST_TIMEOUT=30
RETRY_ATTEMPTS=3
RETRY_DELAY=5
```

### Source Configuration

Configuration is stored in `backend/config/adult_personals_sources.json` with:

- Platform-specific selectors
- Rate limiting settings
- Confidence thresholds
- Timeout and retry settings

## Legal and Ethical Considerations

### Compliance

- **Public data only**: No private or authenticated content
- **Terms of service**: Respect platform rules
- **Robots.txt**: Honor scraping restrictions
- **Rate limiting**: Prevent server overload

### Data Privacy

- **No account compromise**: No password cracking or hacking
- **Secure storage**: Encrypted databases
- **Access controls**: Proper authentication
- **Data retention**: Compliance with regulations

### Ethical Scraping

- **Respectful delays**: Minimum 0.5-2.0 seconds between requests
- **User-agent rotation**: Avoid detection
- **Error handling**: Graceful failure
- **Logging**: Comprehensive audit trails

## Performance Optimization

### Scraping Efficiency

- **Concurrent requests**: 5-10 simultaneous connections
- **Connection pooling**: Reuse HTTP connections
- **Caching**: Store recent results
- **Batch processing**: Group similar requests

### Database Performance

- **Indexing**: Proper database indexes
- **Async operations**: Non-blocking I/O
- **Batch inserts**: Bulk data operations
- **Query optimization**: Efficient SQL queries

## Error Handling

### Common Issues

- **Blocked requests**: User-agent rotation and delays
- **CAPTCHAs**: Manual intervention required
- **Rate limits**: Exponential backoff
- **Connection errors**: Retry with delay

### Monitoring

- **Logging**: Structured logs with timestamps
- **Metrics**: Request success rates
- **Alerts**: Failure notifications
- **Health checks**: API status monitoring

## Testing

### Unit Tests

- **Scraping functions**: HTML parsing validation
- **Data extraction**: Regex pattern testing
- **Confidence scoring**: Algorithm verification
- **Normalization**: Data format consistency

### Integration Tests

- **Database operations**: CRUD validation
- **API endpoints**: Request/response testing
- **Concurrent scraping**: Performance benchmarks
- **Error scenarios**: Failure handling

### Mock Testing

- **Fake responses**: Avoid real site requests
- **Test data**: Sample HTML content
- **Edge cases**: Invalid inputs
- **Performance**: Load testing

## Future Enhancements

### Additional Platforms

- More adult sites (BongaCams, Chaturbate, etc.)
- Additional classified sites (Backpage alternatives)
- International platforms

### Advanced Features

- **Image analysis**: Visual correlation
- **NLP processing**: Better text extraction
- **Geolocation**: Precise location mapping
- **Network analysis**: Relationship mapping

### Performance Improvements

- **Proxy rotation**: Avoid IP blocking
- **Distributed scraping**: Scale horizontally
- **Machine learning**: Better confidence scoring
- **Caching layer**: Redis integration

## Troubleshooting

### Common Issues

1. **Blocked requests**: Increase delay, rotate user agents
2. **Database errors**: Check connection settings
3. **Slow performance**: Reduce concurrent requests
4. **Data quality**: Adjust confidence thresholds

### Debugging

- **Logging**: Check application logs
- **API testing**: Use Swagger UI
- **Database inspection**: Direct SQL queries
- **Network monitoring**: Check request/response

## Conclusion

This integration provides comprehensive adult/NSFW and personals/classified site scraping capabilities while maintaining ethical standards and legal compliance. The modular design allows for easy extension to additional platforms and features.