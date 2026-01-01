from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, Request, Query
import logging

from .username_enum import get_db_manager
from ..utils.database import DatabaseManager

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/api/graph/identity/{username}")
async def get_identity_graph(
    username: str,
    depth: int = Query(2, ge=1, le=5),
    db_manager: DatabaseManager = Depends(get_db_manager)
):
    """
    Get graph data for an identity network
    """
    if not db_manager.neo4j:
        return {"nodes": [], "edges": [], "error": "Neo4j not enabled"}
        
    async with db_manager.neo4j.driver.session() as session:
        # Cypher query to get the network
        result = await session.run("""
            MATCH (u:Username {value: $username})
            CALL apoc.path.subgraphAll(u, {maxDepth: $depth})
            YIELDS nodes, relationships
            RETURN nodes, relationships
        """, username=username, depth=depth)
        
        record = await result.single()
        if not record:
            return {"nodes": [], "edges": []}
            
        nodes = [{"id": str(n.id), "labels": list(n.labels), "properties": dict(n)} for n in record["nodes"]]
        edges = [{"id": str(r.id), "type": r.type, "start": str(r.start_node.id), "end": str(r.end_node.id), "properties": dict(r)} for r in record["relationships"]]
        
        return {"nodes": nodes, "edges": edges}
