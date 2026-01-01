import time
from typing import List, Optional, Dict, Any
from datetime import datetime
import asyncio

from fastapi import APIRouter, HTTPException, Query, Request, Response, Depends, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from pydantic import BaseModel, validator
import logging

from ..models.schemas import (
    UsernameSearchRequest, ReverseLookupRequest, FuzzyMatchRequest,
    SearchResponse, ReverseLookupResponse, IdentityChainResponse,
    FuzzyMatchResponse, ErrorResponse, PlatformResult
)
from ..services.username_enum_service import UsernameEnumerationService
from ..utils.rate_limiter import get_rate_limiter
from ..utils.cache import CacheManager
from ..utils.database import DatabaseManager
from ..utils.export import get_exporter, ExportFormat
from ..utils.websocket import handle_websocket_connection, ProgressTracker


logger = logging.getLogger(__name__)
router = APIRouter()


class RateLimitError(HTTPException):
    """Custom exception for rate limit errors"""
    
    def __init__(self, limit_info: Dict[str, Any]):
        super().__init__(
            status_code=429,
            detail={
                "error": "Rate limit exceeded",
                "message": "Too many requests. Please try again later.",
                "retry_after": limit_info.get('Retry-After', '60'),
                "rate_limit_info": {
                    "minute_limit": limit_info.get('X-RateLimit-Limit-Minute'),
                    "minute_remaining": limit_info.get('X-RateLimit-Remaining-Minute'),
                    "hour_limit": limit_info.get('X-RateLimit-Limit-Hour'),
                    "hour_remaining": limit_info.get('X-RateLimit-Remaining-Hour')
                }
            }
        )


def get_username_service(request: Request) -> UsernameEnumerationService:
    """Dependency to get username enumeration service"""
    return request.app.state.username_service


def get_cache_manager(request: Request) -> CacheManager:
    """Dependency to get cache manager"""
    return request.app.state.cache_manager


def get_db_manager(request: Request) -> DatabaseManager:
    """Dependency to get database manager"""
    return request.app.state.db_manager


def get_rate_limiter_instance(request: Request):
    """Dependency to get rate limiter"""
    return request.app.state.rate_limiter


async def check_rate_limit(
    request: Request,
    endpoint: str,
    rate_limiter=Depends(get_rate_limiter_instance)
) -> bool:
    """Check rate limit for request"""
    is_allowed, limit_info = await rate_limiter.check_rate_limit(request, endpoint)
    
    if not is_allowed:
        raise RateLimitError(limit_info or {})
    
    return True


def rate_limit(endpoint: str):
    """Factory for rate limit dependencies"""
    async def _rate_limit_check(
        request: Request,
        rate_limiter=Depends(get_rate_limiter_instance)
    ) -> bool:
        return await check_rate_limit(request, endpoint, rate_limiter)
    return _rate_limit_check


