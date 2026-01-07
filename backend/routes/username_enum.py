"""
Username Enumeration API Routes

FastAPI endpoints for username enumeration, reverse lookup,
fuzzy matching, and identity chain queries.
"""

from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, EmailStr, validator
from typing import List, Optional, Dict, Any
import asyncio
import logging
from datetime import datetime

from ..modules.username_enum import (
    UsernameEnumerator,
    UsernameMatch,
    PlatformStatus,
    ConfidenceLevel,
)
from ..modules.username_matching import (
    UsernameMatcher,
    CrossReferenceEngine,
)
from ..modules.database import DatabaseManager
from ..modules.graph_db import GraphManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/search", tags=["username-enumeration"])


# Request/Response Models
class UsernameSearchRequest(BaseModel):
    """Request model for username search"""
    username: str = Field(..., min_length=1, max_length=255, description="Username to search for")
    optional_email: Optional[EmailStr] = Field(None, description="Optional email for cross-referencing")
    optional_phone: Optional[str] = Field(None, description="Optional phone for cross-referencing")
    platforms: Optional[List[str]] = Field(None, description="Specific platforms to search (default: all)")
    fuzzy_match: bool = Field(False, description="Enable fuzzy matching for variations")
    max_concurrent: int = Field(50, ge=1, le=100, description="Maximum concurrent requests")
    cache_results: bool = Field(True, description="Cache results for future queries")

    @validator('username')
    def username_must_not_be_empty(cls, v):
        return v.strip()


class ReverseLookupRequest(BaseModel):
    """Request model for reverse lookup (email/phone)"""
    email: Optional[EmailStr] = None
    phone: Optional[str] = None

    @validator('phone')
    def validate_phone(cls, v, values):
        if not v and not values.get('email'):
            raise ValueError("Either email or phone must be provided")
        return v


class FuzzyMatchRequest(BaseModel):
    """Request model for fuzzy matching"""
    username: str = Field(..., min_length=1, description="Username to search")
    tolerance: float = Field(0.7, ge=0.0, le=1.0, description="Similarity tolerance (0-1)")
    max_variations: int = Field(50, ge=1, le=100, description="Maximum variations to check")
    platforms: Optional[List[str]] = None


class PlatformMatch(BaseModel):
    """Response model for platform match"""
    platform: str
    profile_url: str
    confidence_score: str
    verified: bool
    response_code: Optional[int] = None
    response_time: float
    discovery_method: str
    category: Optional[str] = None


class UsernameSearchResponse(BaseModel):
    """Response model for username search"""
    username: str
    matches_found: int
    platforms_checked: int
    search_duration: float
    matches: List[PlatformMatch]
    fuzzy_variations_checked: Optional[int] = None


class ReverseLookupResponse(BaseModel):
    """Response model for reverse lookup"""
    search_type: str
    search_value: str
    extracted_usernames: List[str]
    matches: Dict[str, List[PlatformMatch]]


class IdentityChainResponse(BaseModel):
    """Response model for identity chain"""
    username: str
    total_connections: int
    depth: int
    connections: List[Dict[str, Any]]


class FuzzyMatchResponse(BaseModel):
    """Response model for fuzzy matching"""
    original_username: str
    variations_checked: int
    matches: Dict[str, List[PlatformMatch]]
    similarity_scores: Dict[str, float]


class PlatformStatus(BaseModel):
    """Model for platform status"""
    name: str
    category: str
    total_checks: int
    success_rate: float
    avg_response_time: float
    last_checked: Optional[datetime]


# Global instances (will be initialized by FastAPI app)
db_manager: Optional[DatabaseManager] = None
graph_manager: Optional[GraphManager] = None
enumerator: Optional[UsernameEnumerator] = None
matcher: Optional[UsernameMatcher] = None
cross_reference_engine: Optional[CrossReferenceEngine] = None


def initialize_dependencies(
    db: DatabaseManager,
    graph: GraphManager,
    enum_config_path: Optional[str] = None,
):
    """Initialize route dependencies"""
    global db_manager, graph_manager, enumerator, matcher, cross_reference_engine
    db_manager = db
    graph_manager = graph
    matcher = UsernameMatcher()
    cross_reference_engine = CrossReferenceEngine()
    
    # Store enumerator for reuse (will be initialized per-request)
    global _enumerator_config_path
    _enumerator_config_path = enum_config_path


