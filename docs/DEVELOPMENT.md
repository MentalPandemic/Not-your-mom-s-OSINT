# Development Guide

This guide covers local development setup, workflows, and best practices for the OSINT Intelligence Platform.

## Prerequisites

### Required Software
- **Python 3.9+** (3.11 recommended)
- **Node.js 16+** (18 recommended)
- **PostgreSQL 12+** (15 recommended)
- **Neo4j 4.4+** (5.14 recommended)
- **Docker & Docker Compose** (optional but recommended)
- **Git**

### Optional Tools
- **Redis** (for caching - future)
- **Playwright** (for browser automation)
- **Selenium** (alternative browser automation)

## Quick Start with Docker

The easiest way to get started is using Docker Compose:

```bash
# Clone the repository
git clone <repository-url>
cd Not-your-mom-s-OSINT

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down
```

Access the application:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/api/docs
- Neo4j Browser: http://localhost:7474 (username: neo4j, password: osint_neo4j_password)

## Local Development Setup

For development without Docker:

### Backend Setup

1. **Create Python virtual environment**:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Set up environment variables**:
```bash
cp .env.example .env
# Edit .env with your local database credentials
```

4. **Install and start PostgreSQL**:
```bash
# macOS with Homebrew
brew install postgresql@15
brew services start postgresql@15

# Create database
createdb osint_db
createuser osint_user
psql -c "ALTER USER osint_user WITH PASSWORD 'osint_password';"
psql -c "GRANT ALL PRIVILEGES ON DATABASE osint_db TO osint_user;"
```

5. **Install and start Neo4j**:
```bash
# macOS with Homebrew
brew install neo4j
neo4j start

# Or download from https://neo4j.com/download/
# Set initial password to: osint_neo4j_password
```

6. **Create logs directory**:
```bash
mkdir -p logs
```

7. **Initialize database**:
```bash
# Run the FastAPI app to auto-create tables
python -m app.main
```

8. **Run the backend**:
```bash
# Development mode with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup

1. **Install Node.js dependencies**:
```bash
cd frontend
npm install
```

2. **Set up environment variables**:
```bash
# Create .env file
echo "REACT_APP_API_URL=http://localhost:8000/api" > .env
```

3. **Run the frontend**:
```bash
npm start
```

The application will open at http://localhost:3000

## Project Structure

```
Not-your-mom-s-OSINT/
├── backend/
│   ├── app/
│   │   ├── core/              # Core configuration
│   │   ├── database/          # Database connections
│   │   ├── models/            # SQLAlchemy models
│   │   ├── schemas/           # Pydantic schemas
│   │   ├── routers/           # API endpoints
│   │   ├── services/          # Business logic (to be added)
│   │   └── main.py            # FastAPI application
│   ├── tests/                 # Backend tests
│   ├── requirements.txt       # Python dependencies
│   ├── Dockerfile            # Backend container
│   └── .env.example          # Environment template
│
├── frontend/
│   ├── public/               # Static files
│   ├── src/
│   │   ├── components/       # React components
│   │   ├── pages/           # Page components
│   │   ├── services/        # API client
│   │   ├── utils/           # Utility functions
│   │   ├── App.js           # Main app component
│   │   └── index.js         # Entry point
│   ├── package.json         # Node dependencies
│   ├── Dockerfile          # Frontend container
│   └── nginx.conf          # Nginx configuration
│
├── database/
│   ├── postgresql/
│   │   └── init.sql        # PostgreSQL initialization
│   └── neo4j/
│       └── init.cypher     # Neo4j initialization
│
├── docs/
│   ├── ARCHITECTURE.md     # Architecture documentation
│   ├── PHASE1_ROADMAP.md  # Phase 1 data sources
│   └── DEVELOPMENT.md     # This file
│
├── docker-compose.yml      # Docker orchestration
├── .gitignore             # Git ignore rules
└── README.md              # Project overview
```

## Development Workflow

### Adding a New Data Source

1. **Create a service module**:
```bash
touch backend/app/services/source_name.py
```

2. **Implement the collector**:
```python
# backend/app/services/source_name.py
import aiohttp
from loguru import logger

class SourceNameCollector:
    def __init__(self):
        self.base_url = "https://api.source.com"
    
    async def search(self, query: str) -> dict:
        """Search for query on SourceName"""
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(
                    f"{self.base_url}/search",
                    params={"q": query}
                ) as response:
                    data = await response.json()
                    return self.parse_results(data)
            except Exception as e:
                logger.error(f"SourceName error: {e}")
                return {}
    
    def parse_results(self, data: dict) -> dict:
        """Parse and normalize results"""
        # Transform data to standard format
        return {
            "identities": [...],
            "attributes": [...],
            "content": [...]
        }
```

3. **Register in search orchestrator** (when implemented)

4. **Add tests**:
```bash
touch backend/tests/test_source_name.py
```

### Database Migrations

Using Alembic for PostgreSQL migrations:

1. **Initialize Alembic** (already done):
```bash
cd backend
alembic init alembic
```

2. **Create a migration**:
```bash
alembic revision --autogenerate -m "Add new table"
```

3. **Apply migrations**:
```bash
alembic upgrade head
```

4. **Rollback**:
```bash
alembic downgrade -1
```

### Neo4j Graph Operations

Initialize constraints and indexes:

```python
from app.database.neo4j import Neo4jConnection