@router.post("/api/search/username", response_model=SearchResponse)
async def search_username(
    request: Request,
    search_request: UsernameSearchRequest,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    username_service: UsernameEnumerationService = Depends(get_username_service),
    cache_manager: CacheManager = Depends(get_cache_manager),
    db_manager: DatabaseManager = Depends(get_db_manager),
    rate_ok: bool = Depends(rate_limit("/api/search/username"))
):
    """
    Primary endpoint for username enumeration.
    
    - Input: {username, email (optional), phone (optional)}
    - Output: {results: [{platform, profile_url, confidence, match_type}]}
    - Uses exact + fuzzy + pattern matching
    - Returns all matches sorted by confidence
    """
    start_time = time.time()
    username = search_request.username
    
    try:
        # Generate cache key
        cache_key = cache_manager.get_cache_key_for_search(
            'username_search',
            username=username,
            email=search_request.email,
            phone=search_request.phone
        )
        
        # Check cache
        cached_result = await cache_manager.get(cache_key)
        if cached_result:
            logger.info(f"Cache hit for username search: {username}")
            
            # Update analytics
            if db_manager.postgresql:
                await db_manager.postgresql.update_analytics(
                    datetime.utcnow(),
                    'username_search',
                    int((time.time() - start_time) * 1000),
                    success=True,
                    cache_hit=True
                )
            
            return SearchResponse(**cached_result)
        
        # Perform enumeration
        logger.info(f"Starting username enumeration for: {username}")
        
        results = await username_service.enumerate_username(
            username=username,
            email=search_request.email,
            phone=search_request.phone
        )
        
        # Apply pagination
        total_count = len(results)
        start_idx = (page - 1) * page_size
        end_idx = min(start_idx + page_size, total_count)
        paged_results = results[start_idx:end_idx]
        
        # Convert to PlatformResult objects
        platform_results = [
            PlatformResult(
                platform=result.platform_name,
                profile_url=result.profile_url,
                confidence=result.confidence,
                match_type=result.match_type,
                metadata=result.metadata,
                discovered_at=datetime.utcnow()
            )
            for result in paged_results
        ]
        
        execution_time_ms = int((time.time() - start_time) * 1000)
        
        # Prepare response
        response = SearchResponse(
            results=platform_results,
            total_count=total_count,
            page=page,
            page_size=page_size,
            execution_time_ms=execution_time_ms,
            cached=False
        )
        
        # Cache the result
        await cache_manager.set(cache_key, response.dict(), ttl=3600)  # 1 hour TTL
        
        # Log to database
        if db_manager.postgresql:
            await db_manager.log_complete_search(
                search_type='username_search',
                query_params=search_request.dict(),
                results=[{
                    'username': r.username,
                    'platform': r.platform_name,
                    'profile_url': r.profile_url,
                    'confidence': r.confidence,
                    'match_type': r.match_type,
                    'metadata': r.metadata
                } for r in results],
                execution_time_ms=execution_time_ms,
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get('user-agent'),
                cache_hit=False
            )
        
        logger.info(f"Username search completed for {username}: {total_count} results found")
        return response
        
    except Exception as e:
        logger.error(f"Username search failed: {e}")
        
        # Update analytics
        if db_manager.postgresql:
            await db_manager.postgresql.update_analytics(
                datetime.utcnow(),
                'username_search',
                int((time.time() - start_time) * 1000),
                success=False
            )
        
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error="Search failed",
                message=str(e),
                timestamp=datetime.utcnow(),
                request_id=str(request.url)
            ).dict()
        )


@router.post("/api/search/reverse-lookup", response_model=ReverseLookupResponse)
async def reverse_lookup(
    request: Request,
    lookup_request: ReverseLookupRequest,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    username_service: UsernameEnumerationService = Depends(get_username_service),
    cache_manager: CacheManager = Depends(get_cache_manager),
    db_manager: DatabaseManager = Depends(get_db_manager),
    rate_ok: bool = Depends(lambda req: check_rate_limit(req, "/api/search/reverse-lookup"))
):
    """
    Search by email or phone to find associated usernames.
    
    - Input: {email or phone}
    - Output: {usernames: [{username, platforms}]}
    - Extracts name patterns, searches for variations
    """
    start_time = time.time()
    
    try:
        # Generate cache key
        cache_key = cache_manager.get_cache_key_for_search(
            'reverse_lookup',
            email=lookup_request.email,
            phone=lookup_request.phone
        )
        
        # Check cache
        cached_result = await cache_manager.get(cache_key)
        if cached_result:
            logger.info(f"Cache hit for reverse lookup")
            
            if db_manager.postgresql:
                await db_manager.postgresql.update_analytics(
                    datetime.utcnow(),
                    'reverse_lookup',
                    int((time.time() - start_time) * 1000),
                    success=True,
                    cache_hit=True
                )
            
            return ReverseLookupResponse(**cached_result)
        
        # Perform reverse lookup
        logger.info(f"Starting reverse lookup")
        
        results = await username_service.reverse_lookup(
            email=lookup_request.email,
            phone=lookup_request.phone
        )
        
        execution_time_ms = int((time.time() - start_time) * 1000)
        
        # Prepare response
        response = ReverseLookupResponse(
            usernames=results,
            total_count=len(results),
            execution_time_ms=execution_time_ms
        )
        
        # Cache the result
        await cache_manager.set(cache_key, response.dict(), ttl=3600)
        
        # Log to database
        if db_manager.postgresql:
            await db_manager.log_complete_search(
                search_type='reverse_lookup',
                query_params=lookup_request.dict(),
                results=results,
                execution_time_ms=execution_time_ms,
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get('user-agent'),
                cache_hit=False
            )
        
        logger.info(f"Reverse lookup completed: {len(results)} usernames found")
        return response
        
    except Exception as e:
        logger.error(f"Reverse lookup failed: {e}")
        
        if db_manager.postgresql:
            await db_manager.postgresql.update_analytics(
                datetime.utcnow(),
                'reverse_lookup',
                int((time.time() - start_time) * 1000),
                success=False
            )
        
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error="Reverse lookup failed",
                message=str(e),
                timestamp=datetime.utcnow(),
                request_id=str(request.url)
            ).dict()
        )


