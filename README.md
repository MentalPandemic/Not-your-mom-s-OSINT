# Not-your-mom's-OSINT

A comprehensive open-source intelligence aggregation platform aimed at highlighting relationships between disparate data points and showing connections between pieces of information.

## Installation

```bash
pip install -e .
```

For development:
```bash
pip install -e ".[dev]"
```

## Quick Start

On first run, the interactive setup wizard will guide you through initial configuration:

```bash
osint
```

Or explicitly run the setup wizard:

```bash
osint setup
```

## Configuration

### Setup Wizard

The setup wizard will prompt you for:

1. **Output Format** - Choose between JSON, CSV, or both
2. **Verbose Logging** - Enable detailed logging output
3. **Results Path** - Directory where results will be saved (default: ./results)
4. **Sherlock Integration** - Enable username enumeration across platforms
5. **Social Media API Keys** - Configure Twitter/X, Facebook, LinkedIn, and Instagram APIs
6. **Social Media Platform Configuration** - Detailed configuration for each platform
7. **Caching Configuration** - Enable and configure response caching
8. **Auto-Updates** - Enable automatic updates for OSINT sources
9. **Notification Email** - Optional email address for notifications
10. **Advanced Features** - Enable advanced correlation engine features

### Configuration File

Configuration is stored in JSON format at:
- `~/.osint_config.json` (default)
- `./osint_config.json` (if present in current directory)

Example configuration:
```json
{
  "output_format": "json",
  "verbose_logging": true,
  "results_path": "./results",
  "sherlock_enabled": true,
  "api_keys": {
    "twitter": "your_twitter_api_key",
    "facebook": "",
    "linkedin": "",
    "instagram": ""
  },
  "social_media": {
    "twitter": {
      "enabled": true,
      "bearer_token": "your_twitter_bearer_token",
      "api_version": "v2",
      "rate_limit": 450
    },
    "facebook": {
      "enabled": false,
      "access_token": "",
      "rate_limit": 200
    },
    "linkedin": {
      "enabled": false,
      "username": "",
      "password": "",
      "rate_limit": 100
    },
    "instagram": {
      "enabled": false,
      "username": "",
      "password": "",
      "session_id": "",
      "rate_limit": 200
    }
  },
  "caching": {
    "enabled": true,
    "backend": "file",
    "ttl": {
      "profile": 86400,
      "posts": 604800,
      "followers": 86400
    }
  },
  "auto_updates": true,
  "notification_email": "user@example.com",
  "advanced_features": false,
  "setup_complete": true
}
```

### Configuration Commands

View current configuration:
```bash
osint config --show
```

Re-run setup wizard:
```bash
osint setup
```

Reset configuration:
```bash
osint config --reset
```

Skip setup wizard on first run:
```bash
osint --skip-setup
```

## Username Enumeration (Sherlock)

Search for a username across 400+ sites supported by the Sherlock project:

```bash
# Basic search (uses enabled sources)
osint search --username john_doe

# Search multiple usernames
osint search --username john_doe,jane_smith

# Filter by category/tag (if supported by the Sherlock site database)
osint search --username john_doe --category social-media

# Search specific sites only
osint search --username john_doe --sites twitter,github,linkedin

# Export results
osint search --username john_doe --export json --output ./results/john_doe.json

# Open found profiles in browser
osint search --username john_doe --browser
```

## Social Media Profile Intelligence

### Get Profile Information

```bash
# Get Twitter profile
osint profile --username john_doe --platform twitter --details full

# Get all platform profiles
osint profile --username john_doe --platforms all

# Include sentiment analysis
osint profile --username john_doe --platform twitter --sentiment

# Calculate engagement metrics
osint profile --username john_doe --platform twitter --engagement

# Export to HTML report
osint profile --username john_doe --platform twitter --export html --output report.html
```

### Analyze Posts

```bash
# Get recent posts with sentiment analysis
osint posts --username john_doe --platform twitter --sentiment --limit 100

# Extract hashtags from posts
osint posts --username john_doe --platform twitter --hashtags

# Export posts to CSV
osint posts --username john_doe --platform twitter --export csv --output posts.csv
```

### Get Followers

```bash
# Get Twitter followers
osint followers --username john_doe --platform twitter --limit 1000

# Export followers to JSON
osint followers --username john_doe --platform twitter --export json --output followers.json
```

### Comprehensive Profile Analysis

```bash
# Full profile analysis with all metrics
osint analyze --username john_doe --platform twitter --limit 200

# Analyze across all platforms
osint analyze --username john_doe --platforms all

# Export analysis to HTML report
osint analyze --username john_doe --export html --output analysis.html
```

The analysis command provides:
- **Engagement Metrics**: Average engagement rate, total engagement, post frequency
- **Sentiment Analysis**: Positive/negative/neutral post breakdown
- **Activity Patterns**: Peak posting hours and days
- **Hashtag Usage**: Top hashtags and usage statistics
- **Influence Score**: Calculated influence ranking (Very Low to Very High)
- **Bot Detection**: Identifies potential bot accounts with confidence scores

### Compare Multiple Users

```bash
# Compare Twitter users
osint compare --usernames user1,user2,user3 --platform twitter

# Compare LinkedIn professionals
osint compare --usernames linkedin1,linkedin2 --platform linkedin
```

Comparison includes:
- Follower counts
- Post counts
- Engagement rates
- Most influential user
- User with most followers
```

## Development

Run tests:
```bash
pytest
```

## Features

- Interactive CLI setup wizard
- Flexible configuration management
- Secure API key storage (file permissions: 600)
- Email validation
- Automatic results directory creation
- Support for multiple output formats
- Username enumeration across 400+ platforms (via Sherlock)
- Correlation engine for identifying relationships
- Relationship graph visualization and export
- **Social Media API Integrations**:
  - Twitter/X (user profiles, tweets, followers, engagement)
  - Facebook (user profiles, posts, page info)
  - LinkedIn (professional profiles, connections, experience)
  - Instagram (user profiles, posts, followers, hashtags)
- **Profile Analysis**:
  - Sentiment analysis using TextBlob
  - Engagement metrics calculation
  - Activity pattern detection
  - Hashtag and mention analysis
  - Influence scoring
  - Bot detection heuristics
- **Multi-platform Profile Comparison**
- **Comprehensive Reporting** (JSON, CSV, HTML)
- **Intelligent Rate Limiting** with cooldown and burst protection
- **Response Caching** for improved performance

## License

See LICENSE file for details.
