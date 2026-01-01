import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
import os
from dotenv import load_dotenv

from backend.routes.adult_personals import router as adult_personals_router
from backend.models.database import init_async_db

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="Not-your-mom's-OSINT API",
    description="Comprehensive OSINT aggregation platform with adult/personals site integration",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(adult_personals_router)

@app.on_event("startup")
async def startup_event():
    """Startup event handler"""
    logger.info("Starting Not-your-mom's-OSINT API")
    
    # Initialize database
    try:
        await init_async_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event handler"""
    logger.info("Shutting down Not-your-mom's-OSINT API")

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Not-your-mom's-OSINT API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "docs": "/docs",
            "health": "/api/health",
            "stats": "/api/stats"
        }
    }

if __name__ == "__main__":
    # Run the application
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    
    logger.info(f"Starting server on {host}:{port}")
    uvicorn.run(
        "backend.main:app",
        host=host,
        port=port,
        reload=True,
        log_level="info",
        workers=4
    )