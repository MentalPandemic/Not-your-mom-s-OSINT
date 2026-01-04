"""
Domain Intelligence Module - Main Application.

FastAPI application for domain intelligence operations.
"""

import logging
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes.domain_intelligence import router as domain_intel_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class AppConfig:
    """Application configuration."""
    
    # API Keys
    securitytrails_api_key: Optional[str] = None
    censys_api_id: Optional[str] = None
    censys_api_secret: Optional[str] = None
    shodan_api_key: Optional[str] = None
    
    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/domain_intel"
    
    # GeoIP
    geoip_db_path: Optional[str] = None
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    
    # Rate Limiting
    rate_limit_enabled: bool = True
    rate_limit_requests: int = 100
    rate_limit_window: int = 60


# Global config instance
config = AppConfig()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    logger.info("Starting Domain Intelligence API")
    
    # Initialize database if configured
    if config.database_url:
        try:
            from database.connection import Database
            db = Database(config.database_url)
            await db.create_tables()
            logger.info("Database tables created")
        except Exception as e:
            logger.warning(f"Database initialization failed: {e}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Domain Intelligence API")


# Create FastAPI app
app = FastAPI(
    title="Domain Intelligence API",
    description="""
    Comprehensive domain intelligence API for OSINT gathering.
    
    ## Features
    
    - **WHOIS Lookup**: Domain and IP WHOIS information
    - **DNS Enumeration**: All DNS record types with history
    - **Subdomain Discovery**: CT logs, brute force, and enumeration
    - **SSL Analysis**: Certificate details and chain analysis
    - **Infrastructure Mapping**: IP-to-domain, ASN, and geolocation
    - **Related Domains**: Same registrant, infrastructure, and certificates
    
    ## Rate Limiting
    
    API requests are rate limited to prevent abuse.
    """,
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include routers
app.include_router(domain_intel_router)


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "domain-intelligence",
        "version": "1.0.0",
    }


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "Domain Intelligence API",
        "version": "1.0.0",
        "docs": "/docs",
    }


def get_database():
    """Get database instance."""
    if not config.database_url:
        return None
    
    from database.connection import Database
    return Database(config.database_url)


def set_api_key(service: str, key: str):
    """Set API key for a service."""
    if service == "securitytrails":
        config.securitytrails_api_key = key
    elif service == "censys":
        config.censys_api_id = key.split(":")[0] if ":" in key else key
        config.censys_api_secret = key.split(":")[1] if ":" in key else None
    elif service == "shodan":
        config.shodan_api_key = key


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app:app",
        host=config.host,
        port=config.port,
        reload=config.debug,
    )
