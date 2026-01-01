from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, Request, Query
from pydantic import BaseModel
import logging

from .username_enum import get_username_service, check_rate_limit
from ..services.username_enum_service import UsernameEnumerationService

logger = logging.getLogger(__name__)
router = APIRouter()

class GeneralSearchRequest(BaseModel):
    query: str
    search_type: str = "all"  # all, username, email, phone
    metadata: Optional[Dict[str, Any]] = None

@router.post("/api/search")
async def general_search(
    request: Request,
    search_request: GeneralSearchRequest,
    username_service: UsernameEnumerationService = Depends(get_username_service),
    rate_ok: bool = Depends(lambda req: check_rate_limit(req, "/api/search"))
):
    """
    Unified search endpoint that delegates to specific modules based on search_type
    """
    results = {}
    
    # If search_type is 'all' or 'username', run username enumeration
    if search_request.search_type in ["all", "username"]:
        username_results = await username_service.enumerate_username(
            username=search_request.query
        )
        results["username_enumeration"] = username_results
        
    # In the future, other modules (social media, breach data, etc.) can be integrated here
    
    return {
        "query": search_request.query,
        "search_type": search_request.search_type,
        "results": results
    }