neo4j = Neo4jConnection()
await neo4j.create_indexes()
await neo4j.create_constraints()
```

## Testing

### Backend Tests

Run tests with pytest:

```bash
cd backend
pytest

# With coverage
pytest --cov=app --cov-report=html

# Run specific test
pytest tests/test_search.py

# Run with verbose output
pytest -v
```

### Frontend Tests

Run tests with React Testing Library:

```bash
cd frontend
npm test

# Coverage report
npm test -- --coverage

# Run in CI mode
CI=true npm test
```

### Manual Testing

1. **Test health endpoint**:
```bash
curl http://localhost:8000/health
```

2. **Test search**:
```bash
curl -X POST http://localhost:8000/api/search/ \
  -H "Content-Type: application/json" \
  -d '{"query": "test@example.com", "deep_search": false}'
```

3. **Interactive API docs**:
Visit http://localhost:8000/api/docs for Swagger UI

## Code Style

### Python (Backend)

We use:
- **Black** for formatting
- **Flake8** for linting
- **MyPy** for type checking

```bash
# Format code
black app/

# Lint
flake8 app/

# Type check
mypy app/
```

Configuration in `pyproject.toml` and `.flake8`

### JavaScript (Frontend)

We use:
- **ESLint** for linting
- **Prettier** for formatting

```bash
# Lint
npm run lint

# Format
npm run format
```

## Debugging

### Backend Debugging

1. **Add debug logging**:
```python
from loguru import logger
logger.debug("Debug message")
logger.info("Info message")
logger.warning("Warning message")
logger.error("Error message")
```

2. **Use debugger**:
```python
import pdb; pdb.set_trace()
# Or with iPython
import IPython; IPython.embed()
```

3. **Check logs**:
```bash
tail -f backend/logs/app.log
```

### Frontend Debugging

1. **React DevTools**: Install browser extension
2. **Console logging**: Use `console.log()` judiciously
3. **Network tab**: Monitor API requests
4. **Redux DevTools**: For state management (if using Redux)

## Environment Variables

### Backend (.env)

```bash
# Application
DEBUG=True

# PostgreSQL
POSTGRES_USER=osint_user
POSTGRES_PASSWORD=osint_password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=osint_db

# Neo4j
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=osint_neo4j_password

# Security
SECRET_KEY=your-secret-key-here

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60

# Scraping
MAX_CONCURRENT_REQUESTS=10
REQUEST_TIMEOUT=30
```

### Frontend (.env)

```bash
REACT_APP_API_URL=http://localhost:8000/api
```

## Common Issues

### Issue: PostgreSQL connection refused

**Solution**:
```bash
# Check if PostgreSQL is running
pg_isready

# Start PostgreSQL
brew services start postgresql@15  # macOS
sudo systemctl start postgresql    # Linux
```

### Issue: Neo4j authentication failed

**Solution**:
```bash
# Reset Neo4j password
neo4j-admin set-initial-password osint_neo4j_password
```

### Issue: Port already in use

**Solution**:
```bash
# Find and kill process using port 8000
lsof -ti:8000 | xargs kill -9

# Or use different port
uvicorn app.main:app --port 8001
```

### Issue: Frontend can't connect to backend

**Solution**:
1. Check backend is running: `curl http://localhost:8000/health`
2. Check CORS settings in `backend/app/core/config.py`
3. Verify `REACT_APP_API_URL` in frontend `.env`

## Performance Optimization

### Database Optimization

1. **Add indexes** for frequently queried fields
2. **Use connection pooling**
3. **Optimize queries** with EXPLAIN
4. **Use async queries** where possible

### Backend Optimization

1. **Use async/await** for I/O operations
2. **Implement caching** (Redis future enhancement)
3. **Rate limit** external API calls
4. **Use connection pooling** for HTTP requests

### Frontend Optimization

1. **Code splitting** with React.lazy()
2. **Memoization** with React.memo()
3. **Optimize re-renders**
4. **Lazy load** graph visualizations

## Git Workflow

### Branch Strategy

- `main`: Production-ready code
- `develop`: Integration branch
- `feature/*`: New features
- `bugfix/*`: Bug fixes
- `hotfix/*`: Critical fixes

### Commit Messages

Follow conventional commits:

```
feat: Add Twitter search integration
fix: Resolve PostgreSQL connection issue
docs: Update architecture documentation
test: Add tests for search endpoint
refactor: Simplify graph query logic
```

### Pull Request Process

1. Create feature branch from `develop`
2. Make changes and commit
3. Push to remote
4. Create pull request
5. Address review comments
6. Merge after approval

## Deployment

### Production Checklist

- [ ] Set strong `SECRET_KEY`
- [ ] Disable `DEBUG` mode
- [ ] Use production database credentials
- [ ] Enable HTTPS
- [ ] Set up monitoring
- [ ] Configure logging
- [ ] Set up backups
- [ ] Review security settings
- [ ] Test in staging environment

### Docker Production Build

```bash
# Build for production
docker-compose -f docker-compose.prod.yml build

# Deploy
docker-compose -f docker-compose.prod.yml up -d
```

## Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://react.dev/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Neo4j Documentation](https://neo4j.com/docs/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)

## Getting Help

- Check existing documentation
- Search issues on GitHub
- Review API documentation at `/api/docs`
- Check logs for error messages
- Join development discussions

---

**Happy coding! 🚀**
