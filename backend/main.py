"""
Main FastAPI Application for Username Enumeration Service
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from .modules.database import DatabaseManager
from .modules.graph_db import GraphManager
from .routes import username_enum

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# Global dependencies
db_manager: Optional[DatabaseManager] = None
graph_manager: Optional[GraphManager] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting Username Enumeration Service")
    
    # Initialize database
    global db_manager, graph_manager
    
    # Initialize PostgreSQL database
    try:
        db_url = app.state.settings.database_url
        db_manager = DatabaseManager(db_url)
        await db_manager.initialize()
        logger.info("PostgreSQL database initialized")
    except Exception as e:
        logger.warning(f"Could not initialize PostgreSQL: {e}")
    
    # Initialize Neo4j graph database
    try:
        graph_manager = GraphManager(
            uri=app.state.settings.neo4j_uri,
            username=app.state.settings.neo4j_username,
            password=app.state.settings.neo4j_password,
        )
        await graph_manager.initialize()
        await graph_manager.create_constraints()
        logger.info("Neo4j graph database initialized")
    except Exception as e:
        logger.warning(f"Could not initialize Neo4j: {e}")
        graph_manager = None
    
    # Initialize route dependencies
    username_enum.initialize_dependencies(
        db=db_manager,
        graph=graph_manager,
        enum_config_path=app.state.settings.enum_config_path,
    )
    
    logger.info("Username Enumeration Service started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Username Enumeration Service")
    
    if db_manager:
        await db_manager.close()
    
    if graph_manager:
        await graph_manager.close()
    
    logger.info("Shutdown complete")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application"""
    
    # Import settings
    try:
        from .modules.config import Settings
        settings = Settings()
    except ImportError:
        from pydantic_settings import BaseSettings
        
        class Settings(BaseSettings):
            database_url: str = "postgresql+asyncpg://user:password@localhost/username_enum"
            neo4j_uri: str = "bolt://localhost:7687"
            neo4j_username: str = "neo4j"
            neo4j_password: str = "password"
            enum_config_path: Optional[str] = None
            debug: bool = False
            
            class Config:
                env_file = ".env"
        
        settings = Settings()
    
    app = FastAPI(
        title="Username Enumeration Service",
        description="Comprehensive username enumeration across 100+ platforms",
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
    )
    
    # Store settings in app state
    app.state.settings = settings
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Exception handlers
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": exc.detail,
                "status_code": exc.status_code,
            },
        )
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": "Validation error",
                "details": exc.errors(),
            },
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "Internal server error",
                "detail": str(exc) if settings.debug else "An error occurred",
            },
        )
    
    # Routes
    app.include_router(username_enum.router)
    
    # Health check endpoint
    @app.get("/health")
    async def health_check():
        """Health check endpoint"""
        return {
            "status": "healthy",
            "database": db_manager is not None,
            "graph": graph_manager is not None,
            "service": "username-enumeration",
        }
    
    @app.get("/")
    async def root():
        """Root endpoint"""
        return {
            "service": "Username Enumeration Service",
            "version": "1.0.0",
            "endpoints": {
                "search": "/api/search/username",
                "reverse_lookup": "/api/search/reverse-lookup",
                "fuzzy_match": "/api/search/fuzzy-match",
                "identity_chain": "/api/results/identity-chain/{username}",
                "stats": "/api/statistics/overview",
                "docs": "/docs",
            },
        }
    
    return app


# Create app instance
app = create_app()


if __name__ == "__main__":
    import uvicorn
    
    # Run the application
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