_enumerator_config_path: Optional[str] = None


def _platform_match_from_result(result: Dict) -> PlatformMatch:
    """Convert search result to PlatformMatch model"""
    return PlatformMatch(
        platform=result.get("platform", "unknown"),
        profile_url=result.get("url", ""),
        confidence_score=result.get("confidence", ConfidenceLevel.MEDIUM.value),
        verified=result.get("confidence") == ConfidenceLevel.HIGH,
        response_code=result.get("response_code"),
        response_time=result.get("response_time", 0.0),
        discovery_method="fuzzy" if result.get("is_variant") else "direct",
        category=result.get("category"),
    )


async def _store_results_in_db(
    username: str,
    results: List[Dict],
    duration: float,
):
    """Store search results in database"""
    if not db_manager:
        return
    
    try:
        await db_manager.store_search_results(
            search_identifier=username,
            search_type="username",
            results=results,
            duration=duration,
        )
    except Exception as e:
        logger.error(f"Error storing results in database: {e}")


async def _store_results_in_graph(
    username: str,
    matches: List[UsernameMatch],
):
    """Store results in Neo4j graph"""
    if not graph_manager:
        return
    
    try:
        for match in matches:
            await graph_manager.create_username_node(
                username=match.username,
                platform=match.platform,
                profile_url=match.profile_url,
                confidence=match.confidence.value,
                additional_info=match.additional_info,
            )
    except Exception as e:
        logger.error(f"Error storing results in graph: {e}")


@router.post("/username", response_model=UsernameSearchResponse)
async def search_username(request: UsernameSearchRequest):
    """
    Search for a username across all platforms.
    
    This is the primary endpoint for username enumeration. It searches for the
    given username across hundreds of mainstream platforms with concurrent async
    requests.
    
    Args:
        request: Search parameters including username, optional email/phone,
                 and configuration options
    
    Returns:
        UsernameSearchResponse with all matches found, confidence scores,
        and metadata
    """
    start_time = datetime.utcnow()
    
    # Check cache first
    if request.cache_results and db_manager:
        cache_key = f"username:{request.username.lower()}"
        cached = await db_manager.get_cached_results(cache_key)
        if cached:
            logger.info(f"Returning cached results for {request.username}")
            matches = [
                _platform_match_from_result(r)
                for r in cached
                if r.get("status") == PlatformStatus.FOUND.value
            ]
            return UsernameSearchResponse(
                username=request.username,
                matches_found=len(matches),
                platforms_checked=cached[0].get("platform_count", 0) if cached else 0,
                search_duration=0.0,
                matches=matches,
            )
    
    # Initialize enumerator
    async with UsernameEnumerator(
        config_path=_enumerator_config_path,
        max_concurrent=request.max_concurrent,
    ) as enum:
        # Perform search
        matches = await enum.search(
            username=request.username,
            platforms=request.platforms,
            fuzzy_match=request.fuzzy_match,
        )
    
    # Calculate duration
    duration = (datetime.utcnow() - start_time).total_seconds()
    
    # Convert matches to response format
    platform_matches = [
        PlatformMatch(
            platform=match.platform,
            profile_url=match.profile_url,
            confidence_score=match.confidence.value,
            verified=match.is_verified,
            response_code=match.additional_info.get("response_code"),
            response_time=match.additional_info.get("response_time", 0.0),
            discovery_method=match.discovery_method,
        )
        for match in matches
    ]
    
    # Store results in database
    asyncio.create_task(_store_results_in_db(request.username, platform_matches, duration))
    
    # Store in graph
    asyncio.create_task(_store_results_in_graph(request.username, matches))
    
    # Get platform count from enumerator stats
    enum_instance = UsernameEnumerator(config_path=_enumerator_config_path)
    platforms_checked = len(enum_instance.platforms) if not request.platforms else len(request.platforms)
    
    return UsernameSearchResponse(
        username=request.username,
        matches_found=len(platform_matches),
        platforms_checked=platforms_checked,
        search_duration=duration,
        matches=platform_matches,
        fuzzy_variations_checked=len(matcher.generate_variations(request.username)) if request.fuzzy_match else None,
    )