@router.post("/api/search/fuzzy-match", response_model=FuzzyMatchResponse)
async def fuzzy_match_search(
    request: Request,
    fuzzy_request: FuzzyMatchRequest,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    username_service: UsernameEnumerationService = Depends(get_username_service),
    cache_manager: CacheManager = Depends(get_cache_manager),
    db_manager: DatabaseManager = Depends(get_db_manager),
    rate_ok: bool = Depends(lambda req: check_rate_limit(req, "/api/search/fuzzy-match"))
):
    """
    Fuzzy search with configurable tolerance.
    
    - Input: {username, tolerance_level: low|medium|high}
    - Output: exact + similar matches across all platforms
    """
    start_time = time.time()
    
    try:
        # Generate cache key
        cache_key = cache_manager.get_cache_key_for_search(
            'fuzzy_match',
            username=fuzzy_request.username,
            tolerance=fuzzy_request.tolerance_level
        )
        
        # Check cache
        cached_result = await cache_manager.get(cache_key)
        if cached_result:
            logger.info(f"Cache hit for fuzzy match: {fuzzy_request.username}")
            
            if db_manager.postgresql:
                await db_manager.postgresql.update_analytics(
                    datetime.utcnow(),
                    'fuzzy_match',
                    int((time.time() - start_time) * 1000),
                    success=True,
                    cache_hit=True
                )
            
            return FuzzyMatchResponse(**cached_result)
        
        # Perform fuzzy search
        logger.info(f"Starting fuzzy match for: {fuzzy_request.username}")
        
        results = await username_service.fuzzy_match_search(
            username=fuzzy_request.username,
            tolerance=fuzzy_request.tolerance_level
        )
        
        # Apply pagination
        total_count = len(results)
        start_idx = (page - 1) * page_size
        end_idx = min(start_idx + page_size, total_count)
        paged_results = results[start_idx:end_idx]
        
        # Convert to PlatformResult objects
        platform_results = [
            PlatformResult(
                platform=result.platform_name,
                profile_url=result.profile_url,
                confidence=result.confidence,
                match_type=result.match_type,
                metadata=result.metadata,
                discovered_at=datetime.utcnow()
            )
            for result in paged_results
        ]
        
        execution_time_ms = int((time.time() - start_time) * 1000)
        
        # Prepare response
        response = FuzzyMatchResponse(
            original_username=fuzzy_request.username,
            matches=platform_results,
            total_count=total_count,
            execution_time_ms=execution_time_ms
        )
        
        # Cache the result
        await cache_manager.set(cache_key, response.dict(), ttl=3600)
        
        # Log to database
        if db_manager.postgresql:
            await db_manager.log_complete_search(
                search_type='fuzzy_match',
                query_params=fuzzy_request.dict(),
                results=[{
                    'username': r.username,
                    'platform': r.platform_name,
                    'profile_url': r.profile_url,
                    'confidence': r.confidence,
                    'match_type': r.match_type,
                    'metadata': r.metadata
                } for r in results],
                execution_time_ms=execution_time_ms,
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get('user-agent'),
                cache_hit=False
            )
        
        logger.info(f"Fuzzy match completed for {fuzzy_request.username}: {total_count} results")
        return response
        
    except Exception as e:
        logger.error(f"Fuzzy match failed: {e}")
        
        if db_manager.postgresql:
            await db_manager.postgresql.update_analytics(
                datetime.utcnow(),
                'fuzzy_match',
                int((time.time() - start_time) * 1000),
                success=False
            )
        
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error="Fuzzy match failed",
                message=str(e),
                timestamp=datetime.utcnow(),
                request_id=str(request.url)
            ).dict()
        )


