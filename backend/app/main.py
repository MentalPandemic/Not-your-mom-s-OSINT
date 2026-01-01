from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger
import sys

from app.core.config import settings
from app.database.postgresql import engine as pg_engine
from app.database.neo4j import Neo4jConnection
from app.routers import search, results, graph, export

# Configure logger
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="INFO"
)
logger.add(
    "logs/app.log",
    rotation="500 MB",
    retention="10 days",
    level="DEBUG"
)

# Create FastAPI app
app = FastAPI(
    title="OSINT Intelligence Platform",
    description="Comprehensive OSINT data aggregation and relationship mapping platform",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(search.router, prefix="/api/search", tags=["Search"])
app.include_router(results.router, prefix="/api/results", tags=["Results"])
app.include_router(graph.router, prefix="/api/graph", tags=["Graph"])
app.include_router(export.router, prefix="/api/export", tags=["Export"])


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("Starting OSINT Intelligence Platform")
    
    # Test PostgreSQL connection
    try:
        from app.database.postgresql import Base
        Base.metadata.create_all(bind=pg_engine)
        logger.info("PostgreSQL connection established and tables created")
    except Exception as e:
        logger.error(f"Failed to connect to PostgreSQL: {e}")
    
    # Test Neo4j connection
    try:
        neo4j_conn = Neo4jConnection()
        await neo4j_conn.test_connection()
        logger.info("Neo4j connection established")
    except Exception as e:
        logger.error(f"Failed to connect to Neo4j: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down OSINT Intelligence Platform")
    
    # Close Neo4j connection
    try:
        neo4j_conn = Neo4jConnection()
        await neo4j_conn.close()
        logger.info("Neo4j connection closed")
    except Exception as e:
        logger.error(f"Error closing Neo4j connection: {e}")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "OSINT Intelligence Platform API",
        "version": "1.0.0",
        "status": "operational"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    health_status = {
        "status": "healthy",
        "services": {
            "api": "operational",
            "postgresql": "checking",
            "neo4j": "checking"
        }
    }
    
    # Check PostgreSQL
    try:
        from sqlalchemy import text
        with pg_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        health_status["services"]["postgresql"] = "operational"
    except Exception as e:
        health_status["services"]["postgresql"] = f"error: {str(e)}"
        health_status["status"] = "degraded"
    
    # Check Neo4j
    try:
        neo4j_conn = Neo4jConnection()
        await neo4j_conn.test_connection()
        health_status["services"]["neo4j"] = "operational"
    except Exception as e:
        health_status["services"]["neo4j"] = f"error: {str(e)}"
        health_status["status"] = "degraded"
    
    return health_status


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom HTTP exception handler"""
    logger.error(f"HTTP error: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "status_code": exc.status_code}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """General exception handler"""
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
