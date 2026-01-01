from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime
from loguru import logger
import asyncio

from backend.modules.adult_sites import adult_site_scraper
from backend.modules.personals_sites import personals_site_scraper
from backend.models.database import get_async_db, AsyncSessionLocal
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(
    prefix="/api",
    tags=["adult_personals"]
)

class SearchRequest(BaseModel):
    target: str
    platforms: Optional[List[str]] = None
    sites: Optional[List[str]] = None

class ContactInfoRequest(BaseModel):
    contact_info: str

@router.post("/search/adult-sites")
async def search_adult_sites(request: SearchRequest):
    """Search for target across adult platforms"""
    try:
        logger.info(f"Searching adult sites for: {request.target}")
        
        results = await adult_site_scraper.search_adult_sites(
            target=request.target,
            platforms=request.platforms
        )
        
        return {
            "success": True,
            "target": request.target,
            "results": results,
            "count": len(results)
        }
        
    except Exception as e:
        logger.error(f"Error searching adult sites: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/search/personals-sites")
async def search_personals_sites(request: SearchRequest):
    """Search for target across personals platforms"""
    try:
        logger.info(f"Searching personals sites for: {request.target}")
        
        results = await personals_site_scraper.search_personals_sites(
            target=request.target,
            sites=request.sites
        )
        
        return {
            "success": True,
            "target": request.target,
            "results": results,
            "count": len(results)
        }
        
    except Exception as e:
        logger.error(f"Error searching personals sites: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/results/adult-profiles/{identity_id}")
async def get_adult_profiles(identity_id: int):
    """Retrieve all adult platform profiles linked to an identity"""
    try:
        logger.info(f"Getting adult profiles for identity: {identity_id}")
        
        results = await adult_site_scraper.get_adult_profiles_by_identity(identity_id)
        
        return {
            "success": True,
            "identity_id": identity_id,
            "results": results,
            "count": len(results)
        }
        
    except Exception as e:
        logger.error(f"Error getting adult profiles: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/results/personals-posts/{identity_id}")
async def get_personals_posts(identity_id: int):
    """Retrieve all personals posts linked to an identity"""
    try:
        logger.info(f"Getting personals posts for identity: {identity_id}")
        
        results = await personals_site_scraper.get_personals_posts_by_identity(identity_id)
        
        return {
            "success": True,
            "identity_id": identity_id,
            "results": results,
            "count": len(results)
        }
        
    except Exception as e:
        logger.error(f"Error getting personals posts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/search/contact-info")
async def search_contact_info(request: ContactInfoRequest):
    """Search by phone/email to find associated personals posts and profiles"""
    try:
        logger.info(f"Searching by contact info: {request.contact_info}")
        
        # Search adult sites
        adult_results = await adult_site_scraper.search_by_contact_info(request.contact_info)
        
        # Search personals sites
        personals_results = await personals_site_scraper.search_by_contact_info(request.contact_info)
        
        return {
            "success": True,
            "contact_info": request.contact_info,
            "adult_profiles": adult_results,
            "personals_posts": personals_results,
            "total_results": len(adult_results) + len(personals_results)
        }
        
    except Exception as e:
        logger.error(f"Error searching by contact info: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/results/linked-identities/{identity_id}")
async def get_linked_identities(identity_id: int):
    """Return all alternate usernames/identities discovered on adult/personals sites"""
    try:
        logger.info(f"Getting linked identities for: {identity_id}")
        
        # Get linked identities from adult sites
        adult_identities = await adult_site_scraper.get_linked_identities(identity_id)
        
        # Get linked identities from personals sites
        personals_identities = await personals_site_scraper.get_linked_identities(identity_id)
        
        # Combine and deduplicate
        all_identities = adult_identities + personals_identities
        unique_identities = []
        seen = set()
        
        for identity in all_identities:
            identity_key = (identity['linked_account'] if 'linked_account' in identity else identity['contact_info'], identity['source'])
            if identity_key not in seen:
                seen.add(identity_key)
                unique_identities.append(identity)
        
        return {
            "success": True,
            "identity_id": identity_id,
            "results": unique_identities,
            "count": len(unique_identities)
        }
        
    except Exception as e:
        logger.error(f"Error getting linked identities: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "adult_personals_api"
    }

@router.get("/stats")
async def get_stats():
    """Get statistics about the adult/personals data"""
    try:
        async with AsyncSessionLocal() as session:
            # Get adult profiles count
            adult_profiles_result = await session.execute("SELECT COUNT(*) FROM adult_profiles WHERE is_active = TRUE")
            adult_profiles_count = adult_profiles_result.scalar()
            
            # Get personals posts count
            personals_posts_result = await session.execute("SELECT COUNT(*) FROM personals_posts WHERE is_active = TRUE")
            personals_posts_count = personals_posts_result.scalar()
            
            # Get identities count
            identities_result = await session.execute("SELECT COUNT(*) FROM identities WHERE is_active = TRUE")
            identities_count = identities_result.scalar()
            
            return {
                "success": True,
                "stats": {
                    "adult_profiles": adult_profiles_count,
                    "personals_posts": personals_posts_count,
                    "identities": identities_count,
                    "total_records": adult_profiles_count + personals_posts_count + identities_count
                }
            }
            
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Integration with core search would be handled in the main search module
# This would involve adding adult/personals search to the main search endpoint