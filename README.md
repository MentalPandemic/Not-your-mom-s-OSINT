# Not-your-mom's-OSINT

**Comprehensive Open-Source Intelligence Aggregation Platform**

## Vision

Not-your-mom's-OSINT is a next-generation OSINT (Open Source Intelligence) platform designed to aggregate and analyze publicly available data from across the surface web. The platform specializes in highlighting relationships between disparate data points, providing investigators, researchers, and analysts with powerful tools to uncover connections and patterns.

## Phase 1: Surface-Web Coverage

### Adult/NSFW Platforms Integration ✅

The first major data source integration focuses on adult/NSFW platforms and personals/classified sites:

**Adult Platforms:**
- Pornhub, xHamster, Motherless, RedTube, Xvideos
- Fetlife, OnlyFans, and other adult social networks
- Adult forums and community platforms

**Personals/Classified Sites:**
- Skipthegames, Bedpage, Craigslist, Doublelist
- Additional classified and escort platforms

### Features Implemented

1. **Comprehensive Enumeration**: Search across multiple adult platforms simultaneously
2. **Advanced Scraping**: Extract profiles, posts, and contact information
3. **Data Correlation**: Link identities across platforms
4. **Confidence Scoring**: Probability-based matching algorithms
5. **Database Integration**: PostgreSQL + Neo4j graph storage
6. **API Endpoints**: RESTful interface for programmatic access
7. **Async Processing**: High-performance concurrent scraping
8. **Rate Limiting**: Respectful scraping practices

## Architecture

```
backend/
├── modules/              # Core scraping modules
│   ├── adult_sites.py     # Adult platform enumeration
│   └── personals_sites.py # Personals/classified scraping
├── routes/              # API endpoints
│   └── adult_personals.py # Adult/personals API
├── models/              # Database models
│   └── database.py       # PostgreSQL + Neo4j models
├── config/              # Configuration
│   └── adult_personals_sources.json
├── utils/               # Utilities
│   └── scraping_utils.py # Scraping helpers
└── main.py              # FastAPI application
```

## Getting Started

### Prerequisites

- Python 3.9+
- PostgreSQL 13+
- Neo4j 4.4+
- Redis (optional for caching)

### Installation

```bash
# Clone the repository
git clone https://github.com/your-repo/not-your-moms-osint.git
cd not-your-moms-osint

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your database credentials

# Initialize database
python -m backend.models.database

# Run the application
python main.py
```

### API Usage

**Search Adult Sites:**
```bash
POST /api/search/adult-sites
{
    "target": "username",
    "platforms": ["pornhub", "xhamster"]
}
```

**Search Personals Sites:**
```bash
POST /api/search/personals-sites
{
    "target": "phone_or_email",
    "sites": ["skipthegames", "bedpage"]
}
```

**Get Adult Profiles:**
```bash
GET /api/results/adult-profiles/{identity_id}
```

**Get Personals Posts:**
```bash
GET /api/results/personals-posts/{identity_id}
```

## Technical Stack

- **Backend**: FastAPI, Python 3.9+
- **Database**: PostgreSQL (relational), Neo4j (graph)
- **Scraping**: aiohttp, BeautifulSoup, Selenium
- **Async**: asyncio, aiohttp
- **Validation**: Pydantic, phonenumbers
- **Logging**: Loguru
- **Testing**: pytest

## Legal & Ethical Compliance

✅ **Public Data Only**: No private or authenticated content
✅ **Terms of Service**: Respect platform rules  
✅ **Robots.txt**: Honor scraping restrictions
✅ **Rate Limiting**: Prevent server overload
✅ **No Account Compromise**: No password cracking
✅ **Secure Storage**: Encrypted databases

## Roadmap

### Phase 1 (Current) - Surface-Web Coverage ✅
- [x] Adult/NSFW platform integration
- [x] Personals/classified site scraping
- [x] Core database architecture
- [x] API endpoints
- [x] Confidence scoring system

### Phase 2 - Mainstream Platforms
- [ ] Social media integration (Twitter, Facebook, Instagram)
- [ ] Professional networks (LinkedIn, Indeed)
- [ ] Forum and community sites
- [ ] Blogging platforms

### Phase 3 - Advanced Features
- [ ] Image recognition and correlation
- [ ] Natural language processing
- [ ] Network analysis and visualization
- [ ] Machine learning for pattern detection
- [ ] Real-time monitoring and alerts

### Phase 4 - Enterprise Features
- [ ] User management and permissions
- [ ] Report generation and export
- [ ] API rate limiting and authentication
- [ ] Dashboard and analytics
- [ ] Integration with other OSINT tools

## Contributing

We welcome contributions! Please see our contributing guidelines for details on how to:

- Report bugs
- Suggest features
- Submit pull requests
- Improve documentation

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contact

For questions, issues, or collaboration opportunities, please open an issue on GitHub.

## Disclaimer

This tool is designed for legitimate research and investigative purposes only. Users are responsible for ensuring their use complies with all applicable laws and regulations. The developers assume no liability for misuse of this software.