@router.get("/api/results/username/{username}")
async def get_username_results(
    request: Request,
    username: str,
    include_metadata: bool = Query(True),
    username_service: UsernameEnumerationService = Depends(get_username_service),
    db_manager: DatabaseManager = Depends(get_db_manager),
    rate_ok: bool = Depends(lambda req: check_rate_limit(req, "/api/results/username"))
):
    """
    Get detailed results for a username.
    
    - Output: all platforms found, confidence scores, linked identities
    """
    start_time = time.time()
    
    try:
        logger.info(f"Getting detailed results for: {username}")
        
        # Perform enumeration to get fresh results
        results = await username_service.enumerate_username(username=username)
        
        execution_time_ms = int((time.time() - start_time) * 1000)
        
        # Get identity data from database
        identity_data = None
        if db_manager.postgresql:
            identity_data = await db_manager.postgresql.get_identity_data(username)
        
        response_data = {
            "username": username,
            "results_count": len(results),
            "platforms": {},
            "execution_time_ms": execution_time_ms
        }
        
        # Group results by platform
        for result in results:
            if result.platform_name not in response_data["platforms"]:
                response_data["platforms"][result.platform_name] = []
            
            result_data = {
                "profile_url": result.profile_url,
                "confidence": result.confidence,
                "match_type": result.match_type,
                "discovered_at": datetime.utcnow().isoformat()
            }
            
            if include_metadata and result.metadata:
                result_data["metadata"] = result.metadata
            
            response_data["platforms"][result.platform_name].append(result_data)
        
        if identity_data:
            response_data["identity_data"] = identity_data
        
        logger.info(f"Detailed results retrieved for {username}")
        return response_data
        
    except Exception as e:
        logger.error(f"Failed to get username results: {e}")
        
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error="Failed to get results",
                message=str(e),
                timestamp=datetime.utcnow(),
                request_id=str(request.url)
            ).dict()
        )


@router.get("/api/results/identity-chain/{username}")
async def get_identity_chain(
    request: Request,
    username: str,
    max_depth: int = Query(3, ge=1, le=5),
    username_service: UsernameEnumerationService = Depends(get_username_service),
    db_manager: DatabaseManager = Depends(get_db_manager),
    rate_ok: bool = Depends(lambda req: check_rate_limit(req, "/api/results/identity-chain"))
):
    """
    Get identity connection chains.
    
    - Output: username → email → platform → username chains
    """
    start_time = time.time()
    
    try:
        logger.info(f"Getting identity chain for: {username}")
        
        # Check Neo4j first
        neo4j_chain = None
        if db_manager.neo4j:
            neo4j_chain = await db_manager.neo4j.get_identity_chain(username)
        
        if neo4j_chain and neo4j_chain['chain_length'] > 0:
            execution_time_ms = int((time.time() - start_time) * 1000)
            neo4j_chain['execution_time_ms'] = execution_time_ms
            logger.info(f"Identity chain retrieved from Neo4j for {username}")
            return neo4j_chain
        
        # Fall back to building chain dynamically
        chain_data = await username_service.build_identity_chain(username)
        execution_time_ms = int((time.time() - start_time) * 1000)
        chain_data['execution_time_ms'] = execution_time_ms
        
        logger.info(f"Identity chain build completed for {username}")
        return chain_data
        
    except Exception as e:
        logger.error(f"Failed to get identity chain: {e}")
        
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error="Failed to get identity chain",
                message=str(e),
                timestamp=datetime.utcnow(),
                request_id=str(request.url)
            ).dict()
        )


