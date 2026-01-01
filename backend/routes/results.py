from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, Request, Query, HTTPException
import logging

from .username_enum import get_username_service, get_db_manager
from ..services.username_enum_service import UsernameEnumerationService
from ..utils.database import DatabaseManager

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/api/results")
async def get_all_results(
    query: str = Query(...),
    db_manager: DatabaseManager = Depends(get_db_manager)
):
    """
    Get aggregated results for a specific query from all modules
    """
    results = {}
    
    # Get username enumeration results from database
    if db_manager.postgresql:
        username_results = await db_manager.postgresql.get_search_history(
            search_type="username_search"
        )
        # Filter by query if needed, or get specific results
        # For now, let's just return what we have for this username
        results["username_enumeration"] = [
            r for r in username_results if r.get('query_params', {}).get('username') == query
        ]
        
    return {
        "query": query,
        "results": results
    }
