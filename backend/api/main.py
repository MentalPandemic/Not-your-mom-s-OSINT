"""
Main FastAPI Application

This is the main application file that sets up the FastAPI server,
database connections, and API routes for the domain intelligence module.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import uvicorn
from typing import Dict, Any

# Import database configuration
from database.config import initialize_databases, cleanup_databases, check_database_health
from api.routes.domain_intelligence import router as domain_intelligence_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management."""
    # Startup
    logger.info("Starting Domain Intelligence API...")
    try:
        await initialize_databases()
        logger.info("Database connections established")
        
        # Perform health check
        health_status = await check_database_health()
        if health_status['overall'] != 'healthy':
            logger.warning(f"Database health check failed: {health_status}")
        else:
            logger.info("All database connections are healthy")
            
    except Exception as e:
        logger.error(f"Failed to initialize application: {str(e)}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Domain Intelligence API...")
    try:
        await cleanup_databases()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Error during shutdown: {str(e)}")


# Create FastAPI application
app = FastAPI(
    title="Domain Intelligence API",
    description="""
    Comprehensive domain intelligence API for OSINT operations.
    
    ## Features
    
    * **WHOIS Lookup**: Domain and IP WHOIS information with privacy detection
    * **DNS Enumeration**: Complete DNS record analysis and security assessment  
    * **Subdomain Discovery**: Multi-method subdomain enumeration and analysis
    * **SSL Certificate Analysis**: Certificate details, chain analysis, and security scoring
    * **Infrastructure Mapping**: IP-to-domain mapping, service identification, and ASN analysis
    * **Related Domain Discovery**: Domain variations, typosquatting detection, and relationship mapping
    
    ## Usage Examples
    
    ### WHOIS Lookup
    ```bash
    curl -X POST "http://localhost:8000/api/search/whois" \\
         -H "Content-Type: application/json" \\
         -d '{"target": "example.com", "include_analysis": true}'
    ```
    
    ### DNS Enumeration  
    ```bash
    curl -X POST "http://localhost:8000/api/search/dns-records" \\
         -H "Content-Type: application/json" \\
         -d '{"domain": "example.com", "record_types": ["A", "MX", "TXT"]}'
    ```
    
    ### Subdomain Discovery
    ```bash
    curl -X POST "http://localhost:8000/api/search/subdomains" \\
         -H "Content-Type: application/json" \\
         -d '{"domain": "example.com", "include_cert_transparency": true}'
    ```
    """,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)

# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "type": "HTTPException",
                "detail": exc.detail,
                "status_code": exc.status_code
            }
        }
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    """Handle request validation errors."""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "error": {
                "type": "ValidationError",
                "detail": "Request validation failed",
                "errors": exc.errors()
            }
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": {
                "type": "InternalServerError",
                "detail": "An unexpected error occurred"
            }
        }
    )

# Include routers
app.include_router(domain_intelligence_router)

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "service": "Domain Intelligence API",
        "version": "1.0.0",
        "description": "Comprehensive domain intelligence for OSINT operations",
        "status": "running",
        "endpoints": {
            "documentation": "/docs",
            "redoc": "/redoc", 
            "health": "/health",
            "stats": "/api/search/stats",
            "whois": "/api/search/whois",
            "dns": "/api/search/dns-records",
            "subdomains": "/api/search/subdomains",
            "ssl": "/api/search/ssl-certificates",
            "reverse_ip": "/api/search/reverse-ip",
            "related_domains": "/api/search/related-domains",
            "infrastructure": "/api/search/infrastructure/{domain}",
            "domain_portfolio": "/api/search/domain-portfolio"
        },
        "features": [
            "WHOIS lookup with privacy detection",
            "DNS enumeration and security analysis",
            "Subdomain discovery via multiple methods",
            "SSL/TLS certificate analysis",
            "Infrastructure mapping and service detection",
            "Related domain and typosquatting discovery",
            "Domain portfolio analysis"
        ]
    }

# Health check endpoint
@app.get("/health")
async def health_check():
    """Comprehensive health check endpoint."""
    try:
        # Check database health
        db_health = await check_database_health()
        
        # Overall health status
        overall_healthy = db_health['overall'] == 'healthy'
        
        health_status = {
            "status": "healthy" if overall_healthy else "unhealthy",
            "timestamp": asyncio.get_event_loop().time(),
            "version": "1.0.0",
            "database": db_health,
            "services": {
                "api": "healthy",
                "database": db_health['overall']
            }
        }
        
        status_code = 200 if overall_healthy else 503
        return JSONResponse(status_code=status_code, content=health_status)
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": asyncio.get_event_loop().time()
            }
        )

