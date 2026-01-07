# Username Enumeration Module

## Overview

The Username Enumeration Module is the core identity discovery engine for the OSINT platform. It searches for a given username, email, or phone across hundreds of mainstream social media, community, and public platforms using async concurrent probing.

This module serves as the foundation for identity enrichment—once a username is found on one platform, it discovers all other platforms where that identity exists.

## Architecture

### Data Flow

```
Input (username/email/phone)
    ↓
Username Matcher (generate variations)
    ↓
Username Enumerator (async concurrent platform checks)
    ↓
Results Processing (confidence scoring, deduplication)
    ↓
Database Storage (PostgreSQL + Neo4j)
    ↓
API Response
```

### Components

1. **Username Enumerator** (`username_enum.py`): Core engine for concurrent platform checking
2. **Username Matcher** (`username_matching.py`): Fuzzy matching and pattern recognition
3. **Database Manager** (`database.py`): PostgreSQL integration for persistent storage
4. **Graph Manager** (`graph_db.py`): Neo4j integration for identity graphs
5. **API Routes** (`routes/username_enum.py`): FastAPI endpoints
6. **Configuration** (`config/username_enum_sources.json`): Platform definitions

## Supported Platforms (100+)

### Social Media
- Twitter/X, Reddit, Instagram, TikTok, YouTube, Facebook, LinkedIn, Snapchat, Discord, Mastodon, Bluesky, Keybase

### Code & Tech
- GitHub, GitLab, Bitbucket, SourceForge, CodePen, Stack Overflow, HackerNews, Dev.to, Replit, Pastebin

### Community & Forums
- Reddit (all subreddits), 4chan, 8kun, Voat, Lemmy, Kik, Telegram, Medium, Quora, SlashDot

### Gaming
- Twitch, Steam, Epic Games, Origin, Battle.net, PlayStation Network, Xbox Live, Nintendo, Roblox, Minecraft, League of Legends, Fortnite, Valorant

### Dating & Social
- OkCupid, Tinder, Bumble, Hinge, Match, eHarmony, POF, Badoo, Tagged, Meetup

### Media Sharing
- Flickr, 500px, SmugMug, Imgur, Giphy, Tumblr, Pinterest, WeHeartIt, DeviantArt, SoundCloud

### Streaming
- Twitch, YouTube, Vimeo, Dailymotion, Rumble, BitChute, Odysee, Kick, DLive, Spotify

### Professional
- LinkedIn, Crunchbase, AngelList, Behance, Dribbble, ArtStation, Etsy, eBay

### Reviews
- Yelp, TrustPilot, Glassdoor, Indeed, Zillow, Amazon

### Blogging
- WordPress.com, Blogger, Medium, Substack, Ghost, Patreon, Ko-fi

### Niche
- MyFitnessPal, Strava, Goodreads, Letterboxd, IMDB, MyAnimeList, AniList, ResearchGate, Academia.edu

## API Endpoints

### POST /api/search/username

Search for a username across all platforms.

**Request:**
```json
{
  "username": "john_doe",
  "optional_email": null,
  "optional_phone": null,
  "platforms": null,
  "fuzzy_match": false,
  "max_concurrent": 50,
  "cache_results": true
}
```

**Response:**
```json
{
  "username": "john_doe",
  "matches_found": 15,
  "platforms_checked": 100,
  "search_duration": 45.2,
  "matches": [
    {
      "platform": "twitter",
      "profile_url": "https://twitter.com/john_doe",
      "confidence_score": "high",
      "verified": true,
      "response_code": 200,
      "response_time": 1.2,
      "discovery_method": "direct",
      "category": "social_media"
    }
  ]
}
```

### POST /api/search/reverse-lookup

Search by email or phone to find associated usernames.

**Request:**
```json
{
  "email": "john.smith@example.com",
  "phone": null
}
```

**Response:**
```json
{
  "search_type": "email",
  "search_value": "john.smith@example.com",
  "extracted_usernames": ["john.smith", "johnsmith", "john_smith"],
  "matches": {
    "john.smith": [
      {
        "platform": "twitter",
        "profile_url": "https://twitter.com/john.smith",
        "confidence_score": "high",
        "verified": true
      }
    ]
  }
}
```

### GET /api/results/username/{username}

Get detailed results for a specific username search.