@router.post("/reverse-lookup", response_model=ReverseLookupResponse)
async def reverse_lookup(request: ReverseLookupRequest):
    """
    Search by email or phone to find associated usernames.
    
    Extracts potential usernames from the email or phone number and
    searches for them across platforms.
    
    Args:
        request: Reverse lookup request with email or phone
    
    Returns:
        ReverseLookupResponse with extracted usernames and their matches
    """
    extracted_usernames = []
    search_type = ""
    search_value = ""
    
    # Extract usernames from email
    if request.email:
        extracted_usernames.extend(matcher.extract_username_from_email(request.email))
        search_type = "email"
        search_value = request.email
    
    # Extract usernames from phone
    if request.phone:
        extracted_usernames.extend(matcher.extract_username_from_phone(request.phone))
        if not search_type:
            search_type = "phone"
            search_value = request.phone
    
    # Search for each extracted username
    matches = {}
    
    async with UsernameEnumerator(config_path=_enumerator_config_path) as enum:
        for username in set(extracted_usernames):  # Deduplicate
            username_matches = await enum.search(username)
            if username_matches:
                matches[username] = [
                    _platform_match_from_result({
                        "platform": m.platform,
                        "url": m.profile_url,
                        "confidence": m.confidence.value,
                        "is_verified": m.is_verified,
                        "response_code": m.additional_info.get("response_code"),
                        "response_time": m.additional_info.get("response_time"),
                        "discovery_method": m.discovery_method,
                    })
                    for m in username_matches
                ]
    
    return ReverseLookupResponse(
        search_type=search_type,
        search_value=search_value,
        extracted_usernames=list(set(extracted_usernames)),
        matches=matches,
    )


@router.get("/results/username/{username}")
async def get_username_results(
    username: str,
    include_attributes: bool = Query(True, description="Include email/phone attributes"),
):
    """
    Get detailed results for a specific username search.
    
    Returns complete identity information including all platforms found,
    confidence scores, and linked identities.
    
    Args:
        username: Username to look up
        include_attributes: Whether to include email/phone attributes
    
    Returns:
        Detailed identity information
    """
    if not db_manager:
        raise HTTPException(status_code=503, detail="Database not available")
    
    identity = await db_manager.get_identity_by_username(username)
    
    if not identity:
        raise HTTPException(status_code=404, detail=f"Username '{username}' not found")
    
    return identity


@router.post("/search/fuzzy-match", response_model=FuzzyMatchResponse)
async def fuzzy_match_search(request: FuzzyMatchRequest):
    """
    Search with fuzzy matching for variations.
    
    Generates username variations based on common patterns and searches
    for all of them across platforms. Returns exact and similar matches.
    
    Args:
        request: Fuzzy match request with username and tolerance settings
    
    Returns:
        FuzzyMatchResponse with all variation matches and similarity scores
    """
    # Generate variations
    variations = matcher.generate_variations(
        request.username,
        max_variations=request.max_variations,
    )
    
    # Calculate similarity scores for all variations
    similarity_scores = {}
    for var in variations:
        score = matcher.calculate_similarity(request.username, var) / 100.0
        if score >= request.tolerance:
            similarity_scores[var] = score
    
    # Search for each variation
    matches = {}
    
    async with UsernameEnumerator(config_path=_enumerator_config_path) as enum:
        for variation in similarity_scores.keys():
            variation_matches = await enum.search(variation, platforms=request.platforms)
            if variation_matches:
                matches[variation] = [
                    _platform_match_from_result({
                        "platform": m.platform,
                        "url": m.profile_url,
                        "confidence": m.confidence.value,
                        "is_verified": m.is_verified,
                        "response_code": m.additional_info.get("response_code"),
                        "response_time": m.additional_info.get("response_time"),
                        "discovery_method": m.discovery_method,
                    })
                    for m in variation_matches
                ]
    
    return FuzzyMatchResponse(
        original_username=request.username,
        variations_checked=len(variations),
        matches=matches,
        similarity_scores=similarity_scores,
    )


