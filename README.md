# Not-your-mom-s-OSINT

A comprehensive open-source intelligence (OSINT) aggregation platform designed to highlight relationships between disparate data points across the surface web.

## Vision

This platform provides identity discovery and correlation capabilities by enumerating usernames, emails, and other identifiers across hundreds of mainstream platforms. It builds comprehensive identity graphs showing how different personas and accounts are connected.

## Features

### Phase 1: Core Identity Discovery ✅
- **Username Enumeration Engine**: Search across 100+ platforms concurrently
- **Fuzzy Matching**: Find variations and similar usernames automatically
- **Reverse Lookup**: Search by email or phone to find associated usernames
- **Identity Graphs**: Neo4j-powered visualization of identity networks
- **Confidence Scoring**: High/Medium/Low confidence for all matches
- **Async Processing**: 50+ concurrent platform checks with rate limiting

### Upcoming Features

**Phase 2: Social Media Integration**
- Direct API integration with major platforms
- Real-time profile data extraction
- Follower/following network analysis
- Post and content correlation

**Phase 3: Advanced Correlation**
- Email/people search integration
- WHOIS/DNS enumeration
- GitHub intelligence gathering
- Cross-platform timeline analysis

## Quick Start

### Prerequisites

- Python 3.9+
- PostgreSQL 13+
- Neo4j 4.0+ (optional, for graph features)
- Redis (optional, for advanced caching)

### Installation

```bash
# Clone the repository
git clone https://github.com/your-org/not-your-moms-osint.git
cd not-your-moms-osint

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your database credentials

# Run database migrations
alembic upgrade head

# Start the service
python -m backend.main
```

### API Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Health check: http://localhost:8000/health

## Usage Examples

### Basic Username Search

```bash
curl -X POST "http://localhost:8000/api/search/username" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "fuzzy_match": true
  }'
```

### Reverse Email Lookup

```bash
curl -X POST "http://localhost:8000/api/search/reverse-lookup" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john.smith@example.com"
  }'
```

### Get Identity Chain

```bash
curl "http://localhost:8000/api/results/identity-chain/john_doe"
```

## Architecture

```
┌─────────────┐
│   API Layer │  FastAPI Routes
└──────┬──────┘
       │
┌──────▼──────────────────────┐
│  Business Logic Layer        │
│  - Username Enumerator       │
│  - Username Matcher          │
│  - Cross-reference Engine    │
└──────┬──────────────────────┘
       │
┌──────▼──────────────────────┐
│  Data Access Layer           │
│  - PostgreSQL (relational)  │
│  - Neo4j (graph)            │
│  - Redis (cache)             │
└───────────────────────────────┘
```

## Documentation

- [Username Enumeration Module](backend/docs/USERNAME_ENUMERATION.md)
- [API Reference](backend/docs/API_REFERENCE.md) - Coming Soon
- [Architecture Guide](backend/docs/ARCHITECTURE.md) - Coming Soon
- [Contributing Guide](CONTRIBUTING.md) - Coming Soon

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=backend/modules --cov-report=html

# Run specific test module
pytest backend/tests/test_username_enum.py
```

## Performance

- **Concurrent Requests**: 50+ simultaneous platform checks
- **Search Time**: < 2 minutes for 100+ platforms
- **Cache Hit**: < 100ms for cached searches
- **Rate Limiting**: Configurable per-platform delays

## Supported Platforms (100+)

See [USERNAME_ENUMERATION.md](backend/docs/USERNAME_ENUMERATION.md) for the complete list including:

- **Social Media**: Twitter, Reddit, Instagram, TikTok, YouTube, Facebook, LinkedIn, Discord, Mastodon, Bluesky
- **Code/Tech**: GitHub, GitLab, Bitbucket, Stack Overflow, Dev.to, CodePen
- **Gaming**: Steam, Epic Games, PlayStation Network, Xbox Live, Nintendo, Roblox, Minecraft
- **Professional**: LinkedIn, Crunchbase, Behance, Dribbble, ArtStation
- **Dating**: OkCupid, Tinder, Bumble, Hinge, Match, eHarmony
- **And 80+ more platforms**

## Roadmap

### Phase 1: Core Identity Discovery ✅ COMPLETE
- [x] Username enumeration engine (100+ platforms)
- [x] Fuzzy matching and pattern recognition
- [x] Reverse lookup (email/phone)
- [x] Database integration (PostgreSQL + Neo4j)
- [x] REST API with FastAPI
- [x] Caching and rate limiting
- [x] Comprehensive testing

### Phase 2: Social Media Integration 🚧 IN PROGRESS
- [ ] Platform-specific API integrations
- [ ] Profile data extraction
- [ ] Content analysis
- [ ] Network graph analysis
- [ ] Temporal analysis

### Phase 3: Advanced Correlation 📋 PLANNED
- [ ] Email/people search engines
- [ ] WHOIS/DNS enumeration
- [ ] GitHub intelligence
- [ ] Deep web integration
- [ ] Machine learning correlation

### Phase 4: Visualization & Reporting 📋 PLANNED
- [ ] Interactive web dashboard
- [ ] Graph visualization
- [ ] PDF/CSV export
- [ ] Scheduled reports
- [ ] Alert system

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## Legal & Ethical Use

This tool is designed for OSINT researchers, security professionals, and legitimate investigators. Users are responsible for ensuring their use complies with:

- Applicable laws and regulations
- Platform terms of service
- Privacy and data protection laws

**Disclaimer**: This tool is for educational and research purposes only. The authors are not responsible for misuse.

## License

[License to be determined]

## Acknowledgments

- Inspired by the Sherlock project
- Built with FastAPI, SQLAlchemy, and Neo4j
- Platform detection patterns adapted from various OSINT tools

## Contact

- Issues: https://github.com/your-org/not-your-moms-osint/issues
- Discussions: https://github.com/your-org/not-your-moms-osint/discussions

---

**Note**: This is a placeholder repository for the OSINT platform vision. Full implementation is in progress.
