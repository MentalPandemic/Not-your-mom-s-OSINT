# OSINT Intelligence Platform

A comprehensive open-source intelligence (OSINT) aggregation platform designed to discover and map relationships between disparate data points across the surface web.

## 🎯 Vision

This platform aims to be a powerful tool for OSINT practitioners, investigators, and researchers to efficiently collect, analyze, and visualize publicly available information from across the internet. By aggregating data from hundreds of sources and automatically discovering relationships between entities, it provides unprecedented insights into digital footprints and online identities.

## 🚀 Phase 1: Surface Web Intelligence

Phase 1 focuses on comprehensive surface web data collection from:

### Mainstream Platforms
- Social media platforms (Twitter, LinkedIn, Instagram, Facebook, TikTok, Reddit, etc.)
- GitHub repositories and commits
- Public data aggregators
- WHOIS/DNS records
- Username enumeration across hundreds of sites
- Email and people search services
- Google search indexing

### Adult/NSFW Platforms
- Pornography platforms (Pornhub, xHamster, Motherless, RedTube, etc.)
- Adult social platforms (Fetlife, OnlyFans, etc.)
- Adult forums and communities
- Adult content platforms

### Personals & Classified Sites
- Skipthegames.com
- Bedpage.com
- Craigslist (all sections including personals)
- Doublelist
- Other personals/classifieds platforms
- Contact information extraction (phone, email, location data)
- Cross-reference to other identities

## 📋 Features

- **Multi-Source Intelligence Collection**: Gather data from hundreds of surface web platforms simultaneously
- **Relationship Mapping**: Automatically discover and visualize connections between identities, profiles, and content
- **Graph Database**: Store and query complex relationship networks using Neo4j
- **Async Architecture**: High-performance concurrent data gathering using FastAPI and async/await patterns
- **Multiple Export Formats**: Export findings in JSON, CSV, or GraphML for further analysis
- **Confidence Scoring**: Automatic confidence scoring for discovered relationships and attributes
- **Real-time Updates**: Track search progress in real-time with status updates

## 🏗️ Architecture

### Backend
- **Framework**: FastAPI (Python 3.9+)
- **Database**: PostgreSQL (relational data) + Neo4j (graph relationships)
- **Async Support**: aiohttp, asyncio for concurrent operations
- **Data Collection**: Scrapers, API integrations, and username enumeration tools

### Frontend
- **Framework**: React 18
- **Routing**: React Router v6
- **API Client**: Axios
- **Visualization**: React Force Graph / D3.js (for relationship graphs)

### Infrastructure
- **Containerization**: Docker & Docker Compose
- **Databases**: PostgreSQL 15, Neo4j 5.14
- **Web Server**: Nginx (for frontend)

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- 4GB+ RAM recommended
- 10GB+ disk space

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd Not-your-mom-s-OSINT
```

2. Start all services with Docker Compose:
```bash
docker-compose up -d
```

3. Access the application:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/api/docs
- Neo4j Browser: http://localhost:7474

### Development Setup

For local development without Docker, see [DEVELOPMENT.md](docs/DEVELOPMENT.md)

## 📚 Documentation

- [Architecture Overview](docs/ARCHITECTURE.md) - System design and data flow
- [Phase 1 Roadmap](docs/PHASE1_ROADMAP.md) - Detailed list of all data sources
- [Development Guide](docs/DEVELOPMENT.md) - Setup and development instructions
- [API Documentation](http://localhost:8000/api/docs) - Interactive API documentation (when running)

## 🔒 Privacy & Legal Notice

This platform collects only **publicly available information**. All data is sourced from public websites, APIs, and databases that do not require authentication or bypass any security measures.

**Important:**
- Use this tool responsibly and ethically
- Respect applicable laws and regulations in your jurisdiction
- Obtain proper authorization before conducting investigations
- Be aware of data protection laws (GDPR, CCPA, etc.)
- This tool is for legitimate OSINT research and investigation purposes only

## 🛣️ Roadmap

### Phase 1 (Current): Surface Web Intelligence ✅
- Comprehensive surface web data collection
- Adult sites and personals/classified platforms integration
- Relationship graph visualization
- Basic export capabilities

### Phase 2 (Planned): Advanced Analysis
- Machine learning for entity resolution
- Automated report generation
- Advanced graph algorithms
- Timeline visualization

### Phase 3 (Planned): Deep Web Integration
- Onion services integration
- Encrypted messaging platforms
- Dark web marketplace monitoring
- Advanced anonymization support

## 🤝 Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📄 License

[Add your license here]

## ⚠️ Disclaimer

This tool is provided "as is" for legitimate OSINT research and investigation purposes. The developers are not responsible for any misuse or illegal activities conducted with this platform. Users are solely responsible for ensuring their use complies with applicable laws and regulations.

## 📧 Contact

[Add contact information]

---

**Version**: 1.0.0  
**Status**: Phase 1 - Active Development
