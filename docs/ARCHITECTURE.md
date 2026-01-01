# Architecture Overview

## System Design

The OSINT Intelligence Platform follows a modern microservices architecture with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────────┐
│                         Frontend (React)                     │
│                                                               │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │  Search  │  │ Results  │  │  Graph   │  │  Export  │   │
│  │   Bar    │  │   View   │  │   Viz    │  │  Panel   │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
│                                                               │
│                      API Client (Axios)                      │
└───────────────────────┬─────────────────────────────────────┘
                        │ HTTP/REST
                        │
┌───────────────────────▼─────────────────────────────────────┐
│                     Backend (FastAPI)                        │
│                                                               │
│  ┌────────────────────────────────────────────────────────┐ │
│  │                     API Routers                         │ │
│  │  /search  │  /results  │  /graph  │  /export          │ │
│  └────────────────────────────────────────────────────────┘ │
│                            │                                  │
│  ┌────────────────────────▼────────────────────────────────┐│
│  │                  Service Layer                          ││
│  │  • Search Orchestrator                                  ││
│  │  • Data Collection Services                             ││
│  │  • Graph Builder                                        ││
│  │  • Export Generator                                     ││
│  └─────────────────────────────────────────────────────────┘│
│                            │                                  │
│  ┌────────────────────────▼────────────────────────────────┐│
│  │               Database Managers                         ││
│  │  • PostgreSQL Manager (SQLAlchemy)                      ││
│  │  • Neo4j Manager (neo4j driver)                         ││
│  └─────────────────────────────────────────────────────────┘│
└───────────────────────┬─────────────────────┬───────────────┘
                        │                     │
        ┌───────────────▼──────┐   ┌─────────▼──────────┐
        │   PostgreSQL         │   │      Neo4j         │
        │   (Relational Data)  │   │   (Graph Data)     │
        │                      │   │                    │
        │  • Identities        │   │  • Identity Nodes  │
        │  • Attributes        │   │  • Relationship    │
        │  • Content           │   │    Edges           │
        │  • Sources           │   │  • Properties      │
        │  • Relationships     │   │                    │
        └──────────────────────┘   └────────────────────┘