@router.get("/api/search/stats")
async def get_search_stats(
    request: Request,
    db_manager: DatabaseManager = Depends(get_db_manager),
    days: int = Query(7, ge=1, le=90),
    rate_ok: bool = Depends(lambda req: check_rate_limit(req, "/api/search/stats"))
):
    """Get search statistics"""
    try:
        stats = {}
        
        if db_manager.postgresql:
            platform_stats = await db_manager.postgresql.get_platform_statistics(days)
            
            # Add analytics summary
            async with db_manager.postgresql.pool.acquire() as conn:
                analytics = await conn.fetch("""
                    SELECT 
                        search_type,
                        SUM(request_count) as total_requests,
                        AVG(average_response_time_ms) as avg_response_time,
                        SUM(success_count) as total_success,
                        SUM(error_count) as total_errors,
                        AVG(cache_hit_rate) as avg_cache_hit_rate
                    FROM search_analytics
                    WHERE date >= NOW() - INTERVAL '1 day' * $1
                    GROUP BY search_type
                """, days)
                
                stats['analytics'] = [dict(row) for row in analytics]
            
            stats['platform_statistics'] = platform_stats
        
        return stats
        
    except Exception as e:
        logger.error(f"Failed to get search stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.websocket("/api/ws/search/{search_id}")
async def websocket_search_progress(websocket: WebSocket, search_id: str):
    """
    WebSocket endpoint for real-time search progress updates

    Clients can connect to receive live updates about search progress including:
    - Current progress percentage
    - Platforms completed
    - Number of results found
    - Search status (running, completed, failed)

    Client can send messages:
    - {"action": "get_status"} - Request current status
    - {"action": "cancel"} - Cancel the search
    """
    await handle_websocket_connection(websocket, search_id)


@router.post("/api/export/username")
async def export_username_results(
    username: str,
    format: str = Query(ExportFormat.JSON, regex="^(json|csv)$"),
    include_metadata: bool = Query(True),
    username_service: UsernameEnumerationService = Depends(get_username_service),
    db_manager: DatabaseManager = Depends(get_db_manager),
    rate_ok: bool = Depends(lambda req: check_rate_limit(req, "/api/export"))
):
    """
    Export username enumeration results to JSON or CSV format

    - format: "json" or "csv"
    - include_metadata: Include platform metadata in export
    """
    try:
        exporter = get_exporter()

        # Get results
        results = await username_service.enumerate_username(username=username)

        # Convert to dict format
        results_dict = [
            {
                'username': username,
                'platform': result.platform_name,
                'profile_url': result.profile_url,
                'confidence': result.confidence,
                'match_type': result.match_type,
                'metadata': result.metadata,
                'discovered_at': result.metadata.get('discovered_at', datetime.utcnow()).isoformat() if result.metadata else None
            }
            for result in results
        ]

        # Export based on format
        if format == ExportFormat.JSON:
            return await exporter.create_json_response(
                results_dict,
                metadata={
                    'username': username,
                    'exported_at': datetime.utcnow().isoformat(),
                    'total_results': len(results)
                },
                filename=f"{username}_results.json"
            )
        else:  # CSV
            return await exporter.create_csv_response(
                results_dict,
                include_metadata=include_metadata,
                filename=f"{username}_results.csv"
            )

    except Exception as e:
        logger.error(f"Export failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/export/identity-chain")
async def export_identity_chain(
    username: str,
    format: str = Query(ExportFormat.JSON, regex="^(json|csv)$"),
    username_service: UsernameEnumerationService = Depends(get_username_service),
    db_manager: DatabaseManager = Depends(get_db_manager),
    rate_ok: bool = Depends(lambda req: check_rate_limit(req, "/api/export"))
):
    """
    Export identity chain to JSON or CSV format

    - format: "json" or "csv"
    """
    try:
        exporter = get_exporter()

        # Get identity chain
        chain_data = await username_service.build_identity_chain(username)

        # Export based on format
        return await exporter.create_identity_chain_response(
            chain_data,
            format=format,
            filename=f"{username}_identity_chain"
        )

    except Exception as e:
        logger.error(f"Identity chain export failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check(
    db_manager: DatabaseManager = Depends(get_db_manager),
):
    """Health check endpoint for the username enumeration API"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {}
    }

    # Check PostgreSQL
    if db_manager.postgresql:
        try:
            async with db_manager.postgresql.pool.acquire() as conn:
                await conn.execute("SELECT 1")
                health_status["services"]["postgresql"] = "connected"
        except:
            health_status["services"]["postgresql"] = "disconnected"
            health_status["status"] = "degraded"

    # Check Neo4j
    if db_manager.neo4j:
        try:
            async with db_manager.neo4j.driver.session() as session:
                await session.run("RETURN 1")
                health_status["services"]["neo4j"] = "connected"
        except:
            health_status["services"]["neo4j"] = "disconnected"
            health_status["status"] = "degraded"

    return health_status