import os
import sys
import logging
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from .routes.username_enum import router as username_enum_router
from .routes.search import router as search_router
from .routes.results import router as results_router
from .services.username_enum_service import UsernameEnumerationService
from .utils.cache import CacheManager
from .utils.rate_limiter import get_rate_limiter
from .utils.database import DatabaseManager


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('/var/log/username_enum_api.log') if not os.getenv('TESTING') else logging.NullHandler()
    ]
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting Username Enumeration API...")
    
    try:
        # Initialize configuration
        app.state.config = get_app_config()
        
        # Initialize services
        app.state.username_service = UsernameEnumerationService(app.state.config)
        logger.info("Username enumeration service initialized")
        
        # Initialize cache manager
        app.state.cache_manager = CacheManager(app.state.config.get('cache', {}))
        await app.state.cache_manager.initialize()
        logger.info("Cache manager initialized")
        
        # Initialize rate limiter
        app.state.rate_limiter = get_rate_limiter()
        await app.state.rate_limiter.initialize()
        logger.info("Rate limiter initialized")
        
        # Initialize database manager
        app.state.db_manager = DatabaseManager(app.state.config.get('database', {}))
        await app.state.db_manager.initialize()
        logger.info("Database manager initialized")
        
        logger.info("Username Enumeration API started successfully")
        
    except Exception as e:
        logger.error(f"Failed to start API: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Username Enumeration API...")
    
    try:
        if hasattr(app.state, 'cache_manager'):
            await app.state.cache_manager.close()
        
        if hasattr(app.state, 'rate_limiter'):
            await app.state.rate_limiter.close()
        
        if hasattr(app.state, 'db_manager'):
            await app.state.db_manager.close()
        
        logger.info("Username Enumeration API shutdown complete")
        
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


def get_app_config() -> Dict[str, Any]:
    """Get application configuration from environment and defaults"""
    config = {
        'service': {
            'min_confidence': float(os.getenv('MIN_CONFIDENCE', '0.3')),
            'max_results': int(os.getenv('MAX_RESULTS', '100'))
        },
        'cache': {
            'enabled': os.getenv('CACHE_ENABLED', 'true').lower() == 'true',
            'use_redis': os.getenv('USE_REDIS', 'false').lower() == 'true',
            'default_ttl': int(os.getenv('CACHE_TTL', '3600')),
            'redis_host': os.getenv('REDIS_HOST', 'localhost'),
            'redis_port': int(os.getenv('REDIS_PORT', '6379')),
            'redis_db': int(os.getenv('REDIS_DB', '0')),
            'redis_password': os.getenv('REDIS_PASSWORD'),
            'key_prefix': os.getenv('CACHE_KEY_PREFIX', 'username_enum:')
        },
        'rate_limiting': {
            'default': {
                'requests_per_minute': int(os.getenv('RATE_LIMIT_MINUTE', '10')),
                'requests_per_hour': int(os.getenv('RATE_LIMIT_HOUR', '100')),
                'burst_size': int(os.getenv('RATE_LIMIT_BURST', '5')),
                'block_duration': int(os.getenv('RATE_LIMIT_BLOCK_DURATION', '300'))
            },
            'search': {
                'requests_per_minute': int(os.getenv('SEARCH_RATE_LIMIT_MINUTE', '5')),
                'requests_per_hour': int(os.getenv('SEARCH_RATE_LIMIT_HOUR', '50')),
                'burst_size': int(os.getenv('SEARCH_RATE_LIMIT_BURST', '3')),
                'block_duration': int(os.getenv('SEARCH_RATE_LIMIT_BLOCK_DURATION', '300'))
            }
        },
        'database': {
            'postgresql': {
                'enabled': os.getenv('POSTGRES_ENABLED', 'true').lower() == 'true',
                'host': os.getenv('POSTGRES_HOST', 'localhost'),
                'port': int(os.getenv('POSTGRES_PORT', '5432')),
                'user': os.getenv('POSTGRES_USER', 'postgres'),
                'password': os.getenv('POSTGRES_PASSWORD', 'password'),
                'database': os.getenv('POSTGRES_DB', 'osint_db'),
                'min_connections': int(os.getenv('POSTGRES_MIN_CONNECTIONS', '2')),
                'max_connections': int(os.getenv('POSTGRES_MAX_CONNECTIONS', '10'))
            },
            'neo4j': {
                'enabled': os.getenv('NEO4J_ENABLED', 'true').lower() == 'true',
                'uri': os.getenv('NEO4J_URI', 'bolt://localhost:7687'),
                'user': os.getenv('NEO4J_USER', 'neo4j'),
                'password': os.getenv('NEO4J_PASSWORD', 'password')
            }
        },
        'logging': {
            'level': os.getenv('LOG_LEVEL', 'INFO'),
            'file': os.getenv('LOG_FILE', '/var/log/username_enum_api.log'),
            'format': os.getenv('LOG_FORMAT', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        },
        'server': {
            'host': os.getenv('API_HOST', '0.0.0.0'),
            'port': int(os.getenv('API_PORT', '8000')),
            'workers': int(os.getenv('WORKERS', '1')),
            'reload': os.getenv('DEBUG', 'false').lower() == 'true'
        }
    }
    
    return config


def create_app() -> FastAPI:
    """Create FastAPI application instance"""
    
    app = FastAPI(
        title="Username Enumeration API",
        description="API for username enumeration and identity relationship mapping",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Gzip compression
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    
    # Include routers
    app.include_router(username_enum_router)
    app.include_router(search_router)
    app.include_router(results_router)
    
    # Root endpoint
    @app.get("/")
    async def root():
        return {
            "message": "Username Enumeration API",
            "version": "1.0.0",
            "endpoints": {
                "username_search": "/api/search/username",
                "reverse_lookup": "/api/search/reverse-lookup",
                "fuzzy_match": "/api/search/fuzzy-match",
                "username_results": "/api/results/username/{username}",
                "identity_chain": "/api/results/identity-chain/{username}",
                "export_username": "/api/export/username",
                "export_identity_chain": "/api/export/identity-chain",
                "websocket_progress": "/api/ws/search/{search_id}",
                "search_stats": "/api/search/stats",
                "health_check": "/health",
                "docs": "/docs"
            }
        }
    
    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn
    
    config = get_app_config()
    server_config = config['server']
    
    uvicorn.run(
        "backend.main:app",
        host=server_config['host'],
        port=server_config['port'],
        workers=server_config['workers'],
        log_level=config['logging']['level'].lower(),
        reload=server_config['reload']
    )