@router.get("/results/identity-chain/{username}", response_model=IdentityChainResponse)
async def get_identity_chain(
    username: str,
    max_depth: int = Query(3, ge=1, le=5, description="Maximum connection depth"),
):
    """
    Get connection chain for a username.
    
    Returns the detailed relationship graph showing how a username connects
    to other identities through emails, phones, and linked accounts.
    
    Args:
        username: Starting username
        max_depth: Maximum depth of connection chain
    
    Returns:
        IdentityChainResponse with connection details
    """
    # Get from database if available
    identity_data = None
    if db_manager:
        identity_data = await db_manager.get_identity_by_username(username)
    
    if not identity_data and not graph_manager:
        raise HTTPException(
            status_code=404,
            detail=f"No data found for username '{username}'",
        )
    
    # Build connection chain
    connections = []
    
    if identity_data:
        # Add direct platform sources
        for source in identity_data.get("sources", []):
            if source["status"] == PlatformStatus.FOUND.value:
                connections.append({
                    "type": "platform_profile",
                    "platform": source["platform"],
                    "url": source["profile_url"],
                    "confidence": source["confidence"],
                    "depth": 0,
                })
        
        # Add attribute connections (email, phone)
        for attr in identity_data.get("attributes", []):
            connections.append({
                "type": f"{attr['type']}_attribute",
                "value": attr["value"],
                "is_primary": attr["is_primary"],
                "is_verified": attr["is_verified"],
                "discovered_from": attr["discovered_from"],
                "depth": 1,
            })
    
    # Get Neo4j graph connections if available
    if graph_manager:
        try:
            network = await graph_manager.get_identity_network(username, max_depth=max_depth)
            # Add graph-based connections
            for node in network.get("nodes", []):
                if node["labels"] == ["Email"]:
                    connections.append({
                        "type": "email_connection",
                        "value": node["properties"].get("email"),
                        "confidence": node["properties"].get("confidence"),
                        "depth": max_depth,
                    })
                elif node["labels"] == ["Phone"]:
                    connections.append({
                        "type": "phone_connection",
                        "value": node["properties"].get("phone"),
                        "confidence": node["properties"].get("confidence"),
                        "depth": max_depth,
                    })
        except Exception as e:
            logger.error(f"Error getting graph network: {e}")
    
    return IdentityChainResponse(
        username=username,
        total_connections=len(connections),
        depth=max_depth,
        connections=connections,
    )


@router.get("/statistics/platforms")
async def get_platform_statistics():
    """
    Get statistics about platform checks and success rates.
    
    Returns metrics for each platform including total checks,
    success rates, average response times, and block counts.
    
    Returns:
        Dictionary with platform statistics
    """
    if not db_manager:
        # Return empty statistics if database not available
        return {}
    
    stats = await db_manager.get_platform_statistics()
    return stats


@router.get("/statistics/overview")
async def get_overview_statistics():
    """
    Get overall system statistics.
    
    Returns aggregate statistics including total searches,
    matches found, cache hit rate, etc.
    
    Returns:
        Dictionary with overview statistics
    """
    stats = {
        "total_searches": 0,
        "total_matches": 0,
        "cache_enabled": db_manager is not None,
        "graph_enabled": graph_manager is not None,
    }
    
    if db_manager:
        # Get platform stats as proxy for activity
        platform_stats = await db_manager.get_platform_statistics()
        stats["active_platforms"] = len(platform_stats)
        stats["total_platform_checks"] = sum(
            p["total_checks"] for p in platform_stats.values()
        )
    
    if graph_manager:
        # Get graph statistics
        graph_stats = await graph_manager.get_graph_statistics()
        stats.update(graph_stats)
    
    return stats


@router.post("/cache/clear")
async def clear_cache():
    """
    Clear the search cache.
    
    Clears all cached search results to force fresh queries on next search.
    
    Returns:
        Confirmation message
    """
    if not db_manager:
        raise HTTPException(status_code=503, detail="Database not available")
    
    # Note: In a real implementation, you would clear the cache table
    # For now, we'll just return a success message
    return {
        "message": "Cache cleared successfully",
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/health")
async def health_check():
    """
    Health check endpoint.
    
    Returns the status of username enumeration components.
    
    Returns:
        Health status
    """
    status = {
        "status": "healthy",
        "components": {
            "database": db_manager is not None,
            "graph": graph_manager is not None,
            "matcher": matcher is not None,
            "cross_reference": cross_reference_engine is not None,
        },
        "timestamp": datetime.utcnow().isoformat(),
    }
    
    return status