```

## Data Flow

### Search Flow

1. **User Initiates Search**
   - User enters identifier (email, username, phone, etc.)
   - Frontend sends POST request to `/api/search/`
   - Backend generates unique search_id

2. **Search Orchestration**
   - Search orchestrator analyzes query type
   - Determines relevant data sources based on:
     - Query type (email, username, phone, etc.)
     - User preferences (include adult sites, personals, etc.)
     - Deep search setting
   - Queues async tasks for each data source

3. **Parallel Data Collection**
   - Multiple async workers collect data simultaneously
   - Each worker handles a specific data source category:
     - Social media scrapers
     - Adult site scrapers
     - Personals/classified scrapers
     - Public database queries
     - API integrations
   - Rate limiting and error handling per source

4. **Data Storage**
   - Raw data stored in PostgreSQL:
     - Identities (people, usernames, emails, etc.)
     - Attributes (profile info, contact details, etc.)
     - Content (posts, profiles, ads, etc.)
     - Metadata (sources, confidence scores, timestamps)
   
   - Relationship graph built in Neo4j:
     - Nodes for each entity
     - Edges for relationships
     - Properties on nodes and edges

5. **Results Delivery**
   - User polls `/api/search/{search_id}/status` for progress
   - When complete, user fetches results from `/api/results/{search_id}`
   - Graph visualization fetched from `/api/graph/{search_id}`

### Data Enrichment Flow

```
Raw Data → Entity Resolution → Confidence Scoring → Graph Building → Results
```

1. **Entity Resolution**: Merge duplicate entities across sources
2. **Confidence Scoring**: Calculate confidence based on:
   - Number of sources confirming data
   - Source reliability ratings
   - Data freshness
   - Cross-validation between sources

3. **Graph Building**: Create relationships in Neo4j:
   - Direct connections (same email/phone used on multiple sites)
   - Inferred connections (usernames, naming patterns)
   - Content-based connections (mentions, links)

## Database Schema

### PostgreSQL Schema

#### Identities Table
Core table representing discovered entities.

```sql
CREATE TABLE identities (
    id SERIAL PRIMARY KEY,
    name VARCHAR(500) NOT NULL,
    type VARCHAR(50) NOT NULL,  -- person, organization, username, email, phone, domain
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP
);
```

#### Attributes Table
Stores all attributes discovered for identities.

```sql
CREATE TABLE attributes (
    id SERIAL PRIMARY KEY,
    identity_id INTEGER REFERENCES identities(id),
    attribute_type VARCHAR(100) NOT NULL,  -- email, phone, address, username, etc.
    value TEXT NOT NULL,
    source VARCHAR(500),
    confidence_score FLOAT DEFAULT 0.5,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP
);
```

#### Content Table
Stores content items (posts, profiles, ads, etc.)

```sql
CREATE TABLE content (
    id SERIAL PRIMARY KEY,
    identity_id INTEGER REFERENCES identities(id),
    source VARCHAR(500) NOT NULL,
    content_type VARCHAR(100) NOT NULL,  -- social_post, adult_profile, personals_ad, etc.
    text TEXT,
    media_urls TEXT,
    posted_date TIMESTAMP,
    scraped_date TIMESTAMP DEFAULT NOW(),
    url VARCHAR(1000),
    metadata TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### Relationships Table
Stores relationships between identities.

```sql
CREATE TABLE relationships (
    id SERIAL PRIMARY KEY,
    identity_1_id INTEGER REFERENCES identities(id),
    identity_2_id INTEGER REFERENCES identities(id),
    relationship_type VARCHAR(100) NOT NULL,
    strength FLOAT DEFAULT 0.5,
    evidence TEXT,
    source VARCHAR(500),
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### Sources Table
Tracks data sources and their reliability.

```sql
CREATE TABLE sources (
    id SERIAL PRIMARY KEY,
    source_name VARCHAR(255) UNIQUE NOT NULL,
    url VARCHAR(1000),
    source_type VARCHAR(100),
    last_scraped TIMESTAMP,
    reliability_rating FLOAT DEFAULT 0.5,
    is_active INTEGER DEFAULT 1,
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Neo4j Graph Schema

#### Node Types

- **Identity**: Main entity nodes
- **Email**: Email address nodes
- **Phone**: Phone number nodes
- **Username**: Username nodes (with platform context)
- **Domain**: Website/domain nodes
- **SocialMedia**: Social media profile nodes
- **Address**: Physical location nodes
- **AdultProfile**: Adult site profile nodes
- **PersonalsPost**: Personals/classified ad nodes

#### Relationship Types

- **LINKED_TO**: General connection
- **MENTIONED_IN**: Entity mentioned in content
- **REGISTERED_ON**: User registered on platform
- **CONNECTED_VIA**: Connection through intermediate entity
- **POSTED_ON**: Content posted on platform
- **ASSOCIATED_WITH**: General association
- **LOCATED_AT**: Geographic location
- **OWNS**: Ownership relationship
- **USES**: Usage relationship (email, phone, etc.)

#### Properties

All relationships include:
- `confidence`: Float (0.0-1.0)
- `source`: String (data source)
- `timestamp`: DateTime
- `evidence`: String (supporting information)

## API Contract

### Search Endpoints

**POST /api/search/**
```json
Request:
{
  "query": "example@email.com",
  "search_type": "email",
  "sources": ["social", "adult", "personals"],
  "deep_search": true,
  "include_adult_sites": true,
  "include_personals": true
}

Response:
{
  "search_id": "uuid",
  "query": "example@email.com",
  "status": "initiated",
  "message": "Search initiated successfully",
  "estimated_time": 30
}
```

**GET /api/search/{search_id}/status**
```json
Response:
{
  "search_id": "uuid",
  "status": "processing",
  "progress": 45,
  "sources_completed": 23,
  "sources_total": 51,
  "message": "Collecting data from personals sites..."
}
```

### Results Endpoints

**GET /api/results/{search_id}**
```json
Response:
{
  "search_id": "uuid",
  "identities": [...],
  "attributes": [...],
  "relationships": [...],
  "content": [...],
  "total_identities": 5,
  "total_attributes": 23,
  "total_relationships": 12,
  "total_content": 18
}
```

### Graph Endpoints

**GET /api/graph/{search_id}**
```json
Parameters:
  - depth: 2 (traversal depth)
  - max_nodes: 100

Response:
{
  "nodes": [
    {
      "id": "node-1",
      "label": "john.doe@example.com",
      "type": "email",
      "properties": {...}
    }
  ],
  "edges": [
    {
      "id": "edge-1",
      "source": "node-1",
      "target": "node-2",
      "type": "LINKED_TO",
      "properties": {"confidence": 0.85}
    }
  ],
  "total_nodes": 45,
  "total_edges": 67
}
```

### Export Endpoints

**POST /api/export/**
```json
Request:
{
  "search_id": "uuid",
  "format": "json",
  "include_content": true,
  "include_relationships": true
}

Response:
{
  "export_id": "uuid",
  "format": "json",
  "download_url": "/api/export/uuid/download",
  "created_at": "2024-01-01T12:00:00Z",
  "expires_at": "2024-01-02T12:00:00Z"
}
```

## Async Architecture

The backend uses FastAPI's async capabilities for high-performance concurrent operations:

### Async Search Orchestration
```python
async def orchestrate_search(query: str, options: dict):
    tasks = []
    
    # Create async tasks for each data source
    for source in selected_sources:
        task = asyncio.create_task(collect_from_source(source, query))
        tasks.append(task)
    
    # Wait for all tasks to complete
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Process and store results
    await process_results(results)
```

### Connection Pooling
- PostgreSQL: async connection pool via asyncpg
- Neo4j: async driver with connection pool
- HTTP requests: aiohttp session pool

### Rate Limiting
- Per-source rate limiting to avoid overwhelming targets
- Exponential backoff on errors
- Configurable concurrent request limits

## Security Considerations

1. **No Authentication Bypass**: Only collects publicly available data
2. **Rate Limiting**: Respects robots.txt and implements rate limiting
3. **Data Privacy**: No storage of authentication credentials
4. **Legal Compliance**: Designed for legitimate OSINT use cases
5. **Error Handling**: Graceful handling of blocked/unavailable sources

## Performance Optimization

1. **Caching**: Redis cache for frequently accessed data (future)
2. **Database Indexing**: Strategic indexes on frequently queried fields
3. **Async Operations**: Maximize concurrent data collection
4. **Connection Pooling**: Reuse database connections
5. **Query Optimization**: Efficient graph traversal queries

## Scalability

The architecture is designed to scale:

1. **Horizontal Scaling**: Multiple backend workers can process searches in parallel
2. **Database Scaling**: Both PostgreSQL and Neo4j support clustering
3. **Queue System**: Task queue for background processing (future: Celery/Redis)
4. **Microservices**: Can split into separate services (search, collection, analysis)

## Technology Stack Summary

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Frontend | React 18 | User interface |
| Backend | FastAPI | REST API server |
| Relational DB | PostgreSQL 15 | Structured data storage |
| Graph DB | Neo4j 5.14 | Relationship storage |
| Async Runtime | asyncio, aiohttp | Concurrent operations |
| Containerization | Docker Compose | Deployment |
| Web Server | Nginx | Frontend serving |
| ORM | SQLAlchemy | Database abstraction |
| Validation | Pydantic | Data validation |
| Logging | Loguru | Application logging |
