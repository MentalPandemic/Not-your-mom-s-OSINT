# Quick Start Guide

Get the OSINT Intelligence Platform running in 5 minutes!

## Prerequisites

- Docker Desktop installed and running
- 4GB+ RAM available
- 10GB+ disk space

## Option 1: Docker (Recommended)

### Start Everything

```bash
# Navigate to project directory
cd Not-your-mom-s-OSINT

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Check status
docker-compose ps
```

### Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/api/docs (Interactive Swagger UI)
- **Neo4j Browser**: http://localhost:7474
  - Username: `neo4j`
  - Password: `osint_neo4j_password`

### Stop Everything

```bash
docker-compose down

# To also remove volumes (clear all data)
docker-compose down -v
```

## Option 2: Local Development

### Backend Setup

```bash
# Install PostgreSQL 12+
# Install Neo4j 4.4+
# Install Python 3.9+

# Navigate to backend
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env

# Edit .env with your database credentials
nano .env

# Run the backend
uvicorn app.main:app --reload --port 8000
```

Backend will be available at: http://localhost:8000

### Frontend Setup

```bash
# Install Node.js 16+

# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Set API URL
echo "REACT_APP_API_URL=http://localhost:8000/api" > .env

# Run the frontend
npm start
```

Frontend will open automatically at: http://localhost:3000

## Verify Installation

### 1. Check Backend Health

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "services": {
    "api": "operational",
    "postgresql": "operational",
    "neo4j": "operational"
  }
}
```

### 2. Test Search Endpoint

```bash
curl -X POST http://localhost:8000/api/search/ \
  -H "Content-Type: application/json" \
  -d '{
    "query": "test@example.com",
    "deep_search": false,
    "include_adult_sites": true,
    "include_personals": true
  }'
```

### 3. Access API Documentation

Open http://localhost:8000/api/docs in your browser to see the interactive API documentation.

### 4. Use the Frontend

1. Open http://localhost:3000
2. Click "Start Investigation"
3. Enter a search query (email, username, phone, etc.)
4. Configure search options
5. Click "Search"

## Project Structure

```
Not-your-mom-s-OSINT/
├── backend/           # FastAPI backend
│   ├── app/          # Application code
│   └── tests/        # Backend tests
├── frontend/         # React frontend
│   ├── src/         # Source code
│   └── public/      # Static files
├── database/        # Database initialization scripts
├── docs/           # Documentation
└── docker-compose.yml  # Docker orchestration
```

## Key Files

- **README.md** - Project overview
- **ARCHITECTURE.md** - System design details
- **PHASE1_ROADMAP.md** - All Phase 1 data sources
- **DEVELOPMENT.md** - Detailed development guide
- **PROJECT_STATUS.md** - Current status and completed features
- **VERIFICATION.md** - Verification checks

## Running Tests

### Backend Tests

```bash
cd backend
source venv/bin/activate
pytest
```

### Frontend Tests

```bash
cd frontend
npm test
```

## Common Commands

### Docker

```bash
# Restart a service
docker-compose restart backend

# View logs for a specific service
docker-compose logs -f backend

# Execute commands in a container
docker-compose exec backend bash
docker-compose exec postgresql psql -U osint_user -d osint_db

# Rebuild images
docker-compose build

# Remove all containers and volumes
docker-compose down -v
```

### Database

```bash
# Access PostgreSQL
docker-compose exec postgresql psql -U osint_user -d osint_db

# Access Neo4j Cypher Shell
docker-compose exec neo4j cypher-shell -u neo4j -p osint_neo4j_password
```

## Troubleshooting

### Port Already in Use

If you get "port already in use" errors:

```bash
# Check what's using the port
lsof -i :8000  # or :3000, :5432, etc.

# Kill the process
kill -9 <PID>

# Or change the port in docker-compose.yml
```

### Database Connection Failed

```bash
# Check if databases are running
docker-compose ps

# Restart databases
docker-compose restart postgresql neo4j

# View logs
docker-compose logs postgresql
docker-compose logs neo4j
```

### Frontend Can't Connect to Backend

1. Check backend is running: `curl http://localhost:8000/health`
2. Check CORS settings in `backend/app/core/config.py`
3. Verify `REACT_APP_API_URL` in frontend `.env`
4. Clear browser cache and reload

## Next Steps

Now that the platform is running:

1. **Explore the API**: Visit http://localhost:8000/api/docs
2. **Read the Documentation**: Check `docs/` directory
3. **Review the Roadmap**: See `docs/PHASE1_ROADMAP.md` for data sources
4. **Start Development**: See `docs/DEVELOPMENT.md` for development workflow

## Need Help?

- Check `DEVELOPMENT.md` for detailed development instructions
- Review `ARCHITECTURE.md` for system design
- See `PHASE1_ROADMAP.md` for data source integration plans
- Check `PROJECT_STATUS.md` for current implementation status

## Important Notes

⚠️ **Current Status**: This is the Phase 1 foundation. Data source integrations are next.

⚠️ **Test Data**: The platform returns placeholder data until data sources are integrated.

⚠️ **Development Mode**: Docker Compose is configured for development with hot-reloading.

⚠️ **Production**: For production deployment, see `DEVELOPMENT.md` deployment section.

---

**Happy investigating! 🔍**