**Response:**
```json
{
  "id": "uuid",
  "primary_username": "john_doe",
  "primary_email": "john@example.com",
  "confidence_score": 0.95,
  "last_verified": "2024-01-07T12:00:00",
  "verification_count": 5,
  "attributes": [
    {
      "type": "username",
      "value": "john_doe",
      "is_primary": true,
      "is_verified": true,
      "confidence": "high"
    }
  ],
  "sources": [
    {
      "platform": "twitter",
      "profile_url": "https://twitter.com/john_doe",
      "status": "found",
      "confidence": "high",
      "last_checked": "2024-01-07T12:00:00"
    }
  ]
}
```

### POST /api/search/fuzzy-match

Search with fuzzy matching for variations.

**Request:**
```json
{
  "username": "john_smith",
  "tolerance": 0.7,
  "max_variations": 50,
  "platforms": null
}
```

**Response:**
```json
{
  "original_username": "john_smith",
  "variations_checked": 45,
  "matches": {
    "john_smith": [...],
    "john.smith": [...],
    "johnsmith": [...]
  },
  "similarity_scores": {
    "john_smith": 1.0,
    "john.smith": 0.92,
    "johnsmith": 0.89
  }
}
```

### GET /api/results/identity-chain/{username}

Get connection chain showing relationships between identities.

**Response:**
```json
{
  "username": "john_doe",
  "total_connections": 12,
  "depth": 2,
  "connections": [
    {
      "type": "platform_profile",
      "platform": "twitter",
      "url": "https://twitter.com/john_doe",
      "confidence": "high",
      "depth": 0
    },
    {
      "type": "email_attribute",
      "value": "john@example.com",
      "is_primary": true,
      "is_verified": true,
      "discovered_from": "twitter",
      "depth": 1
    }
  ]
}
```

### GET /api/statistics/platforms

Get statistics about platform checks and success rates.

**Response:**
```json
{
  "twitter": {
    "total_checks": 1523,
    "found_count": 891,
    "success_rate": 58.5,
    "avg_response_time": 1.2,
    "blocked_count": 12
  }
}
```

## Matching Algorithms

### Exact Matching
Direct username match across platforms. Highest confidence.

**Example:** `john_doe` on Twitter matches `john_doe` on GitHub

### Fuzzy Matching
Similar usernames based on Levenshtein distance or fuzzywuzzy.

**Example:** `john_doe` might also match `john.doe`, `john-smith`, `j0hn_doe`

**Similarity Thresholds:**
- 90-100: High confidence (very similar or same)
- 70-89: Medium confidence (likely variations)
- <70: Low confidence (possible matches)

### Pattern Recognition

#### Email-based Enumeration
Extracts usernames from email addresses:
- `john.smith@gmail.com` → `john.smith`, `johnsmith`, `john_smith`
- `john.smith+work@gmail.com` → `john.smith`, `johnsmith`

#### Phone-based Enumeration
Extracts potential usernames from phone numbers:
- Last 4 digits: `4567`
- T9 word combinations: limited variations

#### Name-based Enumeration
Generates username patterns from names:
- `John Doe` → `johndoe`, `john.doe`, `john_doe`, `jdoe`, `j.doe`

### Common Username Variations

**Separator Variations:**
- `john_doe` ↔ `john.doe` ↔ `john-doe`

**Case Variations:**
- `john_doe` ↔ `JohnDoe` ↔ `jOhN_dOe`

**Leet Speak:**
- `john_doe` ↔ `j0hn_d0e` ↔ `j@hn_doe`

**Numeric Suffixes:**
- `john_doe` ↔ `john_doe123` ↔ `john_doe90`

**Common Additions:**
- `john_doe` ↔ `john_doe_official` ↔ `realjohn_doe`

## Confidence Scoring

### High Confidence (0.9-1.0)
- Exact username match
- Verified profile
- Multiple indicators (e.g., username + email match)

### Medium Confidence (0.5-0.89)
- Partial match (separator variations)
- Unverified profile
- Single indicator

### Low Confidence (0.1-0.49)
- Possible match based on fuzzy matching
- Incomplete data
- Low similarity score

## Configuration

### Platform Configuration

Platform definitions in `config/username_enum_sources.json`:

```json
{
  "twitter": {
    "name": "Twitter/X",
    "url_template": "https://twitter.com/{username}",
    "category": "social_media",
    "method": "status_code",
    "not_found_status": [404],
    "found_status": [200],
    "timeout": 5,
    "user_agent_required": true,
    "rate_limit_delay": 1
  }
}
```

### Detection Methods

1. **status_code**: Uses HTTP status codes
   - 200 = found
   - 404 = not found
   - 429 = rate limited

2. **html_content**: Parses HTML for patterns
   - Looks for found_patterns in response
   - Checks for not_found_patterns

3. **json_api**: Parses JSON API responses
   - Checks for found/not_found indicators