# API information endpoint
@app.get("/api/info")
async def api_info():
    """Get API information and capabilities."""
    return {
        "name": "Domain Intelligence API",
        "version": "1.0.0",
        "description": "Comprehensive domain intelligence for OSINT operations",
        "supported_features": [
            "Domain and IP WHOIS lookup with privacy detection",
            "Complete DNS enumeration (A, AAAA, MX, TXT, CNAME, NS, SRV)",
            "DNS security analysis (SPF, DKIM, DMARC, DNSSEC)",
            "Multi-method subdomain discovery (brute force, CT logs)",
            "SSL/TLS certificate analysis and security scoring",
            "Infrastructure mapping and service identification",
            "Reverse IP lookup and ASN analysis",
            "Related domain and typosquatting discovery",
            "Domain portfolio analysis by registrant",
            "Certificate transparency log analysis"
        ],
        "api_endpoints": {
            "WHOIS": {
                "endpoint": "POST /api/search/whois",
                "description": "Domain or IP WHOIS lookup with analysis",
                "input": "target (domain or IP), include_analysis (boolean)",
                "output": "WHOIS data, registrant analysis, execution time"
            },
            "DNS": {
                "endpoint": "POST /api/search/dns-records", 
                "description": "DNS record enumeration and security analysis",
                "input": "domain, record_types (array), include_propagation (boolean)",
                "output": "DNS records, security analysis, propagation status"
            },
            "Subdomains": {
                "endpoint": "POST /api/search/subdomains",
                "description": "Subdomain discovery and analysis",
                "input": "domain, use_extended_wordlist (boolean), include_cert_transparency (boolean)",
                "output": "Subdomain list, analysis results, discovery summary"
            },
            "SSL": {
                "endpoint": "POST /api/search/ssl-certificates",
                "description": "SSL/TLS certificate analysis",
                "input": "target (domain or IP), include_chain (boolean), analyze_security (boolean)",
                "output": "Certificate details, security analysis, related domains"
            },
            "Reverse IP": {
                "endpoint": "POST /api/search/reverse-ip",
                "description": "Reverse IP lookup and service detection",
                "input": "ip_address, include_services (boolean)",
                "output": "Domains on IP, IP information, open services"
            },
            "Related Domains": {
                "endpoint": "POST /api/search/related-domains",
                "description": "Related domain discovery and typosquatting detection",
                "input": "target (domain/email/company), search_types (array)",
                "output": "Domain variations, related domains, risk assessment"
            },
            "Infrastructure": {
                "endpoint": "GET /api/search/infrastructure/{domain}",
                "description": "Complete infrastructure mapping",
                "input": "domain, include_port_scan (query param), include_services (query param)",
                "output": "IP addresses, services, CDN info, infrastructure summary"
            },
            "Domain Portfolio": {
                "endpoint": "POST /api/search/domain-portfolio",
                "description": "Find all domains for a person or company",
                "input": "identifier (email or company), identifier_type, include_analysis (boolean)",
                "output": "Domain list, WHOIS analysis, portfolio summary"
            }
        },
        "rate_limits": {
            "requests_per_minute": 60,
            "concurrent_requests": 10,
            "timeout_default": 30
        },
        "external_apis": [
            "WHOISXML API",
            "SecurityTrails API", 
            "Censys API",
            "Shodan API",
            "Certificate Transparency Logs",
            "MaxMind GeoIP API"
        ]
    }


# Error handling for specific scenarios
@app.exception_handler(404)
async def not_found_handler(request, exc):
    """Handle 404 errors with helpful information."""
    return JSONResponse(
        status_code=404,
        content={
            "success": False,
            "error": {
                "type": "NotFound",
                "detail": "The requested endpoint was not found",
                "available_endpoints": [
                    "GET /",
                    "GET /health",
                    "GET /api/info",
                    "POST /api/search/whois",
                    "POST /api/search/dns-records",
                    "POST /api/search/subdomains",
                    "POST /api/search/ssl-certificates",
                    "POST /api/search/reverse-ip",
                    "POST /api/search/related-domains",
                    "GET /api/search/infrastructure/{domain}",
                    "POST /api/search/domain-portfolio"
                ],
                "documentation": "/docs"
            }
        }
    )


# Development server configuration
if __name__ == "__main__":
    # Development configuration
    config = {
        "app": "api.main:app",
        "host": "0.0.0.0",
        "port": 8000,
        "reload": True,
        "log_level": "info",
        "access_log": True,
        "workers": 1
    }
    
    logger.info("Starting Domain Intelligence API in development mode")
    logger.info(f"Configuration: {config}")
    
    uvicorn.run(**config)