4. **redirect**: Analyzes redirect behavior
   - Checks final URL for not_found patterns

### Adding New Platforms

1. Add entry to `username_enum_sources.json`:
```json
{
  "new_platform": {
    "name": "New Platform",
    "url_template": "https://example.com/{username}",
    "category": "social_media",
    "method": "status_code",
    "not_found_status": [404],
    "found_status": [200],
    "timeout": 5,
    "user_agent_required": true,
    "rate_limit_delay": 1
  }
}
```

2. Restart the service to load new configuration

## Performance

### Concurrency
- Default: 50 simultaneous requests
- Maximum: 100 simultaneous requests
- Configurable via `max_concurrent` parameter

### Caching
- Enabled by default
- TTL: 24 hours (configurable)
- Reduces redundant platform checks
- Stores both search parameters and results

### Rate Limiting
- Per-platform rate limits
- Configurable delays between requests
- Prevents blocks and bans

### Connection Pooling
- Database: 20 base connections, 40 overflow
- HTTP: Reused connections via aiohttp
- Efficient resource usage

### Expected Performance
- Single username search: < 2 minutes (100 platforms)
- Cached search: < 100ms
- Fuzzy match: 2-3 minutes (50 variations)

## Database Schema

### PostgreSQL Tables

**identities**: Core identity records
- Primary identifiers (username, email, phone)
- Confidence scores
- Verification timestamps

**identity_attributes**: Discovered attributes
- Username/email/phone values
- Primary/verified flags
- Source information

**identity_sources**: Platform results
- Platform profile URLs
- Status and confidence
- Response times and codes
- Profile data (JSONB)

**identity_relationships**: Identity connections
- Relationship types (SAME_PERSON, LINKED_ACCOUNT)
- Confidence scores
- Evidence and verification

**search_cache**: Search result cache
- Search keys and parameters
- Cached results (JSONB)
- TTL and hit tracking

### Neo4j Graph

**Nodes:**
- Username: {username, platform, profile_url, confidence}
- Email: {email, confidence}
- Phone: {phone, confidence}
- Platform: {name}

**Edges:**
- FOUND_ON: Username → Platform
- VARIATION_OF: Username ↔ Username
- EMAIL_ASSOCIATED: Username → Email
- PHONE_ASSOCIATED: Username → Phone

## Logging & Monitoring

### Log Levels
- INFO: Normal operations, search completions
- WARNING: Timeouts, rate limits, blocks
- ERROR: Exceptions, failures

### Metrics Tracked
- Total searches
- Average search time
- Success rate per platform
- Cache hit rate
- Connection pool usage

### Alerts
- Platform blocks (> 10 blocks in 5 min)
- High error rates (> 20% failures)
- Slow searches (> 3 minutes)

## Usage Examples

### Python Client
```python
import httpx

async def search_username(username: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/search/username",
            json={"username": username, "fuzzy_match": True}
        )
        return response.json()

result = await search_username("john_doe")
print(f"Found {result['matches_found']} matches")
```

### cURL
```bash
curl -X POST "http://localhost:8000/api/search/username" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "fuzzy_match": true,
    "max_concurrent": 50
  }'
```

### Reverse Lookup
```bash
curl -X POST "http://localhost:8000/api/search/reverse-lookup" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john.smith@example.com"
  }'
```

## Testing

### Run Tests
```bash
# Run all tests
pytest backend/tests/

# Run specific test file
pytest backend/tests/test_username_enum.py

# Run with coverage
pytest backend/tests/ --cov=backend/modules --cov-report=html
```

### Test Coverage
- Platform check logic (status code, HTML, JSON)
- Fuzzy matching algorithms
- Database operations
- Graph operations
- API endpoints
- Concurrent request handling
- Timeout and retry logic

## Troubleshooting

### Common Issues

**High timeout rate:**
- Reduce `max_concurrent`
- Increase platform-specific timeouts
- Check network connectivity

**Platform blocks:**
- Increase `rate_limit_delay` in config
- Enable proxy rotation
- Reduce request frequency

**Slow searches:**
- Enable caching
- Reduce number of platforms searched
- Check database performance

**Cache not working:**
- Verify cache_ttl_hours setting
- Check database connection
- Clear cache manually via API

## Future Enhancements

- [ ] Selenium integration for JS-heavy sites
- [ ] Proxy rotation for heavy scraping
- [ ] WebSocket progress updates
- [ ] Export to CSV/JSON/GraphML
- [ ] Machine learning for confidence scoring
- [ ] Mobile app support
- [ ] Dark web platform integration
- [ ] Historical tracking and alerts
